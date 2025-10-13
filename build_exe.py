#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 生成 Windows 可执行文件
"""

import PyInstaller.__main__
import os
from pathlib import Path

# 获取当前目录
current_dir = Path(__file__).parent

# 检查logo是否存在
logo_path = current_dir / "logo.png"
has_logo = logo_path.exists()

# 构建PyInstaller参数
args = [
    str(current_dir / 'geo2gltf_gui_simple.py'),  # 主脚本
    '--name=地理数据转GLTF工具',  # 程序名称
    '--onefile',  # 打包成单个exe
    '--windowed',  # 不显示控制台窗口
    '--clean',  # 清理临时文件
    '--noconfirm',  # 不询问确认
    # 添加隐藏导入
    '--hidden-import=tkinter',
    '--hidden-import=tkinter.ttk',
    '--hidden-import=tkinter.filedialog',
    '--hidden-import=tkinter.messagebox',
    '--hidden-import=tkinter.colorchooser',
    '--hidden-import=geo2gltf',
    '--hidden-import=pygltflib',
    '--hidden-import=geopandas',
    '--hidden-import=shapely',
    '--hidden-import=shapely.geometry',
    '--hidden-import=fiona',
    '--hidden-import=numpy',
    '--hidden-import=pandas',
    '--hidden-import=PIL',
    '--hidden-import=PIL.Image',
    '--hidden-import=PIL.ImageTk',
    '--hidden-import=mapbox_earcut',
    '--collect-all=geopandas',
    '--collect-all=fiona',
    '--collect-all=shapely',
    '--copy-metadata=geopandas',
    '--copy-metadata=fiona',
    '--copy-metadata=shapely',
]

# 如果logo存在，添加图标
if has_logo:
    print(f"找到 logo.png，将其添加为图标和数据文件")
    args.extend([
        f'--add-data={logo_path};.',  # 添加logo作为数据文件
    ])
else:
    print("未找到 logo.png，将不包含图标")

print("\n开始打包...")
print(f"参数: {' '.join(args)}")
print("-" * 60)

# 运行PyInstaller
PyInstaller.__main__.run(args)

print("-" * 60)
print("打包完成！")
print(f"可执行文件位于: {current_dir / 'dist' / '地理数据转GLTF工具.exe'}")

