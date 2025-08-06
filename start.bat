@echo off
:: =================================================================
::  一键启动前后端项目脚本 (Windows Batch Script)
:: =================================================================
::
::  使用说明:
::  1. 将此文件另存为 `start_project.bat` (或任何以 .bat 结尾的文件名)。
::  2. 将此文件放置在您项目的根目录下。
::     您的项目结构应该如下所示:
::
::     /你的项目根目录
::     |-- /backend
::     |-- /frontend
::     |-- start_project.bat  <-- (就是这个脚本文件)
::
::  3. 直接双击运行 `start_project.bat` 文件即可。
::

echo.
echo =================================================
echo           正在启动项目...
echo =================================================
echo.

REM 检查 backend 文件夹是否存在
if not exist "backend" (
    echo 错误: 未在当前目录下找到 'backend' 文件夹。
    pause
    exit
)

REM 检查 frontend 文件夹是否存在
if not exist "ai4exam-frontend" (
    echo 错误: 未在当前目录下找到 'frontend' 文件夹。
    pause
    exit
)


echo [1/2] 正在启动后端服务 (uvicorn)...
:: 启动一个新的命令提示符窗口，命名为 "Backend Server"
:: 然后进入 `backend` 目录，并执行 uvicorn 启动命令
:: 使用 /k 参数可以在命令执行后保持窗口打开，方便你查看日志和错误信息
start "Backend Server" cmd /k "conda activate open_llm_vtuber && cd backend && python -m uvicorn main:app"

echo [2/2] 正在启动前端开发服务器...
:: 启动另一个新的命令提示符窗口，命名为 "Frontend Server"
:: 然后进入 `frontend` 目录，并执行 `npm start`
:: !!! 注意: 如果你的前端启动命令不是 `npm start`，请修改下面这行命令 !!!
:: (例如: `yarn start`, `npm run dev`, `vite` 等)
start "Frontend Server" cmd /k "cd ai4exam-frontend && npm run dev"

echo.
echo -------------------------------------------------
echo  启动指令已发送!
echo  后端和前端服务已在新的窗口中分别启动。
echo  请在新打开的窗口中查看各自的运行日志。
echo -------------------------------------------------
echo.

:: 等待几秒钟，让用户看到消息，然后这个主窗口会自动关闭
timeout /t 4 > nul
exit