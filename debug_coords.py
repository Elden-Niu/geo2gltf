#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试坐标转换脚本
"""

import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon

# 读取示例文件
gdf = gpd.read_file(r"C:\Users\chenhm\Desktop\shp2fbx\examples\example_buildings.geojson")

print("=" * 60)
print("源文件坐标检查")
print("=" * 60)

for idx, geom in enumerate(gdf.geometry):
    print(f"\n建筑 {idx + 1}:")
    print(f"  几何类型: {geom.geom_type}")
    
    if isinstance(geom, Polygon):
        # 原始坐标
        raw_coords = list(geom.exterior.coords)
        print(f"\n  原始坐标 (共 {len(raw_coords)} 个点):")
        for i, (x, y) in enumerate(raw_coords):
            print(f"    点 {i}: ({x:.6f}, {y:.6f})")
        
        # 去除最后重复点后
        exterior_coords = raw_coords[:-1]
        print(f"\n  去重后坐标 (共 {len(exterior_coords)} 个点):")
        for i, (x, y) in enumerate(exterior_coords):
            print(f"    点 {i}: ({x:.6f}, {y:.6f})")
        
        # 边界框
        bounds = geom.bounds
        print(f"\n  边界框: minx={bounds[0]:.6f}, miny={bounds[1]:.6f}, maxx={bounds[2]:.6f}, maxy={bounds[3]:.6f}")
        print(f"  宽度: {bounds[2] - bounds[0]:.6f}")
        print(f"  高度: {bounds[3] - bounds[1]:.6f}")

print("\n" + "=" * 60)
print("3D顶点生成检查 (Y=0 底面)")
print("=" * 60)

for idx, geom in enumerate(gdf.geometry):
    if isinstance(geom, Polygon):
        exterior_coords = list(geom.exterior.coords)[:-1]
        print(f"\n建筑 {idx + 1} 底面顶点 (X, Y=0, Z):")
        for i, (x, y) in enumerate(exterior_coords):
            print(f"  顶点 {i}: ({x:.6f}, 0.000000, {y:.6f})")

print("\n" + "=" * 60)
print("检查是否为标准矩形")
print("=" * 60)

for idx, geom in enumerate(gdf.geometry):
    if isinstance(geom, Polygon):
        exterior_coords = list(geom.exterior.coords)[:-1]
        if len(exterior_coords) == 4:
            xs = [x for x, y in exterior_coords]
            ys = [y for x, y in exterior_coords]
            print(f"\n建筑 {idx + 1}:")
            print(f"  X坐标集合: {set(xs)}")
            print(f"  Y坐标集合: {set(ys)}")
            print(f"  是否为矩形: {len(set(xs)) == 2 and len(set(ys)) == 2}")

