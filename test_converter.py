#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试SHP转GLTF转换器
创建示例SHP文件并测试转换功能
"""

import os
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon
import logging
from shp2gltf import SHP2GLTFConverter

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_test_point_shp(filename="test_points.shp"):
    """创建测试点SHP文件"""
    points = [
        Point(0, 0),
        Point(10, 0),
        Point(10, 10),
        Point(0, 10),
        Point(5, 5)
    ]
    
    gdf = gpd.GeoDataFrame({'id': range(len(points))}, geometry=points)
    gdf.to_file(filename)
    logger.info(f"创建测试点文件: {filename}")
    return filename


def create_test_line_shp(filename="test_lines.shp"):
    """创建测试线SHP文件"""
    lines = [
        LineString([(0, 0), (5, 5), (10, 0)]),
        LineString([(0, 10), (10, 10)]),
        LineString([(5, 0), (5, 10), (15, 10)])
    ]
    
    gdf = gpd.GeoDataFrame({'id': range(len(lines))}, geometry=lines)
    gdf.to_file(filename)
    logger.info(f"创建测试线文件: {filename}")
    return filename


def create_test_polygon_shp(filename="test_polygons.shp"):
    """创建测试面SHP文件"""
    polygons = [
        Polygon([(0, 0), (5, 0), (5, 5), (0, 5)]),
        Polygon([(10, 10), (20, 10), (20, 20), (10, 20)]),
        Polygon([(15, 0), (25, 5), (20, 10), (10, 5)])
    ]
    
    gdf = gpd.GeoDataFrame({'id': range(len(polygons))}, geometry=polygons)
    gdf.to_file(filename)
    logger.info(f"创建测试面文件: {filename}")
    return filename


def test_conversion(shp_file, gltf_file, height=20, color=(1.0, 0.0, 0.0), alpha=0.5):
    """测试SHP到GLTF转换"""
    try:
        logger.info(f"测试转换: {shp_file} -> {gltf_file}")
        converter = SHP2GLTFConverter(default_height=height)
        converter.convert(shp_file, gltf_file, color, alpha)
        
        # 检查输出文件
        if os.path.exists(gltf_file):
            file_size = os.path.getsize(gltf_file)
            logger.info(f"转换成功! 输出文件大小: {file_size} 字节")
            return True
        else:
            logger.error("转换失败: 输出文件未生成")
            return False
            
    except Exception as e:
        logger.error(f"转换过程中出错: {e}")
        return False


def main():
    """主测试函数"""
    logger.info("开始测试SHP转GLTF转换器")
    
    # 创建测试数据
    test_files = []
    
    try:
        # 创建测试SHP文件
        point_shp = create_test_point_shp()
        line_shp = create_test_line_shp()
        polygon_shp = create_test_polygon_shp()
        
        test_files.extend([point_shp, line_shp, polygon_shp])
        
        # 测试转换
        test_cases = [
            {
                'shp': point_shp,
                'gltf': 'test_points.gltf',
                'height': 15,
                'color': (1.0, 0.0, 0.0),  # 红色
                'alpha': 0.8
            },
            {
                'shp': line_shp,
                'gltf': 'test_lines.gltf',
                'height': 10,
                'color': (0.0, 1.0, 0.0),  # 绿色
                'alpha': 0.6
            },
            {
                'shp': polygon_shp,
                'gltf': 'test_polygons.gltf',
                'height': 25,
                'color': (0.0, 0.0, 1.0),  # 蓝色
                'alpha': 0.7
            }
        ]
        
        success_count = 0
        for test_case in test_cases:
            if test_conversion(**test_case):
                success_count += 1
                test_files.append(test_case['gltf'])
        
        logger.info(f"测试完成: {success_count}/{len(test_cases)} 个测试用例成功")
        
        if success_count == len(test_cases):
            logger.info("所有测试通过! ✅")
        else:
            logger.warning("部分测试失败 ⚠️")
            
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
    
    # 清理选项
    cleanup = input("\n是否清理测试文件? (y/N): ").strip().lower()
    if cleanup == 'y':
        for file_pattern in test_files:
            # 删除SHP相关文件
            if file_pattern.endswith('.shp'):
                base_name = file_pattern[:-4]
                extensions = ['.shp', '.shx', '.dbf', '.prj', '.cpg']
                for ext in extensions:
                    file_path = base_name + ext
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"已删除: {file_path}")
            # 删除GLTF文件
            elif file_pattern.endswith('.gltf'):
                if os.path.exists(file_pattern):
                    os.remove(file_pattern)
                    logger.info(f"已删除: {file_pattern}")


if __name__ == '__main__':
    main()
