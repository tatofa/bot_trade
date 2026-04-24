from risk_manager import trade_budget


def test_trade_budget_example():
    result = trade_budget(
        account_size_usdt=1000,
        risk_per_trade=0.005,
        stop_loss_pct=0.004,
        leverage=3,
    )
    assert round(result["account_risk"], 2) == 5.00
    assert round(result["notional_size"], 2) == 1250.00
    assert round(result["margin_required"], 2) == 416.67
