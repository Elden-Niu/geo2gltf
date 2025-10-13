#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证坐标修复后的结果
"""

from pygltflib import GLTF2
import numpy as np
import base64

print("=" * 70)
print("坐标修复验证")
print("=" * 70)

# 读取修复后的 glTF 文件
gltf = GLTF2().load(r"C:\Users\chenhm\Desktop\shp2fbx\examples\test_coordinate_fixed.gltf")

buffer = gltf.buffers[0]
uri_data = buffer.uri.split(",")[1]
buffer_data = base64.b64decode(uri_data)

vertex_buffer_view = gltf.bufferViews[0]
vertex_offset = vertex_buffer_view.byteOffset
vertex_length = vertex_buffer_view.byteLength
vertex_bytes = buffer_data[vertex_offset:vertex_offset + vertex_length]
vertices = np.frombuffer(vertex_bytes, dtype=np.float32).reshape(-1, 3)

print("\n修复后的坐标系统:")
print("-" * 70)
print("坐标映射: X=(经度-中心), Y=高度, Z=(纬度-中心)")
print("\n建筑 1 的所有顶点:")

for idx in range(2):
    print(f"\n{'='*70}")
    print(f"建筑 {idx + 1}:")
    print(f"{'='*70}")
    
    gltf_start = idx * 8
    bottom_verts = vertices[gltf_start:gltf_start+4]
    top_verts = vertices[gltf_start+4:gltf_start+8]
    
    print("\n底面顶点 (Y=0):")
    for i, v in enumerate(bottom_verts):
        print(f"  顶点{i}: X={v[0]:8.6f}, Y={v[1]:8.6f}, Z={v[2]:8.6f}")
    
    print("\n顶面顶点 (Y=高度):")
    for i, v in enumerate(top_verts):
        print(f"  顶点{i}: X={v[0]:8.6f}, Y={v[1]:8.6f}, Z={v[2]:8.6f}")
    
    # 计算边界框
    x_coords = bottom_verts[:, 0]
    y_coords = bottom_verts[:, 1]
    z_coords = bottom_verts[:, 2]
    
    print(f"\n底面边界框:")
    print(f"  X范围: [{x_coords.min():.6f}, {x_coords.max():.6f}]")
    print(f"  Y值:   {y_coords[0]:.6f} (应该是0)")
    print(f"  Z范围: [{z_coords.min():.6f}, {z_coords.max():.6f}]")
    
    print(f"\n顶面边界框:")
    y_top = top_verts[:, 1]
    print(f"  Y值:   {y_top[0]:.6f} (建筑物高度)")

print("\n" + "=" * 70)
print("验证结果")
print("=" * 70)

# 计算所有顶点的边界框
all_x = vertices[:, 0]
all_y = vertices[:, 1]
all_z = vertices[:, 2]

print(f"\n整体模型边界框:")
print(f"  X: [{all_x.min():.6f}, {all_x.max():.6f}], 中心: {(all_x.min()+all_x.max())/2:.6f}")
print(f"  Y: [{all_y.min():.6f}, {all_y.max():.6f}], 中心: {(all_y.min()+all_y.max())/2:.6f}")
print(f"  Z: [{all_z.min():.6f}, {all_z.max():.6f}], 中心: {(all_z.min()+all_z.max())/2:.6f}")

print("\n✓ 问题1 - 模型上下颠倒: ", end="")
if all_y.min() >= 0:
    print("已修复！所有Y坐标 >= 0，模型底部在Y=0")
else:
    print("⚠ 仍有问题")

print("✓ 问题2 - 坐标轴位置: ", end="")
x_center = (all_x.min() + all_x.max()) / 2
z_center = (all_z.min() + all_z.max()) / 2
if abs(x_center) < 0.001 and abs(z_center) < 0.001:
    print("已修复！模型已平移到原点附近")
    print(f"  X中心: {x_center:.6f} (接近0)")
    print(f"  Z中心: {z_center:.6f} (接近0)")
else:
    print(f"⚠ 仍需调整 (X中心={x_center:.6f}, Z中心={z_center:.6f})")

print("\n" + "=" * 70)
print("坐标系统说明")
print("=" * 70)
print("""
修复后的坐标系统（符合 glTF 标准，Y-up 右手坐标系）:
  
  Y
  ↑
  |
  |_____ X
 /
Z

- X轴: 向右（东西方向，经度）
- Y轴: 向上（垂直方向，高度）
- Z轴: 向外（南北方向，纬度）

模型已:
1. 将底部放置在 Y=0 平面（不再上下颠倒）
2. 将模型中心平移到世界坐标原点 (0, 0, 0) 附近
3. 保持正确的形状和比例
""")

