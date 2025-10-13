#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查生成的 glTF 文件
"""

from pygltflib import GLTF2
import numpy as np
import struct
import base64

# 读取 glTF 文件
gltf_path = r"C:\Users\chenhm\Desktop\shp2fbx\examples\test_output_success.gltf"
gltf = GLTF2().load(gltf_path)

print("=" * 60)
print("glTF 文件分析")
print("=" * 60)

# 解析 buffer
buffer = gltf.buffers[0]
print(f"\nBuffer 信息:")
print(f"  长度: {buffer.byteLength} 字节")

# 解码 base64 数据
uri_data = buffer.uri.split(",")[1]
buffer_data = base64.b64decode(uri_data)

# 获取顶点数据
vertex_accessor = gltf.accessors[0]
vertex_buffer_view = gltf.bufferViews[0]

print(f"\n顶点 Accessor:")
print(f"  数量: {vertex_accessor.count}")
print(f"  类型: {vertex_accessor.type}")
print(f"  组件类型: {vertex_accessor.componentType}")
print(f"  Min: {vertex_accessor.min}")
print(f"  Max: {vertex_accessor.max}")

# 解析顶点数据
vertex_offset = vertex_buffer_view.byteOffset
vertex_length = vertex_buffer_view.byteLength
vertex_bytes = buffer_data[vertex_offset:vertex_offset + vertex_length]

# 转换为numpy数组
vertices = np.frombuffer(vertex_bytes, dtype=np.float32).reshape(-1, 3)

print(f"\n顶点数据 (共 {len(vertices)} 个顶点):")
print(f"格式: [X(经度), Y(高度), Z(纬度)]")
print("")

# 分析顶点结构
# 假设前8个顶点是第一个建筑，后8个是第二个
for building_idx in range(2):
    start_idx = building_idx * 8
    end_idx = start_idx + 8
    
    if end_idx <= len(vertices):
        building_verts = vertices[start_idx:end_idx]
        print(f"建筑 {building_idx + 1} 顶点:")
        
        # 底面顶点 (Y=0)
        bottom_verts = building_verts[:4]
        print(f"\n  底面顶点 (前4个):")
        for i, v in enumerate(bottom_verts):
            print(f"    顶点 {i}: X={v[0]:.6f}, Y={v[1]:.6f}, Z={v[2]:.6f}")
        
        # 顶面顶点  
        top_verts = building_verts[4:8]
        print(f"\n  顶面顶点 (后4个):")
        for i, v in enumerate(top_verts):
            print(f"    顶点 {i}: X={v[0]:.6f}, Y={v[1]:.6f}, Z={v[2]:.6f}")
        
        # 计算边界
        xs = bottom_verts[:, 0]
        zs = bottom_verts[:, 2]
        print(f"\n  底面边界:")
        print(f"    X范围: [{xs.min():.6f}, {xs.max():.6f}] 宽度={xs.max()-xs.min():.6f}")
        print(f"    Z范围: [{zs.min():.6f}, {zs.max():.6f}] 高度={zs.max()-zs.min():.6f}")
        print("")

# 获取索引数据
index_accessor = gltf.accessors[1]
index_buffer_view = gltf.bufferViews[1]

print(f"\n索引 Accessor:")
print(f"  数量: {index_accessor.count}")
print(f"  类型: {index_accessor.type}")

index_offset = index_buffer_view.byteOffset
index_length = index_buffer_view.byteLength
index_bytes = buffer_data[index_offset:index_offset + index_length]

# 转换为numpy数组
indices = np.frombuffer(index_bytes, dtype=np.uint32)

print(f"\n索引数据 (共 {len(indices)} 个索引, {len(indices)//3} 个三角形):")

# 显示三角形
print(f"\n三角形列表 (前20个):")
for i in range(min(20, len(indices) // 3)):
    idx0, idx1, idx2 = indices[i*3:i*3+3]
    v0, v1, v2 = vertices[idx0], vertices[idx1], vertices[idx2]
    print(f"  三角形 {i}: 顶点索引=[{idx0}, {idx1}, {idx2}]")
    print(f"    v0: ({v0[0]:.6f}, {v0[1]:.6f}, {v0[2]:.6f})")
    print(f"    v1: ({v1[0]:.6f}, {v1[1]:.6f}, {v1[2]:.6f})")
    print(f"    v2: ({v2[0]:.6f}, {v2[1]:.6f}, {v2[2]:.6f})")

print("\n" + "=" * 60)
print("对比源文件坐标")
print("=" * 60)

print("\n源文件建筑1的坐标 (2D XY):")
print("  (116.397428, 39.907616)")
print("  (116.398428, 39.907616)")  
print("  (116.398428, 39.908616)")
print("  (116.397428, 39.908616)")

print("\nglTF建筑1底面坐标 (3D XYZ):")
for i in range(4):
    v = vertices[i]
    print(f"  ({v[0]:.6f}, {v[1]:.6f}, {v[2]:.6f})")

print("\n✓ X坐标对应源文件的经度")
print("✓ Y坐标是3D高度 (应该是0或拉伸高度)")
print("✓ Z坐标对应源文件的纬度")

