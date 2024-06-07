import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
# ROUTERS
from handlers import router
# ROUTERS

config = Config()


async def main():
    bot = Bot(token=config.get_bot_token(), parse_mode='HTML')
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_routers(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == '__main__':
    config.create_config()
    config.get_lines()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
