# 批量转换工具使用说明

## 功能介绍

`batch_convert.py` 是一个强大的批量转换工具，可以一次性将多个 GeoJSON 或 Shapefile 文件转换为 glTF 格式。

## 主要特性

✅ **批量处理** - 一次转换整个目录中的所有文件  
✅ **递归搜索** - 支持搜索子目录中的文件  
✅ **保持结构** - 递归模式下保持原始目录结构  
✅ **进度显示** - 实时显示转换进度和统计信息  
✅ **错误处理** - 单个文件失败不影响其他文件继续转换  
✅ **自动命名** - 自动根据源文件名生成输出文件名  

## 基本用法

### 1. 批量转换当前目录

转换 `input_dir` 目录下的所有 GeoJSON 和 Shapefile 文件：

```bash
python batch_convert.py input_dir output_dir
```

### 2. 递归转换所有子目录

使用 `-r` 或 `--recursive` 选项递归搜索所有子目录：

```bash
python batch_convert.py input_dir output_dir --recursive
```

递归模式会保持原始目录结构，例如：
```
input_dir/
  ├── building1.geojson
  ├── subdir/
  │   └── building2.geojson
  
→ 转换为 →

output_dir/
  ├── building1.gltf
  ├── subdir/
  │   └── building2.gltf
```

### 3. 只转换特定类型的文件

使用 `--extensions` 指定要处理的文件类型：

```bash
# 只转换 GeoJSON 文件
python batch_convert.py input_dir output_dir --extensions .geojson .json

# 只转换 Shapefile
python batch_convert.py input_dir output_dir --extensions .shp
```

## 高级参数

### 自定义高度

```bash
python batch_convert.py input_dir output_dir --height 20
```

### 自定义颜色

```bash
# RGB 0-1 范围
python batch_convert.py input_dir output_dir --color 0.2,0.6,1.0

# RGB 0-255 范围
python batch_convert.py input_dir output_dir --color 51,153,255
```

### 自定义透明度

```bash
python batch_convert.py input_dir output_dir --alpha 0.7
```

### 组合使用多个参数

```bash
python batch_convert.py input_dir output_dir \
  --recursive \
  --height 30 \
  --color 0,128,255 \
  --alpha 0.6 \
  --extensions .geojson .json
```

## 完整示例

### 示例 1：批量转换建筑物数据

```bash
python batch_convert.py \
  C:\Data\Buildings \
  C:\Output\Buildings_3D \
  --height 50 \
  --color 255,128,64 \
  --alpha 0.8
```

### 示例 2：递归转换整个项目

```bash
python batch_convert.py \
  D:\GIS_Project\Data \
  D:\GIS_Project\3D_Models \
  --recursive \
  --height 20 \
  --color 100,200,100
```

### 示例 3：只转换特定区域的 GeoJSON

```bash
python batch_convert.py \
  ./regions \
  ./models \
  --extensions .geojson \
  --height 15 \
  --alpha 0.5
```

## 输出信息

批量转换会显示详细的进度和统计信息：

```
======================================================================
[1/5] 正在转换: building1.geojson
  输入: C:\Data\building1.geojson
  输出: C:\Output\building1.gltf
  坐标转换信息:
    中心纬度: 39.908116°
    1度经度 = 85294.77 米
    1度纬度 = 111194.93 米
    缩放因子: 98244.85 米/度
  ✓ 转换成功！输出文件大小: 2.34 KB

[2/5] 正在转换: building2.geojson
  ...

======================================================================
批量转换完成!
======================================================================
总文件数: 5
成功: 5
失败: 0
跳过: 0
总耗时: 1.23 秒
平均速度: 0.25 秒/文件
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `input_dir` | 输入目录路径 | 必需 |
| `output_dir` | 输出目录路径 | 必需 |
| `-r, --recursive` | 递归搜索子目录 | 否 |
| `--extensions` | 文件扩展名列表 | `.geojson .json .shp` |
| `--height` | 默认高度（百分比） | 5.0 |
| `--color` | RGB 颜色值 | `1.0,0.0,0.0` (红色) |
| `--alpha` | 透明度 (0-1) | 0.5 |
| `--no-auto-scale` | 禁用自动高度缩放 | 启用 |

## 注意事项

1. **覆盖警告**：如果输出文件已存在，会显示警告并覆盖
2. **错误继续**：单个文件转换失败不会终止整个批处理
3. **内存占用**：大量文件时注意内存使用
4. **文件命名**：输出文件与输入文件同名，仅扩展名改为 `.gltf`

## 中断操作

如需中断批量转换，按 `Ctrl+C`：

```
用户中断操作
```

已转换的文件会保留，未转换的文件会被跳过。

## 故障排查

### 问题：找不到文件

```
在 input_dir 中未找到地理数据文件
```

**解决方案**：
- 检查输入目录路径是否正确
- 确认文件扩展名（`.geojson`, `.json`, `.shp`）
- 如果文件在子目录中，使用 `--recursive` 选项

### 问题：某个文件转换失败

```
✗ 转换失败: [错误信息]
```

**解决方案**：
- 查看错误信息确定原因
- 检查该文件的数据格式是否正确
- 使用单文件转换工具 `geo2gltf.py` 进行详细调试

## 相关工具

- **geo2gltf.py** - 单文件转换工具（支持 GeoJSON 和 Shapefile）
- **shp2gltf.py** - Shapefile 专用转换工具

## 性能提示

- 小文件（< 1MB）：约 0.1-0.5 秒/文件
- 中等文件（1-10MB）：约 0.5-2 秒/文件
- 大文件（> 10MB）：约 2-10 秒/文件

实际性能取决于：
- 文件大小和复杂度
- 几何对象数量
- CPU 性能
- 磁盘 I/O 速度

