#!/bin/bash
cd "$(dirname "$0")"

echo "Starting Crypto MA Monitor..."

# 检查依赖
python3 -c "import requests; import yaml; import telegram" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# 运行监控
python3 main.py "$@"
