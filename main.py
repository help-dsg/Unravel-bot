import telebot

# Kendi bot token'ın
TOKEN = '8616505304:AAFe9LkM9mviTmcXBMXTZ1HF_EYIYrqXqeQ'
bot = telebot.TeleBot(TOKEN)

# Sadece /tgunravel_bot komutuna yanıt veren temiz handler
@bot.message_handler(commands=['tgunravel_bot'])
def handle_tgunravel(message):
    bot.reply_to(message, "Efendim usta, tgunravel_bot aktif ve emrinde!")

# Botun çalışmasını sağlayan döngü
print("Bot çalışıyor...")
bot.infinity_polling()
