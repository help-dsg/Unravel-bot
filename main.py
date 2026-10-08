import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Butonları oluşturan fonksiyon
def get_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton("📝 Alım Şartları", callback_data="btn_alim"),
        InlineKeyboardButton("⚠️ Kurallar", callback_data="btn_kurallar"),
        InlineKeyboardButton("📞 İletişim", callback_data="btn_iletisim")
    )
    return markup

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    yardim_metni = (
        "Unravel destek botuna hoş geldin! Fişek gibi çalışıyor.\n\n"
        "Aşağıdaki menüden dilediğin bilgiye ulaşabilirsin:\n\n"
        "(Önce kuralları okuyun)"
    )
    bot.reply_to(message, yardim_metni, reply_markup=get_menu_markup())

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        name = user.first_name or "üye"
        hosgeldin_mesaji = (
            f"Hoş geldin {name}! 🎉 Unravel kulübüne katıldın.\n"
            "Ortama uyum sağlamak ve detayları incelemek için aşağıdaki butonları kullanabilirsin.\n\n"
            "(Önce kuralları okuyun)"
        )
        bot.send_message(message.chat.id, hosgeldin_mesaji, reply_markup=get_menu_markup())

# Butonlara tıklandığında çalışacak kısım (Sadece tıkayana gizli bildirim/pop-up şeklinde gösterir)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "btn_alim":
        bot.answer_callback_query(
            call.id, 
            "📝 Ana Kulüp: 82QYGLVCY (135k üstü)\n🔹 Yan Kulüp: 2UCCV8VGG (90k üstü)", 
            show_alert=True
        )
    elif call.data == "btn_kurallar":
        bot.answer_callback_query(
            call.id, 
            "⚠️ Kurallar:\n1. Küfür ve argo yasak.\n2. Tartışma kesinlikle yasak.\n3. Kalıcılık şart.\n4. Herkesin eğlendiği bir ortam.", 
            show_alert=True
        )
    elif call.data == "btn_iletisim":
        bot.answer_callback_query(
            call.id, 
            "📞 Instagram:\ntheprestige897 & hlx993", 
            show_alert=True
        )

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.lower()
    
    if "selam" in text or "merhaba" in text:
        bot.reply_to(message, "Aleykümselam!")
    elif "nasılsın" in text:
        bot.reply_to(message, "Taş gibiyim, sen nasılsın?")

print("Kulüp botu fişek gibi başlatılıyor...")
bot.infinity_polling()
