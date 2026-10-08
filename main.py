import telebot

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    yardim_metni = (
        "Unravel destek botuna hoş geldin! \n\n"
        "İşte kullanabileceğin komutlar:\n"
        "👉 /alım — Kulübe alım şartları\n"
        "👉 /kurallar — Kulüp kuralları\n"
        "👉 /iletisim — İletişim ve yetkili bilgileri\n\n"
        "(Önce kuralları okuyun)"
    )
    bot.reply_to(message, yardim_metni)

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        name = user.first_name or "üye"
        hosgeldin_mesaji = (
            f"Hoş geldin {name}! 🎉 Unravel kulübüne katıldın.\n"
            "Ortama uyum sağlamak ve kuralları öğrenmek için lütfen /kurallar komutuna göz at.\n\n"
            "(Önce kuralları okuyun)"
        )
        bot.reply_to(message, hosgeldin_mesaji)

@bot.message_handler(commands=['alım'])
def handle_alim(message):
    bot.reply_to(
        message, 
        "📝 **Kulübe Alım Şartları:**\n\n"
        "🔸 Ana Kulüp: `#82QYGLVCY` (135k üstü)\n"
        "🔹 Yan Kulüp: `#2UCCV8VGG` (90k üstü)",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=['kurallar'])
def handle_kurallar(message):
    bot.reply_to(
        message, 
        "⚠️ **Kulüp Kuralları:**\n\n"
        "1. Küfür ve argo yasak.\n"
        "2. Tartışma kesinlikle yasak.\n"
        "3. Kalıcılık şart.\n"
        "4. Herkesin eğlendiği bir ortam istiyoruz."
    )

@bot.message_handler(commands=['iletisim'])
def handle_iletisim(message):
    bot.reply_to(
        message, 
        "📞 **İletişim Bilgileri:**\n\n"
        "Instagram: `theprestige897` & `hlx993`",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()
    
    if "selam" in text or "merhaba" in text:
        bot.reply_to(message, "Aleykümselam!")
    elif "nasılsın" in text:
        bot.reply_to(message, "Taş gibiyim, sen nasılsın?")
    else:
        bot.reply_to(message, "Komutları görmek için /start yazabilirsin, önce kuralları okuyun!")

print("Kulüp botu fişek gibi başlatılıyor...")
bot.infinity_polling()
