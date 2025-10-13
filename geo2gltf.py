#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用地理数据转GLTF转换工具
支持 GeoJSON 和 Shapefile (SHP) 格式
支持点、线、面几何体的转换，添加默认高度，生成半透明材质
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, MultiLineString, MultiPoint
from pygltflib import GLTF2, Scene, Node, Mesh, Primitive, Accessor, BufferView, Buffer, Material, PbrMetallicRoughness
import struct
try:
    import mapbox_earcut
except ImportError:
    print("警告: mapbox-earcut库未找到，将使用简单三角化算法")
    mapbox_earcut = None

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Geo2GLTFConverter:
    """地理数据到GLTF转换器（支持 GeoJSON 和 Shapefile）"""
    
    def __init__(self, default_height: float = 5.0, auto_scale: bool = True):
        """
        初始化转换器
        
        Args:
            default_height: 默认高度（百分比）
            auto_scale: 是否自动缩放高度以保持合理比例
        """
        self.default_height = default_height
        self.auto_scale = auto_scale
        self.vertices = []
        self.indices = []
        self.current_index = 0
        self.bounds = None  # 存储所有几何体的边界框
        self.center_x = 0.0  # 数据中心点X坐标（用于平移到原点）
        self.center_z = 0.0  # 数据中心点Z坐标（用于平移到原点）
        self.scale_factor = 1.0  # 坐标缩放因子（经纬度转米）
        
    def detect_file_type(self, file_path: str) -> str:
        """
        检测输入文件类型
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件类型 ('geojson', 'shapefile', 或 'unknown')
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix in ['.geojson', '.json']:
            return 'geojson'
        elif suffix == '.shp':
            return 'shapefile'
        else:
            return 'unknown'
    
    def read_geofile(self, file_path: str) -> gpd.GeoDataFrame:
        """
        读取地理数据文件（自动检测 GeoJSON 或 Shapefile）
        
        Args:
            file_path: 文件路径
            
        Returns:
            GeoDataFrame: 地理数据框
        """
        file_type = self.detect_file_type(file_path)
        logger.info(f"正在读取 {file_type.upper()} 文件: {file_path}")
        
        try:
            if file_type == 'geojson':
                # GeoJSON 读取（无需处理编码问题，JSON默认UTF-8）
                gdf = gpd.read_file(file_path)
                logger.info("成功读取 GeoJSON 文件")
                
            elif file_type == 'shapefile':
                # Shapefile 读取（需要尝试不同编码）
                gdf = self._read_shapefile_with_encoding(file_path)
                logger.info("成功读取 Shapefile 文件")
                
            else:
                # 尝试自动检测
                logger.warning(f"未知文件类型，尝试自动检测...")
                gdf = gpd.read_file(file_path)
                logger.info("成功读取文件（自动检测）")
            
            logger.info(f"成功读取 {len(gdf)} 个几何对象")
            logger.info(f"几何类型: {gdf.geometry.geom_type.unique()}")
            
            # 检查坐标系统
            if gdf.crs:
                logger.info(f"坐标系统: {gdf.crs}")
            else:
                logger.warning("未检测到坐标系统信息")
            
            return gdf
            
        except Exception as e:
            logger.error(f"读取文件失败: {e}")
            raise
    
    def _read_shapefile_with_encoding(self, shp_path: str) -> gpd.GeoDataFrame:
        """
        使用多种编码方式读取 Shapefile
        
        Args:
            shp_path: Shapefile 路径
            
        Returns:
            GeoDataFrame: 地理数据框
        """
        # 尝试不同的编码方式读取SHP文件
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1', 'cp936']
        gdf = None
        
        for encoding in encodings:
            try:
                logger.info(f"尝试使用 {encoding} 编码读取 Shapefile")
                gdf = gpd.read_file(shp_path, encoding=encoding)
                logger.info(f"使用 {encoding} 编码成功读取文件")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if "codec can't decode" in str(e):
                    continue
                else:
                    raise e
        
        if gdf is None:
            logger.warning("所有编码尝试失败，使用默认方式读取（可能丢失属性数据）")
            # 最后尝试只读取几何数据
            gdf = gpd.read_file(shp_path, ignore_fields=['*'])
        
        return gdf
    
    def process_point(self, point: Point) -> List[float]:
        """
        处理点几何
        
        Args:
            point: 点对象
            
        Returns:
            List[float]: 顶点坐标列表
        """
        x, y = point.x, point.y
        # 创建一个小立方体来表示点
        size = 1.0
        vertices = []
        
        # 平移到原点并修正坐标系统，然后缩放到米制
        x_local = (x - self.center_x) * self.scale_factor
        z_local = -(y - self.center_z) * self.scale_factor  # 负号使得Z轴方向符合glTF标准
        
        # 立方体的8个顶点（Y轴向上）
        cube_vertices = [
            [x_local - size/2, 0, z_local - size/2],
            [x_local + size/2, 0, z_local - size/2],
            [x_local + size/2, 0, z_local + size/2],
            [x_local - size/2, 0, z_local + size/2],
            [x_local - size/2, self.default_height, z_local - size/2],
            [x_local + size/2, self.default_height, z_local - size/2],
            [x_local + size/2, self.default_height, z_local + size/2],
            [x_local - size/2, self.default_height, z_local + size/2],
        ]
        
        # 立方体的12个三角面（每个面2个三角形）
        cube_faces = [
            # 底面
            [0, 1, 2], [0, 2, 3],
            # 顶面
            [4, 6, 5], [4, 7, 6],
            # 前面
            [0, 4, 5], [0, 5, 1],
            # 后面
            [2, 6, 7], [2, 7, 3],
            # 左面
            [0, 3, 7], [0, 7, 4],
            # 右面
            [1, 5, 6], [1, 6, 2]
        ]
        
        # 添加顶点
        start_index = len(self.vertices) // 3
        for vertex in cube_vertices:
            self.vertices.extend(vertex)
        
        # 添加索引
        for face in cube_faces:
            for idx in face:
                self.indices.append(start_index + idx)
        
        return cube_vertices
    
    def process_linestring(self, linestring: LineString) -> List[float]:
        """
        处理线几何
        
        Args:
            linestring: 线对象
            
        Returns:
            List[float]: 顶点坐标列表
        """
        coords = list(linestring.coords)
        width = 0.5  # 线宽
        
        # 为线条创建带状几何体
        vertices = []
        start_index = len(self.vertices) // 3
        
        for i, (x, y) in enumerate(coords):
            # 平移到原点并翻转Z轴，然后缩放到米制
            x_local = (x - self.center_x) * self.scale_factor
            z_local = -(y - self.center_z) * self.scale_factor  # 负号使得Z轴方向符合glTF标准
            
            # 每个点创建8个顶点（矩形截面）
            vertices.extend([
                [x_local - width/2, 0, z_local - width/2],
                [x_local + width/2, 0, z_local - width/2],
                [x_local + width/2, 0, z_local + width/2],
                [x_local - width/2, 0, z_local + width/2],
                [x_local - width/2, self.default_height, z_local - width/2],
                [x_local + width/2, self.default_height, z_local - width/2],
                [x_local + width/2, self.default_height, z_local + width/2],
                [x_local - width/2, self.default_height, z_local + width/2]
            ])
        
        # 添加顶点到全局列表
        for vertex_group in vertices:
            for vertex in vertex_group:
                self.vertices.extend(vertex)
        
        # 连接相邻的矩形截面
        for i in range(len(coords) - 1):
            base_idx = start_index + i * 8
            next_idx = base_idx + 8
            
            # 连接底面
            self.indices.extend([
                base_idx, base_idx + 1, next_idx,
                base_idx + 1, next_idx + 1, next_idx,
                base_idx + 1, base_idx + 2, next_idx + 1,
                base_idx + 2, next_idx + 2, next_idx + 1,
                base_idx + 2, base_idx + 3, next_idx + 2,
                base_idx + 3, next_idx + 3, next_idx + 2,
                base_idx + 3, base_idx, next_idx + 3,
                base_idx, next_idx, next_idx + 3
            ])
            
            # 连接顶面
            base_idx_top = base_idx + 4
            next_idx_top = next_idx + 4
            
            self.indices.extend([
                base_idx_top, next_idx_top, base_idx_top + 1,
                base_idx_top + 1, next_idx_top, next_idx_top + 1,
                base_idx_top + 1, next_idx_top + 1, base_idx_top + 2,
                base_idx_top + 2, next_idx_top + 1, next_idx_top + 2,
                base_idx_top + 2, next_idx_top + 2, base_idx_top + 3,
                base_idx_top + 3, next_idx_top + 2, next_idx_top + 3,
                base_idx_top + 3, next_idx_top + 3, base_idx_top,
                base_idx_top, next_idx_top + 3, next_idx_top
            ])
        
        return vertices
    
    def process_polygon(self, polygon: Polygon) -> List[float]:
        """
        处理面几何
        
        Args:
            polygon: 面对象
            
        Returns:
            List[float]: 顶点坐标列表
        """
        exterior_coords = list(polygon.exterior.coords)[:-1]  # 去除重复的最后一个点
        
        logger.debug(f"处理多边形，顶点数量: {len(exterior_coords)}")
        
        # 检查多边形是否足够大以进行三角化
        if len(exterior_coords) < 3:
            logger.warning("多边形顶点数量少于3，跳过处理")
            return []
        
        # 三角化外环
        vertices = []
        start_index = len(self.vertices) // 3
        
        # 添加底面顶点（平移到原点，Y=0为底部，翻转Z轴，缩放到米制）
        bottom_vertices = []
        for x, y in exterior_coords:
            x_local = (x - self.center_x) * self.scale_factor
            z_local = -(y - self.center_z) * self.scale_factor  # 负号使得Z轴方向符合glTF标准
            bottom_vertices.append([x_local, 0, z_local])
            self.vertices.extend([x_local, 0, z_local])
        
        # 添加顶面顶点（Y=高度为顶部）
        top_vertices = []
        for x, y in exterior_coords:
            x_local = (x - self.center_x) * self.scale_factor
            z_local = -(y - self.center_z) * self.scale_factor  # 负号使得Z轴方向符合glTF标准
            top_vertices.append([x_local, self.default_height, z_local])
            self.vertices.extend([x_local, self.default_height, z_local])
        
        vertices = bottom_vertices + top_vertices
        n = len(exterior_coords)
        
        # 三角化底面和顶面
        if mapbox_earcut is not None:
            # 使用earcut进行三角化
            try:
                # 准备earcut所需的数据格式
                # mapbox_earcut 需要 (nverts, 2) 形状的二维数组
                coords_array = np.array(exterior_coords, dtype=np.float32)
                
                # 对于简单多边形（无洞），传入ring_end_indices表示外环结束位置
                ring_end_indices = np.array([len(exterior_coords)], dtype=np.uint32)
                
                # triangulate_float32 返回三角形索引数组
                triangle_indices = mapbox_earcut.triangulate_float32(coords_array, ring_end_indices)
                
                if len(triangle_indices) > 0:
                    # 添加底面三角形
                    for i in range(0, len(triangle_indices), 3):
                        idx0 = start_index + triangle_indices[i]
                        idx1 = start_index + triangle_indices[i + 1]
                        idx2 = start_index + triangle_indices[i + 2]
                        self.indices.extend([idx0, idx1, idx2])
                    
                    # 添加顶面三角形（逆时针）
                    for i in range(0, len(triangle_indices), 3):
                        idx0 = start_index + n + triangle_indices[i]
                        idx1 = start_index + n + triangle_indices[i + 2]  # 注意逆序
                        idx2 = start_index + n + triangle_indices[i + 1]  # 注意逆序
                        self.indices.extend([idx0, idx1, idx2])
                        
                    logger.debug(f"Earcut三角化成功，生成{len(triangle_indices)//3}个三角形")
                else:
                    logger.warning("Earcut返回空结果，使用简单三角化")
                    self._simple_triangulation(start_index, n)
                
            except Exception as e:
                logger.warning(f"Earcut三角化失败: {e}，回退到简单三角化")
                self._simple_triangulation(start_index, n)
        else:
            # 使用简单的扇形三角化
            logger.info("Earcut库未安装，使用简单扇形三角化")
            self._simple_triangulation(start_index, n)
        
        # 侧面
        for i in range(n):
            next_i = (i + 1) % n
            # 每个侧面两个三角形
            self.indices.extend([
                start_index + i, start_index + next_i, start_index + n + i,
                start_index + next_i, start_index + n + next_i, start_index + n + i
            ])
        
        return vertices
    
    def _simple_triangulation(self, start_index: int, n: int):
        """
        简单的扇形三角化（回退方案）
        
        Args:
            start_index: 起始索引
            n: 顶点数量
        """
        # 底面三角化（扇形三角化）
        for i in range(1, n - 1):
            self.indices.extend([start_index, start_index + i, start_index + i + 1])
        
        # 顶面三角化（逆时针）
        for i in range(1, n - 1):
            self.indices.extend([start_index + n, start_index + n + i + 1, start_index + n + i])
    
    def process_geometry(self, geometry):
        """
        处理几何对象
        
        Args:
            geometry: Shapely几何对象
        """
        if isinstance(geometry, Point):
            self.process_point(geometry)
        elif isinstance(geometry, MultiPoint):
            for point in geometry.geoms:
                self.process_point(point)
        elif isinstance(geometry, LineString):
            self.process_linestring(geometry)
        elif isinstance(geometry, MultiLineString):
            for linestring in geometry.geoms:
                self.process_linestring(linestring)
        elif isinstance(geometry, Polygon):
            self.process_polygon(geometry)
        elif isinstance(geometry, MultiPolygon):
            for polygon in geometry.geoms:
                self.process_polygon(polygon)
        else:
            logger.warning(f"不支持的几何类型: {type(geometry)}")
    
    def create_gltf(self, color: Tuple[float, float, float] = (1.0, 0.0, 0.0), 
                   alpha: float = 0.5) -> GLTF2:
        """
        创建GLTF对象
        
        Args:
            color: RGB颜色（0-1范围）
            alpha: 透明度（0-1范围）
            
        Returns:
            GLTF2: GLTF对象
        """
        logger.info("正在创建GLTF文件...")
        
        gltf = GLTF2()
        
        # 创建顶点数据缓冲区
        vertex_data = np.array(self.vertices, dtype=np.float32)
        vertex_buffer = vertex_data.tobytes()
        
        # 创建索引数据缓冲区
        index_data = np.array(self.indices, dtype=np.uint32)
        index_buffer = index_data.tobytes()
        
        # 合并缓冲区
        combined_buffer = vertex_buffer + index_buffer
        
        # 创建Buffer
        buffer = Buffer()
        buffer.byteLength = len(combined_buffer)
        buffer.uri = f"data:application/octet-stream;base64,{self._encode_base64(combined_buffer)}"
        gltf.buffers.append(buffer)
        
        # 创建BufferView for vertices
        vertex_buffer_view = BufferView()
        vertex_buffer_view.buffer = 0
        vertex_buffer_view.byteOffset = 0
        vertex_buffer_view.byteLength = len(vertex_buffer)
        vertex_buffer_view.target = 34962  # ARRAY_BUFFER
        gltf.bufferViews.append(vertex_buffer_view)
        
        # 创建BufferView for indices
        index_buffer_view = BufferView()
        index_buffer_view.buffer = 0
        index_buffer_view.byteOffset = len(vertex_buffer)
        index_buffer_view.byteLength = len(index_buffer)
        index_buffer_view.target = 34963  # ELEMENT_ARRAY_BUFFER
        gltf.bufferViews.append(index_buffer_view)
        
        # 创建Accessor for vertices
        vertex_accessor = Accessor()
        vertex_accessor.bufferView = 0
        vertex_accessor.componentType = 5126  # FLOAT
        vertex_accessor.count = len(self.vertices) // 3
        vertex_accessor.type = "VEC3"
        vertex_accessor.min = [float(vertex_data[i::3].min()) for i in range(3)]
        vertex_accessor.max = [float(vertex_data[i::3].max()) for i in range(3)]
        gltf.accessors.append(vertex_accessor)
        
        # 创建Accessor for indices
        index_accessor = Accessor()
        index_accessor.bufferView = 1
        index_accessor.componentType = 5125  # UNSIGNED_INT
        index_accessor.count = len(self.indices)
        index_accessor.type = "SCALAR"
        gltf.accessors.append(index_accessor)
        
        # 创建半透明材质
        material = Material()
        material.pbrMetallicRoughness = PbrMetallicRoughness()
        material.pbrMetallicRoughness.baseColorFactor = [color[0], color[1], color[2], alpha]
        material.pbrMetallicRoughness.metallicFactor = 0.0
        material.pbrMetallicRoughness.roughnessFactor = 0.5
        material.alphaMode = "BLEND"
        material.doubleSided = True
        gltf.materials.append(material)
        
        # 创建Primitive
        primitive = Primitive()
        primitive.attributes.POSITION = 0
        primitive.indices = 1
        primitive.material = 0
        
        # 创建Mesh
        mesh = Mesh()
        mesh.primitives.append(primitive)
        gltf.meshes.append(mesh)
        
        # 创建Node
        node = Node()
        node.mesh = 0
        gltf.nodes.append(node)
        
        # 创建Scene
        scene = Scene()
        scene.nodes.append(0)
        gltf.scenes.append(scene)
        gltf.scene = 0
        
        logger.info(f"GLTF创建完成，包含{len(self.vertices)//3}个顶点和{len(self.indices)//3}个三角面")
        return gltf
    
    def _encode_base64(self, data: bytes) -> str:
        """将字节数据编码为base64字符串"""
        import base64
        return base64.b64encode(data).decode('utf-8')
    
    def _calculate_bounds_and_scale(self, gdf: gpd.GeoDataFrame):
        """
        计算边界框并调整高度缩放
        
        Args:
            gdf: 地理数据框
        """
        # 计算所有几何体的总边界框
        total_bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        self.bounds = total_bounds
        
        # 计算数据中心点（用于平移到原点）
        self.center_x = (total_bounds[0] + total_bounds[2]) / 2.0
        self.center_z = (total_bounds[1] + total_bounds[3]) / 2.0
        
        # 计算缩放因子：将经纬度转换为米
        # 在中纬度附近，1度经度 ≈ 111km，1度纬度 ≈ 111km
        # 使用中心纬度计算精确的缩放因子
        import math
        center_lat = self.center_z
        
        # 地球平均半径（米）
        EARTH_RADIUS = 6371000.0
        
        # 1度纬度的米数（固定）
        meters_per_degree_lat = (math.pi / 180.0) * EARTH_RADIUS
        
        # 1度经度的米数（根据纬度变化）
        meters_per_degree_lon = meters_per_degree_lat * math.cos(math.radians(center_lat))
        
        # 使用平均值作为缩放因子
        self.scale_factor = (meters_per_degree_lon + meters_per_degree_lat) / 2.0
        
        logger.info(f"坐标转换信息:")
        logger.info(f"  中心纬度: {center_lat:.6f}°")
        logger.info(f"  1度经度 = {meters_per_degree_lon:.2f} 米")
        logger.info(f"  1度纬度 = {meters_per_degree_lat:.2f} 米")
        logger.info(f"  缩放因子: {self.scale_factor:.2f} 米/度")
        
        width = total_bounds[2] - total_bounds[0]  # maxx - minx
        height = total_bounds[3] - total_bounds[1]  # maxy - miny
        max_dimension = max(width, height)
        
        logger.info(f"数据边界框: {total_bounds}")
        logger.info(f"数据尺寸: 宽={width:.6f}, 高={height:.6f}")
        
        if self.auto_scale and max_dimension > 0:
            # 自动调整高度以保持合理比例
            # 高度应该是数据最大尺寸的一个合理倍数，而不是固定值
            # 默认使用 default_height 作为目标比例（例如 height:max_dim = 20:100 = 0.2:1）
            
            # 计算目标高度：使高度为数据最大尺寸的指定百分比
            # default_height 代表目标百分比（例如 20 表示 20%）
            height_ratio = self.default_height / 100.0  # 将百分比转换为比例
            adjusted_height = max_dimension * height_ratio
            
            logger.info(f"自动调整高度以匹配数据尺寸:")
            logger.info(f"  原始高度参数: {self.default_height}")
            logger.info(f"  数据最大尺寸: {max_dimension:.6f}")
            logger.info(f"  调整后高度: {adjusted_height:.6f} ({height_ratio*100:.1f}% 的数据尺寸)")
            logger.info(f"  高度/最大尺寸比例: {height_ratio:.2f}:1")
            
            self.default_height = adjusted_height
    
    def convert(self, input_path: str, gltf_path: str, 
               color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
               alpha: float = 0.5):
        """
        执行地理数据到GLTF的转换
        
        Args:
            input_path: 输入文件路径（GeoJSON 或 Shapefile）
            gltf_path: 输出GLTF文件路径
            color: RGB颜色值（0-1范围）
            alpha: 透明度（0-1范围）
        """
        try:
            # 读取地理数据文件
            gdf = self.read_geofile(input_path)
            
            # 计算边界框并调整缩放
            self._calculate_bounds_and_scale(gdf)
            
            # 处理所有几何对象
            logger.info("正在处理几何对象...")
            for idx, geometry in enumerate(gdf.geometry):
                if geometry is not None:
                    self.process_geometry(geometry)
                    if (idx + 1) % 100 == 0:
                        logger.info(f"已处理 {idx + 1}/{len(gdf)} 个对象")
            
            # 创建GLTF
            gltf = self.create_gltf(color, alpha)
            
            # 保存文件
            logger.info(f"正在保存GLTF文件到: {gltf_path}")
            gltf.save(gltf_path)
            logger.info("转换完成!")
            
        except Exception as e:
            logger.error(f"转换失败: {e}")
            raise


def parse_color(color_str: str) -> Tuple[float, float, float]:
    """
    解析颜色字符串
    
    Args:
        color_str: 颜色字符串，格式如 "255,0,0" 或 "1.0,0.0,0.0"
        
    Returns:
        Tuple[float, float, float]: RGB颜色值（0-1范围）
    """
    try:
        r, g, b = map(float, color_str.split(','))
        # 如果值大于1，假设是0-255范围，转换为0-1范围
        if r > 1 or g > 1 or b > 1:
            r, g, b = r / 255.0, g / 255.0, b / 255.0
        return (r, g, b)
    except ValueError:
        logger.error(f"无效的颜色格式: {color_str}，使用默认红色")
        return (1.0, 0.0, 0.0)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='通用地理数据转GLTF工具（支持 GeoJSON 和 Shapefile）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 转换 GeoJSON 文件
  python geo2gltf.py input.geojson output.gltf
  
  # 转换 Shapefile
  python geo2gltf.py input.shp output.gltf
  
  # 自定义参数
  python geo2gltf.py input.geojson output.gltf --height 10 --color "0.2,0.6,1.0" --alpha 0.7
        """
    )
    parser.add_argument('input', help='输入文件路径（GeoJSON 或 Shapefile）')
    parser.add_argument('output', help='输出GLTF文件路径')
    parser.add_argument('--height', type=float, default=5.0, 
                       help='默认高度（百分比），默认5%%')
    parser.add_argument('--color', default='1.0,0.0,0.0',
                       help='颜色设置，格式为R,G,B（0-1范围）或R,G,B（0-255范围），默认红色')
    parser.add_argument('--alpha', type=float, default=0.5,
                       help='透明度（0-1范围），默认0.5')
    parser.add_argument('--no-auto-scale', action='store_true',
                       help='禁用自动缩放高度功能')
    
    args = parser.parse_args()
    
    # 验证输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"输入文件不存在: {args.input}")
        return 1
    
    # 确保输出目录存在
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 解析颜色
    color = parse_color(args.color)
    
    # 执行转换
    converter = Geo2GLTFConverter(
        default_height=args.height,
        auto_scale=not args.no_auto_scale  # 取反，如果用户指定--no-auto-scale则禁用自动缩放
    )
    try:
        converter.convert(args.input, args.output, color, args.alpha)
        return 0
    except Exception as e:
        logger.error(f"转换失败: {e}")
        return 1


if __name__ == '__main__':
    exit(main())

