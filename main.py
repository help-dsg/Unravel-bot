import asyncio
from datetime import datetime, timedelta
import re
import sqlite3
import time
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import (
    ChatMemberUpdatedFilter,
    Command,
    CommandStart,
    IS_MEMBER,
    IS_NOT_MEMBER,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# --- AYARLAR VE SABİTLER ---
TOKEN = "8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s"
ADMIN_ID = 8647573045  # Senin Admin ID'n

bot = Bot(token=TOKEN)
router = Router()
dp = Dispatcher()

# --- VERİTABANI BAĞLANTISI ---
conn = sqlite3.connect("bot_database.db", check_same_thread=False)
cursor = conn.cursor()

# Tabloları Oluştur
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    game_nick TEXT,
    real_name TEXT,
    age INTEGER,
    instagram TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS applications (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    game_nick TEXT,
    trophies TEXT,
    rank TEXT,
    club_type TEXT,
    status TEXT DEFAULT 'Beklemede'
)
"""
)
conn.commit()


# --- FSM (STATE) TANIMLARI ---
class ProfileStates(StatesGroup):
    game_nick = State()
    real_name = State()
    age = State()
    instagram = State()


class ApplicationStates(StatesGroup):
    game_nick = State()
    trophies = State()
    rank = State()


# --- KÜFÜR VE SPAM FİLTRESİ İÇİN BELLEK ---
spam_tracker = {}

# Geniş Küfür Regex Kalıbı (Boşluk, nokta ve karakterleri yakalar)
BAD_WORDS_REGEX = re.compile(
    r"(s\s*i\s*k|o\s*ç|oc|a\s*q|am\s*k|yarrak|orospu|piç|amık|göt|sikik|amcık)",
    re.IGNORECASE,
)


# --- 1. GRUP KARSILAMA, KATILIM BİLDİRİMİ VE KÜFÜR/SPAM KORUMASI ---
@router.message(F.chat.type.in_({"group", "supergroup"}))
async def group_message_handler(message: Message):
    if message.from_user.id == ADMIN_ID:
        return

    text = message.text or message.caption or ""
    user_id = message.from_user.id
    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.full_name
    )

    # 1. Spam Koruması (1 saniyede 1 mesaj)
    current_time = time.time()
    if user_id in spam_tracker:
        if current_time - spam_tracker[user_id] < 1.0:
            try:
                await message.delete()
            except:
                pass
            await bot.send_message(
                ADMIN_ID,
                f"🚨 **SPAM TESPİT EDİLDİ!**\n\n👤 Kişi: {username} (`{user_id}`)\n💬 Mesaj: {text}",
                parse_mode="Markdown",
            )
            return
    spam_tracker[user_id] = current_time

    # 2. Küfür Filtresi (Geniş Regex)
    if BAD_WORDS_REGEX.search(text):
        try:
            await message.delete()
        except:
            pass
        await bot.send_message(
            ADMIN_ID,
            f"🚨 **KÜFÜR TESPİT EDİLDİ!**\n\n👤 Kişi: {username} (`{user_id}`)\n💬 Mesaj: {text}",
            parse_mode="Markdown",
        )
        return


# --- SÜRELİ SUSTURMA KOMUTU (/sustur) ---
@router.message(Command("sustur"))
async def cmd_sustur(message: Message):
    if message.from_user.id != 8647573045
        return

    if not message.reply_to_message:
        await message.answer(
            "Kanka susturmak istediğin kişinin mesajına yanıt vererek `/sustur <saniye>` yazmalısın."
        )
        return

    args = message.text.split()
    duration = (
        int(args[1]) if len(args) > 1 and args[1].isdigit() else 300
    )  # Varsayılan 5 dk

    target_user = message.reply_to_message.from_user
    chat_id = message.chat.id
    until_time = datetime.now() + timedelta(seconds=duration)

    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until_time,
        )
        await message.answer(
            f"🔇 {target_user.full_name}, {duration} saniye boyunca susturuldu kanka."
        )
    except Exception as e:
        await message.answer(
            f"Hata oluştu kanka: {e} (Botun grupta admin yetkisi olduğundan emin ol)"
        )


# --- YENİ ÜYE KATILIM BİLDİRİMİ (Grup/Kanal) ---
@router.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def member_joined_alert(event: ChatMemberUpdated):
    user = event.new_chat_member.user
    chat_title = event.chat.title or "Grup/Kanal"

    if event.chat.type in {"group", "supergroup"}:
        uname = f"@{user.username}" if user.username else user.full_name
        welcome_text = (
            f"Hoşgeldin {uname}\n"
            f"Ortama uyum sağlamak ve kuralları öğrenmek için benimle iletişime geç\n"
            f"https://t.me/tgunravel_bot"
        )
        try:
            await event.bot.send_message(event.chat.id, welcome_text)
        except:
            pass

    alert_text = (
        f"🚨 **Yeni Biri Katıldı Kanka!**\n\n"
        f"📌 Yer: {chat_title}\n"
        f"👤 Ad Soyad: {user.full_name}\n"
        f"🆔 ID: `{user.id}`\n"
        f"🔗 Kullanıcı Adı: @{user.username if user.username else 'Yok'}"
    )
    await event.bot.send_message(chat_id=ADMIN_ID, text=alert_text)


# --- 2. ÖZEL SOHBET (DM) ANA MENÜ VE BUTONLAR ---
@router.message(CommandStart(), F.chat.type == "private")
async def cmd_start(message: Message):
    kb = [
        [
            InlineKeyboardButton(text="Sosyal Medya", callback_data="btn_sosyal"),
            InlineKeyboardButton(
                text="Alım Şartları", callback_data="btn_sartlar"
            ),
        ],
        [
            InlineKeyboardButton(text="İletişim", callback_data="btn_iletisim"),
            InlineKeyboardButton(text="Kurallar", callback_data="btn_kurallar"),
        ],
        [
            InlineKeyboardButton(
                text="📥 Başvuru Yap", callback_data="menu_basvuru"
            ),
            InlineKeyboardButton(text="👤 Profilim", callback_data="menu_profil"),
        ],
        [
            InlineKeyboardButton(
                text="✏️ Profil Düzenle", callback_data="menu_duzenle"
            ),
        ],
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)
    await message.answer(
        "Selam kanka! Botumuza hoş geldin. Aşağıdaki menüden işlemlerini gerçekleştirebilirsin.",
        reply_markup=markup,
    )


@router.callback_query(F.data.startswith("btn_"))
async def menu_callbacks(callback: CallbackQuery):
    data = callback.data
    if data == "btn_sosyal":
        text = (
            "📱 **Sosyal Medya Hesaplarımız:**\n\n"
            "• TikTok: bayrobrawlstars & hlx993\n"
            "• Instagram: theprestige897 & hlx993\n"
            "• YouTube: helpbs"
        )
    elif data == "btn_sartlar":
        text = "📋 **Alım Şartları:**\n\n" "• Kalıcılık\n" "• Saygı\n" "• Aktiflik"
    elif data == "btn_iletisim":
        text = (
            "📞 **İletişim:**\n\n"
            "Instagram: theprestige897 & hlx993 üzerinden ulaşabilirsin."
        )
    elif data == "btn_kurallar":
        text = (
            "⚠️ **Kurallar:**\n\n"
            "• Küfür and Argo yasak\n"
            "• Tartışma yasak\n"
            "• Reklam yasak\n"
            "• Din ve siyaset yasak\n"
            "• Spam yasak"
        )
    else:
        text = "İşlem bulunamadı."

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="⬅️ Ana Menü", callback_data="back_home"
                    )
                ]
            ]
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "back_home")
async def back_home(callback: CallbackQuery):
    kb = [
        [
            InlineKeyboardButton(text="Sosyal Medya", callback_data="btn_sosyal"),
            InlineKeyboardButton(
                text="Alım Şartları", callback_data="btn_sartlar"
            ),
        ],
        [
            InlineKeyboardButton(text="İletişim", callback_data="btn_iletisim"),
            InlineKeyboardButton(text="Kurallar", callback_data="btn_kurallar"),
        ],
        [
            InlineKeyboardButton(
                text="📥 Başvuru Yap", callback_data="menu_basvuru"
            ),
            InlineKeyboardButton(text="👤 Profilim", callback_data="menu_profil"),
        ],
        [
            InlineKeyboardButton(
                text="✏️ Profil Düzenle", callback_data="menu_duzenle"
            ),
        ],
    ]
    await callback.message.edit_text(
        "Selam kanka! Botumuza hoş geldin. Aşağıdaki menüden işlemlerini gerçekleştirebilirsin.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
    )
    await callback.answer()


@router.callback_query(F.data == "menu_basvuru")
async def menu_basvuru_trigger(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(ApplicationStates.game_nick)
    await bot.send_message(
        callback.from_user.id, "Lütfen oyun içi ismini (nickini) yaz:"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_profil")
async def menu_profil_trigger(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(ProfileStates.game_nick)
    await bot.send_message(
        callback.from_user.id, "Lütfen oyun içi ismini (nickini) yaz:"
    )
    await callback.answer()


@router.callback_query(F.data == "menu_duzenle")
async def menu_duzenle_trigger(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.set_state(ProfileStates.game_nick)
    await bot.send_message(
        callback.from_user.id, "Lütfen oyun içi ismini (nickini) yaz:"
    )
    await callback.answer()


# --- 3. BAŞVURU SİSTEMİ (/basvuru) ---
@router.message(Command("basvuru"), F.chat.type == "private")
async def cmd_basvuru(message: Message, state: FSMContext):
    await state.set_state(ApplicationStates.game_nick)
    await message.answer("Lütfen oyun içi ismini (nickini) yaz:")


@router.message(ApplicationStates.game_nick)
async def process_app_nick(message: Message, state: FSMContext):
    await state.update_data(game_nick=message.text)
    await state.set_state(ApplicationStates.trophies)
    await message.answer("Güncel kupa sayını yaz (Örn: 120000):")


@router.message(ApplicationStates.trophies)
async def process_app_trophies(message: Message, state: FSMContext):
    await state.update_data(trophies=message.text)
    await state.set_state(ApplicationStates.rank)
    await message.answer(
        "Aşamalı Rank değerini yaz (Örn: Masters, Legendary vb.):"
    )


@router.message(ApplicationStates.rank)
async def process_app_rank(message: Message, state: FSMContext):
    data = await state.get_data()
    rank = message.text
    game_nick = data["game_nick"]
    trophies = data["trophies"]
    await state.clear()

    kb = [
        [
            InlineKeyboardButton(
                text="Ana Kulüp", callback_data=f"club_ana_{message.from_user.id}"
            ),
            InlineKeyboardButton(
                text="Yan Kulüp", callback_data=f"club_yan_{message.from_user.id}"
            ),
        ]
    ]
    markup = InlineKeyboardMarkup(inline_keyboard=kb)

    cursor.execute(
        "REPLACE INTO applications (user_id, username, game_nick, trophies, rank, status) VALUES (?, ?, ?, ?, ?, ?)",
        (
            message.from_user.id,
            f"@{message.from_user.username}"
            if message.from_user.username
            else message.from_user.full_name,
            game_nick,
            trophies,
            rank,
            "Beklemede",
        ),
    )
    conn.commit()

    await message.answer(
        "Bilgilerin alındı! Şimdi katılmak istediğin kulübü seç:",
        reply_markup=markup,
    )


@router.callback_query(F.data.startswith("club_"))
async def select_club_type(callback: CallbackQuery):
    parts = callback.data.split("_")
    club_type = parts[1]
    user_id = int(parts[2])

    c_text = "Ana Kulüp" if club_type == "ana" else "Yan Kulüp"

    cursor.execute(
        "UPDATE applications SET club_type = ? WHERE user_id = ?",
        (c_text, user_id),
    )
    conn.commit()

    cursor.execute(
        "SELECT username, game_nick, trophies, rank, club_type FROM applications WHERE user_id = ?",
        (user_id,),
    )
    app_data = cursor.fetchone()

    admin_kb = [
        [
            InlineKeyboardButton(
                text="✅ Onayla", callback_data=f"app_onay_{user_id}"
            ),
            InlineKeyboardButton(
                text="❌ Reddet", callback_data=f"app_red_{user_id}"
            ),
        ]
    ]

    text = (
        f"📥 **YENİ BAŞVURU VAR!**\n\n"
        f"👤 Kullanıcı: {app_data[0]} (`{user_id}`)\n"
        f"🎮 Nick: {app_data[1]}\n"
        f"🏆 Kupa: {app_data[2]}\n"
        f"🎖️ Rank: {app_data[3]}\n"
        f"📌 Seçilen: {app_data[4]}"
    )

    await bot.send_message(
        ADMIN_ID, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=admin_kb)
    )
    await callback.message.edit_text(
        f"Başvurun **{c_text}** için alındı! Yönetici onayından sonra bilgilendirileceksin."
    )


# --- 4. PROFİL SİSTEMİ (/profilim ve /profilimi_duzenle) ---
@router.message(Command("profilim"), F.chat.type == "private")
async def cmd_profilim(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.game_nick)
    await message.answer("Lütfen oyun içi ismini (nickini) yaz:")


@router.message(ProfileStates.game_nick)
async def prof_nick(message: Message, state: FSMContext):
    await state.update_data(game_nick=message.text)
    await state.set_state(ProfileStates.real_name)
    await message.answer("Lütfen adını yaz:")


@router.message(ProfileStates.real_name)
async def prof_name(message: Message, state: FSMContext):
    await state.update_data(real_name=message.text)
    await state.set_state(ProfileStates.age)
    await message.answer("Lütfen yaşını yaz:")


@router.message(ProfileStates.age)
async def prof_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(ProfileStates.instagram)
    await message.answer("Lütfen Instagram adresini yaz (Örn:@user123):")


@router.message(ProfileStates.instagram)
async def prof_insta(message: Message, state: FSMContext):
    data = await state.get_data()
    instagram = message.text
    user_id = message.from_user.id
    username = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else message.from_user.full_name
    )

    cursor.execute(
        "SELECT game_nick, real_name, age, instagram FROM profiles WHERE user_id = ?",
        (user_id,),
    )
    old_data = cursor.fetchone()

    cursor.execute(
        "REPLACE INTO profiles (user_id, username, game_nick, real_name, age, instagram) VALUES (?, ?, ?, ?, ?, ?)",
        (
            user_id,
            username,
            data["game_nick"],
            data["real_name"],
            data["age"],
            instagram,
        ),
    )
    conn.commit()
    await state.clear()

    await message.answer("Profilin başarıyla kaydedildi/güncellendi!")

    if old_data:
        admin_text = (
            f"🔄 **PROFİL GÜNCELLENDİ**\n👤 {username} (`{user_id}`)\n\n"
            f"📜 **Eski Bilgiler:**\n• Nick: {old_data[0]}\n• Ad: {old_data[1]}\n• Yaş: {old_data[2]}\n• IG: {old_data[3]}\n\n"
            f"✨ **Yeni Bilgiler:**\n• Nick: {data['game_nick']}\n• Ad: {data['real_name']}\n• Yaş: {data['age']}\n• IG: {instagram}"
        )
    else:
        admin_text = (
            f"🆕 **YENİ PROFİL OLUŞTURULDU**\n👤 {username} (`{user_id}`)\n\n"
            f"• Nick: {data['game_nick']}\n• Ad: {data['real_name']}\n• Yaş: {data['age']}\n• IG: {instagram}"
        )

    await bot.send_message(ADMIN_ID, admin_text)


@router.message(Command("profilimi_duzenle"), F.chat.type == "private")
async def cmd_profil_duzenle(message: Message, state: FSMContext):
    await cmd_profilim(message, state)


# --- 5. YÖNETİCİ KOMUTLARI (LİSTE VE AKILLI TAM EŞLEŞME SORGULAMA) ---
@router.message(Command("liste"))
async def cmd_liste(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    cursor.execute(
        "SELECT user_id, username, game_nick, real_name, age, instagram FROM profiles"
    )
    rows = cursor.fetchall()

    if not rows:
        await message.answer("Kayıtlı hiç profil yok.")
        return

    text = "📋 **Kayıtlı Profiller Listesi:**\n\n"
    for r in rows:
        text += f"• 👤 {r[1]} | Nick: {r[2]} | Ad: {r[3]} | Yaş: {r[4]} | IG: {r[5]} (`{r[0]}`)\n"

    await message.answer(text)


@router.message(F.chat.type == "private")
async def query_user_profile(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    if message.text.startswith("/"):
        return

    query = message.text.strip()
    clean_query = query.lstrip("@")

    if query.isdigit():
        cursor.execute(
            "SELECT user_id, username, game_nick, real_name, age, instagram, updated_at FROM profiles WHERE user_id = ?",
            (int(query),),
        )
    else:
        cursor.execute(
            "SELECT user_id, username, game_nick, real_name, age, instagram, updated_at FROM profiles WHERE username = ? OR username = ?",
            (query, f"@{clean_query}"),
        )

    res = cursor.fetchone()

    if not res:
        await message.answer(
            f"Veritabanında `{query}` ile tam eşleşen bir profil bulunamadı kanka. (Sadece tam kullanıcı adı veya ID yazarak arayabilirsin)"
        )
        return

    text = (
        f"🔍 **Profil Sorgulama Sonucu:**\n\n"
        f"🆔 ID: `{res[0]}`\n"
        f"👤 Kullanıcı Adı: {res[1]}\n"
        f"🎮 Oyun Nick: {res[2]}\n"
        f"👤 Ad Soyad: {res[3]}\n"
        f"📅 Yaş: {res[4]}\n"
        f"📸 Instagram: {res[5]}\n"
        f"⏱️ Son Güncelleme: {res[6]}"
    )
    await message.answer(text)


# --- 6. ADMIN BAŞVURU ONAY / RED CALLBACKLERİ ---
@router.callback_query(F.data.startswith("app_"))
async def admin_decision(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Bu işlemi yapmaya yetkin yok!", show_alert=True)
        return

    parts = callback.data.split("_")
    action = parts[1]
    user_id = int(parts[2])

    cursor.execute(
        "SELECT club_type FROM applications WHERE user_id = ?", (user_id,)
    )
    res = cursor.fetchone()
    if not res:
        await callback.message.edit_text("Bu başvuru veritabanında bulunamadı.")
        return

    club_type = res[0]

    if action == "onay":
        if club_type == "Ana Kulüp":
            msg_to_user = "Başvurunuz onaylanmıştır kulüp kodu:#82QYGLVCY"
        else:
            msg_to_user = "Başvurunuz onaylanmıştır kulüp kodu:#2UCCV8VGG"
    else:
        if club_type == "Ana Kulüp":
            msg_to_user = "Başvurunuz reddedilmiştir lütfen yan kulübe katılmak için tekrar başvuru gönderin"
        else:
            msg_to_user = (
                "Başvurunuz reddedilmiştir lütfen daha sonra tekrar başvurun"
            )

    try:
        await bot.send_message(user_id, msg_to_user)
        status_msg = "İşlem başarıyla kullanıcıya iletildi."
    except:
        status_msg = (
            "İşlem yapıldı ancak kullanıcı botu engellediği için mesaj gidemedi."
        )

    await callback.message.edit_text(
        f"{callback.message.text}\n\n---\n📌 **Durum:** {status_msg}"
    )


# --- BOTU BAŞLATMA ---
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot aktif ve mermi gibi çalışıyor kanka!
