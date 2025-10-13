#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 mapbox_earcut 的正确调用方式
"""

import numpy as np
import mapbox_earcut

# 测试简单矩形
print("=" * 70)
print("测试 mapbox_earcut 调用方式")
print("=" * 70)

# 矩形顶点（逆时针）
vertices = np.array([
    [0.0, 0.0],
    [1.0, 0.0],
    [1.0, 1.0],
    [0.0, 1.0]
], dtype=np.float32)

print(f"\n顶点数组形状: {vertices.shape}")
print(f"顶点数组:\n{vertices}")

# 尝试1: 传入空数组
print("\n" + "=" * 70)
print("尝试1: 传入空的 uint32 数组")
try:
    holes = np.array([], dtype=np.uint32)
    print(f"holes: {holes}, shape: {holes.shape}")
    result = mapbox_earcut.triangulate_float32(vertices, holes)
    print(f"✓ 成功! 结果: {result}")
except Exception as e:
    print(f"✗ 失败: {e}")

# 尝试2: 传入包含顶点数的数组（ring_end_indices）
print("\n" + "=" * 70)
print("尝试2: 传入 ring_end_indices（外环结束索引）")
try:
    ring_end_indices = np.array([4], dtype=np.uint32)  # 第一个环在索引4结束
    print(f"ring_end_indices: {ring_end_indices}, shape: {ring_end_indices.shape}")
    result = mapbox_earcut.triangulate_float32(vertices, ring_end_indices)
    print(f"✓ 成功! 结果: {result}")
    print(f"三角形数量: {len(result) // 3}")
except Exception as e:
    print(f"✗ 失败: {e}")

# 尝试3: 测试带洞的多边形
print("\n" + "=" * 70)
print("尝试3: 测试带洞的多边形")
try:
    # 外环 + 内环（洞）
    vertices_with_hole = np.array([
        # 外环（正方形）
        [0.0, 0.0],
        [4.0, 0.0],
        [4.0, 4.0],
        [0.0, 4.0],
        # 内环（小正方形，作为洞）
        [1.0, 1.0],
        [3.0, 1.0],
        [3.0, 3.0],
        [1.0, 3.0],
    ], dtype=np.float32)
    
    ring_end_indices = np.array([4, 8], dtype=np.uint32)  # 第一个环索引0-3，第二个环索引4-7
    print(f"顶点数组形状: {vertices_with_hole.shape}")
    print(f"ring_end_indices: {ring_end_indices}")
    result = mapbox_earcut.triangulate_float32(vertices_with_hole, ring_end_indices)
    print(f"✓ 成功! 结果: {result}")
    print(f"三角形数量: {len(result) // 3}")
except Exception as e:
    print(f"✗ 失败: {e}")

print("\n" + "=" * 70)
print("结论")
print("=" * 70)
print("""
mapbox_earcut.triangulate_float32 的第二个参数是 ring_end_indices（环结束索引），
不是 holes（洞的起始索引）。

正确用法：
- 对于简单多边形（无洞）：ring_end_indices = np.array([顶点数], dtype=np.uint32)
- 对于带洞的多边形：ring_end_indices = np.array([外环顶点数, 总顶点数], dtype=np.uint32)
""")

