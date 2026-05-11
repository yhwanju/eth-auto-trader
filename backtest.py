import sys
from pathlib import Path

import pandas as pd
import pyupbit


ETH_TICKER = "KRW-ETH"
BTC_TICKER = "KRW-BTC"
INTERVAL = "minute5"
COUNT = 2000
INITIAL_CASH = 50_000.0
FEE_RATE = 0.0005
RESULT_FILE = Path("backtest_result.csv")


def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def add_eth_indicators(df):
    df = df.copy()

    df["EMA5"] = df["close"].ewm(span=5, adjust=False).mean()
    df["EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["EMA60"] = df["close"].ewm(span=60, adjust=False).mean()
    df["RSI"] = calculate_rsi(df["close"])
    df["volume_ma20"] = df["volume"].rolling(window=20).mean()

    return df


def add_btc_indicators(df):
    df = df.copy()

    df["BTC_EMA20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["BTC_EMA60"] = df["close"].ewm(span=60, adjust=False).mean()
    df["BTC_UPTREND"] = df["BTC_EMA20"] > df["BTC_EMA60"]

    return df[["BTC_EMA20", "BTC_EMA60", "BTC_UPTREND"]]


def merge_eth_btc(eth_df, btc_df):
    eth_df = eth_df.sort_index().copy()
    btc_df = btc_df.sort_index().copy()

    eth_df.index.name = "timestamp"
    btc_df.index.name = "timestamp"

    eth_data = eth_df.reset_index()
    btc_data = btc_df.reset_index()

    merged = pd.merge_asof(
        eth_data,
        btc_data,
        on="timestamp",
        direction="backward",
    )

    return merged.set_index("timestamp")


def is_buy_signal(row):
    return (
        row["EMA5"] > row["EMA20"]
        and row["EMA20"] > row["EMA60"]
        and row["RSI"] > 55
        and row["volume"] > row["volume_ma20"]
        and bool(row["BTC_UPTREND"])
    )


def get_sell_reason(entry_price, current_price, rsi):
    change_rate = (current_price - entry_price) / entry_price

    if change_rate <= -0.03:
        return "STOP_LOSS"
    if change_rate >= 0.06:
        return "TAKE_PROFIT"
    if rsi > 72:
        return "RSI_OVER_72"

    return None


def calculate_mdd(equity_curve):
    if not equity_curve:
        return 0.0

    equity = pd.Series(equity_curve)
    peak = equity.cummax()
    drawdown = (equity - peak) / peak

    return drawdown.min() * 100


def run_backtest(df):
    cash = INITIAL_CASH
    eth_amount = 0.0
    entry_price = 0.0
    entry_time = None
    entry_cash = 0.0

    trades = []
    equity_curve = [INITIAL_CASH]

    for timestamp, row in df.iterrows():
        current_price = float(row["close"])

        if eth_amount == 0 and is_buy_signal(row):
            entry_time = timestamp
            entry_price = current_price
            entry_cash = cash

            buy_fee = cash * FEE_RATE
            eth_amount = (cash - buy_fee) / current_price
            cash = 0.0

        elif eth_amount > 0:
            sell_reason = get_sell_reason(entry_price, current_price, float(row["RSI"]))

            if sell_reason:
                gross_cash = eth_amount * current_price
                sell_fee = gross_cash * FEE_RATE
                cash = gross_cash - sell_fee

                profit = cash - entry_cash
                profit_rate = (cash / entry_cash - 1) * 100

                trades.append(
                    {
                        "buy_time": entry_time,
                        "sell_time": timestamp,
                        "buy_price": round(entry_price, 2),
                        "sell_price": round(current_price, 2),
                        "quantity": eth_amount,
                        "buy_amount": round(entry_cash, 2),
                        "sell_amount": round(cash, 2),
                        "profit": round(profit, 2),
                        "profit_rate": round(profit_rate, 2),
                        "sell_reason": sell_reason,
                    }
                )

                eth_amount = 0.0
                entry_price = 0.0
                entry_time = None
                entry_cash = 0.0

        equity_curve.append(cash + eth_amount * current_price)

    final_price = float(df.iloc[-1]["close"])
    final_asset = cash + eth_amount * final_price
    total_return = (final_asset / INITIAL_CASH - 1) * 100
    mdd = calculate_mdd(equity_curve)

    return trades, final_asset, total_return, mdd


def save_trades(trades):
    columns = [
        "buy_time",
        "sell_time",
        "buy_price",
        "sell_price",
        "quantity",
        "buy_amount",
        "sell_amount",
        "profit",
        "profit_rate",
        "sell_reason",
    ]

    pd.DataFrame(trades, columns=columns).to_csv(
        RESULT_FILE,
        index=False,
        encoding="utf-8-sig",
    )


def print_summary(df, trades, final_asset, total_return, mdd):
    trade_count = len(trades)
    win_count = sum(1 for trade in trades if trade["profit"] > 0)
    win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0.0

    latest = df.iloc[-1]
    btc_trend = "UPTREND" if bool(latest["BTC_UPTREND"]) else "DOWNTREND"

    print("===== ETH Backtest Result =====")
    print(f"ETH Ticker: {ETH_TICKER}")
    print(f"BTC Trend: {btc_trend}")
    print(f"BTC EMA20: {latest['BTC_EMA20']:,.0f}")
    print(f"BTC EMA60: {latest['BTC_EMA60']:,.0f}")
    print(f"Initial Cash: {INITIAL_CASH:,.0f} KRW")
    print(f"Trades: {trade_count}")
    print(f"Win Rate: {win_rate:.2f}%")
    print(f"Final Asset: {final_asset:,.0f} KRW")
    print(f"Return: {total_return:.2f}%")
    print(f"MDD: {mdd:.2f}%")
    print(f"CSV Saved: {RESULT_FILE}")


def main():
    try:
        df = pyupbit.get_ohlcv(ETH_TICKER, interval=INTERVAL, count=COUNT)
        if df is None or df.empty:
            raise RuntimeError(f"Failed to fetch data: {ETH_TICKER}")
        df = df.copy()

        btc_df = pyupbit.get_ohlcv(BTC_TICKER, interval=INTERVAL, count=COUNT)
        if btc_df is None or btc_df.empty:
            raise RuntimeError(f"Failed to fetch data: {BTC_TICKER}")
        btc_df = btc_df.copy()

        df = add_eth_indicators(df)
        btc_df = add_btc_indicators(btc_df)
        df = merge_eth_btc(df, btc_df)

        df = df.dropna(
            subset=[
                "EMA5",
                "EMA20",
                "EMA60",
                "RSI",
                "volume_ma20",
                "BTC_EMA20",
                "BTC_EMA60",
                "BTC_UPTREND",
            ]
        )

        if df.empty:
            raise RuntimeError("Not enough data after indicator calculation.")

        trades, final_asset, total_return, mdd = run_backtest(df)
        save_trades(trades)
        print_summary(df, trades, final_asset, total_return, mdd)

        return 0
    except Exception as error:
        print(f"Backtest failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

