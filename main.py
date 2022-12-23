import datetime
import sys
import time

from telebot.async_telebot import AsyncTeleBot
import asyncio
from db_interactor import DBInteractor
from constants import *

bot = AsyncTeleBot(TOKEN)
db_interactor: DBInteractor = asyncio.run(DBInteractor.create())


def delete_first_word(string, symbol=" "):
    return string.split(symbol, 1)


# process /start
@bot.message_handler(commands=["start"])
async def start(m):
    print(m.chat.id)
    await bot.send_message(m.chat.id, START_STRING)


# process /add_deadline dd:mm:yyyy hh:mm <desc>
@bot.message_handler(commands=["add_deadline"])
async def add_deadline(message):
    s = message.text
    try:
        _, args = delete_first_word(s)
        dmy, args = delete_first_word(args)
        day = dmy
        if "." in dmy:
            day, dmy = delete_first_word(dmy, symbol=".")
        else:
            dmy = ""
        month = datetime.datetime.now().month
        if "." in dmy:
            month, dmy = delete_first_word(dmy, symbol=".")
        year = dmy
        if not year:
            year = datetime.datetime.now().year
        hm = "23:59"
        if " " in args:
            hm, args = delete_first_word(args)
        hour, hm = delete_first_word(hm, ":")
        minute = hm
        desc = args
        dt = datetime.datetime(year=int(year), month=int(month), day=int(day), hour=int(hour),
                               minute=int(minute))
        # if dt - datetime.timedelta(hours=3) < datetime.datetime.now():
        #     await bot.send_message(message.chat.id,
        #                            'Дедлайн уже слишком скоро! Возможно лучше выйти из телеграма и начать уже что то делать)')
        #     return
        await db_interactor.create_deadline(message.chat.id, desc, dt)
    except:
        await bot.send_message(message.chat.id, 'Не правильный формат команды')
        return
    await bot.send_message(message.chat.id, f'Успешно создан дедлайн "{desc}"')


async def send_passed_deadlines():
    li = await db_interactor.get_overdue_weak()
    for user_id, desc, date in li:
        await bot.send_message(user_id, "Мягкое напоминание про дедлайн " + desc)
    li = await db_interactor.get_overdue_strong()
    for user_id, desc, date in li:
        await bot.send_message(user_id, "СРОЧНО! Жесткое напоминание про дедлайн " + desc + " " + str(
            date + datetime.timedelta(hours=2)))


# process /deadlines_list
@bot.message_handler(commands=["deadlines_list"])
async def deadlines_list(msg):
    li = await db_interactor.deadlines_list(msg.chat.id)
    await bot.send_message(msg.chat.id,
                           "Список дедлайнов:\n" + "\n".join(map(lambda x: x[0] + " в " + str(x[1]), li)))


# process /closest_deadline
@bot.message_handler(commands=["closest_deadline"])
async def closest_deadline(msg):
    li = await db_interactor.deadlines_list(msg.chat.id)
    opt = 0
    for i in range(len(li)):
        if li[opt][1] > li[i][1]:
            opt = i
    await bot.send_message(msg.chat.id,
                           "Ближайший дедлайн:\n" + f"{li[opt[0]]} в {li[opt[1]]}")


# process /procrastinate
@bot.message_handler(commands=["procrastinate"])
async def procrastinate(msg):
    await db_interactor.shift_all_until(datetime.datetime.now() + datetime.timedelta(days=1))


async def main():
    await db_interactor.create_tables_if_not_exists()
    await bot.polling(none_stop=True, interval=0)


async def notify():
    while True:
        print("Started sending...", end="")
        await send_passed_deadlines()
        await db_interactor.delete_overdue()
        print("Finished!")
        await asyncio.sleep(10)


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    background_tasks = set()
    main_task = loop.create_task(main())
    background_tasks.add(main_task)
    main_task.add_done_callback(background_tasks.discard)

    task2 = loop.create_task(notify())
    background_tasks.add(task2)
    task2.add_done_callback(background_tasks.discard)

    loop.run_until_complete(asyncio.wait(background_tasks))
    loop.close()
