import telebot

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    bot.reply_to(message, "Eyvallah usta, safkan Telegram botu aktif! Fişek gibi çalışıyor, yaz bakalım!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()
    
    # Buraya istediğin anahtar kelimelere karşılık gelecek cevapları ekleyebilirsin usta
    if "selam" in text or "merhaba" in text:
        bot.reply_to(message, "Aleykümselam usta!")
    elif "nasılsın" in text:
        bot.reply_to(message, "Taş gibiyim usta, sen nasılsın?")
    elif "saat" in text:
        bot.reply_to(message, "Vakit tam gaz ilerliyor usta!")
    else:
        # Yapay zeka yerine buradaki standart lafı çakar
        bot.reply_to(message, f"Dedini aldım usta: {message.text}")

print("Safkan bot fişek gibi başlatılıyor...")
bot.infinity_polling()
