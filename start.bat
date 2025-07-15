@echo off
REM 一键启动脚本 for Windows

REM 1. 检查并创建虚拟环境
if not exist venv (
    echo [INFO] 创建Python虚拟环境...
    python -m venv venv
)

REM 2. 激活虚拟环境
call venv\Scripts\activate.bat

REM 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

REM 4. 启动Flask服务
python app.py

REM 5. 保持窗口
pause 