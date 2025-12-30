import telebot
from telebot import types
import numpy as np
import pandas as pd
TOKEN = "8437078936:AAFJQrotXczZ4Er_e6xnbizNSFPMRJ8BTcc"
bot = telebot.TeleBot(TOKEN)

user_data = {}

# ---------- ИНДИКАТОРЫ ----------

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_ema(prices, period):
    return prices.ewm(span=period, adjust=False).mean().iloc[-1]

# ⚠️ временные свечи (заглушка)
def get_fake_prices():
    prices = np.cumsum(np.random.randn(120)) + 100
    return pd.Series(prices)

def generate_signal():
    prices = get_fake_prices()
    rsi = calculate_rsi(prices)
    ema_fast = calculate_ema(prices, 9)
    ema_slow = calculate_ema(prices, 21)

    # сильные условия
    if rsi < 30 and ema_fast > ema_slow:
        return "📈 BUY", rsi

    if rsi > 70 and ema_fast < ema_slow:
        return "📉 SELL", rsi

    # 🔥 принудительно по тренду (без WAIT)
    if ema_fast > ema_slow:
        return "📈 BUY", rsi
    else:
        return "📉 SELL", rsi

# ---------- START ----------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Привет 👋\n"
        "Я торговый бот (RSI + EMA + тренд)\n\n"
        "Нажми /signal чтобы получить сигнал"
    )

# ---------- SIGNAL ----------

@bot.message_handler(commands=['signal'])
def signal(message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
    for p in pairs:
        keyboard.add(p)

    bot.send_message(
        message.chat.id,
        "📊 Выбери валютную пару:",
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, get_pair)

def get_pair(message):
    user_data[message.chat.id] = {"pair": message.text}

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    times = ["30s", "1m", "3m", "5m"]
    for t in times:
        keyboard.add(t)

    bot.send_message(
        message.chat.id,
        "⏱ Выбери время сделки:",
        reply_markup=keyboard
    )
    bot.register_next_step_handler(message, get_time)

def get_time(message):
    chat_id = message.chat.id
    user_data[chat_id]["time"] = message.text

    signal, rsi = generate_signal()
    pair = user_data[chat_id]["pair"]
    time = user_data[chat_id]["time"]

    bot.send_message(
        chat_id,
        f"📊 Пара: {pair}\n"
        f"⏱ Время: {time}\n"
        f"📉 RSI: {round(rsi, 2)}\n\n"
        f"🔥 СИГНАЛ: {signal}\n\n"
        f"⚠️ Аналитический сигнал, не гарантия",
        reply_markup=types.ReplyKeyboardRemove()
    )

bot.polling(timeout=60)