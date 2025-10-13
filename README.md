# 地理数据转GLTF工具 🌍

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-windows-lightgrey.svg)](https://www.microsoft.com/windows)

一个功能强大的地理数据转换工具，支持将 GeoJSON 和 Shapefile 格式转换为 GLTF 3D 模型格式。提供简洁易用的图形界面和命令行工具。

![Screenshot](screenshot.png)

## ✨ 特性

- 🗺️ **多格式支持**：支持 GeoJSON 和 Shapefile (.shp) 格式
- 🎨 **可视化配置**：图形界面支持颜色、高度、透明度等参数自定义
- 📦 **批量处理**：支持批量转换多个文件，每个文件可独立配置颜色
- 🚀 **独立运行**：提供打包好的 Windows exe 文件，无需安装 Python
- 🎯 **精确转换**：支持点、线、面几何体，自动处理坐标系统
- 📊 **实时反馈**：转换进度实时显示，详细日志输出

## 🎥 功能演示

### 单文件转换
- 选择 GeoJSON 或 Shapefile 文件
- 自定义输出参数（高度、颜色、透明度）
- 一键转换生成 GLTF 文件

### 批量转换
- 扫描整个目录（支持递归）
- 每个文件可单独配置颜色
- 批量处理，显示进度和统计

## 📦 安装使用

### 方式一：使用预编译的 exe 文件（推荐）

1. 从 [Releases](../../releases) 下载最新版本
2. 解压后直接运行 `地理数据转GLTF工具.exe`
3. 无需安装任何依赖

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/Elden-Niu/geo2gltf.git
cd geo2gltf

# 安装依赖
pip install -r requirements.txt

# 运行图形界面
python geo2gltf_gui_simple.py

# 或使用命令行
python geo2gltf.py input.geojson output.gltf
```

## 🛠️ 依赖库

- **geopandas** - 地理数据处理
- **shapely** - 几何操作
- **fiona** - 文件读写
- **pygltflib** - GLTF 文件生成
- **numpy** - 数值计算
- **tkinter** - GUI界面（Python标准库）

## 📖 使用指南

### GUI 界面使用

#### 单文件转换
```
1. 点击"单文件转换"标签页
2. 选择输入文件（GeoJSON 或 Shapefile）
3. 选择输出目录（可选）
4. 调整参数：
   - 高度值：地理要素的挤出高度
   - 启用自动缩放：自动调整比例
   - 默认颜色：点击色块选择
   - 透明度：0.0 到 1.0
5. 点击"开始转换"
```

#### 批量转换
```
1. 点击"批量转换"标签页
2. 选择输入目录和输出目录
3. 配置扫描选项（递归、文件类型）
4. 点击"扫描文件"
5. 双击文件名可单独配置颜色
6. 点击"开始批量转换"
```

### 命令行使用

```bash
# 基本用法
python geo2gltf.py input.geojson output.gltf

# 自定义参数
python geo2gltf.py input.shp output.gltf \
  --height 10.0 \
  --color 0.2,0.6,1.0 \
  --alpha 0.7 \
  --auto-scale

# 批量转换
python batch_convert.py \
  --input-dir ./data \
  --output-dir ./output \
  --recursive \
  --file-types geojson shp
```

## 🔧 开发指南

### 项目结构

```
geo2gltf/
├── geo2gltf.py              # 核心转换模块
├── geo2gltf_gui_simple.py   # GUI主程序
├── batch_convert.py         # 批量转换脚本
├── build_exe.py             # 打包脚本
├── requirements.txt         # 依赖列表
└── README.md                # 文档
```

### 打包为 exe

```bash
# 安装 PyInstaller
pip install pyinstaller

# 运行打包脚本
python build_exe.py

# 可执行文件位于 dist/ 目录
```

### 运行测试

```bash
# 测试单文件转换
python test_converter.py

# 测试批量转换
python batch_convert.py --input-dir test --output-dir test_output
```

## 🌐 应用场景

- **城市规划可视化**：将城市建筑数据转换为3D模型
- **GIS数据展示**：在Web应用中使用 Three.js 或 Cesium 展示
- **游戏开发**：导入 Blender 进行场景设计
- **数据分析可视化**：将分析结果转换为可视化模型

## 🎯 输出格式

输出的 GLTF 文件可以使用以下软件查看：

- [Blender](https://www.blender.org/) - 免费3D软件
- [Cesium](https://cesium.com/) - 在线地理可视化
- [Three.js](https://threejs.org/) - Web 3D库
- 各种支持 GLTF 格式的3D查看器

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📝 更新日志

### v1.0.0 (2025-10-13)
- ✅ 初始版本发布
- ✅ 支持 GeoJSON 和 Shapefile 格式
- ✅ 图形界面和命令行工具
- ✅ 批量转换功能
- ✅ 独立文件颜色配置
- ✅ Windows exe 打包

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

感谢以下开源项目：
- [geopandas](https://geopandas.org/)
- [shapely](https://shapely.readthedocs.io/)
- [pygltflib](https://gitlab.com/dodgyville/pygltflib)
- [PyInstaller](https://www.pyinstaller.org/)

## 📧 联系方式

- 作者：chenhm
- GitHub：[@Elden-Niu](https://github.com/Elden-Niu)
- 项目地址：[https://github.com/Elden-Niu/geo2gltf](https://github.com/Elden-Niu/geo2gltf)

## ⭐ Star History

如果这个项目对你有帮助，请给它一个 Star ⭐！

---

**Made with ❤️ by chenhm**

