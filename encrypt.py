#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件保密柜 - 加密脚本
用于加密 source 目录下的所有文件
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from secret_vault.crypto import SecretVaultCrypto, SecureFileOperations


class EncryptionGUI:
    """加密界面"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文件保密柜 - 加密")
        self.root.geometry("550x480")
        self.root.resizable(True, True)
        self.root.minsize(500, 450)
        
        # 居中显示
        self.center_window()
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 扫描文件
        self.scan_files()
    
    def center_window(self):
        """居中显示窗口"""
        self.root.update_idletasks()
        width = 550
        height = 480
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Microsoft YaHei', 14, 'bold'))
        style.configure('Info.TLabel', font=('Microsoft YaHei', 10))
        style.configure('Big.TButton', font=('Microsoft YaHei', 11), padding=10)
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔒 文件加密", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # 文件列表框架
        list_frame = ttk.LabelFrame(main_frame, text="待加密文件", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # 文件列表
        self.file_listbox = tk.Listbox(list_frame, height=10, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文件统计
        self.stats_label = ttk.Label(main_frame, text="", style='Info.TLabel')
        self.stats_label.pack(pady=(0, 10))
        
        # 密码输入框架
        pwd_frame = ttk.Frame(main_frame)
        pwd_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(pwd_frame, text="加密密码:", style='Info.TLabel').pack(side=tk.LEFT)
        self.password_entry = ttk.Entry(pwd_frame, show="*", width=35, font=('Consolas', 11))
        self.password_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 确认密码
        pwd_confirm_frame = ttk.Frame(main_frame)
        pwd_confirm_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(pwd_confirm_frame, text="确认密码:", style='Info.TLabel').pack(side=tk.LEFT)
        self.password_confirm_entry = ttk.Entry(pwd_confirm_frame, show="*", width=35, font=('Consolas', 11))
        self.password_confirm_entry.pack(side=tk.LEFT, padx=(10, 0), fill=tk.X, expand=True)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        self.encrypt_btn = ttk.Button(btn_frame, text="🔐 开始加密", style='Big.TButton', command=self.do_encrypt)
        self.encrypt_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=self.root.quit)
        cancel_btn.pack(side=tk.RIGHT)
    
    def get_source_dir(self):
        """获取source目录路径"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, 'source')
    
    def scan_files(self):
        """扫描source目录下的文件"""
        source_dir = self.get_source_dir()
        self.files_to_encrypt = []
        
        if os.path.exists(source_dir):
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    # 跳过已加密的文件
                    if not file.endswith('.secret'):
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, source_dir)
                        self.files_to_encrypt.append((rel_path, file_path))
        
        # 更新列表
        self.file_listbox.delete(0, tk.END)
        for rel_path, _ in self.files_to_encrypt:
            self.file_listbox.insert(tk.END, f"  📄 {rel_path}")
        
        # 更新统计
        count = len(self.files_to_encrypt)
        if count == 0:
            self.stats_label.config(text="⚠️ source目录下没有可加密的文件")
            self.encrypt_btn.config(state=tk.DISABLED)
        else:
            total_size = sum(os.path.getsize(fp) for _, fp in self.files_to_encrypt)
            size_str = self.format_size(total_size)
            self.stats_label.config(text=f"共 {count} 个文件，总大小: {size_str}")
    
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def do_encrypt(self):
        """执行加密"""
        password = self.password_entry.get()
        password_confirm = self.password_confirm_entry.get()
        
        # 验证密码
        if not password:
            messagebox.showerror("错误", "请输入加密密码！")
            return
        
        if len(password) < 4:
            messagebox.showerror("错误", "密码长度至少4个字符！")
            return
        
        if password != password_confirm:
            messagebox.showerror("错误", "两次输入的密码不一致！")
            return
        
        # 确认加密
        if not messagebox.askyesno("确认", 
                f"即将加密 {len(self.files_to_encrypt)} 个文件。\n\n"
                "⚠️ 警告：\n"
                "1. 加密后原文件将被安全删除\n"
                "2. 请牢记密码，忘记密码将无法恢复文件\n"
                "3. 连续输错3次密码，文件将被永久销毁\n\n"
                "确定要继续吗？"):
            return
        
        # 禁用按钮
        self.encrypt_btn.config(state=tk.DISABLED)
        
        success_count = 0
        fail_count = 0
        
        for rel_path, file_path in self.files_to_encrypt:
            try:
                # 读取原文件
                original_data = SecureFileOperations.read_file_binary(file_path)
                
                # 加密
                encrypted_data = SecretVaultCrypto.encrypt_data(original_data, password)
                
                # 写入加密文件
                encrypted_path = file_path + '.secret'
                SecureFileOperations.write_file_binary(encrypted_path, encrypted_data)
                
                # 安全删除原文件
                SecureFileOperations.secure_delete(file_path, passes=10)
                
                success_count += 1
                
                # 更新列表显示
                idx = self.files_to_encrypt.index((rel_path, file_path))
                self.file_listbox.delete(idx)
                self.file_listbox.insert(idx, f"  ✅ {rel_path} -> {rel_path}.secret")
                self.root.update()
                
            except Exception as e:
                fail_count += 1
                print(f"加密失败 {rel_path}: {e}")
        
        # 显示结果
        if fail_count == 0:
            messagebox.showinfo("完成", 
                f"✅ 成功加密 {success_count} 个文件！\n\n"
                "提示：双击 .secret 文件可进行解密")
        else:
            messagebox.showwarning("完成", 
                f"加密完成\n成功: {success_count}\n失败: {fail_count}")
        
        self.root.quit()
    
    def run(self):
        """运行界面"""
        self.root.mainloop()


def main():
    """主函数"""
    # 检查依赖
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        print("错误：缺少 cryptography 库")
        print("请运行: pip install cryptography")
        
        # 尝试显示GUI错误
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("依赖缺失", 
                "缺少 cryptography 库\n\n"
                "请在命令行运行:\npip install cryptography")
            root.destroy()
        except:
            pass
        sys.exit(1)
    
    # 运行GUI
    app = EncryptionGUI()
    app.run()


if __name__ == '__main__':
    main()
