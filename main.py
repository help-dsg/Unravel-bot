import telebot
import google.generativeai as genai

TELEGRAM_TOKEN = '8616505304:AAEbkkGWnkTyW0O_Yhfv5_s2rV6H6rPlevQ'
GEMINI_API_KEY = 'AQ.Ab8RN6L3TXw11l7P73-2FIIAqSgVFI9-hvS5TVmwVnRQ2YfK4A'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# Doğrudan model tanımı
model = genai.GenerativeModel('gemini-1.5-flash')

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, eski ve stabil SDK'ya döndük, sistem tam gaz emrinde!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = model.generate_content(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Hata çıktı usta: {str(e)}")

print("Bot kararlı sürümle ayağa kalkıyor...")
bot.infinity_polling()
