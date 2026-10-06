import os
import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = '8616505304:AAEbkkGWnkTyW0O_Yhfv5_s2rV6H6rPlevQ'
GEMINI_API_KEY = 'AQ.Ab8RN6IXg6Nl2q_q_W6GysgWYywEN5yFzdikXqLKZTr6AIgzGw'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, bütün gereksiz reklamlar temizlendi. Yaz bakalım ne soracaksan!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Hata çıktı usta: {str(e)}")

print("Bot reklamsız modda başlatılıyor...")
bot.infinity_polling()
