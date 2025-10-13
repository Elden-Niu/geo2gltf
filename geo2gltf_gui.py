#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用地理数据转GLTF转换工具 - GUI版本（现代化iOS风格）
支持 GeoJSON 和 Shapefile (SHP) 格式
提供图形化界面，方便选择文件、设置参数
支持单文件转换和批量转换（每个文件独立配置颜色）
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Tuple, List, Dict
import threading
import logging
import time
from PIL import Image, ImageTk

# 导入转换器
from geo2gltf import Geo2GLTFConverter, parse_color

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# iOS风格颜色方案
COLORS = {
    'bg': '#F5F5F7',  # 浅灰背景
    'card': '#FFFFFF',  # 白色卡片
    'primary': '#007AFF',  # iOS蓝
    'secondary': '#5856D6',  # iOS紫
    'success': '#34C759',  # iOS绿
    'danger': '#FF3B30',  # iOS红
    'warning': '#FF9500',  # iOS橙
    'text': '#1D1D1F',  # 深色文字
    'text_secondary': '#86868B',  # 次要文字
    'border': '#D2D2D7',  # 边框
    'shadow': '#00000010',  # 阴影
}


class Geo2GLTFGui:
    """通用地理数据转GLTF GUI应用（支持 GeoJSON 和 Shapefile）"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("地理数据转GLTF转换工具 (GeoJSON/SHP)")
        self.root.geometry("750x650")
        self.root.resizable(True, True)
        
        # 单文件转换变量
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # 批量转换变量
        self.batch_input_dir = tk.StringVar()
        self.batch_output_dir = tk.StringVar()
        self.recursive = tk.BooleanVar(value=False)
        self.file_type_geojson = tk.BooleanVar(value=True)
        self.file_type_shp = tk.BooleanVar(value=True)
        
        # 共享参数
        self.height_value = tk.DoubleVar(value=5.0)  # 默认高度5%
        self.color_rgb = (0.2, 0.6, 1.0)  # 默认蓝色
        self.alpha_value = tk.DoubleVar(value=0.7)
        self.auto_scale = tk.BooleanVar(value=True)
        
        # 批量转换统计
        self.batch_total = 0
        self.batch_current = 0
        self.batch_success = 0
        self.batch_failed = 0
        self.is_batch_converting = False
        
        # 创建UI
        self.create_widgets()
        
    def create_widgets(self):
        """创建UI组件"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="地理数据 转 GLTF 转换工具", 
                              font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        # 副标题
        subtitle_label = ttk.Label(main_frame, text="支持 GeoJSON (.geojson, .json) 和 Shapefile (.shp)", 
                                  font=("Arial", 9), foreground="gray")
        subtitle_label.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # 创建单文件转换标签页
        self.single_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.single_frame, text="单文件转换")
        self.create_single_conversion_tab()
        
        # 创建批量转换标签页
        self.batch_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.batch_frame, text="批量转换")
        self.create_batch_conversion_tab()
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def create_single_conversion_tab(self):
        """创建单文件转换标签页"""
        
        # 输入文件选择
        ttk.Label(self.single_frame, text="输入文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.single_frame, textvariable=self.input_file, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(self.single_frame, text="浏览...", command=self.browse_input).grid(row=0, column=2, pady=5)
        
        # 输出目录选择
        ttk.Label(self.single_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.single_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(self.single_frame, text="浏览...", command=self.browse_output).grid(row=1, column=2, pady=5)
        
        # 分隔线
        ttk.Separator(self.single_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 参数设置区域
        params_frame = ttk.LabelFrame(self.single_frame, text="参数设置", padding="10")
        params_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 高度设置
        ttk.Label(params_frame, text="高度值 (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        height_frame = ttk.Frame(params_frame)
        height_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.height_scale = ttk.Scale(height_frame, from_=1, to=50, variable=self.height_value, 
                                     orient=tk.HORIZONTAL, length=300, command=self.update_height_label)
        self.height_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        self.height_label = ttk.Label(height_frame, text=f"{self.height_value.get():.1f}%")
        self.height_label.pack(side=tk.LEFT)
        
        ttk.Label(params_frame, text="(高度占数据尺寸的百分比)", 
                 font=("Arial", 8), foreground="gray").grid(row=1, column=1, columnspan=2, sticky=tk.W)
        
        # 自动缩放选项
        ttk.Checkbutton(params_frame, text="启用自动缩放", variable=self.auto_scale).grid(
            row=2, column=1, sticky=tk.W, pady=10)
        
        # 颜色设置
        ttk.Label(params_frame, text="颜色:").grid(row=3, column=0, sticky=tk.W, pady=5)
        color_frame = ttk.Frame(params_frame)
        color_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.color_preview = tk.Canvas(color_frame, width=40, height=25, bg=self.rgb_to_hex(self.color_rgb))
        self.color_preview.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(color_frame, text="选择颜色...", command=self.choose_color).pack(side=tk.LEFT)
        
        # 透明度设置
        ttk.Label(params_frame, text="透明度:").grid(row=4, column=0, sticky=tk.W, pady=5)
        alpha_frame = ttk.Frame(params_frame)
        alpha_frame.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.alpha_scale = ttk.Scale(alpha_frame, from_=0, to=1, variable=self.alpha_value, 
                                    orient=tk.HORIZONTAL, length=300, command=self.update_alpha_label)
        self.alpha_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        self.alpha_label = ttk.Label(alpha_frame, text=f"{self.alpha_value.get():.2f}")
        self.alpha_label.pack(side=tk.LEFT)
        
        # 分隔线
        ttk.Separator(self.single_frame, orient='horizontal').grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 转换按钮
        self.convert_button = ttk.Button(self.single_frame, text="开始转换", command=self.start_conversion)
        self.convert_button.grid(row=5, column=0, columnspan=3, pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(self.single_frame, mode='indeterminate', length=400)
        self.progress.grid(row=6, column=0, columnspan=3, pady=5)
        
        # 状态文本框
        status_frame = ttk.LabelFrame(self.single_frame, text="转换日志", padding="5")
        status_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.status_text = tk.Text(status_frame, height=8, width=70, wrap=tk.WORD)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # 配置单文件转换标签页的行列权重
        self.single_frame.columnconfigure(1, weight=1)
        self.single_frame.rowconfigure(7, weight=1)
        
    def create_batch_conversion_tab(self):
        """创建批量转换标签页"""
        
        # 输入目录选择
        ttk.Label(self.batch_frame, text="输入目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.batch_frame, textvariable=self.batch_input_dir, width=50).grid(row=0, column=1, pady=5, padx=5)
        ttk.Button(self.batch_frame, text="浏览...", command=self.browse_batch_input).grid(row=0, column=2, pady=5)
        
        # 输出目录选择
        ttk.Label(self.batch_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(self.batch_frame, textvariable=self.batch_output_dir, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(self.batch_frame, text="浏览...", command=self.browse_batch_output).grid(row=1, column=2, pady=5)
        
        # 选项设置区域
        options_frame = ttk.LabelFrame(self.batch_frame, text="批量转换选项", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 递归选项
        ttk.Checkbutton(options_frame, text="递归搜索子目录", variable=self.recursive).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        
        # 文件类型选择
        ttk.Label(options_frame, text="文件类型:").grid(row=1, column=0, sticky=tk.W, pady=5)
        filetype_frame = ttk.Frame(options_frame)
        filetype_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(filetype_frame, text="GeoJSON (.geojson, .json)", 
                       variable=self.file_type_geojson).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Checkbutton(filetype_frame, text="Shapefile (.shp)", 
                       variable=self.file_type_shp).pack(side=tk.LEFT)
        
        # 分隔线
        ttk.Separator(self.batch_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 参数设置区域（共享参数）
        batch_params_frame = ttk.LabelFrame(self.batch_frame, text="参数设置", padding="10")
        batch_params_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 高度设置
        ttk.Label(batch_params_frame, text="高度值 (%):").grid(row=0, column=0, sticky=tk.W, pady=5)
        batch_height_frame = ttk.Frame(batch_params_frame)
        batch_height_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.batch_height_scale = ttk.Scale(batch_height_frame, from_=1, to=50, variable=self.height_value, 
                                           orient=tk.HORIZONTAL, length=300, command=self.update_height_label)
        self.batch_height_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_height_label = ttk.Label(batch_height_frame, text=f"{self.height_value.get():.1f}%")
        self.batch_height_label.pack(side=tk.LEFT)
        
        # 自动缩放选项
        ttk.Checkbutton(batch_params_frame, text="启用自动缩放", variable=self.auto_scale).grid(
            row=1, column=1, sticky=tk.W, pady=5)
        
        # 颜色和透明度（简化显示）
        ttk.Label(batch_params_frame, text="颜色:").grid(row=2, column=0, sticky=tk.W, pady=5)
        batch_color_frame = ttk.Frame(batch_params_frame)
        batch_color_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.batch_color_preview = tk.Canvas(batch_color_frame, width=40, height=25, bg=self.rgb_to_hex(self.color_rgb))
        self.batch_color_preview.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(batch_color_frame, text="选择颜色...", command=self.choose_color_batch).pack(side=tk.LEFT)
        
        ttk.Label(batch_params_frame, text="透明度:").grid(row=3, column=0, sticky=tk.W, pady=5)
        batch_alpha_frame = ttk.Frame(batch_params_frame)
        batch_alpha_frame.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.batch_alpha_scale = ttk.Scale(batch_alpha_frame, from_=0, to=1, variable=self.alpha_value, 
                                          orient=tk.HORIZONTAL, length=300, command=self.update_alpha_label)
        self.batch_alpha_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        self.batch_alpha_label = ttk.Label(batch_alpha_frame, text=f"{self.alpha_value.get():.2f}")
        self.batch_alpha_label.pack(side=tk.LEFT)
        
        # 分隔线
        ttk.Separator(self.batch_frame, orient='horizontal').grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # 批量转换按钮
        self.batch_convert_button = ttk.Button(self.batch_frame, text="开始批量转换", command=self.start_batch_conversion)
        self.batch_convert_button.grid(row=6, column=0, columnspan=3, pady=10)
        
        # 进度信息
        progress_info_frame = ttk.Frame(self.batch_frame)
        progress_info_frame.grid(row=7, column=0, columnspan=3, pady=5)
        
        self.batch_progress_label = ttk.Label(progress_info_frame, text="准备开始...")
        self.batch_progress_label.pack()
        
        # 进度条
        self.batch_progress = ttk.Progressbar(self.batch_frame, mode='determinate', length=400)
        self.batch_progress.grid(row=8, column=0, columnspan=3, pady=5)
        
        # 状态文本框
        batch_status_frame = ttk.LabelFrame(self.batch_frame, text="批量转换日志", padding="5")
        batch_status_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.batch_status_text = tk.Text(batch_status_frame, height=8, width=70, wrap=tk.WORD)
        self.batch_status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        batch_scrollbar = ttk.Scrollbar(batch_status_frame, command=self.batch_status_text.yview)
        batch_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.batch_status_text.config(yscrollcommand=batch_scrollbar.set)
        
        # 配置批量转换标签页的行列权重
        self.batch_frame.columnconfigure(1, weight=1)
        self.batch_frame.rowconfigure(9, weight=1)
    
    def rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """将RGB(0-1)转换为十六进制颜色"""
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_height_label(self, value):
        """更新高度标签"""
        self.height_label.config(text=f"{float(value):.1f}%")
        # 同步更新批量转换标签页的高度标签
        if hasattr(self, 'batch_height_label'):
            self.batch_height_label.config(text=f"{float(value):.1f}%")
    
    def update_alpha_label(self, value):
        """更新透明度标签"""
        self.alpha_label.config(text=f"{float(value):.2f}")
        # 同步更新批量转换标签页的透明度标签
        if hasattr(self, 'batch_alpha_label'):
            self.batch_alpha_label.config(text=f"{float(value):.2f}")
    
    def browse_input(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择地理数据文件",
            filetypes=[
                ("所有支持格式", "*.geojson *.json *.shp"),
                ("GeoJSON", "*.geojson *.json"),
                ("Shapefile", "*.shp"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.input_file.set(filename)
            # 自动设置输出目录为输入文件所在目录
            if not self.output_dir.get():
                self.output_dir.set(str(Path(filename).parent))
    
    def browse_output(self):
        """浏览输出目录"""
        dirname = filedialog.askdirectory(title="选择输出目录")
        if dirname:
            self.output_dir.set(dirname)
    
    def browse_batch_input(self):
        """浏览批量转换输入目录"""
        dirname = filedialog.askdirectory(title="选择输入目录")
        if dirname:
            self.batch_input_dir.set(dirname)
            # 自动设置输出目录
            if not self.batch_output_dir.get():
                self.batch_output_dir.set(dirname + "_output")
    
    def browse_batch_output(self):
        """浏览批量转换输出目录"""
        dirname = filedialog.askdirectory(title="选择输出目录")
        if dirname:
            self.batch_output_dir.set(dirname)
    
    def choose_color(self):
        """选择颜色（单文件转换）"""
        # 转换当前颜色为RGB(0-255)
        current_color = tuple(int(c * 255) for c in self.color_rgb)
        
        color = colorchooser.askcolor(
            title="选择颜色",
            initialcolor=current_color
        )
        
        if color[0]:  # color[0] 是 RGB(0-255) 元组
            # 转换为 0-1 范围
            self.color_rgb = tuple(c / 255.0 for c in color[0])
            self.color_preview.config(bg=color[1])  # color[1] 是十六进制颜色
            # 同步更新批量转换标签页的颜色预览
            if hasattr(self, 'batch_color_preview'):
                self.batch_color_preview.config(bg=color[1])
    
    def choose_color_batch(self):
        """选择颜色（批量转换）"""
        # 转换当前颜色为RGB(0-255)
        current_color = tuple(int(c * 255) for c in self.color_rgb)
        
        color = colorchooser.askcolor(
            title="选择颜色",
            initialcolor=current_color
        )
        
        if color[0]:  # color[0] 是 RGB(0-255) 元组
            # 转换为 0-1 范围
            self.color_rgb = tuple(c / 255.0 for c in color[0])
            self.batch_color_preview.config(bg=color[1])  # color[1] 是十六进制颜色
            # 同步更新单文件转换标签页的颜色预览
            if hasattr(self, 'color_preview'):
                self.color_preview.config(bg=color[1])
    
    def log_message(self, message: str):
        """记录消息到状态文本框"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def start_conversion(self):
        """开始转换"""
        # 验证输入
        if not self.input_file.get():
            messagebox.showerror("错误", "请选择输入文件！")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("错误", "请选择输出目录！")
            return
        
        input_path = Path(self.input_file.get())
        if not input_path.exists():
            messagebox.showerror("错误", "输入文件不存在！")
            return
        
        # 验证文件类型
        if input_path.suffix.lower() not in ['.geojson', '.json', '.shp']:
            result = messagebox.askyesno(
                "警告", 
                f"文件扩展名 '{input_path.suffix}' 可能不受支持。\n\n是否继续尝试转换？"
            )
            if not result:
                return
        
        output_dir = Path(self.output_dir.get())
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {e}")
                return
        
        # 生成输出文件名
        output_filename = input_path.stem + ".gltf"
        output_path = output_dir / output_filename
        
        # 禁用按钮，显示进度条
        self.convert_button.config(state=tk.DISABLED)
        self.progress.start()
        self.status_text.delete(1.0, tk.END)
        
        # 在新线程中执行转换
        thread = threading.Thread(target=self.perform_conversion, args=(input_path, output_path))
        thread.daemon = True
        thread.start()
    
    def perform_conversion(self, input_path: Path, output_path: Path):
        """执行转换（在后台线程中运行）"""
        try:
            self.log_message(f"输入文件: {input_path}")
            self.log_message(f"文件类型: {input_path.suffix.upper()}")
            self.log_message(f"输出文件: {output_path}")
            self.log_message(f"高度: {self.height_value.get():.1f}%")
            self.log_message(f"颜色: RGB{self.color_rgb}")
            self.log_message(f"透明度: {self.alpha_value.get():.2f}")
            self.log_message(f"自动缩放: {'启用' if self.auto_scale.get() else '禁用'}")
            self.log_message("-" * 50)
            
            # 创建转换器
            converter = Geo2GLTFConverter(
                default_height=self.height_value.get(),
                auto_scale=self.auto_scale.get()
            )
            
            # 重定向日志到GUI
            class GuiLogHandler(logging.Handler):
                def __init__(self, gui):
                    super().__init__()
                    self.gui = gui
                
                def emit(self, record):
                    msg = self.format(record)
                    self.gui.log_message(msg)
            
            gui_handler = GuiLogHandler(self)
            gui_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
            logger.addHandler(gui_handler)
            
            # 执行转换
            converter.convert(
                str(input_path),
                str(output_path),
                self.color_rgb,
                self.alpha_value.get()
            )
            
            # 转换成功
            self.root.after(0, lambda: self.conversion_complete(True, output_path))
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: self.conversion_complete(False, None, error_msg))
    
    def conversion_complete(self, success: bool, output_path: Path = None, error_msg: str = None):
        """转换完成回调"""
        self.progress.stop()
        self.convert_button.config(state=tk.NORMAL)
        
        if success:
            self.log_message("=" * 50)
            self.log_message("✓ 转换成功！")
            self.log_message(f"输出文件: {output_path}")
            messagebox.showinfo("成功", f"转换完成！\n\n输出文件:\n{output_path}")
        else:
            self.log_message("=" * 50)
            self.log_message(f"✗ 转换失败: {error_msg}")
            messagebox.showerror("失败", f"转换失败！\n\n{error_msg}")
    
    # ========== 批量转换相关方法 ==========
    
    def batch_log_message(self, message: str):
        """记录批量转换消息到状态文本框"""
        self.batch_status_text.insert(tk.END, message + "\n")
        self.batch_status_text.see(tk.END)
        self.root.update()
    
    def find_geo_files(self, input_dir: Path, recursive: bool, extensions: List[str]) -> List[Path]:
        """查找目录中的地理数据文件"""
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
    
    def start_batch_conversion(self):
        """开始批量转换"""
        # 验证输入
        if not self.batch_input_dir.get():
            messagebox.showerror("错误", "请选择输入目录！")
            return
        
        if not self.batch_output_dir.get():
            messagebox.showerror("错误", "请选择输出目录！")
            return
        
        input_path = Path(self.batch_input_dir.get())
        if not input_path.exists():
            messagebox.showerror("错误", "输入目录不存在！")
            return
        
        if not input_path.is_dir():
            messagebox.showerror("错误", "输入路径不是目录！")
            return
        
        # 检查是否至少选择了一种文件类型
        if not self.file_type_geojson.get() and not self.file_type_shp.get():
            messagebox.showerror("错误", "请至少选择一种文件类型！")
            return
        
        # 构建文件扩展名列表
        extensions = []
        if self.file_type_geojson.get():
            extensions.extend(['.geojson', '.json'])
        if self.file_type_shp.get():
            extensions.append('.shp')
        
        # 查找文件
        self.batch_log_message("正在搜索文件...")
        files = self.find_geo_files(input_path, self.recursive.get(), extensions)
        
        if not files:
            messagebox.showwarning("警告", f"在输入目录中未找到匹配的文件！")
            return
        
        self.batch_total = len(files)
        self.batch_current = 0
        self.batch_success = 0
        self.batch_failed = 0
        
        self.batch_log_message(f"找到 {self.batch_total} 个文件待转换")
        self.batch_log_message("=" * 70)
        
        # 禁用按钮，显示进度条
        self.batch_convert_button.config(state=tk.DISABLED)
        self.batch_progress['maximum'] = self.batch_total
        self.batch_progress['value'] = 0
        self.batch_status_text.delete(1.0, tk.END)
        self.is_batch_converting = True
        
        # 在新线程中执行批量转换
        thread = threading.Thread(target=self.perform_batch_conversion, args=(files, input_path))
        thread.daemon = True
        thread.start()
    
    def perform_batch_conversion(self, files: List[Path], input_base_path: Path):
        """执行批量转换（在后台线程中运行）"""
        output_path = Path(self.batch_output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        for idx, input_file in enumerate(files, 1):
            if not self.is_batch_converting:
                self.batch_log_message("\n用户取消操作")
                break
            
            try:
                self.batch_current = idx
                
                # 计算相对路径（用于保持目录结构）
                if self.recursive.get():
                    rel_path = input_file.relative_to(input_base_path)
                    output_file = output_path / rel_path.parent / f"{input_file.stem}.gltf"
                else:
                    output_file = output_path / f"{input_file.stem}.gltf"
                
                # 创建输出文件的父目录
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 更新进度标签
                progress_msg = f"正在转换 {idx}/{self.batch_total}: {input_file.name}"
                self.root.after(0, lambda msg=progress_msg: self.batch_progress_label.config(text=msg))
                
                self.batch_log_message(f"\n[{idx}/{self.batch_total}] {input_file.name}")
                self.batch_log_message(f"  输入: {input_file}")
                self.batch_log_message(f"  输出: {output_file}")
                
                # 执行转换
                converter = Geo2GLTFConverter(
                    default_height=self.height_value.get(),
                    auto_scale=self.auto_scale.get()
                )
                
                converter.convert(
                    str(input_file),
                    str(output_file),
                    color=self.color_rgb,
                    alpha=self.alpha_value.get()
                )
                
                # 获取文件大小
                output_size = output_file.stat().st_size / 1024  # KB
                self.batch_log_message(f"  ✓ 成功！文件大小: {output_size:.2f} KB")
                self.batch_success += 1
                
            except Exception as e:
                self.batch_log_message(f"  ✗ 失败: {str(e)}")
                self.batch_failed += 1
            
            # 更新进度条
            self.root.after(0, lambda: self.batch_progress.step(1))
        
        # 计算耗时
        elapsed_time = time.time() - start_time
        
        # 转换完成
        self.root.after(0, lambda: self.batch_conversion_complete(elapsed_time))
    
    def batch_conversion_complete(self, elapsed_time: float):
        """批量转换完成回调"""
        self.batch_convert_button.config(state=tk.NORMAL)
        self.is_batch_converting = False
        
        # 输出统计信息
        self.batch_log_message("\n" + "=" * 70)
        self.batch_log_message("批量转换完成！")
        self.batch_log_message("=" * 70)
        self.batch_log_message(f"总文件数: {self.batch_total}")
        self.batch_log_message(f"成功: {self.batch_success}")
        self.batch_log_message(f"失败: {self.batch_failed}")
        self.batch_log_message(f"总耗时: {elapsed_time:.2f} 秒")
        
        if self.batch_success > 0:
            avg_time = elapsed_time / self.batch_success
            self.batch_log_message(f"平均速度: {avg_time:.2f} 秒/文件")
        
        # 更新进度标签
        self.batch_progress_label.config(
            text=f"完成！成功: {self.batch_success}, 失败: {self.batch_failed}"
        )
        
        # 显示完成对话框
        if self.batch_failed == 0:
            messagebox.showinfo(
                "批量转换完成", 
                f"所有文件转换成功！\n\n"
                f"成功: {self.batch_success}\n"
                f"总耗时: {elapsed_time:.2f} 秒\n\n"
                f"输出目录: {self.batch_output_dir.get()}"
            )
        else:
            messagebox.showwarning(
                "批量转换完成", 
                f"批量转换完成，但部分文件失败。\n\n"
                f"成功: {self.batch_success}\n"
                f"失败: {self.batch_failed}\n"
                f"总耗时: {elapsed_time:.2f} 秒\n\n"
                f"详细信息请查看日志。"
            )


def main():
    """主函数"""
    root = tk.Tk()
    app = Geo2GLTFGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()

