#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHP转GLTF转换工具 - GUI版本
提供图形化界面，方便选择文件、设置参数
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from typing import Tuple
import threading
import logging

# 导入转换器
from shp2gltf import SHP2GLTFConverter, parse_color

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SHP2GLTFGui:
    """SHP转GLTF GUI应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SHP转GLTF转换工具")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        
        # 变量
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.height_value = tk.DoubleVar(value=5.0)  # 降低默认高度到5%
        self.color_rgb = (0.2, 0.6, 1.0)  # 默认蓝色
        self.alpha_value = tk.DoubleVar(value=0.7)
        self.auto_scale = tk.BooleanVar(value=True)
        
        # 创建UI
        self.create_widgets()
        
    def create_widgets(self):
        """创建UI组件"""
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 标题
        title_label = ttk.Label(main_frame, text="SHP 转 GLTF 转换工具", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 输入文件选择
        ttk.Label(main_frame, text="输入SHP文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.input_file, width=50).grid(row=1, column=1, pady=5, padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_input).grid(row=1, column=2, pady=5)
        
        # 输出目录选择
        ttk.Label(main_frame, text="输出目录:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.output_dir, width=50).grid(row=2, column=1, pady=5, padx=5)
        ttk.Button(main_frame, text="浏览...", command=self.browse_output).grid(row=2, column=2, pady=5)
        
        # 分隔线
        ttk.Separator(main_frame, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # 参数设置区域
        params_frame = ttk.LabelFrame(main_frame, text="参数设置", padding="10")
        params_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
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
        ttk.Separator(main_frame, orient='horizontal').grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        
        # 转换按钮
        self.convert_button = ttk.Button(main_frame, text="开始转换", command=self.start_conversion)
        self.convert_button.grid(row=6, column=0, columnspan=3, pady=10)
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.grid(row=7, column=0, columnspan=3, pady=5)
        
        # 状态文本框
        status_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="5")
        status_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.status_text = tk.Text(status_frame, height=8, width=70, wrap=tk.WORD)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(status_frame, command=self.status_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scrollbar.set)
        
        # 配置行列权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def rgb_to_hex(self, rgb: Tuple[float, float, float]) -> str:
        """将RGB(0-1)转换为十六进制颜色"""
        r = int(rgb[0] * 255)
        g = int(rgb[1] * 255)
        b = int(rgb[2] * 255)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def update_height_label(self, value):
        """更新高度标签"""
        self.height_label.config(text=f"{float(value):.1f}%")
    
    def update_alpha_label(self, value):
        """更新透明度标签"""
        self.alpha_label.config(text=f"{float(value):.2f}")
    
    def browse_input(self):
        """浏览输入文件"""
        filename = filedialog.askopenfilename(
            title="选择SHP文件",
            filetypes=[("Shapefile", "*.shp"), ("所有文件", "*.*")]
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
    
    def choose_color(self):
        """选择颜色"""
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
    
    def log_message(self, message: str):
        """记录消息到状态文本框"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def start_conversion(self):
        """开始转换"""
        # 验证输入
        if not self.input_file.get():
            messagebox.showerror("错误", "请选择输入SHP文件！")
            return
        
        if not self.output_dir.get():
            messagebox.showerror("错误", "请选择输出目录！")
            return
        
        input_path = Path(self.input_file.get())
        if not input_path.exists():
            messagebox.showerror("错误", "输入文件不存在！")
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
            self.log_message(f"输出文件: {output_path}")
            self.log_message(f"高度: {self.height_value.get():.1f}%")
            self.log_message(f"颜色: RGB{self.color_rgb}")
            self.log_message(f"透明度: {self.alpha_value.get():.2f}")
            self.log_message(f"自动缩放: {'启用' if self.auto_scale.get() else '禁用'}")
            self.log_message("-" * 50)
            
            # 创建转换器
            converter = SHP2GLTFConverter(
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


def main():
    """主函数"""
    root = tk.Tk()
    app = SHP2GLTFGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()

