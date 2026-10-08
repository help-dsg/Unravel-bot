import os
import telebot
from openai import OpenAI

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'
GROQ_API_KEY = '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'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, sistem taş gibi ayakta! Yaz bakalım!")

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
