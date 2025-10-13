@echo off
chcp 65001 >nul
echo ========================================
echo   测试打包后的可执行文件
echo ========================================
echo.
echo 正在启动程序...
echo 如果程序正常打开GUI窗口，说明打包成功！
echo.
echo 提示：
echo - 首次运行可能需要几秒钟解压资源
echo - 如果防火墙弹窗，请选择"允许访问"
echo - 测试完成后关闭GUI窗口即可
echo.
pause
echo.
echo 启动中...
start "" "dist\地理数据转GLTF工具.exe"
echo.
echo 程序已启动！
echo 请检查是否正常显示GUI界面
echo.
pause

