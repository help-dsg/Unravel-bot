import os
import telebot
from google import genai

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'
GEMINI_API_KEY = 'AQ.Ab8RN6LNsUqZNAxZQE4Yl6shPbQW710YJPW3Y0ucjpavdPTFIw'

# AQ anahtarının kimlik doğrulamasını sağlaması için ortam değişkenine atıyoruz
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client()

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Nasıl Yardımcı olabilirim?")

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

print("Bot en son AQ anahtarıyla başlatılıyor...")
bot.infinity_polling()
