# Crypto MA Monitor

Web3 代币均线密集度监控程序

## 功能特性

### 核心功能
- **多币种监控**: 支持 BTC、BNB、SOL、ETH 等主流代币
- **多周期分析**: 支持 1小时、4小时、1天 三个时间周期
- **均线密集度检测**: 采用双指标判定
  - 均线极差率: `(MA_max - MA_min) / 参考价 × 100%`
  - 均线标准差率: `std(MA) / mean(MA) × 100%`
- **Telegram 告警**: 符合条件时自动发送通知

### 均线参数
- 默认均线: MA20, MA60, MA120

### 密集度阈值
| 市场 | 极差率 | 标准差率 |
|------|--------|----------|
| 牛市 | ≤ 3.0% | ≤ 2.0% |
| 熊市 | ≤ 1.5% | ≤ 1.0% |

### 触发条件
- 均线极差率 或 标准差率 低于阈值
- 连续 3 根 K 线都处于密集状态

---

## 快速开始

### 1. 安装依赖

```bash
cd /home/zj/crypto_monitor
pip3 install -r requirements.txt
```

### 2. 配置 Telegram

1. 搜索 `@BotFather` 发送 `/newbot` 创建机器人
2. 复制 Bot Token
3. 搜索 `@userinfobot` 发送任意消息获取 Chat ID

### 3. 复制并配置

```bash
cp config/config.yaml.example config/config.yaml
# 编辑 config.yaml 填写 Telegram 配置
```

### 4. 运行程序

```bash
# 默认运行 (牛市模式)
python3 main.py

# 熊市模式 (更严格阈值)
python3 main.py -b

# 自定义检查间隔
python3 main.py -i 600
```

---

## 命令行参数

| 参数 | 短命令 | 说明 | 默认值 |
|------|--------|------|--------|
| `--config` | `-c` | 配置文件路径 | config/config.yaml |
| `--bear` | `-b` | 熊市模式 | 牛市模式 |
| `--interval` | `-i` | 检查间隔(秒) | 配置文件中值 |
| `help` | - | 显示帮助 | - |

---

## 配置文件说明

```yaml
# 监控代币
symbols:
  - BTC
  - BNB
  - SOL
  - ETH

# 时间周期
timeframes:
  - 1h
  - 4h
  - 1d

# 均线周期
ma_periods: [20, 60, 120]

# 均线密集度阈值 (%)
ma_density_threshold:
  spread_bull: 3.0   # 极差率 - 牛市
  spread_bear: 1.5  # 极差率 - 熊市
  std_bull: 2.0      # 标准差 - 牛市
  std_bear: 1.0      # 标准差 - 熊市

# 连续密集K线根数
consecutive_days: 3

# 检查间隔(秒)
check_interval: 30

# 告警重置时间(小时)
alert_reset_hours: 6

# Telegram配置
telegram:
  bot_token: ""
  chat_id: ""
```

---

## 告警消息示例

```
🚀 均线密集告警

📌 BTC (1h)

💰 现价: $67,543.21

📊 均线密集度:
• 极差率: 2.15%
• 标准差率: 0.85%

📐 均线值:
• 最大: $67,890.00
• 最小: $67,200.00
• 均值: $67,540.00

⏰ 连续密集: 3根

🔥 状态: 密集!
```

---

## 数据源

使用 **Bitget** 公开 API (免费，无需 Key)

---

## 守护进程运行 (Linux)

```bash
# 使用 nohup 后台运行
nohup python3 main.py > monitor.log 2>&1 &

# 使用 systemd
sudo tee /etc/systemd/system/crypto-ma-monitor.service << EOF
[Unit]
Description=Crypto MA Monitor
After=network.target

[Service]
Type=simple
User=zj
WorkingDirectory=/home/zj/crypto_monitor
ExecStart=/usr/bin/python3 main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable crypto-ma-monitor
sudo systemctl start crypto-ma-monitor
```

---

## 许可证

MIT License
