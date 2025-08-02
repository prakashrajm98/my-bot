# Real-time EMA Crossover Paper Trading Bot with Telegram Alerts (Binance)

import pandas as pd
import requests
import time
import datetime
from binance.client import Client
from binance.enums import *

# === Configuration ===
TELEGRAM_TOKEN = "7992868622:AAH39V5wNjGWQeJY2zKu2ZGdFgQIHTBYIBs"
TELEGRAM_CHAT_ID = "5221151930"
VIRTUAL_BALANCE = 10.0  # Fake starting balance in USD
TRADE_AMOUNT = 1.0      # Virtual trade size in USD
SYMBOL = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_1MINUTE

# === Initialize Binance client (No API Key needed for market data) ===
client = Client(api_key='', api_secret='')

# === Telegram Alert Function ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# === EMA Calculation ===
def calculate_ema(df, span):
    return df['close'].ewm(span=span, adjust=False).mean()

# === Strategy State ===
position = None  # None, "LONG"
balance = VIRTUAL_BALANCE
entry_price = 0.0

# === Fetch historical + live candles ===
def fetch_candles(symbol=SYMBOL):
    klines = client.get_klines(symbol=symbol, interval=INTERVAL, limit=100)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = df['close'].astype(float)
    return df[['timestamp', 'close']]

# === Main Loop ===
print("📡 Starting EMA Crossover Bot (Paper Trading Mode)")
send_telegram_message("📡 EMA Crossover Bot Started (Paper Trading Mode)")

while True:
    try:
        df = fetch_candles()
        df['ema5'] = calculate_ema(df, 5)
        df['ema20'] = calculate_ema(df, 20)

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # Crossover conditions
        if previous['ema5'] < previous['ema20'] and latest['ema5'] > latest['ema20']:
            if position is None and balance >= TRADE_AMOUNT:
                position = "LONG"
                entry_price = latest['close']
                balance -= TRADE_AMOUNT
                send_telegram_message(f"🔼 BUY Signal (Paper Trade) @ {entry_price:.2f}\nBalance: ${balance:.2f}")

        elif previous['ema5'] > previous['ema20'] and latest['ema5'] < latest['ema20']:
            if position == "LONG":
                exit_price = latest['close']
                profit = (exit_price - entry_price) / entry_price * TRADE_AMOUNT
                balance += TRADE_AMOUNT + profit
                send_telegram_message(f"🔽 SELL Signal (Paper Trade) @ {exit_price:.2f}\nProfit: ${profit:.2f}\nBalance: ${balance:.2f}")
                position = None

        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Close: {latest['close']:.2f} | EMA5: {latest['ema5']:.2f} | EMA20: {latest['ema20']:.2f} | Balance: ${balance:.2f}")

    except Exception as e:
        print("❌ Error:", e)
        send_telegram_message(f"❌ Error: {e}")

    time.sleep(60)

