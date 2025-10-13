#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用地理数据转GLTF转换工具 - 简洁传统GUI
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

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL/Pillow 未安装，LOGO功能将被禁用")

# 导入转换器
from geo2gltf import Geo2GLTFConverter, parse_color

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FileColorManager:
    """文件颜色管理器"""
    def __init__(self):
        self.file_colors: Dict[str, Tuple[float, float, float]] = {}
        self.default_color = (0.2, 0.6, 1.0)  # 默认蓝色
    
    def set_color(self, filename: str, color: Tuple[float, float, float]):
        """设置文件颜色"""
        self.file_colors[filename] = color
    
    def get_color(self, filename: str) -> Tuple[float, float, float]:
        """获取文件颜色"""
        return self.file_colors.get(filename, self.default_color)
    
    def clear(self):
        """清除所有颜色设置"""
        self.file_colors.clear()


class Geo2GLTFGui:
    """地理数据转GLTF GUI应用（简洁传统风格）"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("地理数据转GLTF转换工具")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # 设置窗口图标（如果logo存在）
        logo_path = Path("logo.png")
        if logo_path.exists() and PIL_AVAILABLE:
            try:
                icon = Image.open(logo_path)
                icon_photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, icon_photo)
            except:
                pass
        
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
        self.height_value = tk.DoubleVar(value=5.0)
        self.color_rgb = (0.2, 0.6, 1.0)  # 默认蓝色
        self.alpha_value = tk.DoubleVar(value=0.7)
        self.auto_scale = tk.BooleanVar(value=True)
        
        # 批量转换相关
        self.batch_total = 0
        self.batch_current = 0
        self.batch_success = 0
        self.batch_failed = 0
        self.is_batch_converting = False
        
        # 文件颜色管理器
        self.file_color_manager = FileColorManager()
        self.batch_files: List[Path] = []
        
        # 创建UI
        self.create_widgets()
    
    def create_widgets(self):
        """创建UI组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 顶部标题区域
        self.create_header(main_frame)
        
        # 标签页
        self.create_tabs(main_frame)
    
    def create_header(self, parent):
        """创建头部区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 标题
        title_label = ttk.Label(header_frame, text="地理数据转GLTF转换工具", 
                               font=('', 14, 'bold'))
        title_label.pack()
        
        # 副标题
        subtitle_label = ttk.Label(header_frame, 
                                   text="支持 GeoJSON 和 Shapefile 格式 | 单文件/批量转换 | 独立颜色配置",
                                   font=('', 9))
        subtitle_label.pack(pady=(2, 0))
    
    def create_tabs(self, parent):
        """创建标签页"""
        # 标签页控件
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 单文件转换标签页
        self.single_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.single_frame, text="单文件转换")
        self.create_single_tab()
        
        # 批量转换标签页
        self.batch_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.batch_frame, text="批量转换")
        self.create_batch_tab()
    
    def create_single_tab(self):
        """创建单文件转换标签页"""
        # 配置网格权重
        self.single_frame.columnconfigure(0, weight=1)
        self.single_frame.rowconfigure(3, weight=1)
        
        # 文件选择组
        file_group = ttk.LabelFrame(self.single_frame, text="文件选择", padding="10")
        file_group.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_group.columnconfigure(1, weight=1)
        
        # 输入文件
        ttk.Label(file_group, text="输入文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_group, textvariable=self.input_file).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(file_group, text="浏览...", command=self.browse_input).grid(
            row=0, column=2, pady=5)
        
        # 输出目录
        ttk.Label(file_group, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(file_group, textvariable=self.output_dir).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(file_group, text="浏览...", command=self.browse_output).grid(
            row=1, column=2, pady=5)
        
        # 参数设置组
        params_group = ttk.LabelFrame(self.single_frame, text="参数设置", padding="10")
        params_group.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.create_param_controls(params_group, is_batch=False)
        
        # 转换按钮
        btn_frame = ttk.Frame(self.single_frame)
        btn_frame.grid(row=2, column=0, pady=10)
        ttk.Button(btn_frame, text="开始转换", command=self.start_conversion,
                  width=20).pack()
        
        # 日志输出组
        log_group = ttk.LabelFrame(self.single_frame, text="转换日志", padding="5")
        log_group.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        log_group.columnconfigure(0, weight=1)
        log_group.rowconfigure(0, weight=1)
        
        # 日志文本框和滚动条
        log_frame = ttk.Frame(log_group)
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.status_text = tk.Text(log_frame, height=10, wrap=tk.WORD, font=('Consolas', 9))
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text['yscrollcommand'] = scrollbar.set
    
    def create_batch_tab(self):
        """创建批量转换标签页"""
        # 配置网格权重
        self.batch_frame.columnconfigure(0, weight=1)
        self.batch_frame.rowconfigure(3, weight=1)
        
        # 目录选择组
        dir_group = ttk.LabelFrame(self.batch_frame, text="目录选择", padding="10")
        dir_group.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_group.columnconfigure(1, weight=1)
        
        # 输入目录
        ttk.Label(dir_group, text="输入目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_group, textvariable=self.batch_input_dir).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(dir_group, text="浏览...", command=self.browse_batch_input).grid(
            row=0, column=2, pady=5)
        
        # 输出目录
        ttk.Label(dir_group, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_group, textvariable=self.batch_output_dir).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(dir_group, text="浏览...", command=self.browse_batch_output).grid(
            row=1, column=2, pady=5)
        
        # 选项组
        options_group = ttk.LabelFrame(self.batch_frame, text="扫描选项", padding="10")
        options_group.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 第一行：递归选项
        ttk.Checkbutton(options_group, text="递归搜索子目录", 
                       variable=self.recursive).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 第二行：文件类型
        type_frame = ttk.Frame(options_group)
        type_frame.grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(type_frame, text="文件类型:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Checkbutton(type_frame, text="GeoJSON", 
                       variable=self.file_type_geojson).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(type_frame, text="Shapefile", 
                       variable=self.file_type_shp).pack(side=tk.LEFT, padx=5)
        
        # 第三行：扫描按钮
        ttk.Button(options_group, text="扫描文件", command=self.scan_files,
                  width=15).grid(row=2, column=0, pady=(10, 5))
        
        # 文件列表组
        files_group = ttk.LabelFrame(self.batch_frame, text="文件列表（双击配置颜色）", padding="5")
        files_group.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_group.columnconfigure(0, weight=1)
        files_group.rowconfigure(0, weight=1)
        
        # 文件列表框和滚动条
        list_frame = ttk.Frame(files_group)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        self.file_listbox = tk.Listbox(list_frame, height=8, font=('', 9))
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.file_listbox.bind('<Double-Button-1>', self.configure_file_color)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.file_listbox['yscrollcommand'] = scrollbar.set
        
        # 参数设置组（横向布局以节省空间）
        params_group = ttk.LabelFrame(self.batch_frame, text="默认参数设置", padding="10")
        params_group.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        self.create_param_controls(params_group, is_batch=True)
        
        # 转换按钮和进度
        control_frame = ttk.Frame(self.batch_frame)
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        
        # 按钮
        ttk.Button(control_frame, text="开始批量转换", command=self.start_batch_conversion,
                  width=20).grid(row=0, column=0, pady=5)
        
        # 进度标签
        self.batch_progress_label = ttk.Label(control_frame, text="准备开始...")
        self.batch_progress_label.grid(row=1, column=0, pady=2)
        
        # 进度条
        self.batch_progress = ttk.Progressbar(control_frame, mode='determinate', length=400)
        self.batch_progress.grid(row=2, column=0, pady=5)
        
        # 日志输出组
        log_group = ttk.LabelFrame(self.batch_frame, text="批量转换日志", padding="5")
        log_group.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_group.columnconfigure(0, weight=1)
        log_group.rowconfigure(0, weight=1)
        
        # 日志文本框和滚动条
        log_frame = ttk.Frame(log_group)
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.batch_status_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=('Consolas', 9))
        self.batch_status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.batch_status_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.batch_status_text['yscrollcommand'] = scrollbar.set
    
    def create_param_controls(self, parent, is_batch=False):
        """创建参数控制组件"""
        parent.columnconfigure(1, weight=1)
        
        row = 0
        
        # 高度值
        ttk.Label(parent, text="高度值 (%):").grid(row=row, column=0, sticky=tk.W, pady=5)
        height_frame = ttk.Frame(parent)
        height_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        height_frame.columnconfigure(0, weight=1)
        
        height_scale = ttk.Scale(height_frame, from_=1, to=50, variable=self.height_value,
                                orient=tk.HORIZONTAL,
                                command=lambda v: self.update_height_label(v, is_batch))
        height_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        if is_batch:
            self.batch_height_label = ttk.Label(height_frame, text=f"{self.height_value.get():.1f}",
                                               width=6)
            self.batch_height_label.grid(row=0, column=1)
        else:
            self.height_label = ttk.Label(height_frame, text=f"{self.height_value.get():.1f}",
                                         width=6)
            self.height_label.grid(row=0, column=1)
        
        row += 1
        
        # 自动缩放
        ttk.Checkbutton(parent, text="启用自动缩放", 
                       variable=self.auto_scale).grid(row=row, column=1, sticky=tk.W, 
                                                      padx=5, pady=5)
        row += 1
        
        # 颜色选择
        ttk.Label(parent, text="默认颜色:").grid(row=row, column=0, sticky=tk.W, pady=5)
        color_frame = ttk.Frame(parent)
        color_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        if is_batch:
            self.batch_color_canvas = tk.Canvas(color_frame, width=60, height=25,
                                               bg=self.rgb_to_hex(self.color_rgb),
                                               relief=tk.SUNKEN, bd=1)
            self.batch_color_canvas.pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(color_frame, text="选择颜色", 
                      command=lambda: self.choose_color(True), width=12).pack(side=tk.LEFT)
        else:
            self.color_canvas = tk.Canvas(color_frame, width=60, height=25,
                                         bg=self.rgb_to_hex(self.color_rgb),
                                         relief=tk.SUNKEN, bd=1)
            self.color_canvas.pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(color_frame, text="选择颜色", 
                      command=lambda: self.choose_color(False), width=12).pack(side=tk.LEFT)
        
        row += 1
        
        # 透明度
        ttk.Label(parent, text="透明度:").grid(row=row, column=0, sticky=tk.W, pady=5)
        alpha_frame = ttk.Frame(parent)
        alpha_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        alpha_frame.columnconfigure(0, weight=1)
        
        alpha_scale = ttk.Scale(alpha_frame, from_=0, to=1, variable=self.alpha_value,
                               orient=tk.HORIZONTAL,
                               command=lambda v: self.update_alpha_label(v, is_batch))
        alpha_scale.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        if is_batch:
            self.batch_alpha_label = ttk.Label(alpha_frame, text=f"{self.alpha_value.get():.2f}",
                                              width=6)
            self.batch_alpha_label.grid(row=0, column=1)
        else:
            self.alpha_label = ttk.Label(alpha_frame, text=f"{self.alpha_value.get():.2f}",
                                        width=6)
            self.alpha_label.grid(row=0, column=1)
    
    def rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """将RGB(0-1)转换为十六进制颜色"""
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_height_label(self, value, is_batch):
        """更新高度标签"""
        text = f"{float(value):.1f}"
        if is_batch and hasattr(self, 'batch_height_label'):
            self.batch_height_label.config(text=text)
        if not is_batch and hasattr(self, 'height_label'):
            self.height_label.config(text=text)
    
    def update_alpha_label(self, value, is_batch):
        """更新透明度标签"""
        text = f"{float(value):.2f}"
        if is_batch and hasattr(self, 'batch_alpha_label'):
            self.batch_alpha_label.config(text=text)
        if not is_batch and hasattr(self, 'alpha_label'):
            self.alpha_label.config(text=text)
    
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
            if not self.output_dir.get():
                self.output_dir.set(str(Path(filename).parent))
    
    def browse_output(self):
        """浏览输出目录"""
        dirname = filedialog.askdirectory(title="选择输出目录")
        if dirname:
            self.output_dir.set(dirname)
    
    def browse_batch_input(self):
        """浏览批量输入目录"""
        dirname = filedialog.askdirectory(title="选择输入目录")
        if dirname:
            self.batch_input_dir.set(dirname)
            if not self.batch_output_dir.get():
                self.batch_output_dir.set(dirname + "_output")
    
    def browse_batch_output(self):
        """浏览批量输出目录"""
        dirname = filedialog.askdirectory(title="选择输出目录")
        if dirname:
            self.batch_output_dir.set(dirname)
    
    def choose_color(self, is_batch):
        """选择颜色"""
        current_color = tuple(int(c * 255) for c in self.color_rgb)
        color = colorchooser.askcolor(title="选择颜色", initialcolor=current_color)
        
        if color[0]:
            self.color_rgb = tuple(c / 255.0 for c in color[0])
            if is_batch and hasattr(self, 'batch_color_canvas'):
                self.batch_color_canvas.config(bg=color[1])
            if not is_batch and hasattr(self, 'color_canvas'):
                self.color_canvas.config(bg=color[1])
    
    def scan_files(self):
        """扫描文件"""
        if not self.batch_input_dir.get():
            messagebox.showerror("错误", "请先选择输入目录！")
            return
        
        input_path = Path(self.batch_input_dir.get())
        if not input_path.exists():
            messagebox.showerror("错误", "输入目录不存在！")
            return
        
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
        self.batch_files = self.find_geo_files(input_path, self.recursive.get(), extensions)
        
        # 更新列表
        self.file_listbox.delete(0, tk.END)
        self.file_color_manager.clear()
        
        for f in self.batch_files:
            self.file_listbox.insert(tk.END, f.name)
            # 设置默认颜色
            self.file_color_manager.set_color(f.name, self.color_rgb)
        
        messagebox.showinfo("扫描完成", f"找到 {len(self.batch_files)} 个文件")
    
    def configure_file_color(self, event):
        """配置单个文件的颜色"""
        selection = self.file_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        filename = self.file_listbox.get(index)
        
        # 获取当前颜色
        current_color = self.file_color_manager.get_color(filename)
        current_color_255 = tuple(int(c * 255) for c in current_color)
        
        # 选择新颜色
        color = colorchooser.askcolor(
            title=f"选择 {filename} 的颜色",
            initialcolor=current_color_255
        )
        
        if color[0]:
            new_color = tuple(c / 255.0 for c in color[0])
            self.file_color_manager.set_color(filename, new_color)
            
            # 更新列表显示（添加颜色标记）
            hex_color = self.rgb_to_hex(new_color)
            self.file_listbox.itemconfig(index, fg=hex_color)
            
            messagebox.showinfo("颜色已设置", 
                              f"{filename}\n新颜色: RGB{new_color}")
    
    def find_geo_files(self, input_dir: Path, recursive: bool, extensions: List[str]) -> List[Path]:
        """查找地理数据文件"""
        files = []
        if recursive:
            for ext in extensions:
                files.extend(input_dir.rglob(f'*{ext}'))
        else:
            for ext in extensions:
                files.extend(input_dir.glob(f'*{ext}'))
        return sorted(files)
    
    def log_message(self, message: str):
        """记录消息"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def batch_log_message(self, message: str):
        """记录批量转换消息"""
        self.batch_status_text.insert(tk.END, message + "\n")
        self.batch_status_text.see(tk.END)
        self.root.update()
    
    def start_conversion(self):
        """开始单文件转换"""
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
        
        output_dir = Path(self.output_dir.get())
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{input_path.stem}.gltf"
        
        self.status_text.delete(1.0, tk.END)
        
        # 在新线程中执行
        thread = threading.Thread(target=self.perform_conversion, args=(input_path, output_path))
        thread.daemon = True
        thread.start()
    
    def perform_conversion(self, input_path: Path, output_path: Path):
        """执行转换"""
        try:
            self.log_message(f"开始转换: {input_path.name}")
            self.log_message(f"输出: {output_path}")
            self.log_message("-" * 60)
            
            converter = Geo2GLTFConverter(
                default_height=self.height_value.get(),
                auto_scale=self.auto_scale.get()
            )
            
            converter.convert(
                str(input_path),
                str(output_path),
                self.color_rgb,
                self.alpha_value.get()
            )
            
            self.log_message("=" * 60)
            self.log_message("✓ 转换成功！")
            self.root.after(0, lambda: messagebox.showinfo("成功", "转换完成！"))
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            self.log_message("=" * 60)
            self.log_message(f"✗ {error_msg}")
            self.root.after(0, lambda: messagebox.showerror("失败", error_msg))
    
    def start_batch_conversion(self):
        """开始批量转换"""
        if not self.batch_files:
            messagebox.showerror("错误", "请先扫描文件！")
            return
        
        if not self.batch_output_dir.get():
            messagebox.showerror("错误", "请选择输出目录！")
            return
        
        self.batch_total = len(self.batch_files)
        self.batch_current = 0
        self.batch_success = 0
        self.batch_failed = 0
        
        self.batch_progress['maximum'] = self.batch_total
        self.batch_progress['value'] = 0
        self.batch_status_text.delete(1.0, tk.END)
        self.is_batch_converting = True
        
        # 在新线程中执行
        input_base = Path(self.batch_input_dir.get())
        thread = threading.Thread(target=self.perform_batch_conversion, args=(self.batch_files, input_base))
        thread.daemon = True
        thread.start()
    
    def perform_batch_conversion(self, files: List[Path], input_base_path: Path):
        """执行批量转换"""
        output_path = Path(self.batch_output_dir.get())
        output_path.mkdir(parents=True, exist_ok=True)
        
        start_time = time.time()
        
        for idx, input_file in enumerate(files, 1):
            if not self.is_batch_converting:
                break
            
            try:
                self.batch_current = idx
                
                # 计算输出路径
                if self.recursive.get():
                    rel_path = input_file.relative_to(input_base_path)
                    output_file = output_path / rel_path.parent / f"{input_file.stem}.gltf"
                else:
                    output_file = output_path / f"{input_file.stem}.gltf"
                
                output_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 更新进度
                progress_msg = f"正在转换 {idx}/{self.batch_total}: {input_file.name}"
                self.root.after(0, lambda msg=progress_msg: self.batch_progress_label.config(text=msg))
                
                self.batch_log_message(f"\n[{idx}/{self.batch_total}] {input_file.name}")
                
                # 获取文件特定颜色
                file_color = self.file_color_manager.get_color(input_file.name)
                
                # 执行转换
                converter = Geo2GLTFConverter(
                    default_height=self.height_value.get(),
                    auto_scale=self.auto_scale.get()
                )
                
                converter.convert(
                    str(input_file),
                    str(output_file),
                    color=file_color,
                    alpha=self.alpha_value.get()
                )
                
                output_size = output_file.stat().st_size / 1024
                self.batch_log_message(f"  ✓ 成功！文件大小: {output_size:.2f} KB")
                self.batch_success += 1
                
            except Exception as e:
                self.batch_log_message(f"  ✗ 失败: {str(e)}")
                self.batch_failed += 1
            
            self.root.after(0, lambda: self.batch_progress.step(1))
        
        elapsed_time = time.time() - start_time
        self.root.after(0, lambda: self.batch_conversion_complete(elapsed_time))
    
    def batch_conversion_complete(self, elapsed_time: float):
        """批量转换完成"""
        self.is_batch_converting = False
        
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
        
        self.batch_progress_label.config(
            text=f"完成！成功: {self.batch_success}, 失败: {self.batch_failed}"
        )
        
        if self.batch_failed == 0:
            messagebox.showinfo(
                "批量转换完成",
                f"所有文件转换成功！\n\n成功: {self.batch_success}\n总耗时: {elapsed_time:.2f} 秒"
            )
        else:
            messagebox.showwarning(
                "批量转换完成",
                f"批量转换完成，但部分文件失败。\n\n成功: {self.batch_success}\n失败: {self.batch_failed}"
            )


def main():
    """主函数"""
    root = tk.Tk()
    app = Geo2GLTFGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()

