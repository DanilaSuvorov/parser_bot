import asyncio
import logging
from telethon import TelegramClient, events
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# 🔹 Данные Telegram API (получить на https://my.telegram.org/apps)
API_ID = 27771899  # Замени на свой API_ID
API_HASH = "79a67124f8aa60638bc5bb4b8e650027"  # Замени на свой API_HASH
PHONE_NUMBER = "+79263676550"  # Твой номер телефона

# 🔹 Данные для бота
BOT_TOKEN = "7824768301:AAGfUdrjnWNFrg5n3p7eIpN7CYAszQHpqRU"

# 🔹 Мониторинг чатов и каналов (ID или username)
MONITORED_CHATS = [
    -1002005877458, -1001099860397, -1001211876896,
    -1001498653424, -1002409669849, -1001202159807, -1001581728407
]

# 🔹 Ключевые слова
KEYWORDS = {"рубл", "госдум", "трамп", "путин", "ввел", "власт", "Россия"}

# 🔹 Ссылка на техподдержку
SUPPORT_CHAT_LINK = "https://t.me/suvorov_danila"

# 🔹 Логирование
logging.basicConfig(level=logging.INFO)

# 🔹 Создаем Telethon-клиент (работает от имени пользователя)
client = TelegramClient("user_session", API_ID, API_HASH)

# 🔹 Создаем бота Aiogram
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# 🔹 Список подписанных пользователей
subscribed_users = set()

async def get_chat_names():
    """ Получает названия и ссылки на чаты/каналы """
    chat_names = []
    for chat_id in MONITORED_CHATS:
        try:
            chat = await client.get_entity(chat_id)
            chat_link = f"https://t.me/{chat.username}" if getattr(chat, 'username', None) else "нет ссылки"
            chat_names.append(f"{chat.title} ({chat_link})")
        except Exception as e:
            logging.error(f"Ошибка получения данных чата {chat_id}: {str(e)}")
            chat_names.append(f"Не удалось получить название для {chat_id}")
    return chat_names

@dp.message(CommandStart())
async def start(message: Message):
    """ Добавляет пользователя в список подписчиков и отправляет приветственное сообщение """
    user_id = message.from_user.id
    subscribed_users.add(user_id)  # Добавляем пользователя в список

    chat_names = await get_chat_names()
    chat_list = "\n".join(chat_names)
    keywords_list = ", ".join(KEYWORDS)

    response = (f"✅ <b>Вы подписались на уведомления!</b>\n\n"
                f"📢 <b>Мониторятся чаты и каналы:</b>\n{chat_list}\n\n"
                f"🔍 <b>Ключевые слова:</b> {keywords_list}")

    # 🔹 Reply-кнопки
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🆘 Техподдержка")]],
        resize_keyboard=True
    )

    await message.answer(response, reply_markup=keyboard, parse_mode="HTML")

@dp.message(lambda message: message.text == "🆘 Техподдержка")
async def support(message: Message):
    """ Отправляет ссылку на техподдержку """
    await message.answer(f"Для связи с техподдержкой перейдите по ссылке: {SUPPORT_CHAT_LINK}")

@client.on(events.NewMessage(chats=MONITORED_CHATS))
async def monitor_messages(event):
    """ Обрабатывает новые сообщения в мониторимых чатах и отправляет подписчикам """
    message_text = event.message.text.lower() if event.message.text else ""
    if any(keyword in message_text for keyword in KEYWORDS):
        sender = await event.get_sender()
        chat = await event.get_chat()
        
        # Определяем ссылку на сообщение
        if event.is_channel:
            message_link = f"https://t.me/{chat.username}/{event.message.id}" if chat.username else f"https://t.me/c/{chat.id}/{event.message.id}"
            source_info = f"📢 Канал: <b>{chat.title}</b>\n<a href='{message_link}'>Открыть сообщение</a>\n"
        else:
            sender_name = f"{sender.first_name} {sender.last_name or ''}".strip()
            sender_username = f"(@{sender.username})" if sender.username else ""
            message_link = f"https://t.me/{chat.username}/{event.message.id}" if chat.username else "нет ссылки"
            source_info = f"👤 Отправитель: <b>{sender_name}</b> {sender_username}\n<a href='{message_link}'>Открыть сообщение</a>\n"

        alert_text = f"🔍 <b>Найдено совпадение!</b>\n\n{source_info}\n{event.message.text}"

        # Отправляем сообщение ВСЕМ подписанным пользователям
        for user_id in subscribed_users:
            try:
                await bot.send_message(user_id, alert_text, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Ошибка отправки пользователю {user_id}: {e}")

async def main():
    """ Запуск Telethon-клиента и бота """
    await client.start(PHONE_NUMBER)  # Вход через номер телефона
    await dp.start_polling(bot)
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())

