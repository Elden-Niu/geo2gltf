@echo off
chcp 65001 >nul
echo ========================================
echo   创建发布包
echo ========================================
echo.

REM 创建发布目录
set RELEASE_DIR=地理数据转GLTF工具_v1.0
if exist "%RELEASE_DIR%" (
    echo 删除旧的发布目录...
    rmdir /s /q "%RELEASE_DIR%"
)

echo 创建发布目录...
mkdir "%RELEASE_DIR%"

REM 复制exe文件
echo 复制可执行文件...
copy "dist\地理数据转GLTF工具.exe" "%RELEASE_DIR%\" >nul

REM 复制使用说明
echo 复制使用说明...
copy "README_EXE.txt" "%RELEASE_DIR%\使用说明.txt" >nul

REM 复制logo（如果存在）
if exist "logo.png" (
    echo 复制Logo文件...
    copy "logo.png" "%RELEASE_DIR%\" >nul
)

REM 创建示例目录
echo 创建示例目录...
mkdir "%RELEASE_DIR%\示例文件"

echo.
echo ========================================
echo   发布包创建完成！
echo ========================================
echo.
echo 发布包位置: %RELEASE_DIR%
echo 包含以下文件:
dir /b "%RELEASE_DIR%"
echo.
echo 可以将整个文件夹打包分发给用户使用
echo.
pause

