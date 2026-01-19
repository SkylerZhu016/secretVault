@echo off
chcp 65001 >nul
echo ============================================
echo   文件保密柜 - 安装依赖
echo ============================================
echo.

:: 检查Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到Python！
    echo.
    echo 请先安装Python:
    echo   1. 访问 https://www.python.org/downloads/
    echo   2. 下载并安装最新版Python
    echo   3. 安装时勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [信息] 检测到Python:
python --version
echo.

echo [步骤1] 升级pip...
python -m pip install --upgrade pip
echo.

echo [步骤2] 安装cryptography库...
pip install cryptography
echo.

if %errorLevel% neq 0 (
    echo [错误] 安装失败！
    echo.
    echo 请尝试手动运行:
    echo   pip install cryptography
    pause
    exit /b 1
)

echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo 现在可以运行:
echo   - encrypt.py  加密文件
echo   - decrypt.py  解密文件
echo.
pause
