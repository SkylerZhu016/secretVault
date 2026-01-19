"""
文件保密柜 - 核心加密模块
使用 AES-256-GCM 加密算法
"""

import os
import json
import hashlib
import secrets
import uuid
import sqlite3
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class SecretVaultCrypto:
    """加密解密核心类"""
    
    # 加密文件的魔术字节，用于验证文件格式
    MAGIC_BYTES = b'SECVAULT'
    VERSION = 1
    
    # 加密参数
    SALT_SIZE = 32  # 盐值长度
    NONCE_SIZE = 12  # GCM nonce长度
    KEY_SIZE = 32   # AES-256 密钥长度
    ITERATIONS = 600000  # PBKDF2 迭代次数（较高以增加暴力破解难度）
    
    @classmethod
    def derive_key(cls, password: str, salt: bytes) -> bytes:
        """从密码派生加密密钥"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=cls.KEY_SIZE,
            salt=salt,
            iterations=cls.ITERATIONS,
            backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
    
    @classmethod
    def encrypt_data(cls, data: bytes, password: str) -> bytes:
        """
        加密数据
        
        返回格式:
        [MAGIC_BYTES(8)] [VERSION(1)] [SALT(32)] [NONCE(12)] [MAX_ATTEMPTS(1)] [ATTEMPT_COUNT(1)] [ENCRYPTED_DATA(...)] [AUTH_TAG(16)]
        """
        # 生成随机盐值和nonce
        salt = secrets.token_bytes(cls.SALT_SIZE)
        nonce = secrets.token_bytes(cls.NONCE_SIZE)
        
        # 派生密钥
        key = cls.derive_key(password, salt)
        
        # 使用AES-GCM加密
        aesgcm = AESGCM(key)
        encrypted_data = aesgcm.encrypt(nonce, data, None)
        
        # 组装加密文件
        result = bytearray()
        result.extend(cls.MAGIC_BYTES)           # 魔术字节
        result.append(cls.VERSION)                # 版本号
        result.extend(salt)                       # 盐值
        result.extend(nonce)                      # nonce
        result.append(3)                          # 最大尝试次数
        result.append(0)                          # 当前尝试次数
        result.extend(encrypted_data)             # 加密数据（包含认证标签）
        
        return bytes(result)
    
    @classmethod
    def parse_encrypted_file(cls, data: bytes) -> Tuple[bytes, bytes, int, int, bytes]:
        """
        解析加密文件格式
        
        返回: (salt, nonce, max_attempts, attempt_count, encrypted_data)
        """
        if len(data) < 8 + 1 + 32 + 12 + 1 + 1 + 16:
            raise ValueError("无效的加密文件格式：文件太小")
        
        if data[:8] != cls.MAGIC_BYTES:
            raise ValueError("无效的加密文件格式：魔术字节不匹配")
        
        version = data[8]
        if version != cls.VERSION:
            raise ValueError(f"不支持的文件版本: {version}")
        
        offset = 9
        salt = data[offset:offset + cls.SALT_SIZE]
        offset += cls.SALT_SIZE
        
        nonce = data[offset:offset + cls.NONCE_SIZE]
        offset += cls.NONCE_SIZE
        
        max_attempts = data[offset]
        offset += 1
        
        attempt_count = data[offset]
        offset += 1
        
        encrypted_data = data[offset:]
        
        return salt, nonce, max_attempts, attempt_count, encrypted_data
    
    @classmethod
    def update_attempt_count(cls, data: bytes, new_count: int) -> bytes:
        """更新尝试次数"""
        data = bytearray(data)
        # 尝试次数位于固定偏移位置
        attempt_offset = 8 + 1 + cls.SALT_SIZE + cls.NONCE_SIZE + 1
        data[attempt_offset] = new_count
        return bytes(data)
    
    @classmethod
    def decrypt_data(cls, encrypted_file_data: bytes, password: str) -> Tuple[bytes, bool, int]:
        """
        解密数据
        
        返回: (解密后的数据, 是否成功, 剩余尝试次数)
        如果解密失败，返回的数据为空bytes
        """
        salt, nonce, max_attempts, attempt_count, encrypted_data = cls.parse_encrypted_file(encrypted_file_data)
        
        remaining = max_attempts - attempt_count
        
        try:
            # 派生密钥
            key = cls.derive_key(password, salt)
            
            # 解密
            aesgcm = AESGCM(key)
            decrypted_data = aesgcm.decrypt(nonce, encrypted_data, None)
            
            return decrypted_data, True, remaining
        except Exception:
            # 解密失败
            return b'', False, remaining - 1
    
    @classmethod
    def get_attempt_info(cls, encrypted_file_data: bytes) -> Tuple[int, int]:
        """获取尝试次数信息"""
        _, _, max_attempts, attempt_count, _ = cls.parse_encrypted_file(encrypted_file_data)
        return max_attempts, attempt_count


class SecureFileOperations:
    """安全文件操作类"""
    
    @staticmethod
    def secure_delete(file_path: str, passes: int = 10) -> bool:
        """
        安全删除文件，多次覆盖
        
        Args:
            file_path: 要删除的文件路径
            passes: 覆盖次数
        
        Returns:
            是否成功删除
        """
        try:
            if not os.path.exists(file_path):
                return True
            
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'r+b') as f:
                for pass_num in range(passes):
                    f.seek(0)
                    if pass_num % 3 == 0:
                        # 用0x00覆盖
                        f.write(b'\x00' * file_size)
                    elif pass_num % 3 == 1:
                        # 用0xFF覆盖
                        f.write(b'\xFF' * file_size)
                    else:
                        # 用随机数据覆盖
                        f.write(secrets.token_bytes(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # 最终删除文件
            os.remove(file_path)
            return True
        except Exception as e:
            print(f"安全删除失败: {e}")
            # 尝试普通删除
            try:
                os.remove(file_path)
                return True
            except:
                return False
    
    @staticmethod
    def read_file_binary(file_path: str) -> bytes:
        """读取二进制文件"""
        with open(file_path, 'rb') as f:
            return f.read()
    
    @staticmethod
    def write_file_binary(file_path: str, data: bytes) -> None:
        """写入二进制文件"""
        with open(file_path, 'wb') as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())


class AttemptTracker:
    """
    全局尝试次数跟踪器
    
    使用SQLite数据库记录每个加密文件的尝试次数。
    即使文件被复制，只要文件ID相同，尝试次数就是共享的。
    """
    
    # 数据库存储位置（用户AppData目录下，难以被发现）
    DB_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), '.secret_vault')
    DB_PATH = os.path.join(DB_DIR, '.attempts.db')
    
    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        """获取数据库连接"""
        # 确保目录存在
        os.makedirs(cls.DB_DIR, exist_ok=True)
        
        # 隐藏目录（Windows）
        try:
            import ctypes
            ctypes.windll.kernel32.SetFileAttributesW(cls.DB_DIR, 0x02)  # HIDDEN
        except:
            pass
        
        conn = sqlite3.connect(cls.DB_PATH)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS attempts (
                file_id TEXT PRIMARY KEY,
                attempt_count INTEGER DEFAULT 0,
                max_attempts INTEGER DEFAULT 3,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_attempt TIMESTAMP
            )
        ''')
        conn.commit()
        return conn
    
    @classmethod
    def get_file_id(cls, encrypted_data: bytes) -> str:
        """
        从加密文件数据中提取唯一ID
        使用盐值和nonce的组合作为文件唯一标识
        """
        if len(encrypted_data) < 55:
            raise ValueError("无效的加密文件")
        
        # 提取盐值(32字节)和nonce(12字节)作为唯一标识
        salt_nonce = encrypted_data[9:53]  # offset 9, length 44
        return hashlib.sha256(salt_nonce).hexdigest()
    
    @classmethod
    def get_attempts(cls, file_id: str) -> Tuple[int, int]:
        """
        获取文件的尝试次数信息
        
        返回: (当前尝试次数, 最大尝试次数)
        """
        conn = cls._get_connection()
        cursor = conn.execute(
            'SELECT attempt_count, max_attempts FROM attempts WHERE file_id = ?',
            (file_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return row[0], row[1]
        return 0, 3  # 默认值
    
    @classmethod
    def register_file(cls, file_id: str, max_attempts: int = 3) -> None:
        """注册新的加密文件"""
        conn = cls._get_connection()
        conn.execute('''
            INSERT OR IGNORE INTO attempts (file_id, max_attempts, attempt_count)
            VALUES (?, ?, 0)
        ''', (file_id, max_attempts))
        conn.commit()
        conn.close()
    
    @classmethod
    def increment_attempts(cls, file_id: str) -> int:
        """
        增加尝试次数
        
        返回: 新的尝试次数
        """
        conn = cls._get_connection()
        
        # 确保记录存在
        conn.execute('''
            INSERT OR IGNORE INTO attempts (file_id, max_attempts, attempt_count)
            VALUES (?, 3, 0)
        ''', (file_id,))
        
        # 增加计数
        conn.execute('''
            UPDATE attempts
            SET attempt_count = attempt_count + 1,
                last_attempt = CURRENT_TIMESTAMP
            WHERE file_id = ?
        ''', (file_id,))
        
        conn.commit()
        
        # 获取新的计数
        cursor = conn.execute(
            'SELECT attempt_count FROM attempts WHERE file_id = ?',
            (file_id,)
        )
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else 1
    
    @classmethod
    def reset_attempts(cls, file_id: str) -> None:
        """重置尝试次数（解密成功后调用）"""
        conn = cls._get_connection()
        conn.execute('DELETE FROM attempts WHERE file_id = ?', (file_id,))
        conn.commit()
        conn.close()
    
    @classmethod
    def mark_destroyed(cls, file_id: str) -> None:
        """标记文件已销毁（设置一个极大的尝试次数）"""
        conn = cls._get_connection()
        conn.execute('''
            INSERT OR REPLACE INTO attempts (file_id, max_attempts, attempt_count)
            VALUES (?, 3, 999)
        ''', (file_id,))
        conn.commit()
        conn.close()
    
    @classmethod
    def is_destroyed(cls, file_id: str) -> bool:
        """检查文件是否已被标记为销毁"""
        attempts, max_attempts = cls.get_attempts(file_id)
        return attempts >= 999 or attempts >= max_attempts
