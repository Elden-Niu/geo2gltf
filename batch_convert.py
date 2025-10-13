#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量转换脚本
支持批量将 GeoJSON 和 Shapefile 文件转换为 glTF 格式
"""

import argparse
import logging
from pathlib import Path
from typing import List, Tuple
import sys
import time

# 导入转换器
from geo2gltf import Geo2GLTFConverter, parse_color

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def find_geo_files(input_dir: Path, recursive: bool = False, extensions: List[str] = None) -> List[Path]:
    """
    查找目录中的地理数据文件
    
    Args:
        input_dir: 输入目录
        recursive: 是否递归搜索子目录
        extensions: 要搜索的文件扩展名列表
        
    Returns:
        找到的文件路径列表
    """
    if extensions is None:
        extensions = ['.geojson', '.json', '.shp']
    
    files = []
    
    if recursive:
        # 递归搜索
        for ext in extensions:
            files.extend(input_dir.rglob(f'*{ext}'))
    else:
        # 仅搜索当前目录
        for ext in extensions:
            files.extend(input_dir.glob(f'*{ext}'))
    
    return sorted(files)


def batch_convert(
    input_dir: str,
    output_dir: str,
    recursive: bool = False,
    height: float = 5.0,
    color: Tuple[float, float, float] = (1.0, 0.0, 0.0),
    alpha: float = 0.5,
    auto_scale: bool = True,
    file_extensions: List[str] = None
):
    """
    批量转换地理数据文件
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        recursive: 是否递归搜索子目录
        height: 默认高度
        color: RGB颜色
        alpha: 透明度
        auto_scale: 是否自动缩放
        file_extensions: 要处理的文件扩展名列表
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 验证输入目录
    if not input_path.exists():
        logger.error(f"输入目录不存在: {input_dir}")
        return 1
    
    if not input_path.is_dir():
        logger.error(f"输入路径不是目录: {input_dir}")
        return 1
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_path}")
    
    # 查找所有地理数据文件
    logger.info(f"正在搜索文件...")
    files = find_geo_files(input_path, recursive, file_extensions)
    
    if not files:
        logger.warning(f"在 {input_dir} 中未找到地理数据文件")
        return 0
    
    logger.info(f"找到 {len(files)} 个文件待转换")
    logger.info("=" * 70)
    
    # 统计信息
    success_count = 0
    failed_count = 0
    skipped_count = 0
    start_time = time.time()
    
    # 批量转换
    for idx, input_file in enumerate(files, 1):
        try:
            # 计算相对路径（用于保持目录结构）
            if recursive:
                rel_path = input_file.relative_to(input_path)
                output_file = output_path / rel_path.parent / f"{input_file.stem}.gltf"
            else:
                output_file = output_path / f"{input_file.stem}.gltf"
            
            # 创建输出文件的父目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"\n[{idx}/{len(files)}] 正在转换: {input_file.name}")
            logger.info(f"  输入: {input_file}")
            logger.info(f"  输出: {output_file}")
            
            # 检查输出文件是否已存在
            if output_file.exists():
                logger.warning(f"  ⚠ 输出文件已存在，将覆盖")
            
            # 执行转换
            converter = Geo2GLTFConverter(
                default_height=height,
                auto_scale=auto_scale
            )
            
            converter.convert(
                str(input_file),
                str(output_file),
                color=color,
                alpha=alpha
            )
            
            # 获取文件大小
            output_size = output_file.stat().st_size / 1024  # KB
            logger.info(f"  ✓ 转换成功！输出文件大小: {output_size:.2f} KB")
            success_count += 1
            
        except Exception as e:
            logger.error(f"  ✗ 转换失败: {e}")
            failed_count += 1
            continue
    
    # 输出统计信息
    elapsed_time = time.time() - start_time
    logger.info("\n" + "=" * 70)
    logger.info("批量转换完成!")
    logger.info("=" * 70)
    logger.info(f"总文件数: {len(files)}")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {failed_count}")
    logger.info(f"跳过: {skipped_count}")
    logger.info(f"总耗时: {elapsed_time:.2f} 秒")
    
    if success_count > 0:
        logger.info(f"平均速度: {elapsed_time/success_count:.2f} 秒/文件")
    
    return 0 if failed_count == 0 else 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='批量将地理数据文件转换为 glTF 格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 批量转换当前目录下的所有文件
  python batch_convert.py input_dir output_dir
  
  # 递归转换所有子目录
  python batch_convert.py input_dir output_dir --recursive
  
  # 只转换 GeoJSON 文件
  python batch_convert.py input_dir output_dir --extensions .geojson .json
  
  # 自定义参数
  python batch_convert.py input_dir output_dir --height 20 --color 0,128,255 --alpha 0.7
        """
    )
    
    parser.add_argument('input_dir', help='输入目录（包含 GeoJSON 或 Shapefile 文件）')
    parser.add_argument('output_dir', help='输出目录（生成的 glTF 文件）')
    
    parser.add_argument('-r', '--recursive', action='store_true',
                       help='递归搜索子目录')
    
    parser.add_argument('--extensions', nargs='+',
                       default=['.geojson', '.json', '.shp'],
                       help='要处理的文件扩展名（默认: .geojson .json .shp）')
    
    parser.add_argument('--height', type=float, default=5.0,
                       help='默认高度（百分比），默认5%%')
    
    parser.add_argument('--color', default='1.0,0.0,0.0',
                       help='颜色设置，格式为R,G,B（0-1或0-255范围），默认红色')
    
    parser.add_argument('--alpha', type=float, default=0.5,
                       help='透明度（0-1范围），默认0.5')
    
    parser.add_argument('--no-auto-scale', action='store_true',
                       help='禁用自动缩放高度功能')
    
    args = parser.parse_args()
    
    # 解析颜色
    color = parse_color(args.color)
    
    # 执行批量转换
    try:
        return batch_convert(
            input_dir=args.input_dir,
            output_dir=args.output_dir,
            recursive=args.recursive,
            height=args.height,
            color=color,
            alpha=args.alpha,
            auto_scale=not args.no_auto_scale,
            file_extensions=args.extensions
        )
    except KeyboardInterrupt:
        logger.info("\n\n用户中断操作")
        return 1
    except Exception as e:
        logger.error(f"批量转换失败: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

