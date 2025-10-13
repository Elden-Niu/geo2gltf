# GeoJSON 转 glTF 快速指南

## 概述

本工具现已完全支持 **GeoJSON** 和 **Shapefile** 两种地理数据格式转换为 glTF 3D 模型！

## 为什么选择 GeoJSON？

✅ **单文件格式** - 不像 Shapefile 需要多个配套文件（.shp, .shx, .dbf, .prj）  
✅ **原生 UTF-8** - 完美支持中文和各种字符，无编码问题  
✅ **Web 友好** - JSON 格式，易于与 Web 应用集成  
✅ **易于编辑** - 文本格式，可以直接用编辑器查看和修改  
✅ **标准化** - 遵循 RFC 7946 标准，通用性强  

## 快速开始

### 方法 1: GUI 图形界面（最简单）

```bash
python geo2gltf_gui.py
```

1. 点击"浏览"选择你的 `.geojson` 或 `.json` 文件
2. 选择输出目录
3. 调整参数（高度、颜色、透明度）
4. 点击"开始转换"

### 方法 2: 命令行

```bash
# 基本转换
python geo2gltf.py input.geojson output.gltf

# 自定义参数
python geo2gltf.py buildings.geojson output.gltf --height 10 --color "0.2,0.6,1.0" --alpha 0.8
```

## 测试示例

运行示例生成器：

```bash
# 创建并转换示例 GeoJSON 文件
python example_geojson.py

# 仅创建示例文件
python example_geojson.py --create

# 仅转换示例文件
python example_geojson.py --convert
```

这将在 `examples/` 目录下创建以下示例：
- `example_buildings.geojson` - 建筑物多边形示例
- `example_roads.geojson` - 道路线段示例
- `example_pois.geojson` - 地标点示例
- `example_mixed.geojson` - 混合几何类型示例

## GeoJSON 格式示例

### 最简单的 GeoJSON（单个多边形）

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "建筑物A"
      },
      "geometry": {
        "type": "Polygon",
        "coordinates": [[
          [116.397428, 39.907616],
          [116.398428, 39.907616],
          [116.398428, 39.908616],
          [116.397428, 39.908616],
          [116.397428, 39.907616]
        ]]
      }
    }
  ]
}
```

### 支持的几何类型

- ✅ `Point` - 点
- ✅ `MultiPoint` - 多点
- ✅ `LineString` - 线段
- ✅ `MultiLineString` - 多线段
- ✅ `Polygon` - 多边形
- ✅ `MultiPolygon` - 多多边形

## 转换参数说明

| 参数 | 说明 | 默认值 | 示例 |
|------|------|--------|------|
| `--height` | 3D 高度（占数据尺寸的百分比） | 5.0 | `--height 10` |
| `--color` | RGB 颜色值 | 红色 (1.0,0.0,0.0) | `--color "0.2,0.6,1.0"` |
| `--alpha` | 透明度 | 0.5 | `--alpha 0.8` |
| `--no-auto-scale` | 禁用自动缩放 | 启用 | `--no-auto-scale` |

## 使用场景示例

### 场景 1: Web 地图导出

```bash
# 从 Web 地图导出的 GeoJSON
python geo2gltf.py web_export.geojson model.gltf --height 8 --color "0.3,0.7,0.9"
```

### 场景 2: QGIS 导出

```bash
# QGIS 导出的 GeoJSON 文件
python geo2gltf.py qgis_export.geojson output.gltf --height 12 --alpha 0.9
```

### 场景 3: 自定义 GeoJSON

```python
# 使用 Python 创建自定义 GeoJSON
import json

geojson = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[...]]
            }
        }
    ]
}

with open("custom.geojson", "w") as f:
    json.dump(geojson, f)
```

然后转换：
```bash
python geo2gltf.py custom.geojson output.gltf
```

## 常见问题

### Q: GeoJSON 和 Shapefile 有什么区别？

**GeoJSON:**
- ✅ 单文件，易于分享
- ✅ 文本格式，可读性好
- ✅ 无编码问题
- ⚠️ 文件可能较大（文本格式）

**Shapefile:**
- ✅ 行业标准，兼容性好
- ✅ 二进制格式，文件较小
- ⚠️ 需要多个配套文件
- ⚠️ 可能有编码问题

### Q: 如何将 Shapefile 转换为 GeoJSON？

使用 GDAL/OGR:
```bash
ogr2ogr -f GeoJSON output.geojson input.shp
```

或使用 Python:
```python
import geopandas as gpd
gdf = gpd.read_file("input.shp")
gdf.to_file("output.geojson", driver='GeoJSON')
```

### Q: 坐标系统如何处理？

- GeoJSON 默认使用 WGS84 (EPSG:4326)
- 工具会保持原始坐标系统不变
- 建议在转换前统一坐标系统

### Q: 文件太大怎么办？

1. 简化几何体（减少顶点数）
2. 使用 QGIS 或其他工具简化
3. 分块处理大文件

## 在线工具

- **GeoJSON 验证**: http://geojson.io/
- **glTF 查看器**: https://gltf-viewer.donmccurdy.com/
- **坐标转换**: https://epsg.io/

## 工具对比

| 功能 | geo2gltf.py (新) | shp2gltf.py (旧) |
|------|------------------|------------------|
| GeoJSON 支持 | ✅ | ❌ |
| Shapefile 支持 | ✅ | ✅ |
| 自动格式检测 | ✅ | ❌ |
| GUI 界面 | geo2gltf_gui.py | shp2gltf_gui.py |
| 推荐使用 | ✅ 是 | ⚠️ 仅用于 SHP |

## 技术支持

遇到问题？
1. 查看 README.md 获取详细文档
2. 运行示例：`python example_geojson.py`
3. 提交 Issue 或 Pull Request

---

**快乐转换！** 🎉

