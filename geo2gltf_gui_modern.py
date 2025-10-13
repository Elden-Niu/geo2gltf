#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用地理数据转GLTF转换工具 - 现代化iOS风格GUI
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

# iOS风格颜色方案（优化版）
COLORS = {
    'bg': '#F2F2F7',  # 浅灰背景（更柔和）
    'card': '#FFFFFF',  # 白色卡片
    'primary': '#007AFF',  # iOS蓝
    'primary_hover': '#0051D5',  # iOS蓝悬停
    'secondary': '#5856D6',  # iOS紫
    'secondary_hover': '#4139C8',  # iOS紫悬停
    'success': '#34C759',  # iOS绿
    'success_hover': '#248A3D',  # iOS绿悬停
    'danger': '#FF3B30',  # iOS红
    'warning': '#FF9500',  # iOS橙
    'text': '#1C1C1E',  # 深色文字
    'text_secondary': '#8E8E93',  # 次要文字
    'border': '#C6C6C8',  # 边框
    'separator': '#E5E5EA',  # 分隔线
    'input_bg': '#FAFAFA',  # 输入框背景
    'shadow': 'rgba(0, 0, 0, 0.08)',  # 阴影
}

# 字体配置
FONTS = {
    'title': ('SF Pro Display', 20, 'bold'),
    'subtitle': ('SF Pro Text', 11),
    'heading': ('SF Pro Text', 14, 'bold'),
    'body': ('SF Pro Text', 11),
    'small': ('SF Pro Text', 9),
}

# 在Windows上使用Segoe UI替代SF Pro
if sys.platform == 'win32':
    FONTS = {
        'title': ('Segoe UI', 20, 'bold'),
        'subtitle': ('Segoe UI', 10),
        'heading': ('Segoe UI', 12, 'bold'),
        'body': ('Segoe UI', 10),
        'small': ('Segoe UI', 9),
    }


class ModernButton(tk.Canvas):
    """现代化圆角按钮（增强版）"""
    def __init__(self, parent, text, command, bg_color=COLORS['primary'], 
                 fg_color='white', width=120, height=40, style='filled', **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=parent.cget('bg'), highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.width = width
        self.height = height
        self.style = style  # 'filled' or 'outlined'
        self.is_hovered = False
        self.is_pressed = False
        
        self.draw()
        self.bind('<Button-1>', self.on_press)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def draw(self):
        self.delete('all')
        radius = 10
        
        # 根据状态选择颜色
        if self.is_pressed:
            color = self.get_pressed_color()
            shadow_offset = 0
        elif self.is_hovered:
            color = self.get_hover_color()
            shadow_offset = 1
        else:
            color = self.bg_color
            shadow_offset = 2
        
        # 绘制阴影（仅filled样式）
        if self.style == 'filled' and not self.is_pressed:
            shadow_y = shadow_offset
            self.create_rounded_rectangle(
                2, 2+shadow_y, self.width-2, self.height-2+shadow_y,
                radius, fill='#D0D0D0', outline=''
            )
        
        # 绘制按钮主体
        if self.style == 'filled':
            self.create_rounded_rectangle(
                2, 2, self.width-2, self.height-2,
                radius, fill=color, outline=''
            )
            text_color = self.fg_color
        else:  # outlined
            self.create_rounded_rectangle(
                2, 2, self.width-2, self.height-2,
                radius, fill='', outline=color, width=2
            )
            text_color = color
        
        # 绘制文字
        y_offset = 1 if self.is_pressed else 0
        self.create_text(
            self.width//2, self.height//2 + y_offset,
            text=self.text, fill=text_color, font=FONTS['body']
        )
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=10, **kwargs):
        """创建圆角矩形"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def get_hover_color(self):
        """获取悬停颜色"""
        color_map = {
            COLORS['primary']: COLORS.get('primary_hover', '#0051D5'),
            COLORS['secondary']: COLORS.get('secondary_hover', '#4139C8'),
            COLORS['success']: COLORS.get('success_hover', '#248A3D'),
        }
        return color_map.get(self.bg_color, self.lighten_color(self.bg_color))
    
    def get_pressed_color(self):
        """获取按下颜色"""
        return self.darken_color(self.bg_color)
    
    def lighten_color(self, color):
        """变亮颜色"""
        try:
            # 简单的颜色变亮算法
            if color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                r = min(255, r + 30)
                g = min(255, g + 30)
                b = min(255, b + 30)
                return f'#{r:02x}{g:02x}{b:02x}'
        except:
            pass
        return color
    
    def darken_color(self, color):
        """变暗颜色"""
        try:
            if color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                r = max(0, r - 30)
                g = max(0, g - 30)
                b = max(0, b - 30)
                return f'#{r:02x}{g:02x}{b:02x}'
        except:
            pass
        return color
    
    def on_press(self, event):
        self.is_pressed = True
        self.draw()
    
    def on_release(self, event):
        self.is_pressed = False
        self.draw()
        if self.command and self.is_hovered:
            self.command()
    
    def on_enter(self, event):
        self.is_hovered = True
        self.draw()
        self.config(cursor='hand2')
    
    def on_leave(self, event):
        self.is_hovered = False
        self.is_pressed = False
        self.draw()
        self.config(cursor='')


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


class Geo2GLTFGuiModern:
    """现代化iOS风格地理数据转GLTF GUI应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("地理数据转GLTF转换工具")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        self.root.configure(bg=COLORS['bg'])
        
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
        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # 顶部区域（LOGO + 标题）
        self.create_header(main_container)
        
        # 标签页（使用Canvas和Scrollbar）
        self.create_tabs(main_container)
        
        # 配置网格权重
        main_container.grid_rowconfigure(1, weight=1)
        main_container.grid_columnconfigure(0, weight=1)
    
    def create_header(self, parent):
        """创建头部区域"""
        header_frame = tk.Frame(parent, bg=COLORS['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # LOGO
        logo_path = Path("logo.png")
        if logo_path.exists() and PIL_AVAILABLE:
            try:
                logo_img = Image.open(logo_path)
                # 调整logo大小
                logo_img.thumbnail((80, 80), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(header_frame, image=self.logo_photo, bg=COLORS['bg'])
                logo_label.pack(side=tk.TOP, pady=(0, 10))
            except Exception as e:
                print(f"加载LOGO失败: {e}")
        
        # 标题
        title_label = tk.Label(header_frame, text="地理数据转换工具",
                              font=FONTS['title'], bg=COLORS['bg'], fg=COLORS['text'])
        title_label.pack()
        
        # 副标题
        subtitle_label = tk.Label(header_frame, 
                                 text="支持 GeoJSON 和 Shapefile  •  批量转换  •  独立颜色配置",
                                 font=FONTS['small'], bg=COLORS['bg'], fg=COLORS['text_secondary'])
        subtitle_label.pack(pady=(5, 0))
    
    def create_tabs(self, parent):
        """创建标签页"""
        # 创建样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置标签页样式
        style.configure('TNotebook', background=COLORS['bg'], borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=COLORS['card'],
                       foreground=COLORS['text'],
                       padding=[20, 10],
                       font=FONTS['body'])
        style.map('TNotebook.Tab',
                 background=[('selected', COLORS['primary'])],
                 foreground=[('selected', 'white')])
        
        # 标签页控件
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 单文件转换标签页
        self.single_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.single_frame, text="单文件转换")
        self.create_single_tab()
        
        # 批量转换标签页
        self.batch_frame = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(self.batch_frame, text="批量转换")
        self.create_batch_tab()
    
    def create_card(self, parent, title=None):
        """创建卡片容器（带阴影效果）"""
        # 外层容器（用于阴影）
        shadow_frame = tk.Frame(parent, bg=COLORS['bg'])
        shadow_frame.pack(fill=tk.X, padx=8, pady=8)
        
        # 卡片主体
        card = tk.Frame(shadow_frame, bg=COLORS['card'], relief=tk.FLAT, bd=0)
        card.pack(fill=tk.BOTH, expand=True)
        
        # 添加边框效果
        card.config(highlightbackground=COLORS['border'], highlightthickness=1)
        
        if title:
            title_frame = tk.Frame(card, bg=COLORS['card'])
            title_frame.pack(fill=tk.X, padx=15, pady=(12, 0))
            
            title_label = tk.Label(title_frame, text=title, font=FONTS['heading'],
                                  bg=COLORS['card'], fg=COLORS['text'], anchor=tk.W)
            title_label.pack(side=tk.LEFT)
            
            # 标题下方分隔线
            separator = tk.Frame(card, bg=COLORS['separator'], height=1)
            separator.pack(fill=tk.X, padx=15, pady=(8, 0))
        
        return card
    
    def create_single_tab(self):
        """创建单文件转换标签页"""
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(self.single_frame, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.single_frame, orient='vertical', command=canvas.yview)
        
        # 创建可滚动的框架
        container = tk.Frame(canvas, bg=COLORS['bg'])
        
        # 配置canvas
        canvas_frame = canvas.create_window((0, 0), window=container, anchor='nw')
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        container.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # 文件选择卡片
        file_card = self.create_card(container, "文件选择")
        file_inner = tk.Frame(file_card, bg=COLORS['card'])
        file_inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # 输入文件
        tk.Label(file_inner, text="输入文件:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=0, column=0, sticky=tk.W, pady=8)
        
        entry = tk.Entry(file_inner, textvariable=self.input_file, width=50,
                        font=FONTS['body'], bg=COLORS['input_bg'], relief=tk.FLAT, bd=1)
        entry.grid(row=0, column=1, pady=8, padx=10, ipady=4)
        
        ModernButton(file_inner, "📁 浏览", self.browse_input, width=90, height=36).grid(row=0, column=2, pady=8)
        
        # 输出目录
        tk.Label(file_inner, text="输出目录:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=1, column=0, sticky=tk.W, pady=5)
        tk.Entry(file_inner, textvariable=self.output_dir, width=50,
                font=FONTS['body']).grid(row=1, column=1, pady=5, padx=10)
        ModernButton(file_inner, "浏览", self.browse_output, width=80).grid(row=1, column=2, pady=5)
        
        # 参数设置卡片
        params_card = self.create_card(container, "参数设置")
        self.create_param_controls(params_card, is_batch=False)
        
        # 转换按钮
        btn_frame = tk.Frame(container, bg=COLORS['bg'])
        btn_frame.pack(pady=15)
        ModernButton(btn_frame, "🚀 开始转换", self.start_conversion, 
                    width=220, height=48, bg_color=COLORS['primary']).pack()
        
        # 日志
        log_card = self.create_card(container, "转换日志")
        self.status_text = tk.Text(log_card, height=10, width=80, wrap=tk.WORD,
                                   font=FONTS['small'], bg='#FAFAFA', relief=tk.FLAT)
        self.status_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    def create_batch_tab(self):
        """创建批量转换标签页"""
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(self.batch_frame, bg=COLORS['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.batch_frame, orient='vertical', command=canvas.yview)
        
        # 创建可滚动的框架
        container = tk.Frame(canvas, bg=COLORS['bg'])
        
        # 配置canvas
        canvas_frame = canvas.create_window((0, 0), window=container, anchor='nw')
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox('all'))
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        container.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # 目录选择卡片
        dir_card = self.create_card(container, "目录选择")
        dir_inner = tk.Frame(dir_card, bg=COLORS['card'])
        dir_inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # 输入目录
        tk.Label(dir_inner, text="输入目录:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=0, column=0, sticky=tk.W, pady=5)
        tk.Entry(dir_inner, textvariable=self.batch_input_dir, width=50,
                font=FONTS['body']).grid(row=0, column=1, pady=5, padx=10)
        ModernButton(dir_inner, "浏览", self.browse_batch_input, width=80).grid(row=0, column=2, pady=5)
        
        # 输出目录
        tk.Label(dir_inner, text="输出目录:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=1, column=0, sticky=tk.W, pady=5)
        tk.Entry(dir_inner, textvariable=self.batch_output_dir, width=50,
                font=FONTS['body']).grid(row=1, column=1, pady=5, padx=10)
        ModernButton(dir_inner, "浏览", self.browse_batch_output, width=80).grid(row=1, column=2, pady=5)
        
        # 选项卡片
        options_card = self.create_card(container, "选项")
        options_inner = tk.Frame(options_card, bg=COLORS['card'])
        options_inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Checkbutton(options_inner, text="递归搜索子目录", variable=self.recursive,
                      font=FONTS['body'], bg=COLORS['card'], activebackground=COLORS['card']).grid(
                          row=0, column=0, sticky=tk.W, pady=5)
        
        tk.Label(options_inner, text="文件类型:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=1, column=0, sticky=tk.W, pady=5)
        type_frame = tk.Frame(options_inner, bg=COLORS['card'])
        type_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        tk.Checkbutton(type_frame, text="GeoJSON", variable=self.file_type_geojson,
                      font=FONTS['body'], bg=COLORS['card'], activebackground=COLORS['card']).pack(
                          side=tk.LEFT, padx=10)
        tk.Checkbutton(type_frame, text="Shapefile", variable=self.file_type_shp,
                      font=FONTS['body'], bg=COLORS['card'], activebackground=COLORS['card']).pack(side=tk.LEFT)
        
        # 扫描文件按钮
        ModernButton(options_inner, "🔍 扫描文件", self.scan_files, 
                    width=140, height=40, bg_color=COLORS['secondary']).grid(row=2, column=0, columnspan=2, pady=10)
        
        # 文件列表卡片（支持独立颜色配置）
        files_card = self.create_card(container, "文件列表（点击文件名配置颜色）")
        
        # 创建滚动区域
        scroll_frame = tk.Frame(files_card, bg=COLORS['card'])
        scroll_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.file_listbox = tk.Listbox(scroll_frame, yscrollcommand=scrollbar.set,
                                       font=FONTS['small'], height=8,
                                       bg='#FAFAFA', relief=tk.FLAT)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_listbox.bind('<Double-Button-1>', self.configure_file_color)
        scrollbar.config(command=self.file_listbox.yview)
        
        # 参数设置卡片
        params_card = self.create_card(container, "默认参数设置")
        self.create_param_controls(params_card, is_batch=True)
        
        # 转换按钮
        btn_frame = tk.Frame(container, bg=COLORS['bg'])
        btn_frame.pack(pady=15)
        ModernButton(btn_frame, "✨ 开始批量转换", self.start_batch_conversion,
                    width=220, height=48, bg_color=COLORS['success']).pack()
        
        # 进度
        progress_frame = tk.Frame(container, bg=COLORS['bg'])
        progress_frame.pack(fill=tk.X, pady=10)
        self.batch_progress_label = tk.Label(progress_frame, text="准备开始...",
                                            font=FONTS['small'], bg=COLORS['bg'],
                                            fg=COLORS['text_secondary'])
        self.batch_progress_label.pack()
        
        self.batch_progress = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.batch_progress.pack(pady=5)
        
        # 日志
        log_card = self.create_card(container, "批量转换日志")
        self.batch_status_text = tk.Text(log_card, height=8, width=80, wrap=tk.WORD,
                                        font=FONTS['small'], bg='#FAFAFA', relief=tk.FLAT)
        self.batch_status_text.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
    
    def create_param_controls(self, parent, is_batch=False):
        """创建参数控制组件"""
        inner = tk.Frame(parent, bg=COLORS['card'])
        inner.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # 高度
        tk.Label(inner, text="高度值 (%):", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        height_frame = tk.Frame(inner, bg=COLORS['card'])
        height_frame.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=5, padx=10)
        
        height_scale = ttk.Scale(height_frame, from_=1, to=50, variable=self.height_value,
                                orient=tk.HORIZONTAL, length=300,
                                command=lambda v: self.update_height_label(v, is_batch))
        height_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        if is_batch:
            self.batch_height_label = tk.Label(height_frame, text=f"{self.height_value.get():.1f}%",
                                              font=FONTS['body'], bg=COLORS['card'], fg=COLORS['text'])
            self.batch_height_label.pack(side=tk.LEFT)
        else:
            self.height_label = tk.Label(height_frame, text=f"{self.height_value.get():.1f}%",
                                        font=FONTS['body'], bg=COLORS['card'], fg=COLORS['text'])
            self.height_label.pack(side=tk.LEFT)
        
        # 自动缩放
        tk.Checkbutton(inner, text="启用自动缩放", variable=self.auto_scale,
                      font=FONTS['body'], bg=COLORS['card'], activebackground=COLORS['card']).grid(
                          row=1, column=1, sticky=tk.W, pady=5, padx=10)
        
        # 颜色
        tk.Label(inner, text="默认颜色:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        color_frame = tk.Frame(inner, bg=COLORS['card'])
        color_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5, padx=10)
        
        if is_batch:
            self.batch_color_preview = tk.Canvas(color_frame, width=40, height=25,
                                                bg=self.rgb_to_hex(self.color_rgb), relief=tk.FLAT)
            self.batch_color_preview.pack(side=tk.LEFT, padx=(0, 10))
            ModernButton(color_frame, "选择", lambda: self.choose_color(True), width=80).pack(side=tk.LEFT)
        else:
            self.color_preview = tk.Canvas(color_frame, width=40, height=25,
                                          bg=self.rgb_to_hex(self.color_rgb), relief=tk.FLAT)
            self.color_preview.pack(side=tk.LEFT, padx=(0, 10))
            ModernButton(color_frame, "选择", lambda: self.choose_color(False), width=80).pack(side=tk.LEFT)
        
        # 透明度
        tk.Label(inner, text="透明度:", font=FONTS['body'],
                bg=COLORS['card'], fg=COLORS['text']).grid(row=3, column=0, sticky=tk.W, pady=5)
        
        alpha_frame = tk.Frame(inner, bg=COLORS['card'])
        alpha_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, pady=5, padx=10)
        
        alpha_scale = ttk.Scale(alpha_frame, from_=0, to=1, variable=self.alpha_value,
                               orient=tk.HORIZONTAL, length=300,
                               command=lambda v: self.update_alpha_label(v, is_batch))
        alpha_scale.pack(side=tk.LEFT, padx=(0, 10))
        
        if is_batch:
            self.batch_alpha_label = tk.Label(alpha_frame, text=f"{self.alpha_value.get():.2f}",
                                            font=FONTS['body'], bg=COLORS['card'], fg=COLORS['text'])
            self.batch_alpha_label.pack(side=tk.LEFT)
        else:
            self.alpha_label = tk.Label(alpha_frame, text=f"{self.alpha_value.get():.2f}",
                                       font=FONTS['body'], bg=COLORS['card'], fg=COLORS['text'])
            self.alpha_label.pack(side=tk.LEFT)
    
    def rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """将RGB(0-1)转换为十六进制颜色"""
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_height_label(self, value, is_batch):
        """更新高度标签"""
        text = f"{float(value):.1f}%"
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
            if is_batch and hasattr(self, 'batch_color_preview'):
                self.batch_color_preview.config(bg=color[1])
            if not is_batch and hasattr(self, 'color_preview'):
                self.color_preview.config(bg=color[1])
    
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
            self.log_message("-" * 50)
            
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
            
            self.log_message("=" * 50)
            self.log_message("✓ 转换成功！")
            self.root.after(0, lambda: messagebox.showinfo("成功", "转换完成！"))
            
        except Exception as e:
            error_msg = f"转换失败: {str(e)}"
            self.log_message("=" * 50)
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
                    color=file_color,  # 使用文件特定颜色
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
    app = Geo2GLTFGuiModern(root)
    root.mainloop()


if __name__ == '__main__':
    main()

