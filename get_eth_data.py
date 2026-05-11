import pyupbit
import time
import csv
import os
from datetime import datetime
from strategy import check_signal
from notifier import send_discord_message

ticker = "KRW-ETH"
LOG_FILE = "trade_signal_log.csv"
POSITION_FILE = "position.txt"

# 로그 파일이 없으면 헤더 생성
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, mode="w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["time", "ticker", "price", "rsi", "ema5", "ema20", "raw_signal", "final_signal", "position"])


# 현재 포지션 상태 읽기
def read_position():
    if not os.path.exists(POSITION_FILE):
        return "NONE"

    with open(POSITION_FILE, mode="r", encoding="utf-8") as file:
        position = file.read().strip()

    if position not in ["NONE", "BUY"]:
        return "NONE"

    return position


# 현재 포지션 상태 저장
def save_position(position):
    with open(POSITION_FILE, mode="w", encoding="utf-8") as file:
        file.write(position)


while True:
    try:
        df = pyupbit.get_ohlcv(ticker, interval="minute5", count=100)

        raw_signal = check_signal(df)
        latest = df.iloc[-1]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        position = read_position()
        final_signal = "HOLD"

        # 중복 BUY 방지 로직
        if raw_signal == "BUY" and position == "NONE":
            final_signal = "BUY"
            save_position("BUY")

        elif raw_signal == "SELL" and position == "BUY":
            final_signal = "SELL"
            save_position("NONE")

        else:
            final_signal = "HOLD"

        position = read_position()

        print(f"\n현재 시간: {now}")
        print(f"원본 신호: {raw_signal}")
        print(f"최종 신호: {final_signal}")
        print(f"현재 포지션: {position}")

        # CSV 로그 저장
        with open(LOG_FILE, mode="a", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow([
                now,
                ticker,
                round(latest["close"], 0),
                round(latest["RSI"], 2),
                round(latest["EMA5"], 0),
                round(latest["EMA20"], 0),
                raw_signal,
                final_signal,
                position
            ])

        print("로그 저장 완료")

        message = f"""
📈 ETH SIGNAL

현재 시간: {now}

원본 신호: {raw_signal}
최종 신호: {final_signal}
현재 포지션: {position}

현재가: {latest['close']:.0f}
RSI: {latest['RSI']:.2f}
EMA5: {latest['EMA5']:.0f}
EMA20: {latest['EMA20']:.0f}
"""

        # 최종 BUY 또는 SELL일 때만 디스코드 전송
        if final_signal in ["BUY", "SELL"]:
            send_discord_message(message)
            print("디스코드 전송 완료")
        else:
            print("HOLD 상태라 디스코드 전송 생략")

        print("5분 대기중...\n")
        time.sleep(300)

    except Exception as e:
        print(f"에러 발생: {e}")
        time.sleep(60)