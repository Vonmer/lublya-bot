import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta

API_TOKEN = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

# Словарь для отслеживания, выпила ли девушка таблетки
user_status = {}

# === Команда /start ===
@dp.message(Command("start"))
async def start_command(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[types.KeyboardButton(text="🕖 Поставить напоминание")]]
    )
    await message.answer(
        "Привет, ❤️\nЯ буду напоминать тебе пить таблетки каждый день!\n"
        "Хочешь, я установлю напоминание на 7:00 утра?",
        reply_markup=keyboard
    )

# === Кнопка «Поставить напоминание» ===
@dp.message(lambda m: m.text == "🕖 Поставить напоминание")
async def set_reminder(message: types.Message):
    chat_id = message.chat.id
    user_status[chat_id] = False  # Ещё не выпила

    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    reminder_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7, 0)

    scheduler.add_job(
        send_reminder,
        "date",
        run_date=reminder_time,
        args=[chat_id]
    )

    await message.answer("Хорошо 😊 Я напомню тебе завтра в 7:00 утра 💊")

# === Отправка напоминания ===
async def send_reminder(chat_id):
    if user_status.get(chat_id) is None:
        user_status[chat_id] = False

    # Отправляем сообщение
    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[[types.KeyboardButton(text="💊 Выпила")]]
    )
    await bot.send_message(chat_id, "Доброе утро ☀️\nНе забудь выпить таблетки 💊", reply_markup=keyboard)

    # Если не нажала — повторяем каждые 3 минуты
    scheduler.add_job(repeat_reminder, "interval", minutes=3, args=[chat_id], id=f"repeat_{chat_id}")

# === Повторное напоминание каждые 3 минуты ===
async def repeat_reminder(chat_id):
    if not user_status.get(chat_id, False):
        await bot.send_message(chat_id, "Напоминаю 💊 — пора выпить таблетки!")
    else:
        # Если выпила — останавливаем повтор
        try:
            scheduler.remove_job(f"repeat_{chat_id}")
        except:
            pass

# === Кнопка «Выпила 💊» ===
@dp.message(lambda m: m.text == "💊 Выпила")
async def took_pill(message: types.Message):
    chat_id = message.chat.id
    user_status[chat_id] = True

    try:
        scheduler.remove_job(f"repeat_{chat_id}")
    except:
        pass

    await message.answer(
        "Молодец ❤️ Я горжусь тобой!\n"
        "Я снова напомню тебе завтра в 7:00 🌞"
    )

    # Ставим новое напоминание на завтра
    tomorrow = datetime.now() + timedelta(days=1)
    reminder_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 7, 0)

    scheduler.add_job(send_reminder, "date", run_date=reminder_time, args=[chat_id])

# === Запуск бота ===
async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())