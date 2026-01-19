#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件保密柜 - 解密脚本
双击 .secret 文件时触发解密
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# 获取脚本所在目录（用于找到secret_vault模块）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from secret_vault.crypto import SecretVaultCrypto, SecureFileOperations, AttemptTracker


class DecryptionGUI:
    """解密界面"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        
        # 读取文件数据
        try:
            self.encrypted_data = SecureFileOperations.read_file_binary(file_path)
            # 获取文件唯一ID（用于全局追踪）
            self.file_id = AttemptTracker.get_file_id(self.encrypted_data)
            
            # 从全局追踪器获取尝试次数（防止复制绕过）
            self.current_attempts, self.max_attempts = AttemptTracker.get_attempts(self.file_id)
            self.remaining_attempts = self.max_attempts - self.current_attempts
            
            # 如果是新文件，注册到追踪器
            if self.current_attempts == 0:
                AttemptTracker.register_file(self.file_id, self.max_attempts)
                
        except Exception as e:
            messagebox.showerror("错误", f"无法读取加密文件：\n{e}")
            sys.exit(1)
        
        # 检查是否已用尽尝试次数（包括通过复制尝试的情况）
        if self.remaining_attempts <= 0 or AttemptTracker.is_destroyed(self.file_id):
            self.trigger_self_destruct()
            return
        
        # 创建窗口
        self.root = tk.Tk()
        self.root.title("文件保密柜 - 解密")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        self.root.minsize(450, 380)
        
        # 设置图标（如果有）
        try:
            self.root.iconbitmap(os.path.join(SCRIPT_DIR, 'icon.ico'))
        except:
            pass
        
        # 居中显示
        self.center_window()
        
        # 绑定回车键
        self.root.bind('<Return>', lambda e: self.do_decrypt())
        
        # 创建界面
        self.create_widgets()
    
    def center_window(self):
        """居中显示窗口"""
        self.root.update_idletasks()
        width = 500
        height = 500
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 锁图标和标题
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = tk.Label(title_frame, text="🔐", font=('Segoe UI Emoji', 40))
        title_label.pack()
        
        subtitle = ttk.Label(title_frame, text="文件已加密", font=('Microsoft YaHei', 14, 'bold'))
        subtitle.pack(pady=(5, 0))
        
        # 文件名
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(file_frame, text="文件:", font=('Microsoft YaHei', 11)).pack(side=tk.LEFT)
        file_label = ttk.Label(file_frame, text=self.file_name, font=('Consolas', 11), foreground='#0066cc')
        file_label.pack(side=tk.LEFT, padx=(8, 0))
        
        # 剩余次数警告
        attempts_frame = ttk.Frame(main_frame)
        attempts_frame.pack(fill=tk.X, pady=(0, 20))
        
        if self.remaining_attempts <= 1:
            warning_color = '#cc0000'
            warning_text = f"⚠️ 最后 {self.remaining_attempts} 次机会！输错将销毁文件！"
        elif self.remaining_attempts <= 2:
            warning_color = '#cc6600'
            warning_text = f"⚠️ 剩余 {self.remaining_attempts} 次尝试机会"
        else:
            warning_color = '#666666'
            warning_text = f"剩余 {self.remaining_attempts} 次尝试机会"
        
        attempts_label = ttk.Label(attempts_frame, text=warning_text,
                                   font=('Microsoft YaHei', 11), foreground=warning_color)
        attempts_label.pack()
        
        # 密码输入
        pwd_frame = ttk.Frame(main_frame)
        pwd_frame.pack(fill=tk.X, pady=(0, 25))
        
        ttk.Label(pwd_frame, text="请输入解密密码:", font=('Microsoft YaHei', 11)).pack(anchor=tk.W)
        
        self.password_entry = ttk.Entry(pwd_frame, show="•", width=40, font=('Consolas', 12))
        self.password_entry.pack(fill=tk.X, pady=(10, 0), ipady=8)
        self.password_entry.focus()
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        decrypt_btn = ttk.Button(btn_frame, text="🔓 解密", command=self.do_decrypt)
        decrypt_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 10), ipady=8)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=self.root.quit)
        cancel_btn.pack(side=tk.RIGHT, ipady=8, ipadx=15)
    
    def do_decrypt(self):
        """执行解密"""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showerror("错误", "请输入密码！")
            return
        
        # 尝试解密
        decrypted_data, success, _ = SecretVaultCrypto.decrypt_data(self.encrypted_data, password)
        
        if success:
            # 解密成功 - 从全局追踪器中移除记录
            AttemptTracker.reset_attempts(self.file_id)
            
            try:
                # 获取原始文件路径（去掉.secret后缀）
                original_path = self.file_path[:-7]  # 移除 '.secret'
                
                # 写入解密后的文件
                SecureFileOperations.write_file_binary(original_path, decrypted_data)
                
                # 安全删除加密文件
                SecureFileOperations.secure_delete(self.file_path, passes=3)
                
                messagebox.showinfo("成功",
                    f"✅ 文件解密成功！\n\n"
                    f"已恢复: {os.path.basename(original_path)}")
                
                # 打开文件所在目录
                os.startfile(os.path.dirname(original_path))
                
            except Exception as e:
                messagebox.showerror("错误", f"保存解密文件失败：\n{e}")
            
            self.root.quit()
        else:
            # 解密失败 - 使用全局追踪器更新尝试次数
            new_attempts = AttemptTracker.increment_attempts(self.file_id)
            remaining = self.max_attempts - new_attempts
            
            # 同时更新文件内的尝试次数（作为备份）
            updated_data = SecretVaultCrypto.update_attempt_count(self.encrypted_data, new_attempts)
            try:
                SecureFileOperations.write_file_binary(self.file_path, updated_data)
            except Exception as e:
                print(f"更新文件尝试次数失败: {e}")
            
            if remaining <= 0:
                # 用尽所有尝试，标记为已销毁并触发自毁
                AttemptTracker.mark_destroyed(self.file_id)
                self.root.withdraw()
                self.trigger_self_destruct()
            else:
                # 还有机会
                if remaining == 1:
                    messagebox.showwarning("密码错误",
                        f"❌ 密码错误！\n\n"
                        f"⚠️ 最后 1 次机会！\n"
                        f"再次输错文件将被永久销毁！\n\n"
                        f"注意：复制文件无法重置尝试次数！")
                else:
                    messagebox.showwarning("密码错误",
                        f"❌ 密码错误！\n\n"
                        f"剩余 {remaining} 次尝试机会\n\n"
                        f"注意：复制文件无法重置尝试次数！")
                
                # 更新界面状态
                self.remaining_attempts = remaining
                self.current_attempts = new_attempts
                self.encrypted_data = updated_data
                
                # 清空密码框
                self.password_entry.delete(0, tk.END)
                self.password_entry.focus()
    
    def trigger_self_destruct(self):
        """触发文件自毁"""
        # 确保标记为已销毁（防止复制文件再次尝试）
        if hasattr(self, 'file_id'):
            AttemptTracker.mark_destroyed(self.file_id)
        
        messagebox.showerror("安全警告",
            "🚨 密码尝试次数已用尽！\n\n"
            "文件将被永久销毁，无法恢复！\n"
            "即使复制的备份也无法使用！")
        
        # 执行安全删除
        print(f"正在安全销毁文件: {self.file_path}")
        success = SecureFileOperations.secure_delete(self.file_path, passes=10)
        
        if success:
            messagebox.showinfo("已销毁",
                "🗑️ 文件已被安全销毁\n\n"
                "数据已被覆盖10次，无法恢复。\n"
                "所有复制的文件也已失效。")
        else:
            messagebox.showwarning("警告",
                "文件销毁过程中出现问题\n"
                "请手动删除文件。\n"
                "注意：复制的文件也已失效。")
        
        sys.exit(0)
    
    def run(self):
        """运行界面"""
        if hasattr(self, 'root'):
            self.root.mainloop()


def main():
    """主函数"""
    # 检查依赖
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("依赖缺失", 
                "缺少 cryptography 库\n\n"
                "请在命令行运行:\npip install cryptography")
            root.destroy()
        except:
            print("错误：缺少 cryptography 库")
            print("请运行: pip install cryptography")
        sys.exit(1)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        # 没有传入文件，显示帮助
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("使用说明", 
                "文件保密柜 - 解密程序\n\n"
                "使用方法：\n"
                "1. 双击 .secret 文件进行解密\n"
                "2. 或将 .secret 文件拖放到本程序上\n\n"
                "注意：连续输错3次密码，文件将被永久销毁！")
            root.destroy()
        except:
            print("使用方法: python decrypt.py <file.secret>")
        sys.exit(0)
    
    # 获取文件路径
    file_path = sys.argv[1]
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        messagebox.showerror("错误", f"文件不存在：\n{file_path}")
        sys.exit(1)
    
    # 检查文件扩展名
    if not file_path.endswith('.secret'):
        messagebox.showerror("错误", "这不是一个有效的加密文件（.secret）")
        sys.exit(1)
    
    # 运行解密界面
    app = DecryptionGUI(file_path)
    app.run()


if __name__ == '__main__':
    main()
