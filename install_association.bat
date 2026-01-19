@echo off
chcp 65001 >nul
echo ============================================
echo   文件保密柜 - 文件关联安装程序
echo ============================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 请以管理员身份运行此脚本！
    echo.
    echo 右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

:: 获取当前目录
set "SCRIPT_DIR=%~dp0"
set "DECRYPT_SCRIPT=%SCRIPT_DIR%decrypt.py"

:: 检查Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 未找到Python！
    echo 请先安装Python并添加到系统PATH
    pause
    exit /b 1
)

:: 获取Python路径
for /f "tokens=*" %%i in ('where python') do (
    set "PYTHON_PATH=%%i"
    goto :found_python
)
:found_python

echo [信息] Python路径: %PYTHON_PATH%
echo [信息] 解密脚本: %DECRYPT_SCRIPT%
echo.

:: 检查解密脚本是否存在
if not exist "%DECRYPT_SCRIPT%" (
    echo [错误] 解密脚本不存在: %DECRYPT_SCRIPT%
    pause
    exit /b 1
)

:: 创建文件类型关联
echo [步骤1] 注册 .secret 文件类型...

:: 注册文件扩展名
reg add "HKEY_CLASSES_ROOT\.secret" /ve /d "SecretVaultFile" /f >nul
if %errorLevel% neq 0 (
    echo [错误] 注册文件扩展名失败
    pause
    exit /b 1
)

:: 注册文件类型
reg add "HKEY_CLASSES_ROOT\SecretVaultFile" /ve /d "加密文件 (文件保密柜)" /f >nul

:: 设置图标（使用锁图标）
reg add "HKEY_CLASSES_ROOT\SecretVaultFile\DefaultIcon" /ve /d "shell32.dll,47" /f >nul

:: 设置打开命令
set "OPEN_CMD=\"%PYTHON_PATH%\" \"%DECRYPT_SCRIPT%\" \"%%1\""
reg add "HKEY_CLASSES_ROOT\SecretVaultFile\shell\open\command" /ve /d "%OPEN_CMD%" /f >nul

echo [成功] 文件类型关联已创建
echo.

:: 添加右键菜单
echo [步骤2] 添加右键菜单...

:: 添加"解密"右键菜单
reg add "HKEY_CLASSES_ROOT\SecretVaultFile\shell\decrypt" /ve /d "🔓 解密文件" /f >nul
reg add "HKEY_CLASSES_ROOT\SecretVaultFile\shell\decrypt\command" /ve /d "%OPEN_CMD%" /f >nul

echo [成功] 右键菜单已添加
echo.

:: 刷新图标缓存
echo [步骤3] 刷新系统图标缓存...
ie4uinit.exe -ClearIconCache >nul 2>&1
ie4uinit.exe -show >nul 2>&1

echo.
echo ============================================
echo   安装完成！
echo ============================================
echo.
echo 现在你可以：
echo   1. 双击 .secret 文件进行解密
echo   2. 右键 .secret 文件选择"解密文件"
echo.
echo 注意：.secret 文件将显示锁图标
echo.
pause
