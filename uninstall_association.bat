@echo off
chcp 65001 >nul
echo ============================================
echo   文件保密柜 - 卸载文件关联
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

echo [步骤1] 删除 .secret 文件类型关联...

:: 删除文件扩展名关联
reg delete "HKEY_CLASSES_ROOT\.secret" /f >nul 2>&1
reg delete "HKEY_CLASSES_ROOT\SecretVaultFile" /f >nul 2>&1

echo [成功] 文件关联已删除
echo.

:: 刷新图标缓存
echo [步骤2] 刷新系统图标缓存...
ie4uinit.exe -ClearIconCache >nul 2>&1

echo.
echo ============================================
echo   卸载完成！
echo ============================================
echo.
echo .secret 文件将不再自动关联到解密程序
echo.
pause
