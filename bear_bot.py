import asyncio
import random
import os
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import Message

BOT_TOKEN = os.getenv("8933271948:AAGH1fKo2476PybeLRtI8OBIt47j9sND7-I")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6183813562"))
GIFT_ID = os.getenv("GIFT_ID", "")

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

def init_db():
    conn = sqlite3.connect('/tmp/bear_bot.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    cur.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
                ('chance', '6'))
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = sqlite3.connect('/tmp/bear_bot.db')
    cur = conn.cursor()
    cur.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else default

def set_setting(key, value):
    conn = sqlite3.connect('/tmp/bear_bot.db')
    cur = conn.cursor()
    cur.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
                (key, str(value)))
    conn.commit()
    conn.close()

@dp.message(Command("start", "help"))
async def start_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "🐻 <b>Бот розыгрыша мишек</b>\n\n"
        "<b>Команды:</b>\n"
        "/chance — текущий шанс\n"
        "/setchance N — установить шанс (0-100)\n"
        "/balance — баланс звёзд бота\n"
        "/gifts — список подарков\n"
        "/chatid — ID чата\n"
        "/myid — твой ID"
    )

@dp.message(Command("chance"))
async def chance_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    chance = get_setting('chance', '6')
    await message.answer(f"🎲 Текущий шанс: <b>{chance}%</b>")

@dp.message(Command("setchance"))
async def set_chance_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    args = message.text.split()
    if len(args) != 2:
        await message.answer("⚠️ Использование: <code>/setchance 10</code>")
        return
    try:
        new_chance = float(args[1])
        if new_chance < 0 or new_chance > 100:
            await message.answer("⚠️ Шанс должен быть от 0 до 100")
            return
        set_setting('chance', new_chance)
        await message.answer(f"✅ Шанс установлен: <b>{new_chance}%</b>")
    except ValueError:
        await message.answer("⚠️ Введите число от 0 до 100")

@dp.message(Command("balance"))
async def balance_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        balance = await bot.get_star_balance()
        stars = balance.amount
        # Считаем сколько мишек можно отправить
        bears_left = stars // 15
        await message.answer(
            f"⭐ <b>Баланс бота:</b> {stars} звёзд\n"
            f"🧸 Можно отправить мишек: ~{bears_left}"
        )
    except Exception as e:
        await message.answer(f"⚠️ Не удалось получить баланс: {e}")

@dp.message(Command("gifts"))
async def gifts_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        gifts = await bot.get_available_gifts()
        lines = []
        for g in gifts.gifts:
            lines.append(f"• <code>{g.id}</code> — {g.name} ({g.star_count}⭐)")
        await message.answer("🎁 <b>Доступные подарки:</b>\n\n" + "\n".join(lines))
    except Exception as e:
        await message.answer(f"Ошибка: {e}")

@dp.message(Command("chatid"))
async def chatid_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"🆔 ID чата: <code>{message.chat.id}</code>")

@dp.message(Command("myid"))
async def myid_cmd(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(f"🆔 Твой ID: <code>{message.from_user.id}</code>")

@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def monitor_messages(message: Message):
    if message.from_user.is_bot:
        return
    if message.text and message.text.startswith('/'):
        return

    chance = float(get_setting('chance', '6'))

    if random.random() * 100 < chance:
        winner = message.from_user
        winner_name = winner.first_name or winner.username or "победитель"

        try:
            await bot.send_gift(
                user_id=winner.id,
                gift_id=GIFT_ID,
                text="Поздравляем! 🧸"
            )
            await message.answer(
                f"🧸 <a href='tg://user?id={winner.id}'>{winner_name}</a>, "
                f"выиграл мишку! 🧸"
            )
        except Exception as e:
            print(f"Ошибка отправки подарка: {e}")

async def main():
    init_db()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())