#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHP转GLTF工具使用示例

本文件演示了如何使用shp2gltf.py工具进行各种转换任务
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """运行命令并输出结果"""
    print(f"\n{'='*50}")
    print(f"示例: {description}")
    print(f"命令: {cmd}")
    print(f"{'='*50}")
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("✅ 执行成功!")
        print(result.stdout)
    else:
        print("❌ 执行失败!")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """主函数 - 展示各种使用示例"""
    print("SHP转GLTF工具使用示例")
    print("支持的功能：")
    print("• 点、线、面几何体转换")
    print("• 自定义高度设置")
    print("• 颜色和透明度调整")
    print("• 半透明材质生成")
    
    # 检查示例文件是否存在
    shp_file = "1.shp"
    if not os.path.exists(shp_file):
        print(f"\n⚠️ 找不到示例SHP文件: {shp_file}")
        print("请确保当前目录下有SHP文件用于测试")
        return
    
    # 示例1: 基本转换（使用默认参数）
    success1 = run_command(
        f"python shp2gltf.py {shp_file} output_basic.gltf",
        "基本转换 - 使用默认参数（20层高度，红色，0.5透明度）"
    )
    
    # 示例2: 自定义高度
    success2 = run_command(
        f"python shp2gltf.py {shp_file} output_height50.gltf --height 50",
        "自定义高度 - 设置为50层"
    )
    
    # 示例3: 蓝色半透明（RGB 0-255格式）
    success3 = run_command(
        f'python shp2gltf.py {shp_file} output_blue.gltf --color "0,0,255" --alpha 0.7',
        "蓝色半透明 - RGB值使用0-255格式"
    )
    
    # 示例4: 绿色不透明（RGB 0-1格式）
    success4 = run_command(
        f'python shp2gltf.py {shp_file} output_green.gltf --color "0.0,1.0,0.0" --alpha 1.0',
        "绿色不透明 - RGB值使用0-1格式"
    )
    
    # 示例5: 组合参数
    success5 = run_command(
        f'python shp2gltf.py {shp_file} output_custom.gltf --height 30 --color "255,165,0" --alpha 0.8',
        "组合参数 - 30层高度，橙色，0.8透明度"
    )
    
    # 总结
    successful = sum([success1, success2, success3, success4, success5])
    total = 5
    
    print(f"\n{'='*50}")
    print("执行总结")
    print(f"{'='*50}")
    print(f"成功执行: {successful}/{total} 个示例")
    
    if successful == total:
        print("🎉 所有示例都执行成功！")
        print("\n生成的文件:")
        for filename in ["output_basic.gltf", "output_height50.gltf", "output_blue.gltf", 
                        "output_green.gltf", "output_custom.gltf"]:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"  • {filename} ({size:,} 字节)")
    else:
        print(f"⚠️  {total - successful} 个示例执行失败")
    
    print("\n💡 使用提示:")
    print("• 颜色格式支持 0-1 范围（如 '1.0,0.0,0.0'）和 0-255 范围（如 '255,0,0'）")
    print("• 透明度范围为 0.0（完全透明）到 1.0（完全不透明）")
    print("• 高度单位为层数，可以是任意正浮点数")
    print("• 生成的GLTF文件包含半透明PBR材质，适合在3D应用中使用")

if __name__ == "__main__":
    main()
