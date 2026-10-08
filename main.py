import os
import telebot
from openai import OpenAI

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'
GROQ_API_KEY = 'Gsk_JSEOB4fk8kBG2v5lJNLrWGdyb3FYDxAMgz0qDFa9DQ7ZzAg7Y22G'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Groq'un kendi API endpoint'ini ve aldığımız anahtarı client'a tanıtıyoruz
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, Groq (Llama 3) altyapısı aktif! Fişek gibi çalışıyor, yaz bakalım!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": message.text}
            ]
        )
        reply = response.choices[0].message.content
        bot.reply_to(message, reply)
    except Exception as e:
        bot.reply_to(message, f"Hata çıktı usta: {str(e)}")

print("Bot Groq altyapısıyla fişek gibi başlatılıyor...")
bot.infinity_polling()
