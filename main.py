import telebot
from google import genai

TELEGRAM_TOKEN = '8616505304:AAEbkkGWnkTyW0O_Yhfv5_s2rV6H6rPlevQ'
GEMINI_API_KEY = 'AQ.Ab8RN6L3TXw11l7P73-2FIIAqSgVFI9-hvS5TVmwVnRQ2YfK4A'

bot = telebot.TeleBot(TELEGRAM_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, paketler yüklendi, sistem tam gaz ayakta!")

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

print("Bot güncel SDK ile çalışmaya başladı...")
bot.infinity_polling()
