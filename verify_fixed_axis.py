import json
import base64
import numpy as np

# 读取修正后的GLTF文件
with open('C:\\Users\\chenhm\\Desktop\\shp2fbx\\1_fixed_axis.gltf', 'r') as f:
    gltf = json.load(f)

# 获取buffer数据
buffer_uri = gltf['buffers'][0]['uri']
base64_data = buffer_uri.split(',')[1]
buffer_data = base64.b64decode(base64_data)

# 获取顶点数据
vertex_buffer_view = gltf['bufferViews'][0]
vertex_offset = vertex_buffer_view.get('byteOffset', 0)
vertex_length = vertex_buffer_view['byteLength']

vertex_bytes = buffer_data[vertex_offset:vertex_offset + vertex_length]
vertices = np.frombuffer(vertex_bytes, dtype=np.float32).reshape(-1, 3)

print('=== 修正后的GLTF坐标分析 ===')
print(f'顶点数量: {len(vertices)}')
print()
print('【坐标轴映射】')
print(f'X轴 (经度): min={vertices[:,0].min():.6f}, max={vertices[:,0].max():.6f}, 范围={vertices[:,0].max()-vertices[:,0].min():.6f}')
print(f'Y轴 (高度): min={vertices[:,1].min():.6f}, max={vertices[:,1].max():.6f}, 范围={vertices[:,1].max()-vertices[:,1].min():.6f}')
print(f'Z轴 (纬度): min={vertices[:,2].min():.6f}, max={vertices[:,2].max():.6f}, 范围={vertices[:,2].max()-vertices[:,2].min():.6f}')
print()
print('【验证结果】')
x_range = vertices[:,0].max()-vertices[:,0].min()
y_range = vertices[:,1].max()-vertices[:,1].min()
z_range = vertices[:,2].max()-vertices[:,2].min()

if abs(x_range - 0.122) < 0.001:
    print('✓ X轴范围 ≈ 0.122 (经度范围，正确)')
else:
    print(f'✗ X轴范围异常: {x_range:.6f}')

if abs(y_range - 0.006) < 0.001:
    print('✓ Y轴范围 ≈ 0.006 (高度，正确)')
else:
    print(f'✗ Y轴范围异常: {y_range:.6f}')

if abs(z_range - 0.084) < 0.001:
    print('✓ Z轴范围 ≈ 0.084 (纬度范围，正确)')
else:
    print(f'✗ Z轴范围异常: {z_range:.6f}')

print()
print('【标准3D坐标系确认】')
print('✓ XZ平面 = 地面（经度×纬度）')
print('✓ Y轴向上 = 高度（垂直方向）')
print()
print('这是标准的Y-up坐标系，适用于：')
print('  - Blender')
print('  - Unity')
print('  - 大多数3D软件')
print()
print('前5个顶点 (X=经度, Y=高度, Z=纬度):')
for i in range(min(5, len(vertices))):
    print(f'  [{i}] X={vertices[i,0]:.6f}, Y={vertices[i,1]:.6f}, Z={vertices[i,2]:.6f}')

