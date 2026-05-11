import pandas as pd

def calculate_rsi(df, period=14):
    delta = df['close'].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return rsi

def check_signal(df):

    df['EMA5'] = df['close'].ewm(span=5).mean()
    df['EMA20'] = df['close'].ewm(span=20).mean()

    df['RSI'] = calculate_rsi(df)

    latest = df.iloc[-1]

    print(f"현재 RSI: {latest['RSI']:.2f}")
    print(f"EMA5: {latest['EMA5']:.0f}")
    print(f"EMA20: {latest['EMA20']:.0f}")

    if latest['EMA5'] > latest['EMA20'] and latest['RSI'] > 55:
        return "BUY"

    elif latest['RSI'] > 72:
        return "SELL"

    else:
        return "HOLD"
    