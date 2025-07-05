from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.utils.markdown import hbold
from aiogram import Router
import asyncio
import pandas as pd
from datetime import datetime
import os

TOKEN = "YOUR_TOKEN_HERE"
ADMIN_IDS = [612570166]

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

# Holatlar klassi
class FSMUserState(StatesGroup):
    awaiting_login = State()

# /start komandasi
@dp.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("🔐 Iltimos, loginni kiriting:")
    await state.set_state(FSMUserState.awaiting_login)

# Login tekshiruvi va javob
@dp.message(FSMUserState.awaiting_login)
async def login_handler(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("❗️ Iltimos, loginni matn ko‘rinishida yuboring.")
        return

    login = message.text.strip().upper()
    await state.update_data(login=login)

    today_str = datetime.now().strftime("%Y-%m-%d")
    file_path = f"data/{today_str}.xlsx"

    try:
        df = pd.read_excel(file_path, sheet_name="xodimlar")
    except FileNotFoundError:
        await message.answer("❗️ Bugungi fayl topilmadi. Iltimos, avval faylni yuklang.")
        return
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi: {e}")
        return

    user_row = df[df['login'].astype(str).str.upper().str.strip() == login]

    if user_row.empty:
        await message.answer("❗️ Siz yuborgan login bo‘yicha ma’lumot topilmadi.")
        return

    row = user_row.iloc[0]
    filial = row['filial nomi']
    fio = row['xodim F.I.O.']
    plan = row['plan']
    qarzdor_soni = row['qarzdorlar soni']
    qarzdor_summasi = row['qarzdorlar summasi']
    bajarilgan_summada = row['bajarildi summada']
    bajarilgan_foizda = row['bajarildi foizda']
    prognoz = row['prognoz (%)']

    text = (
        f"👤 <b>{fio}</b>\n"
        f"🏢 Filial: <b>{filial}</b>\n"
        f"📅 Sana: <b>{today_str}</b>\n\n"
        f"🎯 Reja: <b>{plan}</b>\n"
        f"🧾 Qarzdorlar: <b>{qarzdor_soni} ta</b> | 💰 <b>{qarzdor_summasi}</b>\n"
        f"✅ Bajarilgan: <b>{bajarilgan_summada}</b> | 📊 <b>{bajarilgan_foizda}%</b>\n"
        f"🔮 Prognoz: <b>{prognoz}%</b>"
    )

    await message.answer(text, parse_mode="HTML")
    await state.clear()

# Botni ishga tushurish
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
