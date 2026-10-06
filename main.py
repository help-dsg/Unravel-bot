import telebot

TOKEN = '8616505304:AAEhxeB3OUXtHdNcdLmoEXT-W83l9lNf0Rg'
bot = telebot.TeleBot(TOKEN)

# Hem /start hem de /tgunravel_bot komutlarına tertemiz yanıt versin
@bot.message_handler(commands=['start', 'tgunravel_bot'])
def handle_commands(message):
    bot.reply_to(message, "Efendim usta, tgunravel_bot aktif ve emrinde!")

print("Bot yeni token ile çalışıyor...")
bot.infinity_polling()
