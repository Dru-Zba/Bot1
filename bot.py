import telebot
import sqlite3
import config
import shelve
import random

bot = telebot.TeleBot(config.token)



print(bot.get_me)

def log(message, answer):
    print("\n -----")
    from datetime import datetime
    print(datetime.now())
    print("Сообщение от {0}. Текст - {1}".format(message.from_user.username,
                                                 message.text))
    print(answer)

@bot.message_handler(commands=['start'])
def say_hello(message):
    conn = sqlite3.connect(config.dbname)
    cursor = conn.cursor()
    cursor.execute("SELECT Name FROM Users WHERE Name = ?", (message.from_user.username,))
    result = cursor.fetchone()
    conn.commit()
    print(result)
    if result == None:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users Values (?,1)", (message.from_user.username,))
        conn.commit()
        conn.close()
        answer = '''Добрый день, уважаемый сотрудник!
Тебя приветствует бот по охране труда.
Тебе будут задаваться вопросы в тестовой форме. На каждый вопрос есть 4 варианта ответа. Будь внимателен! 
Набери команду /test, чтобы запустить тест по охране труда.'''
        bot.send_message(message.chat.id, answer)
        log(message, answer)
    else:
        answer = "Ты уже успешно зарегистрирован в боте. Набери команду /test,\nчтобы запустить тест по охране труда."
        bot.send_message(message.chat.id, answer)
        log(message, answer)
    conn.close()

@bot.message_handler(commands=['test'])
def pass_test(message):
    conn = sqlite3.connect(config.dbname)
    cursor = conn.cursor()
    conn.text_factory = str
    cursor.execute("SELECT id FROM Questions LIMIT 1")
    question_id = cursor.fetchone()
    cursor.execute("SELECT QuestionText FROM Questions LIMIT 1")
    question_text = cursor.fetchone()
    cursor.execute("SELECT RightAnswer FROM Questions LIMIT 1")
    question_rightanswer = cursor.fetchone()
    cursor.execute("SELECT WrongAnswer1 FROM Questions LIMIT 1")
    question_wronganswer1 = cursor.fetchone()
    cursor.execute("SELECT WrongAnswer2 FROM Questions LIMIT 1")
    question_wronganswer2 = cursor.fetchone()
    cursor.execute("SELECT WrongAnswer3 FROM Questions LIMIT 1")
    question_wronganswer3 = cursor.fetchone()
    def generate_markup(question_rightanswer, question_wronganswer1, question_wronganswer2, question_wronganswer3):
        markup = telebot.types.ReplyKeyboardMarkup(True, False)
        all_answers = "{0}, {1}, {2}, {3}".format(question_rightanswer[0], question_wronganswer1[0], question_wronganswer2[0], question_wronganswer3[0])
        list_items = []
        for item in all_answers.split(','):
            list_items.append(item)
        random.shuffle(list_items)
        for item in list_items:
            markup.add(item)
        return markup
    markup = generate_markup(question_rightanswer, question_wronganswer1, question_wronganswer2, question_wronganswer3)
    bot.send_message(message.from_user.id, question_text, reply_markup=markup)


@bot.message_handler(commands=['hide'])
def hide_markup(message):
    hide_markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, '..', reply_markup=hide_markup)

bot.polling(none_stop=True, interval=0)