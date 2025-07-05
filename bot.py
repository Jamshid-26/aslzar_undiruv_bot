from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import pandas as pd
import asyncio
from datetime import datetime, timedelta, time
import os
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TOKEN = "7959517653:AAHY1brM8dtlqb6ljfnr0uc7rfECIO4Wi-0"
ADMIN_IDS = [612570166]  # Jamshidning Telegram ID
BELGILANGAN_SOAT = "10:00"
HOZIRGI_FAYL = "Undiruv hisoboti.xlsx"
DATA_FOLDER = "data"

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

os.makedirs(DATA_FOLDER, exist_ok=True)

user_login_map = {}  # user_id: login

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 Salom! Login raqamingizni yuboring:")

@dp.message(Command("admin"))
async def admin_command_handler(message: Message):
    if message.from_user.id in ADMIN_IDS:
        builder = InlineKeyboardBuilder()
        builder.button(text="📈 Reyting", callback_data="reyting")
        builder.button(text="📊 Grafik", callback_data="grafik")
        builder.button(text="📄 PDF", callback_data="pdf")
        builder.button(text="🔁 Solishtirish", callback_data="solishtirish")
        builder.button(text="⚙️ Loginlar", callback_data="loginlar")
        await message.answer("🛠 Admin paneli:", reply_markup=builder.as_markup())
    else:
        await message.answer("🚫 Sizda admin huquqlari yo‘q.")

@dp.callback_query()
async def admin_panel_handler(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    user_id = callback.from_user.id
    today = datetime.today().strftime("%Y-%m-%d")

    try:
        df = pd.read_excel(f"{DATA_FOLDER}/{today}.xlsx", sheet_name="xodimlar")
        df.columns = df.columns.str.lower()
    except Exception as e:
        await callback.message.answer(f"⚠️ Fayl ochishda xatolik: {e}")
        return

    if data == "reyting":
        df_sorted = df.sort_values(by="bajarildi foizda", ascending=False).reset_index(drop=True)
        reyting_text = "📈 *Umumiy reyting:*\n"
        for i, row in df_sorted.iterrows():
            reyting_text += f"{i+1}. {row['xodim f.i.o.']} – {row['bajarildi foizda']}%\n"
        await callback.message.answer(reyting_text, parse_mode="Markdown")

    elif data == "grafik":
        plt.figure(figsize=(10, 6))
        df_sorted = df.sort_values(by="bajarildi foizda", ascending=False)
        plt.barh(df_sorted['xodim f.i.o.'], df_sorted['bajarildi foizda'])
        plt.xlabel('Bajarildi (%)')
        plt.title("Xodimlar bo'yicha bajarilish foizi")
        plt.tight_layout()
        img_path = f"{DATA_FOLDER}/bajarilish_grafik.png"
        plt.savefig(img_path)
        await bot.send_photo(user_id, photo=FSInputFile(img_path))

    elif data == "pdf":
        pdf_path = f"{DATA_FOLDER}/hisobot.pdf"
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 800, f"Hisobot: {today}")
        for i, row in df.iterrows():
            text = f"{i+1}. {row['xodim f.i.o.']}: {row['bajarildi foizda']}%"
            c.drawString(100, 780 - i*15, text)
        c.save()
        await bot.send_document(user_id, document=FSInputFile(pdf_path))

    elif data == "solishtirish":
        yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            df_old = pd.read_excel(f"{DATA_FOLDER}/{yesterday}.xlsx", sheet_name="xodimlar")
            df_old.columns = df_old.columns.str.lower()
            text = "🔁 *Kechagi va bugungi solishtirish:*\n"
            for i, row in df.iterrows():
                login = row['login']
                old_row = df_old[df_old['login'].str.upper() == login.upper()]
                if not old_row.empty:
                    foiz_bugun = row['bajarildi foizda']
                    foiz_kecha = old_row.iloc[0]['bajarildi foizda']
                    farq = foiz_bugun - foiz_kecha
                    belgi = "🟢" if farq > 0 else ("🔴" if farq < 0 else "➖")
                    text += f"{belgi} {row['xodim f.i.o.']}: {farq:.2f}%\n"
            await callback.message.answer(text, parse_mode="Markdown")
        except:
            await callback.message.answer("⚠️ Kechagi fayl topilmadi.")

    elif data == "loginlar":
        login_list = [f"{i+1}. {row['xodim f.i.o.']} – {row['login']}" for i, row in df.iterrows()]
        await callback.message.answer("⚙️ *Loginlar ro‘yxati:*\n" + "\n".join(login_list), parse_mode="Markdown")

@dp.message()
async def login_handler(message: Message):
    login = message.text.strip().upper()
    user_login_map[message.from_user.id] = login
    await send_personal_report(message.from_user.id, login)

async def send_personal_report(user_id, login):
    today = datetime.today().strftime("%Y-%m-%d")
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        df_now = pd.read_excel(f"{DATA_FOLDER}/{today}.xlsx", sheet_name="xodimlar")
        df_now.columns = df_now.columns.str.lower()

        row_now_df = df_now[df_now['login'].str.upper() == login]
        if row_now_df.empty:
            await bot.send_message(chat_id=user_id, text="❗ Siz yuborgan login bo‘yicha ma’lumot topilmadi.")
            return
        row_now = row_now_df.iloc[0]

        df_sorted = df_now.sort_values(by="bajarildi foizda", ascending=False).reset_index(drop=True)
        reyting_umumiy_df = df_sorted[df_sorted['login'].str.upper() == login]
        if reyting_umumiy_df.empty:
            reyting_umumiy = "-"
        else:
            reyting_umumiy = reyting_umumiy_df.index[0] + 1

        filial_df = df_now[df_now['filial nomi'] == row_now['filial nomi']]
        filial_sorted = filial_df.sort_values(by="bajarildi foizda", ascending=False).reset_index(drop=True)
        reyting_filial_df = filial_sorted[filial_sorted['login'].str.upper() == login]
        if reyting_filial_df.empty:
            reyting_filial = "-"
        else:
            reyting_filial = reyting_filial_df.index[0] + 1

        compare_text = ""
        try:
            df_old = pd.read_excel(f"{DATA_FOLDER}/{yesterday}.xlsx", sheet_name="xodimlar")
            df_old.columns = df_old.columns.str.lower()
            row_old_df = df_old[df_old['login'].str.upper() == login]
            if not row_old_df.empty:
                row_old = row_old_df.iloc[0]

                def diff_label(now, old, birlik=""):
                    farq = now - old
                    if farq > 0:
                        return f"🟢 +{farq:,.2f}{birlik}"
                    elif farq < 0:
                        return f"🔴 {farq:,.2f}{birlik}"
                    else:
                        return "➖ 0"

                compare_text += (
                    f"\n\n📉 O‘zgarishlar:\n"
                    f"✅ Bajarildi: {diff_label(row_now['bajarildi summada'], row_old['bajarildi summada'], ' so‘m')}\n"
                    f"📊 Foiz: {diff_label(row_now['bajarildi foizda'], row_old['bajarildi foizda'], '%')}\n"
                    f"📈 Prognoz: {diff_label(row_now['prognoz (%)'], row_old['prognoz (%)'], '%')}"
                )
            else:
                compare_text = "\n\nℹ️ Kechagi natija topilmadi."
        except:
            compare_text = "\n\nℹ️ Kechagi natija topilmadi."

        javob = (
            f"📅 *{today} – soat {BELGILANGAN_SOAT} holatiga:*\n"
            f"🏢 *Filial:* {row_now['filial nomi']}\n"
            f"👤 *Xodim:* {row_now['xodim f.i.o.']}\n"
            f"📋 *Plan:* {int(row_now['plan']):,} so'm\n"
            f"❗ Qarzdorlar soni: {int(row_now['qarzdorlar soni'])} ta\n"
            f"💰 Qarzdorlar summasi: {int(row_now['qarzdorlar summasi']):,} so‘m\n"
            f"✅ Bajarildi: {int(row_now['bajarildi summada']):,} so‘m\n"
            f"📊 Bajarildi foizda: {float(row_now['bajarildi foizda']):.2f}%\n"
            f"📈 Prognoz: {float(row_now['prognoz (%)']):.2f}%\n\n"
            f"🥇 Umumiy reyting: {reyting_umumiy}-o‘rin\n"
            f"🏢 Filial reyting: {reyting_filial}-o‘rin"
            f"{compare_text}"
        ).replace(",", " ")
        await bot.send_message(chat_id=user_id, text=javob, parse_mode="Markdown")
    except Exception as e:
        await bot.send_message(chat_id=user_id, text=f"⚠️ Xatolik: {str(e)}")

async def send_daily_report():
    for user_id, login in user_login_map.items():
        await send_personal_report(user_id, login)

async def main():
    scheduler.add_job(send_daily_report, "cron", hour=10, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
