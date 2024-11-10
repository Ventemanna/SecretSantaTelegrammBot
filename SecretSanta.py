import sqlite3
from telebot import types, telebot

bot = telebot.TeleBot("7852960752:AAFeAMYv_PenQ5G2F2o2MFdoFczSjH7TDOI")

conn = sqlite3.connect('db/database.db', check_same_thread=False)
cursor = conn.cursor()


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Учавствовать!")
    btn2 = types.KeyboardButton("Участники")
    btn3 = types.KeyboardButton("Refresh")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, 'Добро пожаловать', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def func(message):
    if message.text == "Учавствовать!":
        add_student_to_db(message)
    elif message.text == "Участники":
        print_students(message)
    elif message.text == "Refresh":
        start_message(message)


def print_students(message):
    cursor.execute("SELECT id, name, username FROM Student21")
    student_list = cursor.fetchall()
    print(student_list)
    if student_list is None:
        bot.send_message(message.from_user.id, 'Участников пока нет')
    else:
        for el in student_list:
            bot.send_message(message.from_user.id, f'{el[0]}. <a href="https://t.me/{el[2]}">{el[1]}</a>', parse_mode="HTML")


@bot.message_handler(commands=['add'])
def add_student_to_db(message):
    bot.send_message(message.from_user.id, 'Теперь ты учавствуешь!')
    us_id = message.from_user.id
    us_name = message.from_user.first_name
    username = message.from_user.username
    description = message.text
    db_insert_values(id_student=us_id, name=us_name, username=username)


def db_insert_values(id_student: int, username: str, name: str):
    cursor.execute("INSERT OR IGNORE INTO Student21 (id_student, username, name) VALUES (?, ?, ?)",
                   (id_student, username, name))
    conn.commit()


def db_insert_description(message):
    description = message.text
    student_id = message.from_user.id
    cursor.execute('UPDATE Student21 SET description = (?) WHERE id_student = (?)', (description, student_id))
    conn.commit()


@bot.message_handler(commands=['addDescription'])
def get_description(message):
    exist_description = is_empty_description(message)
    if exist_description == 1:
        description = bot.send_message(message.from_user.id, 'Можешь написать что хочешь для своего тайного санты')
        bot.register_next_step_handler(description, db_insert_description)
    elif exist_description == 0:
        bot.send_message(message.from_user.id, 'У тебя уже есть описание!')


def is_empty_description(message):
    student_id = message.from_user.id
    cursor.execute('SELECT description FROM Student21 WHERE (?) = id_student LIMIT 1', [student_id])
    user_description = cursor.fetchall()
    if user_description:
        user_description = (user_description[0])[0]
    else:
        bot.send_message(message.from_user.id, 'Твоего имени нет в списках')
        return 2

    if user_description is None:
        return 1
    return 0


bot.polling(none_stop=True)
