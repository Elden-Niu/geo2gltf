#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标轴诊断脚本
"""

from pygltflib import GLTF2
import numpy as np
import base64
import geopandas as gpd

print("=" * 70)
print("坐标轴诊断")
print("=" * 70)

# 读取源文件
gdf = gpd.read_file(r"C:\Users\chenhm\Desktop\shp2fbx\examples\example_buildings.geojson")
print("\n源数据（GeoJSON - WGS84 经纬度）:")
print("-" * 70)

for idx, geom in enumerate(gdf.geometry):
    coords = list(geom.exterior.coords)[:-1]
    print(f"\n建筑 {idx + 1}:")
    print(f"  第1个点: 经度={coords[0][0]:.6f}, 纬度={coords[0][1]:.6f}")
    print(f"  第2个点: 经度={coords[1][0]:.6f}, 纬度={coords[1][1]:.6f}")
    print(f"  第3个点: 经度={coords[2][0]:.6f}, 纬度={coords[2][1]:.6f}")
    
    # 计算方向
    dx = coords[1][0] - coords[0][0]  # 经度差
    dy = coords[1][1] - coords[0][1]  # 纬度差
    print(f"  点1→点2: Δ经度={dx:.6f}, Δ纬度={dy:.6f}")
    
    if dx > 0 and abs(dy) < 0.00001:
        print(f"  方向: 向东")
    elif dx < 0 and abs(dy) < 0.00001:
        print(f"  方向: 向西")
    elif dy > 0 and abs(dx) < 0.00001:
        print(f"  方向: 向北")
    elif dy < 0 and abs(dx) < 0.00001:
        print(f"  方向: 向南")

# 读取 glTF 文件
gltf = GLTF2().load(r"C:\Users\chenhm\Desktop\shp2fbx\examples\test_final_fixed.gltf")

buffer = gltf.buffers[0]
uri_data = buffer.uri.split(",")[1]
buffer_data = base64.b64decode(uri_data)

vertex_buffer_view = gltf.bufferViews[0]
vertex_offset = vertex_buffer_view.byteOffset
vertex_length = vertex_buffer_view.byteLength
vertex_bytes = buffer_data[vertex_offset:vertex_offset + vertex_length]
vertices = np.frombuffer(vertex_bytes, dtype=np.float32).reshape(-1, 3)

print("\n\nglTF模型坐标（当前映射）:")
print("-" * 70)
print("当前映射: X=经度, Y=高度, Z=纬度")

for idx in range(2):
    gltf_start = idx * 8
    bottom_verts = vertices[gltf_start:gltf_start+4]
    
    print(f"\n建筑 {idx + 1} 底面顶点:")
    print(f"  第1个点: X={bottom_verts[0][0]:.6f}, Y={bottom_verts[0][1]:.6f}, Z={bottom_verts[0][2]:.6f}")
    print(f"  第2个点: X={bottom_verts[1][0]:.6f}, Y={bottom_verts[1][1]:.6f}, Z={bottom_verts[1][2]:.6f}")
    print(f"  第3个点: X={bottom_verts[2][0]:.6f}, Y={bottom_verts[2][1]:.6f}, Z={bottom_verts[2][2]:.6f}")
    
    # 计算方向
    dx = bottom_verts[1][0] - bottom_verts[0][0]
    dy = bottom_verts[1][1] - bottom_verts[0][1]
    dz = bottom_verts[1][2] - bottom_verts[0][2]
    print(f"  点1→点2: ΔX={dx:.6f}, ΔY={dy:.6f}, ΔZ={dz:.6f}")
    
    if abs(dx) > 0.00001 and abs(dz) < 0.00001:
        print(f"  3D方向: 沿+X轴（当前为经度方向，应该向东）")
    elif abs(dz) > 0.00001 and abs(dx) < 0.00001:
        print(f"  3D方向: 沿+Z轴（当前为纬度方向，应该向北）")

print("\n" + "=" * 70)
print("坐标系统分析")
print("=" * 70)

print("""
GIS/地图坐标系统（源数据）:
  - 经度(Longitude): 东西方向，向东为正
  - 纬度(Latitude):  南北方向，向北为正
  - 高度(Elevation): 垂直方向，向上为正

glTF标准坐标系统（右手坐标系，Y-up）:
  - X轴: 向右
  - Y轴: 向上（高度）
  - Z轴: 向外（朝向观察者）

常见映射方案：

方案1（标准地图映射 - 推荐）:
  X = 经度 (Longitude) → 东西方向
  Y = 高度 (Elevation)  → 垂直方向
  Z = -纬度 (-Latitude) → 南北方向（负号使Z轴指向南，符合右手系）
  
方案2（OpenStreetMap风格）:
  X = 经度 (Longitude)  → 东西方向
  Y = 高度 (Elevation)   → 垂直方向
  Z = 纬度 (Latitude)    → 南北方向
  
当前代码使用的映射:
  X = 经度, Y = 高度, Z = 纬度
  
这是方案2，但可能在某些3D查看器中显示方向不符合预期。
""")

print("\n建议:")
print("  1. 如果在查看器中看到模型上下颠倒或方向错误，可能需要调整坐标映射")
print("  2. 如果需要使用方案1（Z轴负向），需要修改代码将 Z = -纬度")
print("  3. 请描述您在查看器中看到的具体问题，我会帮您调整")

