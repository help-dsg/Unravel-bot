import telebot

TOKEN = '8616505304:AAFe9LkM9mviTmcXBMXTZ1HF_EYIYrqXqeQ'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Selam, Unravel bot aktif!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

bot.infinity_polling()
