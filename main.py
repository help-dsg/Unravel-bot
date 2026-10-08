import sqlite3
import logging
import time
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Token'ı ve Yönetici ID'si
TOKEN = "8616505304:AAEbAwnB2xN0DOoAZf6bgZ4w26zcpVPmV6s"
YONETICI_ID = 8647573045

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- 1. DÜZ KÜFÜR KÖKLERİ (Harf arası boşluk/nokta atlatmalı regex) ---
KUFUR_KOKLERI = [
    "amk", "aq", "amina", "amına", "orospu", "oç", "piç", 
    "sik", "sikerim", "siktir", "orospu çocuğu", "ibne", 
    "yarak", "yarrak", "göt", "götveren", "amcık", "ananın"
]
REGEX_KUFURLER = [re.compile(r"[\s\.\-_]*".join(list(kok)), re.IGNORECASE) for kok in KUFUR_KOKLERI]

# --- 2. HASSAS KELİMELER VE KÜFÜR KOMBİNASYONLARI ---
# "Ata" veya "Allah" kelimeleri sadece yanlarında bu ekler/küfürler varsa silinecek (Tek başına serbest)
HASSAS_KELIMELER = ["ata", "allah"]
HASSAS_KUFUR_EKLERI = ["atanı", "atanin", "allahini", "allahını", "siker", "siktir", "orospu", "piç", "amk", "aq", "anani", "ananı", "göt"]

# Spam / Flood takibi için hafıza sözlüğü
user_last_message_time = {}
FLOOD_DELAY = 2.0  # Saniye cinsinden mesaj aralığı sınırı

# --- VERİTABANI BAĞLANTISI VE OLUŞTURMA ---
def init_db():
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS basvurular (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            oyun_adi TEXT,
            kupa TEXT,
            rank TEXT,
            kulup TEXT,
            durum TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiller (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            isim TEXT,
            yas TEXT,
            instagram TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- FSM (STATE) TANIMLARI ---
class BasvuruState(StatesGroup):
    oyun_adi = State()
    kupa = State()
    rank = State()
    kulup = State()

class ProfilState(StatesGroup):
    isim = State()
    yas = State()
    instagram = State()

# --- ANA MENÜ KLAVYESİ ---
def ana_menu_klavyesi():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Alım Şartları", callback_data="artlar"), InlineKeyboardButton(text="⚠️ Kurallar", callback_data="kurallar")],
        [InlineKeyboardButton(text="📞 İletişim", callback_data="iletisim"), InlineKeyboardButton(text="🌐 Sosyal Medya", callback_data="sosyal")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    yazi = (
        "Unravel destek botuna hoş geldin! 🚀\n\n"
        "Özel sohbet üzerinden şu komutları kullanabilirsin:\n"
        "✏️ /basvuru - Kulüp için başvuru yap\n"
        "👤 /profilim - Profilini oluştur veya görüntüle"
    )
    await message.answer(yazi, reply_markup=ana_menu_klavyesi())

# --- KÜFÜR, HASSAS KELİME VE SPAM FİLTRESİ (YÖNETİCİ MUAFİYETLİ) ---
@dp.message(F.text & ~F.text.startswith("/"))
async def genel_mesaj_kontrol(message: types.Message):
    user = message.from_user
    
    # 1. YÖNETİCİ MUAFİYETİ (Eğer mesajı atan yöneticiyse bot hiç karışmaz)
    if user.id == YONETICI_ID:
        if message.text.startswith("@"):
            await query_user_by_username(message)
        return

    # Eğer grupta yetkiliyse de kontrolü geçebilir
    if message.chat.type in ["group", "supergroup"]:
        try:
            member = await message.chat.get_member(user.id)
            if member.status in ["creator", "administrator"]:
                if message.text.startswith("@"):
                    await query_user_by_username(message)
                return
        except Exception:
            pass

    current_time = time.time()
    username_str = f"@{user.username}" if user.username else "Kullanıcı adı yok"
    
    # 2. SPAM / FLOOD KONTROLÜ
    if user.id in user_last_message_time:
        if current_time - user_last_message_time[user.id] < FLOOD_DELAY:
            try:
                await message.delete()
                yonetici_raporu = (
                    f"🚨 **Spam / Flood Yakalandı!**\n\n"
                    f"👤 **Kişi:** {user.full_name} ({username_str})\n"
                    f"🆔 **ID:** `{user.id}`\n"
                    f"💬 **Hızlı Atılan Mesaj:**\n\"{message.text}\""
                )
                await bot.send_message(YONETICI_ID, yonetici_raporu)
            except Exception as e:
                logging.error(f"Spam silme hatası: {e}")
            return
            
    user_last_message_time[user.id] = current_time

    # 3. KÜFÜR VE HASSAS KELİME KONTROLÜ
    text_content = message.text
    text_lower = text_content.lower()
    yasakli_bulundu = False
    
    # A) Standart küfür kökleri ve regex kontrolü
    for pattern in REGEX_KUFURLER:
        if pattern.search(text_content):
            yasakli_bulundu = True
            break
            
    # B) Hassas kelimeler (Ata / Allah) kontrolü -> Sadece yanlarında küfür/hakaret eki varsa silinir
    if not yasakli_bulundu:
        for hassas in HASSAS_KELIMELER:
            if hassas in text_lower:
                for kufur_eki in HASSAS_KUFUR_EKLERI:
                    if kufur_eki in text_lower:
                        yasakli_bulundu = True
                        break
            if yasakli_bulundu:
                break

    if yasakli_bulundu:
        try:
            await message.delete()
            yonetici_raporu = (
                f"🚨 **Yasaklı Kelime / Küfür Yakalandı!**\n\n"
                f"👤 **Kişi:** {user.full_name} ({username_str})\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"💬 **Yazdığı Mesaj:**\n\"{message.text}\""
            )
            await bot.send_message(YONETICI_ID, yonetici_raporu)
        except Exception as e:
            logging.error(f"Küfür silme hatası: {e}")
        return

    # Eğer mesaj @ ile başlıyorsa kullanıcı sorgulama çalışsın
    if message.text.startswith("@"):
        await query_user_by_username(message)

# --- KULÜP BAŞVURU AKIŞI ---
@dp.message(Command("basvuru"))
async def cmd_basvuru(message: types.Message, state: FSMContext):
    await message.answer("📝 **Kulüp Başvuru Sistemi**\n\nLütfen oyun içi ismini (nickini) yaz:")
    await state.set_state(BasvuruState.oyun_adi)

@dp.message(BasvuruState.oyun_adi)
async def process_oyun_adi(message: types.Message, state: FSMContext):
    await state.update_data(oyun_adi=message.text)
    await message.answer("🏆 Güncel kupa sayını yaz (Örn: 140000):")
    await state.set_state(BasvuruState.kupa)

@dp.message(BasvuruState.kupa)
async def process_kupa(message: types.Message, state: FSMContext):
    await state.update_data(kupa=message.text)
    await message.answer("⭐ Aşamalı Rank değerini yaz (Örn: Masters, Legendary vb.):")
    await state.set_state(BasvuruState.rank)

@dp.message(BasvuruState.rank)
async def process_rank(message: types.Message, state: FSMContext):
    await state.update_data(rank=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Ana Kulüp", callback_data="kulup_ana"), InlineKeyboardButton(text="Yan Kulüp", callback_data="kulup_yan")]
    ])
    await message.answer("🏰 Hangi kulübü istiyorsun?", reply_markup=keyboard)
    await state.set_state(BasvuruState.kulup)

@dp.callback_query(F.data.startswith("kulup_"))
async def process_kulup_secim(callback: types.CallbackQuery, state: FSMContext):
    kulup_adi = "Ana kulüp" if callback.data == "kulup_ana" else "Yan kulüp"
    await state.update_data(kulup=kulup_adi)
    data = await state.get_data()
    
    user = callback.from_user
    username = user.username.lower() if user.username else "yok"
    display_username = f"@{user.username}" if user.username else "Yok"
    
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO basvurular (telegram_id, username, oyun_adi, kupa, rank, kulup, durum)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user.id, username, data['oyun_adi'], data['kupa'], data['rank'], data['kulup'], "Bekliyor"))
    conn.commit()
    conn.close()

    await callback.message.edit_text("✅ Başvurun başarıyla yöneticiye iletildi! En kısa sürede dönüş yapılır.")
    
    yonetici_mesaji = (
        f"🚨 **Yeni Kulüp Başvurusu!**\n\n"
        f"👤 Telegram Adı: {user.full_name} ({display_username})\n"
        f"🆔 ID: {user.id}\n"
        f"🎮 Oyun İçi İsim: {data['oyun_adi']}\n"
        f"🏆 Kupa: {data['kupa']}\n"
        f"⭐ Rank: {data['rank']}\n"
        f"🏰 İstediği Kulüp: {data['kulup']}"
    )
    
    yonetim_tuslari = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Onayla", callback_data=f"onayla_{user.id}"),
            InlineKeyboardButton(text="❌ Reddet", callback_data=f"reddet_{user.id}")
        ]
    ])
    
    await bot.send_message(YONETICI_ID, yonetici_mesaji, reply_markup=yonetim_tuslari)
    await state.clear()

# --- YÖNETİCİ ONAY / RET İŞLEMLERİ ---
@dp.callback_query(F.data.startswith(("onayla_", "reddet_")))
async def process_yonetici_karar(callback: types.CallbackQuery):
    islem, hedef_id_str = callback.data.split("_")
    hedef_id = int(hedef_id_str)
    
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    
    if islem == "onayla":
        cursor.execute("UPDATE basvurular SET durum = 'Onaylandı' WHERE telegram_id = ?", (hedef_id,))
        conn.commit()
        await callback.message.edit_text(callback.message.text + "\n\n✅ **Durum:** ONAYLANDI")
        try:
            await bot.send_message(hedef_id, "🎉 Tebrikler! Kulüp başvurunuz **onaylandı**!")
        except Exception:
            pass
    elif islem == "reddet":
        cursor.execute("UPDATE basvurular SET durum = 'Reddedildi' WHERE telegram_id = ?", (hedef_id,))
        conn.commit()
        await callback.message.edit_text(callback.message.text + "\n\n❌ **Durum:** REDDEDİLDİ")
        try:
            await bot.send_message(hedef_id, "Maalesef kulüp başvurunuz bu sefer **reddedildi**.")
        except Exception:
            pass
            
    conn.close()
    await callback.answer("İşlem kaydedildi!")

# --- PROFİL OLUŞTURMA AKIŞI ---
@dp.message(Command("profilim"))
async def cmd_profilim(message: types.Message, state: FSMContext):
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("SELECT isim, yas, instagram FROM profiller WHERE telegram_id = ?", (message.from_user.id,))
    profil = cursor.fetchone()
    
    cursor.execute("SELECT kupa, rank FROM basvurular WHERE telegram_id = ?", (message.from_user.id,))
    basvuru = cursor.fetchone()
    conn.close()

    if profil:
        isim, yas, instagram = profil
        kupa_bilgi = basvuru[0] if basvuru else "Belirtilmemiş"
        rank_bilgi = basvuru[1] if basvuru else "Belirtilmemiş"
        
        metin = (
            f"👤 **Senin Profilin:**\n\n"
            f"📌 İsim: {isim}\n"
            f"🎂 Yaş: {yas}\n"
            f"📸 Instagram: {instagram}\n"
            f"🏆 Kupa: {kupa_bilgi}\n"
            f"⭐ Aşamalı Rank: {rank_bilgi}\n\n"
            f"Bilgilerini güncellemek için tekrar /profilim yazabilirsin."
        )
        await message.answer(metin)
    else:
        await message.answer("👤 **Profil Oluşturma**\n\nKayıt olmak için adını yaz:")
        await state.set_state(ProfilState.isim)

@dp.message(ProfilState.isim)
async def process_profil_isim(message: types.Message, state: FSMContext):
    await state.update_data(isim=message.text)
    await message.answer("🎂 Yaşını yaz:")
    await state.set_state(ProfilState.yas)

@dp.message(ProfilState.yas)
async def process_profil_yas(message: types.Message, state: FSMContext):
    await state.update_data(yas=message.text)
    await message.answer("📸 Instagram adresini yaz (Örn: @kullaniciadi):")
    await state.set_state(ProfilState.instagram)

@dp.message(ProfilState.instagram)
async def process_profil_instagram(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user
    username = user.username.lower() if user.username else "yok"
    
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO profiller (telegram_id, username, isim, yas, instagram)
        VALUES (?, ?, ?, ?, ?)
    """, (user.id, username, data['isim'], data['yas'], message.text))
    conn.commit()
    conn.close()

    await message.answer("🎉 Profilin başarıyla kaydedildi! `/profilim` yazarak her zaman görebilirsin.")
    await state.clear()

# --- YÖNETİCİ İÇİN KULLANICI SORGULAMA (@KULLANICIADI İLE) ---
async def query_user_by_username(message: types.Message):
    aranan_username = message.text.strip().lstrip("@").lower()
    
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT oyun_adi, kupa, rank, kulup, durum FROM basvurular WHERE username = ?", (aranan_username,))
    basvuru = cursor.fetchone()
    
    cursor.execute("SELECT isim, yas, instagram FROM profiller WHERE username = ?", (aranan_username,))
    profil = cursor.fetchone()
    conn.close()
    
    if not basvuru and not profil:
        await message.answer(f"❌ @{aranan_username} kullanıcı adına ait bir kayıt bulunamadı.")
        return
        
    cevap = f"🔍 **Kullanıcı Bilgileri: @{aranan_username}**\n\n"
    
    if profil:
        cevap += f"👤 **Profil Bilgileri:**\n- İsim: {profil[0]}\n- Yaş: {profil[1]}\n- Instagram: {profil[2]}\n\n"
    else:
        cevap += "👤 **Profil Bilgileri:** Kayıt yok.\n\n"
        
    if basvuru:
        cevap += f"📋 **Başvuru Bilgileri:**\n- Oyun İçi İsim: {basvuru[0]}\n- Kupa: {basvuru[1]}\n- Rank: {basvuru[2]}\n- Kulüp: {basvuru[3]}\n- Durum: {basvuru[4]}"
    else:
        cevap += "📋 **Başvuru Bilgileri:** Başvuru bulunamadı."
        
    await message.answer(cevap)

if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
