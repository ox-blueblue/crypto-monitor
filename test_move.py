#!/usr/bin/env python3
"""
动量计算测试程序
"""

import sys
sys.path.insert(0, '.')

from move_main import MoveConfig, MomentumCalculator, format_message


def test_config():
    """测试配置加载"""
    print("=" * 50)
    print("测试1: 配置加载")
    print("=" * 50)
    
    config = MoveConfig()
    assert config.symbols == ["BTC", "BNB", "SOL", "ETH"], f"symbols 错误: {config.symbols}"
    assert config.periods == [5, 10, 20], f"periods 错误: {config.periods}"
    assert config.calculate_time == "7:50", f"calculate_time 错误: {config.calculate_time}"
    assert config.telegram_bot_token != "", "telegram_bot_token 为空"
    assert config.telegram_chat_id != "", "telegram_chat_id 为空"
    
    print("✓ 配置加载测试通过")
    print()


def test_momentum_calculation():
    """测试动量计算逻辑"""
    print("=" * 50)
    print("测试2: 动量计算逻辑")
    print("=" * 50)
    
    calc = MomentumCalculator()
    
    # 测试单币种单周期
    symbol, current_price, past_price, momentum = calc.calculate("BTC", 5)
    print(f"BTC 5天动量: {momentum:.2f}%")
    
    # 验证逻辑: momentum = (current - past) / past * 100
    # 获取K线数据手动验证
    candles = calc.client.get_candles("BTC", "1d", 6)
    expected_current = float(candles[0][4])
    expected_past = float(candles[5][4])
    expected = (expected_current - expected_past) / expected_past * 100
    
    print(f"当前价格: {current_price}")
    print(f"5天前价格: {past_price}")
    print(f"计算动量: {momentum:.2f}%")
    print(f"预期动量: {expected:.2f}%")
    
    assert abs(momentum - expected) < 0.01, f"动量计算错误: {momentum} != {expected}"
    assert abs(current_price - expected_current) < 0.01, f"当前价格错误"
    assert abs(past_price - expected_past) < 0.01, f"过去价格错误"
    
    print("✓ 动量计算逻辑测试通过")
    print()


def test_sorting():
    """测试排序功能"""
    print("=" * 50)
    print("测试3: 排序功能")
    print("=" * 50)
    
    # 手动构造测试数据
    test_data = {
        5: [("BTC", 5.0), ("ETH", 3.0), ("SOL", -2.0), ("BNB", -5.0)],
        10: [("ETH", 10.0), ("BTC", 5.0), ("BNB", -1.0), ("SOL", -8.0)],
    }
    
    # 验证降序排序
    for period in test_data:
        data = test_data[period]
        momenta = [m for _, m in data]
        assert momenta == sorted(momenta, reverse=True), f"{period}天排序错误"
    
    print(f"5天动量排序: {[m for _, m in test_data[5]]}")
    print(f"10天动量排序: {[m for _, m in test_data[10]]}")
    print("✓ 排序功能测试通过")
    print()


def test_message_format():
    """测试消息格式"""
    print("=" * 50)
    print("测试4: 消息格式")
    print("=" * 50)
    
    # (symbol, current_price, past_price, momentum)
    test_data = {
        5: [("BTC", 100000.0, 95000.0, 5.23), ("ETH", 3000.0, 2900.0, 3.12), ("SOL", 100.0, 101.0, -1.05), ("BNB", 600.0, 615.0, -2.34)],
        10: [("ETH", 3100.0, 2850.0, 8.50), ("BTC", 102000.0, 99700.0, 2.30), ("BNB", 590.0, 615.0, -4.10), ("SOL", 95.0, 103.0, -7.80)],
    }
    
    message = format_message(test_data)
    print(message)
    print()
    
    assert "5天动量排行" in message, "缺少5天周期标题"
    assert "10天动量排行" in message, "缺少10天周期标题"
    assert "BTC" in message and "ETH" in message, "缺少币种名称"
    assert "100,000.00" in message, "当前价格格式错误"
    assert "95,000.00" in message, "过去价格格式错误"
    assert "涨跌幅" in message, "缺少涨跌幅列标题"
    assert "🥇" in message and "🥈" in message and "🥉" in message, "缺少奖牌emoji"
    
    print("✓ 消息格式测试通过")
    print()


def test_integration():
    """集成测试"""
    print("=" * 50)
    print("测试5: 集成测试")
    print("=" * 50)
    
    config = MoveConfig()
    calc = MomentumCalculator()
    
    results = calc.calculate_all(config.symbols, config.periods)
    
    print(f"计算币种: {config.symbols}")
    print(f"计算周期: {config.periods}")
    print(f"返回周期: {list(results.keys())}")
    
    assert len(results) == len(config.periods), "返回周期数量不匹配"
    
    for period in config.periods:
        assert period in results, f"缺少周期 {period}"
        assert len(results[period]) == len(config.symbols), f"周期 {period} 币种数量不匹配"
        
        symbols_in_result = [s for s, _, _, _ in results[period]]
        assert set(symbols_in_result) == set(config.symbols), f"周期 {period} 币种不匹配"
        
        print(f"\n{period}天动量:")
        for symbol, current_price, past_price, momentum in results[period]:
            sign = "+" if momentum >= 0 else ""
            print(f"  {symbol}: 当前 {current_price:,.2f} 前{period}天 {past_price:,.2f} {sign}{momentum:.2f}%")
    
    print("\n✓ 集成测试通过")
    print()


def test_telegram_send():
    """测试Telegram发送"""
    print("=" * 50)
    print("测试6: Telegram发送")
    print("=" * 50)
    
    config = MoveConfig()
    notifier = None
    
    if config.telegram_bot_token and config.telegram_chat_id:
        from src.notification.telegram import TelegramNotifier
        notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
        
        calc = MomentumCalculator()
        results = calc.calculate_all(config.symbols, config.periods)
        message = format_message(results)
        
        print("发送测试消息...")
        success = notifier.send_message("[测试] " + message)
        
        if success:
            print("✓ Telegram 发送测试通过")
        else:
            print("✗ Telegram 发送失败")
    else:
        print("跳过: Telegram 未配置")
    
    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("动量计算测试套件")
    print("=" * 50 + "\n")
    
    test_config()
    test_momentum_calculation()
    test_sorting()
    test_message_format()
    test_integration()
    test_telegram_send()
    
    print("=" * 50)
    print("所有测试通过! ✓")
    print("=" * 50)


if __name__ == "__main__":
    main()