#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHP转GLTF工具安装脚本
"""

import sys
import subprocess
import pkg_resources
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    print(f"Python版本检查通过: {sys.version}")
    return True

def install_requirements():
    """安装依赖包"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("错误: requirements.txt文件不存在")
        return False
    
    print("正在安装依赖包...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        print("依赖包安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"依赖包安装失败: {e}")
        return False

def check_dependencies():
    """检查依赖包是否正确安装"""
    required_packages = [
        'geopandas',
        'shapely', 
        'pygltflib',
        'numpy',
        'pyproj',
        'matplotlib'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            pkg_resources.get_distribution(package)
            print(f"✓ {package} 已安装")
        except pkg_resources.DistributionNotFound:
            print(f"✗ {package} 未安装")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def main():
    """主安装函数"""
    print("SHP转GLTF工具 - 安装程序")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        return 1
    
    # 安装依赖包
    if not install_requirements():
        return 1
    
    # 检查依赖包
    success, missing = check_dependencies()
    
    if success:
        print("\n" + "=" * 40)
        print("安装完成! 🎉")
        print("\n使用方法:")
        print("  python shp2gltf.py input.shp output.gltf")
        print("\n运行测试:")
        print("  python test_converter.py")
        print("\n查看帮助:")
        print("  python shp2gltf.py --help")
        return 0
    else:
        print(f"\n安装失败，以下包未能正确安装: {', '.join(missing)}")
        print("请尝试手动安装:")
        for package in missing:
            print(f"  pip install {package}")
        return 1

if __name__ == "__main__":
    exit(main())
