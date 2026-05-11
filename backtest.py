
import pyupbit
import pandas as pd
import csv
from strategy import calculate_rsi  # RSI 함수 import


# 초기 자본금 설정
initial_balance = 50000  # 시작 자본(원)
balance = initial_balance  # 현재 자산
position = 0  # 0: 미보유, 1: 보유
buy_price = 0  # 매수 가격
trade_count = 0  # 총 거래수
win_count = 0  # 수익 거래수
max_balance = initial_balance  # MDD 계산용 최고 자산
mdd = 0  # 최대 낙폭(MDD)

# 업비트 거래 수수료 (0.05%)
FEE_RATE = 0.0005

# 거래 내역 저장 리스트
trade_history = []

df['EMA5'] = df['close'].ewm(span=5).mean()
df['EMA20'] = df['close'].ewm(span=20).mean()
df['RSI'] = calculate_rsi(df)
df['EMA20'] = df['close'].ewm(span=20).mean()
df['RSI'] = calculate_rsi(df)
df['EMA5'] = df['close'].ewm(span=5).mean()
df['EMA20'] = df['close'].ewm(span=20).mean()
df['RSI'] = calculate_rsi(df)


# pyupbit로 5분봉 데이터 2000개 조회 및 지표 계산
ticker = "KRW-ETH"
df = pyupbit.get_ohlcv(ticker, interval="minute5", count=2000)

# 데이터가 정상적으로 받아졌는지 확인
if df is None or len(df) < 80:
    raise Exception("데이터를 불러오지 못했습니다. 데이터 개수 부족.")

# EMA, RSI 계산 (df 생성 후)
df['EMA5'] = df['close'].ewm(span=5).mean()
df['EMA20'] = df['close'].ewm(span=20).mean()
df['EMA60'] = df['close'].ewm(span=60).mean()
df['RSI'] = calculate_rsi(df)


# 백테스트 루프



# 매수 RSI 기준값, 손절/익절 기준 상수로 선언
BUY_RSI_THRESHOLD = 55
STOP_LOSS = -0.03  # -3%
TAKE_PROFIT = 0.06  # +6%

# 백테스트 루프
for i in range(20, len(df)):
    row = df.iloc[i]
    date = row.name.strftime('%Y-%m-%d %H:%M')
    price = row['close']
    ema5 = row['EMA5']
    ema20 = row['EMA20']
    ema60 = row['EMA60']
    rsi = row['RSI']
    volume = row['volume']

    # 거래량 필터: 최근 20개 봉의 평균 거래량 계산
    avg_volume_20 = df['volume'].iloc[i-20:i].mean()

    # 매수 조건: EMA5 > EMA20 > EMA60, RSI > 55, 거래량 > 20봉 평균
    if position == 0 and ema5 > ema20 and ema20 > ema60 and rsi > BUY_RSI_THRESHOLD and volume > avg_volume_20:
        position = 1
        buy_price = price
        trade_count += 1
        # 매수 시 수수료 차감 (전액 진입)
        fee = balance * FEE_RATE
        balance -= fee
        trade_history.append([date, 'BUY', price, balance, f'수수료차감:{fee:.2f}/거래량:{volume:.2f}/20봉평균:{avg_volume_20:.2f}'])
        continue


    # 매도 조건: 손절 -3%, 익절 +6%, RSI > 72
    if position == 1:
        profit_rate = (price - buy_price) / buy_price
        sell_reason = ''
        if profit_rate <= STOP_LOSS:
            sell_reason = '손절'
        elif profit_rate >= TAKE_PROFIT:
            sell_reason = '익절'
        elif rsi > 72:
            sell_reason = 'RSI'
        if sell_reason:
            # 매도 시 수수료 차감
            fee = balance * FEE_RATE
            profit = balance * profit_rate
            balance += profit
            balance -= fee
            if profit > 0:
                win_count += 1
            trade_history.append([date, 'SELL', price, balance, f'{sell_reason}/수수료차감:{fee:.2f}/거래량:{volume:.2f}/20봉평균:{avg_volume_20:.2f}'])
            buy_price = 0
            position = 0

    # MDD(최대 낙폭) 계산
    if balance > max_balance:
        max_balance = balance
    drawdown = (max_balance - balance) / max_balance
    if drawdown > mdd:
        mdd = drawdown

# 최종 수익률, 승률, MDD 계산
final_return = (balance - initial_balance) / initial_balance * 100
win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0

import pyupbit
import pandas as pd
import csv
from strategy import calculate_rsi

# =============================
# 설정값
# =============================
INITIAL_BALANCE = 50000  # 초기 자본(원)
FEE_RATE = 0.0005        # 업비트 거래 수수료 0.05%
BUY_RSI = 55             # 매수 RSI 기준
STOP_LOSS = -0.03        # 손절 -3%
TAKE_PROFIT = 0.06       # 익절 +6%

# =============================
# 데이터 조회 및 지표 계산
# =============================
ticker = "KRW-ETH"
df = pyupbit.get_ohlcv(ticker, interval="minute5", count=2000)

if df is None or len(df) < 80:
    raise Exception("데이터를 불러오지 못했습니다.")

# EMA, RSI 계산 (df 생성 후)
df['EMA5'] = df['close'].ewm(span=5).mean()
df['EMA20'] = df['close'].ewm(span=20).mean()
df['EMA60'] = df['close'].ewm(span=60).mean()
df['RSI'] = calculate_rsi(df)

# =============================
# 백테스트 변수 초기화
# =============================
balance = INITIAL_BALANCE  # 현재 자산
position = 0               # 0: 미보유, 1: 보유
buy_price = 0              # 매수 가격
trade_count = 0            # 총 거래수
win_count = 0              # 수익 거래수
max_balance = INITIAL_BALANCE  # MDD 계산용 최고 자산
mdd = 0                    # 최대 낙폭
trade_history = []         # 거래 내역

# =============================
# 백테스트 루프
# =============================
for i in range(60, len(df)):
    row = df.iloc[i]
    date = row.name.strftime('%Y-%m-%d %H:%M')
    price = row['close']
    ema5 = row['EMA5']
    ema20 = row['EMA20']
    ema60 = row['EMA60']
    rsi = row['RSI']
    volume = row['volume']
    avg_volume_20 = df['volume'].iloc[i-20:i].mean()

    # =============================
    # 매수 조건
    # 1. EMA5 > EMA20
    # 2. EMA20 > EMA60
    # 3. RSI > 55
    # 4. 현재 거래량 > 최근 20봉 평균 거래량
    # =============================
    if position == 0 and ema5 > ema20 and ema20 > ema60 and rsi > BUY_RSI and volume > avg_volume_20:
        position = 1
        buy_price = price
        trade_count += 1
        # 매수 시 수수료 차감
        fee = balance * FEE_RATE
        balance -= fee
        trade_history.append([date, 'BUY', price, balance, f'수수료차감:{fee:.2f}/거래량:{volume:.2f}/20봉평균:{avg_volume_20:.2f}'])
        continue

    # =============================
    # 매도 조건
    # 1. 손절 -3%
    # 2. 익절 +6%
    # 3. RSI > 72
    # =============================
    if position == 1:
        profit_rate = (price - buy_price) / buy_price
        sell_reason = ''
        if profit_rate <= STOP_LOSS:
            sell_reason = '손절'
        elif profit_rate >= TAKE_PROFIT:
            sell_reason = '익절'
        elif rsi > 72:
            sell_reason = 'RSI'
        if sell_reason:
            # 매도 시 수수료 차감
            fee = balance * FEE_RATE
            profit = balance * profit_rate
            balance += profit
            balance -= fee
            if profit > 0:
                win_count += 1
            trade_history.append([date, 'SELL', price, balance, f'{sell_reason}/수수료차감:{fee:.2f}/거래량:{volume:.2f}/20봉평균:{avg_volume_20:.2f}'])
            buy_price = 0
            position = 0

    # =============================
    # MDD(최대 낙폭) 계산
    # =============================
    if balance > max_balance:
        max_balance = balance
    drawdown = (max_balance - balance) / max_balance
    if drawdown > mdd:
        mdd = drawdown

# =============================
# 결과 출력
# =============================
final_return = (balance - INITIAL_BALANCE) / INITIAL_BALANCE * 100
win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
mdd_percent = mdd * 100

print(f"[BUY: EMA5>EMA20>EMA60, RSI>{BUY_RSI}, 거래량>20봉평균] [SELL: 손절 {int(STOP_LOSS*100)}%, 익절 {int(TAKE_PROFIT*100)}%, RSI>72]")
print(f"총 거래수: {trade_count}")
print(f"승률: {win_rate:.2f}%")
print(f"최종 자산: {balance:.0f}원")
print(f"수익률: {final_return:.2f}%")
print(f"최대 손실(MDD): {mdd_percent:.2f}%")

# =============================
# 거래 내역 CSV 저장
# =============================
with open('backtest_result.csv', 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerow(['date', 'type', 'price', 'balance', 'reason'])
    writer.writerows(trade_history)

# =============================
# 초보자를 위한 주석
# =============================
# - 이 코드는 실제 주문, API Key, 잔고조회 기능을 포함하지 않습니다.
# - EMA5, EMA20, EMA60, RSI, 거래량 필터로 매수 신호를 판단합니다.
# - 업비트 거래 수수료(0.05%)가 매수/매도 시 반영됩니다.
# - 한 번 매수하면 전액 진입, 최대 1포지션만 보유합니다.
# - 거래 내역은 backtest_result.csv로 저장됩니다.
# - 최대 손실(MDD)도 함께 출력됩니다.
