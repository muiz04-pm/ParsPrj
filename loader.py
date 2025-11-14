import logging
import random
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import asyncio

API_TOKEN = '8560047195:AAGwTGKGON_HtET7yHX5xwMCzffdrx8DOpY'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Статистика и данные
stats = {"users_started": set(), "total_messages": 0}
user_scores = {}

# Существующие игры
guess_games = {}
hangman_games = {}

# Новые игры
bulls_games = {}      # {user_id: {"secret": str, "length": int, "difficulty": str}}
emoji_games = {}      # {user_id: {"answer": str, "emoji_str": str, "difficulty": str}}

# Слова для эмодзи-игры
EMOJI_QUIZ = {
    "easy": [
        ("кот", "🐱"),
        ("дом", "🏠"),
        ("солнце", "☀️"),
        ("книга", "📚"),
        ("машина", "🚗"),
    ],
    "medium": [
        ("домашний кот", "🏠 + 🐱"),
        ("летающая тарелка", "🛸"),
        ("огненный шар", "🔥 + ⚽"),
        ("черный кофе", "☕ + ⚫"),
    ],
    "hard": [
        ("голодные игры", "🍽️ + 🎮"),
        ("искусственный интеллект", "🤖 + 🧠"),
        ("интернет вещей", "🌐 + 📦 + 📱"),
        ("виртуальная реальность", "🕶️ + 🌐"),
    ]
}

# Слова для виселицы
HANGMAN_WORDS = {
    "easy": ["кот", "дом", "сок", "лук", "сон"],
    "medium": ["книга", "машина", "пирог", "окно", "лес"],
    "hard": ["электричество", "библиотека", "предприниматель"]
}

# === ГЕНЕРАЦИЯ ЧИСЛА БЕЗ ПОВТОРОВ (для "Быков и коров") ===
def generate_unique_number(length: int) -> str:
    digits = list("0123456789")
    random.shuffle(digits)
    if digits[0] == "0" and length > 1:
        # избегаем числа с ведущим нулём
        non_zero = [d for d in digits if d != "0"]
        if non_zero:
            first = random.choice(non_zero)
            digits.remove(first)
            result = [first] + digits[:length - 1]
            return "".join(result)
    return "".join(digits[:length])

# === КЛАВИАТУРЫ ===
def get_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔢 Угадай число", callback_data="select_guess")],
        [InlineKeyboardButton(text="🐮 Быки и коровы", callback_data="select_bulls")],
        [InlineKeyboardButton(text="💀 Виселица", callback_data="select_hangman")],
        [InlineKeyboardButton(text="🎭 Угадай эмодзи", callback_data="select_emoji")],
        [InlineKeyboardButton(text="🪨 КНБ", callback_data="game_rps"),
         InlineKeyboardButton(text="🪙 Монетка", callback_data="game_flip")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")]
    ])

def get_difficulty_menu(game_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Лёгкий", callback_data=f"diff_{game_type}_easy")],
        [InlineKeyboardButton(text="🟡 Средний", callback_data=f"diff_{game_type}_medium")],
        [InlineKeyboardButton(text="🔴 Сложный", callback_data=f"diff_{game_type}_hard")],
        [InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_menu")]
    ])

# === ОСНОВНОЕ МЕНЮ ===
async def show_main_menu(message: types.Message):
    await message.answer("🎮 Выбери игру:", reply_markup=get_main_menu())

@dp.message(CommandStart())
async def start(message: types.Message):
    stats["users_started"].add(message.from_user.id)
    await message.answer(f"👋 Привет, {message.from_user.full_name}!")
    await show_main_menu(message)

# === ВЫБОР ИГРЫ → УРОВЕНЬ ===
@dp.callback_query(lambda c: c.data.startswith("select_"))
async def select_difficulty(callback: types.CallbackQuery):
    game = callback.data.split("_", 1)[1]
    await callback.message.answer("Выбери уровень сложности:", reply_markup=get_difficulty_menu(game))
    await callback.answer()

# === ЗАПУСК ИГР С УРОВНЯМИ ===
@dp.callback_query(lambda c: c.data.startswith("diff_"))
async def start_game_with_difficulty(callback: types.CallbackQuery):
    _, game, difficulty = callback.data.split("_")
    user_id = callback.from_user.id

    if game == "guess":
        ranges = {"easy": (1, 10), "medium": (1, 50), "hard": (1, 100)}
        attempts = {"easy": 5, "medium": 6, "hard": 7}
        low, high = ranges[difficulty]
        secret = random.randint(low, high)
        guess_games[user_id] = {"number": secret, "attempts_left": attempts[difficulty], "max_attempts": attempts[difficulty], "difficulty": difficulty}
        await callback.message.answer(f"🔢 Угадай число от {low} до {high}!\nУ тебя {attempts[difficulty]} попыток.")

    elif game == "hangman":
        word = random.choice(HANGMAN_WORDS[difficulty])
        attempts = {"easy": 8, "medium": 6, "hard": 4}
        hangman_games[user_id] = {"word": word, "guessed": set(), "attempts_left": attempts[difficulty], "difficulty": difficulty}
        display = "⬜" * len(word)
        await callback.message.answer(f"💀 Виселица ({difficulty})\nСлово: {display}\nПопыток: {attempts[difficulty]}\nПрисылай буквы!")

    elif game == "bulls":
        length = {"easy": 3, "medium": 4, "hard": 5}[difficulty]
        secret = generate_unique_number(length)
        bulls_games[user_id] = {"secret": secret, "length": length, "difficulty": difficulty}
        await callback.message.answer(f"🐮 Быки и коровы ({difficulty})\nЗагадано {length}-значное число (без повторов).\nНапиши свой вариант!")

    elif game == "emoji":
        quiz = random.choice(EMOJI_QUIZ[difficulty])
        answer, emoji_str = quiz
        emoji_games[user_id] = {"answer": answer, "emoji_str": emoji_str, "difficulty": difficulty}
        await callback.message.answer(f"🎭 Угадай слово по эмодзи:\n\n{emoji_str}\n\nНапиши ответ:")

    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await show_main_menu(callback.message)
    await callback.answer()

# === ПРОСТЫЕ ИГРЫ (БЕЗ УРОВНЕЙ) ===
@dp.callback_query(lambda c: c.data == "game_rps")
async def rps_info(callback: types.CallbackQuery):
    await callback.message.answer("🪨 Напиши:\n/rps камень\n/rps ножницы\n/rps бумага")
    await callback.answer()

@dp.callback_query(lambda c: c.data == "game_flip")
async def flip_coin(callback: types.CallbackQuery):
    result = random.choice(["орёл", "решка"])
    emoji = "🦅" if result == "орёл" else "🪙"
    await callback.message.answer(f"{emoji} Выпал {result}!")
    await show_main_menu(callback.message)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "show_stats")
async def show_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    score = user_scores.get(user_id, 0)
    await callback.message.answer(
        f"👥 Пользователей: {len(stats['users_started'])}\n"
        f"📨 Сообщений: {stats['total_messages']}\n"
        f"🏆 Твои очки: {score}"
    )
    await callback.answer()

# === /rps ===
@dp.message(Command("rps"))
async def play_rps(message: types.Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("🪨 Используй: /rps камень, ножницы или бумага")
        return
    user = parts[1].strip().lower()
    if user not in ["камень", "ножницы", "бумага"]:
        await message.answer("❓ Только: камень, ножницы, бумага")
        return
    bot_choice = random.choice(["камень", "ножницы", "бумага"])
    if user == bot_choice:
        res = "🤝 Ничья"
    elif (user == "камень" and bot_choice == "ножницы") or \
         (user == "ножницы" and bot_choice == "бумага") or \
         (user == "бумага" and bot_choice == "камень"):
        res = "🎉 Ты победил!"
        user_scores[message.from_user.id] = user_scores.get(message.from_user.id, 0) + 1
    else:
        res = "😢 Я победил"
    await message.answer(f"Ты: {user}\nЯ: {bot_choice}\n{res}")
    await show_main_menu(message)

# === ОБРАБОТКА ИГРОВЫХ СООБЩЕНИЙ ===
@dp.message()
async def handle_game_input(message: types.Message):
    user_id = message.from_user.id

    # Угадай число
    if user_id in guess_games:
        try:
            guess = int(message.text.strip())
            game = guess_games[user_id]
            if guess == game["number"]:
                pts = {"easy": 1, "medium": 2, "hard": 3}[game["difficulty"]]
                user_scores[user_id] = user_scores.get(user_id, 0) + pts
                await message.answer(f"✅ Верно! +{pts} очк{('о' if pts == 1 else 'а' if pts < 5 else 'ов')}")
                del guess_games[user_id]
                await show_main_menu(message)
            else:
                game["attempts_left"] -= 1
                if game["attempts_left"] <= 0:
                    await message.answer(f"💀 Конец. Было: {game['number']}")
                    del guess_games[user_id]
                    await show_main_menu(message)
                else:
                    hint = "⬆️ Больше!" if guess < game["number"] else "⬇️ Меньше!"
                    await message.answer(f"{hint} Осталось: {game['attempts_left']}")
            return
        except ValueError:
            await message.answer("🔢 Введи число!")
            return

    # Быки и коровы
    if user_id in bulls_games:
        game = bulls_games[user_id]
        guess = message.text.strip()
        secret = game["secret"]
        length = game["length"]

        if not guess.isdigit() or len(guess) != length or len(set(guess)) != length:
            await message.answer(f"❌ Число должно быть {length}-значным и без повторяющихся цифр.")
            return

        bulls = sum(1 for i in range(length) if guess[i] == secret[i])
        cows = sum(1 for c in guess if c in secret) - bulls

        if bulls == length:
            pts = {"easy": 2, "medium": 3, "hard": 5}[game["difficulty"]]
            user_scores[user_id] = user_scores.get(user_id, 0) + pts
            await message.answer(f"🎉 Победа! Загадано: {secret}\n+{pts} очков!")
            del bulls_games[user_id]
            await show_main_menu(message)
        else:
            await message.answer(f"Быки: {bulls}, Коровы: {cows}")

        return

    # Виселица
    if user_id in hangman_games and len(message.text.strip()) == 1:
        letter = message.text.strip().lower()
        game = hangman_games[user_id]
        word = game["word"]
        if letter in game["guessed"]:
            await message.answer("🔁 Уже пробовал.")
        elif letter in word:
            game["guessed"].add(letter)
            await message.answer("✅ Есть!")
        else:
            game["attempts_left"] -= 1
            await message.answer(f"❌ Нет. Осталось: {game['attempts_left']}")

        display = "".join([c if c in game["guessed"] else "⬜" for c in word])
        await message.answer(f"Слово: {display}")

        if all(c in game["guessed"] for c in word):
            pts = {"easy": 1, "medium": 2, "hard": 3}[game["difficulty"]]
            user_scores[user_id] += pts
            await message.answer(f"🎉 Спасён! +{pts} очк{('о' if pts == 1 else 'а' if pts < 5 else 'ов')}")
            del hangman_games[user_id]
            await show_main_menu(message)
        elif game["attempts_left"] <= 0:
            await message.answer(f"💀 Повешен! Слово: {word}")
            del hangman_games[user_id]
            await show_main_menu(message)
        return

    # Угадай эмодзи
    if user_id in emoji_games:
        game = emoji_games[user_id]
        user_answer = message.text.strip().lower()
        correct = game["answer"].lower()
        if user_answer == correct:
            pts = {"easy": 1, "medium": 2, "hard": 3}[game["difficulty"]]
            user_scores[user_id] = user_scores.get(user_id, 0) + pts
            await message.answer(f"🎭 Верно! Это: {game['answer']}!\n+{pts} очк{('о' if pts == 1 else 'а' if pts < 5 else 'ов')}")
            del emoji_games[user_id]
            await show_main_menu(message)
        else:
            await message.answer("❌ Не угадал. Попробуй ещё!")
        return

    # Эхо
    if message.chat.type == "private" and message.text and not message.text.startswith("/"):
        stats["total_messages"] += 1
        await message.answer(f"🔁 {message.text}")

# === ПРОЧИЕ КОМАНДЫ ===
@dp.message(Command("me"))
async def me(message: types.Message):
    u = message.from_user
    await message.answer(f"👤 {u.full_name}\nID: {u.id}\nUsername: {f'@{u.username}' if u.username else 'нет'}")

@dp.message(Command("time"))
async def time(message: types.Message):
    await message.answer(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

@dp.message(Command("id"))
async def get_id(message: types.Message):
    await message.answer(f"Ваш ID: `{message.from_user.id}`", parse_mode="Markdown")

# === ЗАПУСК ===
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())