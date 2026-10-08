import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'
BOT_OWNER_ID = 8647573045  # Senin Telegram ID'n

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Genişletilmiş küfür, hakaret ve hassas değer filtresi (Büyük/küçük harf fark etmez)
YASAKLI_KELIMER = [
    # Genel Küfürler & Argo
    "amk", "aq", "aq.", "amina", "amına", "amk.", "orospu", "o.ç", "oc", "piç", "pic", 
    "sik", "sikerim", "siktir", "sikik", "anan", "anani", "ananı", "amina koyim", "amq",
    "yarrak", "yarak", "göt", "got", "amcık", "amcik", "am", "kahpe", "geber", "yavşak",
    "ibne", "orospucocugu", "orosbu", "amını", "amini", "sikiyim", "sikeyim", "orosbu çocuğu",
    "orosbu cocugu", "ananı sikiyim", "anani sikeyim", "pezevenk", "am hoşa", "amhosafi",
    
    # Dinî Değerler & Kutsallara Yönelik Hakaretler
    "allahını", "allani", "allahini", "peygamberini", "peygamber", "dinini", "dini", 
    "kitabını", "kitabini", "kuran", "kuranı", "ayet", "haşa", "haşaallah", "c.c", "hz.",
    "din siki", "allah yok", "peygamber yalandır", "mabet", "secde", "iman", "imanını",
    
    # Ata & Milli Değerler / Kültürel Değerler
    "atatürk", "atam", "bayrak", "vatan", "şehit", "gazi", "milli", "istiklal", 
    "tc", "türkiye", "türk" # (Bu kelimeler tek başına yasak değil ama hakaret ekleriyle birleştiğinde yakalanması için kökleri ekleyebiliriz ya da doğrudan hakaret kalıplarını koyabiliriz)
]

# Spam koruması için sözlük
user_last_message_time = {}

def get_menu_markup():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("📝 Alım Şartları", callback_data="btn_alim"),
        InlineKeyboardButton("⚠️ Kurallar", callback_data="btn_kurallar"),
        InlineKeyboardButton("📞 İletişim", callback_data="btn_iletisim"),
        InlineKeyboardButton("🌐 Sosyal Medya", callback_data="btn_sosyal")
    )
    return markup

@bot.message_handler(commands=['start', 'tgunravel_bot'])
def send_welcome(message):
    yardim_metni = (
        "Unravel destek botuna hoş geldin! \n\n"
        "Aşağıdaki menüden dilediğin bilgiye ulaşabilirsin:\n\n"
        "(Önce kuralları okuyun)"
    )
    bot.reply_to(message, yardim_metni, reply_markup=get_menu_markup(), disable_notification=True)

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        name = user.first_name or "üye"
        hosgeldin_mesaji = (
            f"Hoş geldin {name}! 🎉 Unravel kulübüne katıldın.\n"
            "Ortama uyum sağlamak ve detayları incelemek için aşağıdaki butonları kullanabilirsin.\n\n"
            "(Önce kuralları okuyun)"
        )
        bot.send_message(message.chat.id, hosgeldin_mesaji, reply_markup=get_menu_markup(), disable_notification=True)

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
            "📞 İletişim:\nInstagram: theprestige897 & hlx993", 
            show_alert=True
        )
    elif call.data == "btn_sosyal":
        bot.answer_callback_query(
            call.id, 
            "🌐 Sosyal Medya Hesaplarımız:\n\nTikTok: bayrobrawlstars & hlx993\nInstagram: theprestige897 & hlx993\nYouTube: helpbs", 
            show_alert=True
        )

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.chat.type == 'private':
        text = message.text.lower() if message.text else ""
        if "selam" in text or "merhaba" in text:
            bot.reply_to(message, "Aleykümselam!", disable_notification=True)
        elif "nasılsın" in text:
            bot.reply_to(message, "Taş gibiyim, sen nasılsın?", disable_notification=True)
        return

    # Yöneticileri muaf tut
    try:
        member_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
        if member_status in ['creator', 'administrator']:
            return
    except:
        pass

    # Gelen metni tamamen küçük harfe çeviriyoruz (Büyük/küçük harf takıntısını bitirir)
    text = message.text.lower() if message.text else ""
    user_id = message.from_user.id
    current_time = time.time()

    # 1. KÜFÜR FİLTRESİ VE ÖZEL RAPORLAMA
    for kelime in YASAKLI_KELIMER:
        if kelime in text:
            try:
                # Gruptaki mesajı anında siler
                bot.delete_message(message.chat.id, message.message_id)
                
                # Sana özelden rapor iletir
                user_name = message.from_user.first_name or "İsimsiz"
                username = f"@{message.from_user.username}" if message.from_user.username else "Kullanıcı adı yok"
                grup_adi = message.chat.title or "Grup"
                
                rapor_metni = (
                    f"🚨 **Hassas İçerik / Küfür Tespiti!**\n\n"
                    f"📌 **Grup:** {grup_adi}\n"
                    f"👤 **Kişi:** {user_name} ({username})\n"
                    f"🆔 **ID:** `{user_id}`\n"
                    f"💬 **Yazdığı Mesaj:** {message.text}"
                )
                bot.send_message(BOT_OWNER_ID, rapor_metni, parse_mode="Markdown")
                
            except Exception as e:
                print(f"Küfür yakalama hatası: {e}")
            return

    # 2. SPAM (FLOOD) KONTROLÜ
    if user_id in user_last_message_time:
        if current_time - user_last_message_time[user_id] < 1.5:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                return
            except:
                pass
                
    user_last_message_time[user_id] = current_time

print("Kulüp botu gelişmiş filtre sistemiyle aktif!")
bot.infinity_polling()
