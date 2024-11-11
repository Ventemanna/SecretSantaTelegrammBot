import sqlite3
import random
from telebot import types, telebot
import config

bot = telebot.TeleBot(config.BOT_TOKEN)

conn = sqlite3.connect('db/database.db', check_same_thread=False)
cursor = conn.cursor()


@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Учавствовать!")
    btn2 = types.KeyboardButton("Участники")
    btn4 = types.KeyboardButton("Описание")
    btn3 = types.KeyboardButton("Refresh")
    btn5 = types.KeyboardButton("Узнать кто у меня")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id, 'Привет! Это Бот для тайного санты', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def func(message):
    print(message.text)
    if message.text == "Учавствовать!":
        add_student_to_db(message)
    elif message.text == "Участники":
        print_students(message)
    elif message.text == "Refresh":
        start_message(message)
    elif message.text == "Сгенерировать":
        generate(message)
    elif message.text == "/addDescription" or message.text == "Описание":
        get_description(message)
    elif message.text == "/resetDB":
        reset_db(message)
    elif message.text == "Узнать кто у меня":
        print_student(message)
    else:
        bot.send_message(message.chat.id, f"{message.from_user.first_name}, не балуйся!")


def print_student(message):
    if generate_allow() == 0:
        cursor.execute("SELECT gift_to FROM Student21 WHERE id_student = (?)", (message.from_user.id,))
        gift_to = (cursor.fetchall()[0])[0]
        cursor.execute("SELECT id, name, username, description FROM Student21 WHERE id = (?)", (gift_to,))
        student = cursor.fetchall()[0]
        bot.send_message(message.from_user.id, f'{student[0]}. <a href="https://t.me/{student[2]}">{student[1]}</a>', parse_mode="HTML")
        if student[3] is None:
            bot.send_message(message.from_user.id, f"{student[1]} надеется на твою фантазию!")
        else:
            bot.send_message(message.from_user.id, f'Небольшое пожелание от {student[1]}:\n{student[3]}')
    else:
        bot.send_message(message.from_user.id, "Тайный санта еще не распределен")


def generate(message):
    if generate_allow():
        reset_db(message)
        select_random(message)
    else:
        bot.send_message(message.chat.id, 'Для каждого тайный санта подобран')


def generate_allow():
    cursor.execute("SELECT COUNT(id) FROM Student21 WHERE is_available = 1")
    without_santas = (cursor.fetchall()[0])[0]
    print(without_santas)
    if without_santas == 0:
        return 0
    return 1


@bot.message_handler(commands=['resetDB'])
def reset_db(message):
    cursor.execute("UPDATE Student21 SET gift_to = 0, is_available = 1")
    conn.commit()


def select_random(message):
    flag = 1
    cursor.execute("SELECT id, id_student, name FROM Student21")
    student_list = cursor.fetchall()
    print(student_list)
    for st in student_list:
        if is_available(st[1]):
            change_index(st, len(student_list))
    generate(message)

def change_index(student, counter: int):
    lenght = counter + 1
    while counter >= 0:
        index = random.randrange(1, lenght)

        if index != student[0] and check_student(index):
            add_gift_to(student, index)
            return 1
        counter -= 1
    return 0

def add_gift_to(student, index):
    cursor.execute(
        """UPDATE Student21 
    SET is_available = CASE WHEN id = (?) THEN 0 ELSE is_available END
    """, (index,))
    cursor.execute("""UPDATE Student21
    SET gift_to = CASE WHEN id = (?) THEN (?) ELSE gift_to END""", (student[0], index))
    conn.commit()



def check_student(index: int):
    cursor.execute("SELECT name FROM Student21 WHERE id = (?) AND is_available = 1", (index,))
    result = cursor.fetchall()
    if result is None:
        return 0
    return 1

def is_available(id_student: int):
    cursor.execute("SELECT name FROM Student21 WHERE id_student = (?) AND is_available = 1", (id_student,))
    is_true = cursor.fetchall()
    if is_true is None:
        return 0
    return 1


def print_students(message):
    cursor.execute("SELECT id, name, username FROM Student21")
    student_list = cursor.fetchall()
    if student_list is None:
        bot.send_message(message.from_user.id, 'Участников пока нет')
    else:
        for el in student_list:
            bot.send_message(message.from_user.id, f'{el[0]}. <a href="https://t.me/{el[2]}">{el[1]}</a>',
                             parse_mode="HTML")


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
        description = bot.send_message(message.from_user.id, 'Можешь написать что-нибудь для своего тайного санты')
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
