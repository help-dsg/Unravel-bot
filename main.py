import sqlite3
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Bot Token'ını buraya gir
TOKEN = "BURAYA_BOT_TOKENINI_YAZ"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# --- VERİTABANI BAĞLANTISI VE OLUŞTURMA ---
def init_db():
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    # Başvuru tablosu
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
    # Profil tablosu
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
    username = f"@{user.username}" if user.username else "Yok"
    
    # Veritabanına kaydet/güncelle
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO basvurular (telegram_id, username, oyun_adi, kupa, rank, kulup, durum)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user.id, user.username, data['oyun_adi'], data['kupa'], data['rank'], data['kulup'], "Bekliyor"))
    conn.commit()
    conn.close()

    await callback.message.edit_text("✅ Başvurun başarıyla yöneticiye iletildi! En kısa sürede dönüş yapılır.")
    
    # Yöneticiye bildirim gitmesi için (Yönetici ID'ni buraya yazabilirsin veya grup ID)
    yonetici_id = YONETICI_TELEGRAM_ID_BURAYA 
    yonetici_mesaji = (
        f"🚨 **Yeni Kulüp Başvurusu!**\n\n"
        f"👤 Telegram Adı: {user.full_name} ({username})\n"
        f"🆔 ID: {user.id}\n"
        f"🎮 Oyun İçi İsim: {data['oyun_adi']}\n"
        f"🏆 Kupa: {data['kupa']}\n"
        f"⭐ Rank: {data['rank']}\n"
        f"🏰 İstediği Kulüp: {data['kulup']}"
    )
    await bot.send_message(yonetici_id, yonetici_mesaji)
    await state.clear()

# --- PROFİL OLUŞTURMA AKIŞI ---
@dp.message(Command("profilim"))
async def cmd_profilim(message: types.Message, state: FSMContext):
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("SELECT isim, yas, instagram FROM profiller WHERE telegram_id = ?", (message.from_user.id,))
    profil = cursor.fetchone()
    
    # Başvuru bilgilerini de çekelim (kupa ve rank için)
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
    
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO profiller (telegram_id, username, isim, yas, instagram)
        VALUES (?, ?, ?, ?, ?)
    """, (user.id, user.username, data['isim'], data['yas'], message.text))
    conn.commit()
    conn.close()

    await message.answer("🎉 Profilin başarıyla kaydedildi! `/profilim` yazarak her zaman görebilirsin.")
    await state.clear()

# --- YÖNETİCİ İÇİN KULLANICI SORGULAMA (@KULLANICIADI İLE) ---
@dp.message(F.text.startswith("@"))
async def query_user_by_username(message: types.Message):
    # Bu özellik sadece senin (yöneticinin) kullanması için sınırlandırılabilir
    aranan_username = message.text.strip().lstrip("@")
    
    conn = sqlite3.connect("bot_veritabani.db")
    cursor = conn.cursor()
    
    # Başvuru bilgilerini çek
    cursor.execute("SELECT oyun_adi, kupa, rank, kulup, durum FROM basvurular WHERE username = ?", (aranan_username,))
    basvuru = cursor.fetchone()
    
    # Profil bilgilerini çek
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

# Botu başlatma bloğu
if __name__ == "__main__":
    import asyncio
    async def main():
        await dp.start_polling(bot)
    asyncio.run(main())
