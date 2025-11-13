import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime
import asyncio

# Токен (в реальном проекте лучше хранить в .env)
API_TOKEN = '8560047195:AAGwTGKGON_HtET7yHX5xwMCzffdrx8DOpY'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Статистика
stats = {
    "users_started": set(),
    "total_messages": 0
}

# Создаём клавиатуру
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/help"), KeyboardButton(text="/stats")],
        [KeyboardButton(text="/time"), KeyboardButton(text="/me")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# /start
@dp.message(CommandStart())
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    stats["users_started"].add(user_id)
    await message.answer(
        f"👋 Привет, {full_name}!\nЯ — умный эхо-бот с кнопками и статистикой.\nНажми на команду ниже!",
        reply_markup=main_kb
    )

# /help
@dp.message(Command("help"))
async def send_help(message: types.Message):
    await message.answer(
        "🛠️ Доступные команды:\n"
        "/start — начать\n"
        "/help — эта справка\n"
        "/stats — статистика\n"
        "/time — текущее время\n"
        "/me — твоя информация\n"
        "/id — только твой ID"
    )

# /id
@dp.message(Command("id"))
async def send_id(message: types.Message):
    await message.answer(f"Ваш ID: `{message.from_user.id}`", parse_mode="Markdown")

# /me
@dp.message(Command("me"))
async def send_me(message: types.Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "нет"
    await message.answer(
        f"👤 Ваш профиль:\n"
        f"Имя: {user.full_name}\n"
        f"ID: {user.id}\n"
        f"Username: {username}"
    )

# /time
@dp.message(Command("time"))
async def send_time(message: types.Message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await message.answer(f"🕒 Текущее время (UTC+0): {now}")

# /stats
@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    await message.answer(
        f"📊 Статистика:\n"
        f"👥 Уникальных пользователей: {len(stats['users_started'])}\n"
        f"📨 Обработано сообщений: {stats['total_messages']}"
    )

# Echo — только в личке и только для текста
@dp.message()
async def echo(message: types.Message):
    # Игнорируем всё, кроме личных текстовых сообщений
    if message.chat.type != "private" or not message.text:
        return

    # Не обрабатываем команды (они уже обработаны выше)
    if message.text.startswith("/"):
        return

    stats["total_messages"] += 1
    logging.info(f"Пользователь {message.from_user.id} написал: {message.text}")
    await message.answer(f"🔁 Ты написал: {message.text}")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())