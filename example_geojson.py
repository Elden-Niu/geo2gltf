#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GeoJSON 测试示例
演示如何创建和转换 GeoJSON 文件到 glTF
"""

import json
from pathlib import Path

# 创建示例 GeoJSON 数据
def create_sample_geojson():
    """创建一个简单的 GeoJSON 示例文件"""
    
    # 示例1: 简单多边形（建筑物）
    geojson_polygon = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "示例建筑1",
                    "type": "building"
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
            },
            {
                "type": "Feature",
                "properties": {
                    "name": "示例建筑2",
                    "type": "building"
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [116.399428, 39.907616],
                        [116.400428, 39.907616],
                        [116.400428, 39.908616],
                        [116.399428, 39.908616],
                        [116.399428, 39.907616]
                    ]]
                }
            }
        ]
    }
    
    # 示例2: 线段（道路）
    geojson_linestring = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "示例道路",
                    "type": "road"
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [116.397428, 39.906616],
                        [116.398428, 39.907116],
                        [116.399428, 39.907616],
                        [116.400428, 39.908116]
                    ]
                }
            }
        ]
    }
    
    # 示例3: 点（地标）
    geojson_points = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "name": "地标1",
                    "type": "poi"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [116.397428, 39.907616]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "name": "地标2",
                    "type": "poi"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [116.399428, 39.909616]
                }
            }
        ]
    }
    
    # 示例4: 混合几何类型
    geojson_mixed = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "多边形区域"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [116.395, 39.905],
                        [116.402, 39.905],
                        [116.402, 39.910],
                        [116.395, 39.910],
                        [116.395, 39.905]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "中心线"},
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [116.395, 39.9075],
                        [116.402, 39.9075]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "中心点"},
                "geometry": {
                    "type": "Point",
                    "coordinates": [116.3985, 39.9075]
                }
            }
        ]
    }
    
    # 保存文件
    output_dir = Path(__file__).parent / "examples"
    output_dir.mkdir(exist_ok=True)
    
    samples = {
        "example_buildings.geojson": geojson_polygon,
        "example_roads.geojson": geojson_linestring,
        "example_pois.geojson": geojson_points,
        "example_mixed.geojson": geojson_mixed
    }
    
    for filename, data in samples.items():
        filepath = output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✓ 创建示例文件: {filepath}")
    
    return output_dir

def convert_examples():
    """转换示例文件为 glTF"""
    from geo2gltf import Geo2GLTFConverter
    
    examples_dir = Path(__file__).parent / "examples"
    if not examples_dir.exists():
        print("示例文件不存在，先创建...")
        create_sample_geojson()
    
    # 转换参数配置
    configs = {
        "example_buildings.geojson": {
            "height": 8.0,
            "color": (0.8, 0.4, 0.2),  # 橙色
            "alpha": 0.8
        },
        "example_roads.geojson": {
            "height": 3.0,
            "color": (0.3, 0.3, 0.3),  # 灰色
            "alpha": 0.9
        },
        "example_pois.geojson": {
            "height": 5.0,
            "color": (1.0, 0.2, 0.2),  # 红色
            "alpha": 1.0
        },
        "example_mixed.geojson": {
            "height": 5.0,
            "color": (0.2, 0.6, 1.0),  # 蓝色
            "alpha": 0.7
        }
    }
    
    print("\n开始转换示例文件...\n")
    
    for filename, config in configs.items():
        input_file = examples_dir / filename
        if not input_file.exists():
            print(f"⚠ 跳过不存在的文件: {filename}")
            continue
        
        output_file = examples_dir / (input_file.stem + ".gltf")
        
        print(f"转换: {filename} -> {output_file.name}")
        print(f"  高度: {config['height']}%")
        print(f"  颜色: RGB{config['color']}")
        print(f"  透明度: {config['alpha']}")
        
        converter = Geo2GLTFConverter(
            default_height=config['height'],
            auto_scale=True
        )
        
        try:
            converter.convert(
                str(input_file),
                str(output_file),
                config['color'],
                config['alpha']
            )
            print(f"✓ 转换成功: {output_file}\n")
        except Exception as e:
            print(f"✗ 转换失败: {e}\n")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GeoJSON 示例生成和转换工具')
    parser.add_argument('--create', action='store_true', help='创建示例 GeoJSON 文件')
    parser.add_argument('--convert', action='store_true', help='转换示例文件为 glTF')
    parser.add_argument('--all', action='store_true', help='创建并转换示例文件')
    
    args = parser.parse_args()
    
    if args.all or (not args.create and not args.convert):
        # 默认行为：创建并转换
        print("=" * 60)
        print("GeoJSON 示例生成和转换")
        print("=" * 60 + "\n")
        
        print("步骤 1: 创建示例 GeoJSON 文件")
        print("-" * 60)
        output_dir = create_sample_geojson()
        
        print("\n步骤 2: 转换为 glTF 格式")
        print("-" * 60)
        convert_examples()
        
        print("=" * 60)
        print(f"完成! 所有文件保存在: {output_dir}")
        print("=" * 60)
        
    elif args.create:
        print("创建示例 GeoJSON 文件...")
        output_dir = create_sample_geojson()
        print(f"\n完成! 文件保存在: {output_dir}")
        
    elif args.convert:
        print("转换示例文件为 glTF...")
        convert_examples()
        print("\n转换完成!")

if __name__ == '__main__':
    main()

