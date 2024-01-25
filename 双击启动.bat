@echo off
chcp 65001 > nul

set venvDir=venv
set scriptPath=flight.py

if not exist %venvDir%\Scripts\activate (
    echo 正在创建虚拟环境...请稍后...
    python -m venv %venvDir%
    
    echo 正在安装依赖项...
    call %venvDir%\Scripts\activate
    pip install -r requirements.txt
)

call %venvDir%\Scripts\activate
python %scriptPath%
deactivate