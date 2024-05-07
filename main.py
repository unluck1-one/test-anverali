import telebot
from telebot import types as t
import psycopg2
from psycopg2 import Error
from config import *
import random
import re

bot = telebot.TeleBot(api)

@bot.message_handler(commands=["start", "help"])
def welcome(message):
    hello = open(random.choice([r"./sticker/cherryhello.tgs", r"./sticker/dragonhello.tgs", r"./sticker/duckhello.tgs"]), "rb")
    bot.send_sticker(message.chat.id, hello)
    bot.send_message(message.chat.id, "Привет! Я помогу тебе с созданием задач. Список доступных команд:<i>\n/add\n/tsk\n/del</i>", parse_mode="HTML")
    hello.close()

@bot.message_handler(commands=["add"])
def create_task(message):
    name = bot.send_message(message.chat.id, "Введи название задачи (макс. 64 символа, только буквы и цифры, /cancel для отмены):")
    bot.register_next_step_handler(name, name_task)

def name_task(message):
    pattern = r'^[\da-zA-Zа-яА-ЯёЁ \u00A0]+$'
    result = re.compile(pattern)
    if message.text == "/cancel":
        bot.send_message(message.chat.id, "Операция отменена")
    else:
        try:
            conn = psycopg2.connect(conDet)
            cur = conn.cursor()
            if result.fullmatch(message.text):
                cur.execute(f"SELECT name_task FROM tasks WHERE id_tg = {message.from_user.id}")
                a = cur.fetchall()
                if len(a) <= 10:
                    cur.execute(f"INSERT INTO tasks (id_tg, name_task) VALUES ({message.from_user.id}, '{message.text}')")
                    conn.commit()
                else:
                    raise CreateError
            else:
                raise CreateError
        except Error as _err:
            err = open("./sticker/comaruerror.webm", "rb")
            bot.send_sticker(message.chat.id, err)
            bot.send_message(message.chat.id, "Произошла неизвестная ошибка. Возможно, у вас слишком длинная задача...")
            print("\n")
            print(_err)
            print("\n")
            err.close()
        except Exception as CreateError:
            bot.send_message(message.chat.id, "Либо у вас запрещенные символы в названии, либо вы пытаетесь создать 11 задачу...")
        else:
            bot.send_message(message.chat.id, "Задача создана!")
        finally:
            cur.close()
            conn.close()

@bot.message_handler(commands=["tsk"])
def tasks(message):
    conn = psycopg2.connect(conDet)
    cur = conn.cursor()
    cur.execute(f"SELECT name_task FROM tasks WHERE id_tg = {message.from_user.id}")
    tasks = cur.fetchall()
    if len(tasks) == 0:
        bot.send_message(message.chat.id, "У вас еще нет задач!")
    else:
        bot.send_message(message.chat.id, "Ваши задачи: \n" + "\n".join(row[0] for row in tasks))

@bot.message_handler(commands=["del"])
def choice(message):
    conn = psycopg2.connect(conDet)
    cur = conn.cursor()
    cur.execute(f"SELECT name_task FROM tasks WHERE id_tg = {message.from_user.id}")
    a = cur.fetchall()
    inKeyboard = t.InlineKeyboardMarkup(row_width=2)
    if len(a) == 0:
        bot.send_message(message.chat.id, "У вас еще нет задач!")
    else:
        for row in a:
            button_text = row[0]
            inKeyboard.add(t.InlineKeyboardButton(text=button_text, callback_data=button_text))
        inKeyboard.add(t.InlineKeyboardButton("Отмена ❌", callback_data="Отмена"))
        bot.send_message(message.chat.id, "Выберете, какую задачу удалить", reply_markup=inKeyboard)
    cur.close()
    conn.close()

@bot.callback_query_handler(func=lambda call: call.data)
def deleting(call):
    try:
        conn = psycopg2.connect(conDet)
        cur = conn.cursor()
        if call.data == "Отмена":
            raise ex
        elif call.data:
            cur.execute(f"DELETE FROM tasks WHERE name_task = %s AND id_tg = %s", (call.data, call.from_user.id))
            conn.commit()
    except Error as _err:
        err = open("./sticker/comaruerror.webm", "rb")
        bot.send_sticker(call.message.chat.id, err)
        bot.edit_message_text("Произошла неизвестная ошибка. Попробуйте позже...", call.message.chat.id, call.message.id - 1)
        print(_err)
        err.close()
    except Exception as ex:
        bot.edit_message_text("Операция отменена", call.message.chat.id, call.message.id)
    else:
        bot.edit_message_text("Задача удалена!", call.message.chat.id, call.message.id)
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(3)
            print(e)
