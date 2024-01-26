@echo off
chcp 65001 > nul

IF NOT EXIST .\venv (
    echo 正在创建虚拟环境...
    python -m venv venv
    call .\venv\Scripts\activate
    echo 正在安装依赖项...
    pip install -r requirements.txt
) else (
    echo 加载虚拟环境...
    call .\venv\Scripts\activate
    echo 确认依赖项...
    pip install -r requirements.txt
)

python flight.py
deactivate
