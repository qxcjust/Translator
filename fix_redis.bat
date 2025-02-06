@echo off
chcp 65001
cls

:: 检查管理员权限
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [32m已获取管理员权限[0m
) else (
    echo [31m需要管理员权限才能修复Redis[0m
    echo [36m请右键点击此文件，选择"以管理员身份运行"[0m
    pause
    exit /b 1
)

echo [32m开始修复Redis...[0m

:: 停止Redis服务
echo [32m停止Redis服务...[0m
net stop Redis

:: 修改配置
echo [32m修改Redis配置...[0m
python check_redis.py

:: 启动Redis服务
echo [32m启动Redis服务...[0m
net start Redis

echo [32m修复完成[0m
pause 