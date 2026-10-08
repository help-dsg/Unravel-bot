import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import time

TELEGRAM_TOKEN = '8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s'
BOT_OWNER_ID = 8647573045  # Senin Telegram ID'n

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# Yasaklı küfür/argo kelimeler listesi
YASAKLI_KELIMER = [
    "amk", "aq", "aq.", "amina", "amına", "amk.", "orospu", "o.ç", "oc", "piç", "pic", 
    "sik", "sikerim", "siktir", "sikik", "anan", "anani", "ananı", "amina koyim", "amq",
    "yarrak", "yarak", "göt", "got", "amcık", "amcik", "am", "kahpe", "geber", "yavşak",
    "ibne", "orospucocugu", "orosbu", "amını", "amini", "sikiyim", "sikeyim", "orosbu çocuğu",
    "orosbu cocugu", "ananı sikiyim", "anani sikeyim", "pezevenk", "am hoşa", "amhosafi",
    "allahını", "allani", "allahini", "peygamberini", "peygamber", "dinini", "dini", 
    "kitabını", "kitabini", "kuran", "kuranı", "ayet", "haşa", "haşaallah", "c.c", "hz."
]

# Spam koruması ve geçici veri saklama sözlükleri
user_last_message_time = {}
user_states = {}       # Başvuru adımlarını takip etmek için
user_profiles = {}     # Kullanıcı profillerini saklamak için (Yaş, İsim, IG)
user_applications = {} # Başvuru verilerini geçici tutmak için

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
    if message.chat.type == 'private':
        yardim_metni = (
            "Unravel destek botuna hoş geldin! 🚀\n\n"
            "Özel sohbet üzerinden şu komutları kullanabilirsin:\n"
            "📝 /basvuru - Kulüp için başvuru yap\n"
            "👤 /profilim - Profilini oluştur veya görüntüle\n\n"
            "Aşağıdaki menüden de kulüp bilgilerine göz atabilirsin:"
        )
        bot.reply_to(message, yardim_metni, reply_markup=get_menu_markup(), disable_notification=True)
    else:
        yardim_metni = (
            "Unravel destek botuna hoş geldin!\n"
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
        bot.answer_callback_query(call.id, "📝 Ana Kulüp: 82QYGLVCY (135k üstü)\n🔹 Yan Kulüp: 2UCCV8VGG (90k üstü)", show_alert=True)
    elif call.data == "btn_kurallar":
        bot.answer_callback_query(call.id, "⚠️ Kurallar:\n1. Küfür ve argo yasak.\n2. Tartışma kesinlikle yasak.\n3. Kalıcılık şart.", show_alert=True)
    elif call.data == "btn_iletisim":
        bot.answer_callback_query(call.id, "📞 İletişim:\nInstagram: theprestige897 & hlx993", show_alert=True)
    elif call.data == "btn_sosyal":
        bot.answer_callback_query(call.id, "🌐 Sosyal Medya:\nTikTok: bayrobrawlstars\nInstagram: theprestige897\nYouTube: helpbs", show_alert=True)

# ================= KÜLÜP BAŞVURU SİSTEMİ (ÖZELDEN) =================
@bot.message_handler(commands=['basvuru'])
def start_application(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "⚠️ Başvuru komutunu sadece botun **özel sohbetinde (DM'de)** kullanabilirsin!", disable_notification=True)
        return
    
    user_states[message.from_user.id] = "waiting_for_ingame_name"
    user_applications[message.from_user.id] = {}
    bot.send_message(message.chat.id, "📝 **Kulüp Başvuru Sistemi**\n\nLütfen oyun içi ismini (nickini) yaz:", parse_mode="Markdown")

# ================= PROFİL SİSTEMİ (ÖZELDEN) =================
@bot.message_handler(commands=['profilim'])
def manage_profile(message):
    if message.chat.type != 'private':
        bot.reply_to(message, "⚠️ Profil komutunu sadece botun **özel sohbetinde (DM'de)** kullanabilirsin!", disable_notification=True)
        return
    
    user_id = message.from_user.id
    if user_id in user_profiles:
        p = user_profiles[user_id]
        profil_metni = (
            f"👤 **Senin Profilin:**\n\n"
            f"📌 **İsim:** {p['isim']}\n"
            f"🎂 **Yaş:** {p['yas']}\n"
            f"📸 **Instagram:** {p['instagram']}\n\n"
            f"Bilgilerini güncellemek için tekrar `/profilim` yazabilirsin."
        )
        bot.send_message(message.chat.id, profil_metni, parse_mode="Markdown")
    else:
        user_states[user_id] = "waiting_for_profile_name"
        bot.send_message(message.chat.id, "👤 **Profil Oluşturma**\n\nKayıt olmak için adını yaz:", parse_mode="Markdown")

# ================= ÖZEL MESAJ ADIM YÖNETİCİSİ =================
@bot.message_handler(func=lambda message: message.chat.type == 'private')
def handle_private_conversations(message):
    user_id = message.from_user.id
    text = message.text.strip() if message.text else ""

    # Eğer bir başvuru veya profil oluşturma sürecindeyse:
    if user_id in user_states:
        state = user_states[user_id]

        # --- BAŞVURU ADIMLARI ---
        if state == "waiting_for_ingame_name":
            user_applications[user_id]['ingame_name'] = text
            user_states[user_id] = "waiting_for_trophy"
            bot.send_message(message.chat.id, "🏆 Güncel kupa sayını yaz (Örn: 140000):")
            return

        elif state == "waiting_for_trophy":
            user_applications[user_id]['trophy'] = text
            user_states[user_id] = "waiting_for_club_choice"
            bot.send_message(message.chat.id, "🏰 Hangi kulübü istiyorsun? (Ana Kulüp / Yan Kulüp):")
            return

        elif state == "waiting_for_club_choice":
            user_applications[user_id]['club_choice'] = text
            del user_states[user_id] # Süreç bitti
            
            app = user_applications[user_id]
            user_name = message.from_user.first_name or "İsimsiz"
            username = f"@{message.from_user.username}" if message.from_user.username else "Yok"

            # Başvuruyu sahibine (sana) gönder
            rapor = (
                f"📥 **Yeni Kulüp Başvurusu!**\n\n"
                f"👤 **Telegram Adı:** {user_name} ({username})\n"
                f"🆔 **ID:** `{user_id}`\n"
                f"🎮 **Oyun İçi İsim:** {app['ingame_name']}\n"
                f"🏆 **Kupa:** {app['trophy']}\n"
                f"🏰 **İstediği Kulüp:** {app['club_choice']}"
            )
            bot.send_message(BOT_OWNER_ID, rapor, parse_mode="Markdown")
            bot.send_message(message.chat.id, "✅ Başvurun başarıyla yöneticiye iletildi! En kısa sürede dönüş yapılır.")
            return

        # --- PROFİL ADIMLARI ---
        elif state == "waiting_for_profile_name":
            user_profiles[user_id] = {'isim': text}
            user_states[user_id] = "waiting_for_profile_age"
            bot.send_message(message.chat.id, "🎂 Yaşını yaz:")
            return

        elif state == "waiting_for_profile_age":
            user_profiles[user_id]['yas'] = text
            user_states[user_id] = "waiting_for_profile_ig"
            bot.send_message(message.chat.id, "📸 Instagram adresini yaz (Örn: @kullaniciadi):")
            return

        elif state == "waiting_for_profile_ig":
            user_profiles[user_id]['instagram'] = text
            del user_states[user_id] # Süreç bitti

            p = user_profiles[user_id]
            bot.send_message(message.chat.id, "🎉 Profilin başarıyla kaydedildi! `/profilim` yazarak her zaman görebilirsin.")
            
            # Sana da bildir
            user_name = message.from_user.first_name or "İsimsiz"
            bot.send_message(BOT_OWNER_ID, f"👤 **Yeni Profil Kaydı!**\n\nKişi: {user_name}\nİsim: {p['isim']}\nYaş: {p['yas']}\nIG: {p['instagram']}", parse_mode="Markdown")
            return

    # Normal özel mesaj sohbetleri
    if "selam" in text.lower() or "merhaba" in text.lower():
        bot.reply_to(message, "Aleykümselam! Bot aktif.", disable_notification=True)

# ================= GRUP KÜFÜR VE SPAM KONTROLÜ =================
@bot.message_handler(func=lambda message: True)
def handle_group_messages(message):
    if message.chat.type == 'private':
        return

    # Yöneticileri muaf tut
    try:
        member_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
        if member_status in ['creator', 'administrator']:
            return
    except:
        pass

    text = message.text.lower() if message.text else ""
    user_id = message.from_user.id
    current_time = time.time()

    # 1. Küfür Filtresi
    for kelime in YASAKLI_KELIMER:
        if kelime in text:
            try:
                bot.delete_message(message.chat.id, message.message_id)
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
                print(f"Hata: {e}")
            return

    # 2. Spam (Flood) Koruma
    if user_id in user_last_message_time:
        if current_time - user_last_message_time[user_id] < 1.5:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                return
            except:
                pass
                
    user_last_message_time[user_id] = current_time

print("Kulüp botu başvuru ve profil sistemleriyle aktif!")
bot.infinity_polling()
