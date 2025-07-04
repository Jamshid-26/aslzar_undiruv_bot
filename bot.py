from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import CommandStart
import pandas as pd
import asyncio

TOKEN = "7959517653:AAHY1brM8dtlqb6ljfnr0uc7rfECIO4Wi-0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 Salom! Login raqamingizni yuboring:")

@dp.message()
async def login_handler(message: Message):
    login = message.text.strip().upper()

    try:
        # Excel faylni o‘qish
        df = pd.read_excel("Undiruv hisoboti.xlsx", sheet_name="xodimlar")
        df.columns = df.columns.str.lower()  # ustun nomlarini kichik harfga aylantiramiz

        result = df[df['login'].str.upper() == login]

        if not result.empty:
            row = result.iloc[0]

            javob = (
                f"📌 *Login:* `{login}`\n"
                f"🏢 *Filial:* {row['filial nomi']}\n"
                f"👤 *Xodim:* {row['xodim f.i.o.']}\n"
                f"📋 *Plan:* {int(row['plan']):,} so'm\n"
                f"❗ *Qarzdorlar soni:* {int(row['qarzdorlar soni'])} ta\n"
                f"💰 *Qarzdorlar summasi:* {int(row['qarzdorlar summasi']):,} so'm\n"
                f"✅ *Bajarildi:* {int(row['bajarildi summada']):,} so'm\n"
                f"📊 *Bajarildi foizda:* {float(row['bajarildi foizda']):.2f}%\n"
                f"📈 *Prognoz:* {float(row['prognoz (%)']):.2f}%"
            ).replace(",", " ")  # vergulni bo‘sh joyga almashtiramiz

        else:
            javob = "❌ Bunday login topilmadi."

    except Exception as e:
        javob = f"⚠️ Xatolik yuz berdi: {str(e)}"

    await message.answer(javob, parse_mode="Markdown")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
