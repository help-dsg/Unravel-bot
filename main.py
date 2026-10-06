import os
import telebot
from google import genai
from google.genai import types

TELEGRAM_TOKEN = '8616505304:AAEbkkGWnkTyW0O_Yhfv5_s2rV6H6rPlevQ'
GEMINI_API_KEY = 'AQ.Ab8RN6LNsUqZNAxZQE4Yl6shPbQW710YJPW3Y0ucjpavdPTFIw'

# Ortam değişkenine anahtarı atıyoruz ki SDK otomatik yakalasın
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client()

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, OAuth / AQ anahtar entegrasyonu tamamlandı. Yaz bakalım!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text,
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Hata çıktı usta: {str(e)}")

print("Bot OAuth / AQ anahtar desteğiyle başlatılıyor...")
bot.infinity_polling()
