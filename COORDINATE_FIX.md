# 坐标轴修正说明

## 问题发现

原始转换结果的坐标轴映射不符合标准3D软件的惯例：

### ❌ 修复前（错误的映射）

```
原始SHP坐标：
  X = 经度 (Longitude)  ≈ 104.13 ~ 104.26
  Y = 纬度 (Latitude)   ≈ 31.01 ~ 31.10

转换为GLTF后：
  X轴 = 经度  ≈ 104.13 ~ 104.26  (范围: 0.122)
  Y轴 = 纬度  ≈ 31.01 ~ 31.10    (范围: 0.084)
  Z轴 = 高度  ≈ 0 ~ 0.006        (范围: 0.006)
```

**问题：**
- 模型在XY平面上，而不是XZ平面
- 高度在Z方向，而不是Y方向
- 在Blender、Unity等软件中，模型会"躺"着显示

---

## 解决方案

修改坐标映射，采用标准的**Y-up坐标系**：

### ✅ 修复后（正确的映射）

```
原始SHP坐标：
  X = 经度 (Longitude)  ≈ 104.13 ~ 104.26
  Y = 纬度 (Latitude)   ≈ 31.01 ~ 31.10

转换为GLTF后：
  X轴 = 经度  ≈ 104.13 ~ 104.26  (范围: 0.122)  东西方向
  Y轴 = 高度  ≈ 0 ~ 0.006        (范围: 0.006)  垂直向上 ⬆️
  Z轴 = 纬度  ≈ 31.01 ~ 31.10    (范围: 0.084)  南北方向
```

**优势：**
- ✅ XZ平面 = 地面（经度×纬度）
- ✅ Y轴向上 = 高度（垂直方向）
- ✅ 符合Blender、Unity、Unreal Engine等主流3D软件的标准
- ✅ 模型直立显示，无需额外旋转

---

## 代码修改

修改了 `shp2gltf.py` 中的三个函数：

### 1. `process_point()` - 点几何体

**修改前：**
```python
cube_vertices = [
    [x - size/2, y - size/2, 0],
    [x + size/2, y - size/2, 0],
    # ... 更多顶点
    [x - size/2, y - size/2, self.default_height],
    # ...
]
```

**修改后：**
```python
# 立方体的8个顶点 (X=经度, Y=高度, Z=纬度)
cube_vertices = [
    [x - size/2, 0, y - size/2],
    [x + size/2, 0, y - size/2],
    # ... 更多顶点
    [x - size/2, self.default_height, y - size/2],
    # ...
]
```

### 2. `process_linestring()` - 线几何体

**修改前：**
```python
vertices.extend([
    [x - width/2, y - width/2, 0],
    [x + width/2, y - width/2, 0],
    # ... 更多顶点
    [x - width/2, y - width/2, self.default_height],
    # ...
])
```

**修改后：**
```python
vertices.extend([
    [x - width/2, 0, y - width/2],
    [x + width/2, 0, y - width/2],
    # ... 更多顶点
    [x - width/2, self.default_height, y - width/2],
    # ...
])
```

### 3. `process_polygon()` - 面几何体

**修改前：**
```python
# 添加底面顶点
for x, y in exterior_coords:
    self.vertices.extend([x, y, 0])

# 添加顶面顶点
for x, y in exterior_coords:
    self.vertices.extend([x, y, self.default_height])
```

**修改后：**
```python
# 添加底面顶点 (X=经度, Y=高度, Z=纬度)
for x, y in exterior_coords:
    self.vertices.extend([x, 0, y])

# 添加顶面顶点 (X=经度, Y=高度, Z=纬度)
for x, y in exterior_coords:
    self.vertices.extend([x, self.default_height, y])
```

---

## 验证结果

使用测试文件 `1.shp` 进行验证：

```
=== 修正后的GLTF坐标分析 ===
顶点数量: 13188

【坐标轴映射】
X轴 (经度): min=104.137848, max=104.259476, 范围=0.121628
Y轴 (高度): min=0.000000, max=0.006082, 范围=0.006082
Z轴 (纬度): min=31.015512, max=31.099499, 范围=0.083986

【验证结果】
✓ X轴范围 ≈ 0.122 (经度范围，正确)
✓ Y轴范围 ≈ 0.006 (高度，正确)
✓ Z轴范围 ≈ 0.084 (纬度范围，正确)

【标准3D坐标系确认】
✓ XZ平面 = 地面（经度×纬度）
✓ Y轴向上 = 高度（垂直方向）
```

---

## 适用软件

修正后的坐标系统适用于以下3D软件（均使用Y-up）：

- ✅ **Blender** - 直接导入，无需旋转
- ✅ **Unity** - 标准Y-up坐标系
- ✅ **Unreal Engine** - 兼容
- ✅ **3ds Max** - 支持
- ✅ **Maya** - 支持Y-up模式
- ✅ **在线GLTF查看器** - 正确显示

---

## 使用说明

### 生成修正后的GLTF文件

```bash
# 命令行
python shp2gltf.py input.shp output.gltf

# GUI界面
python shp2gltf_gui.py
```

所有新生成的GLTF文件都会使用正确的Y-up坐标系。

---

## 对比示例

| 属性 | 修复前 | 修复后 |
|------|--------|--------|
| 地面平面 | XY平面 | XZ平面 ✅ |
| 高度方向 | Z轴 | Y轴 ✅ |
| 在Blender中的显示 | 躺着（需旋转90°） | 直立 ✅ |
| 在Unity中的显示 | 躺着（需旋转） | 直立 ✅ |
| 符合标准 | ❌ | ✅ |

---

## 技术说明

**为什么选择Y-up？**

1. **行业标准**：大多数3D软件（Blender、Unity等）默认使用Y-up
2. **直观性**：Y轴向上符合人类的空间认知（高度向上）
3. **兼容性**：减少导入时的坐标转换和旋转操作
4. **GLTF规范**：GLTF 2.0建议使用Y-up坐标系

**注意事项：**

- 原始SHP文件的坐标系统保持不变
- 只是3D空间中的轴映射发生了变化
- 不影响地理坐标的精度和准确性

---

**更新日期：** 2025-10-11  
**修复版本：** v2.1  
**状态：** ✅ 已修复并验证

