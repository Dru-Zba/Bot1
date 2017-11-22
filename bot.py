import telebot
import sqlite3
import config
import shelve
import random
import time
from pprint import pprint

bot = telebot.TeleBot(config.token)



print(bot.get_me)


# Пишем логи
def log(message, answer):
    print("\n -----")
    from datetime import datetime
    print(datetime.now())
    print("Сообщение от {0}. Текст - {1}".format(message.from_user.username,
                                                 message.text))
    print(answer)



# Регистрируем пользователя по команде /start, проверяем на наличие юзернейма
@bot.message_handler(commands=['start'])
def say_hello(message):
        if message.from_user.username is None:
            answer = "Для использование бота необходимо заполнить @Username в Telegram!"
            bot.send_message(message.chat.id, answer)
            log(message, answer)
        else:
            conn = sqlite3.connect(config.dbname)
            cursor = conn.cursor()
            cursor.execute("SELECT Name FROM Users WHERE Name = ?", (message.from_user.username,))
            result = cursor.fetchone()
            conn.commit()
            if result is None:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Users Values (?,1)", (message.from_user.username,))
                conn.commit()
                conn.close()
                answer = '''Добрый день, уважаемый сотрудник!
Тебя приветствует бот по охране труда.
Тебе будут задаваться вопросы в тестовой форме. На каждый вопрос есть 4 варианта ответа. Будь внимателен! 
Набери команду /test, чтобы запустить тест по охране труда.
/del_results для удаления результатов теста
/hide для скрытия клавиатуры выбора ответов (баги)
/help для вызова подсказки'''
                bot.send_message(message.chat.id, answer)
                log(message, answer)
            else:
                answer = "Ты уже успешно зарегистрирован в боте. Набери команду /test,\nчтобы запустить тест по охране труда."
                bot.send_message(message.chat.id, answer)
                log(message, answer)
            conn.close()



# Обработка команды /test -- Переписать запрос на более удобный
@bot.message_handler(commands=['test'])
def pass_test(message):
    conn = sqlite3.connect(config.dbname)
    cursor = conn.cursor()
    conn.text_factory = str
    cursor.execute(
        "SELECT id FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1",
        (message.from_user.username,))
    question_id = cursor.fetchone()
    if question_id is None:
        conn = sqlite3.connect(config.dbname)
        cursor = conn.cursor()
        conn.text_factory = str
        cursor.execute(
            "SELECT count(UserName) FROM Users_Answers WHERE  UserName = ?",
            (message.from_user.username,))
        count = cursor.fetchone()
        cursor.execute(
            "SELECT count(UserName) FROM Users_Answers WHERE  UserName = ? AND IsCorrect = 1",
            (message.from_user.username,))
        counter = cursor.fetchone()
        answer = ("Тест завершен! Ты ответил на "+str(counter[0])+" из "+str(count[0])+" вопросов.")
        bot.send_message(message.chat.id, answer)
        log(message, answer)
        conn.close()
        return None
    else:
        conn = sqlite3.connect(config.dbname)
        cursor = conn.cursor()
        conn.text_factory = str
        cursor.execute("SELECT id FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1", (message.from_user.username, ))
        question_id = cursor.fetchone()
        cursor.execute("SELECT QuestionText FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1", (message.from_user.username, ))
        question_text = cursor.fetchone()
        cursor.execute("SELECT RightAnswer FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1", (message.from_user.username, ))
        question_rightanswer = cursor.fetchone()
        cursor.execute("SELECT WrongAnswer1 FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1", (message.from_user.username, ))
        question_wronganswer1 = cursor.fetchone()
        cursor.execute("SELECT WrongAnswer2 FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1", (message.from_user.username, ))
        question_wronganswer2 = cursor.fetchone()
        cursor.execute("SELECT WrongAnswer3 FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?) LIMIT 1", (message.from_user.username, ))
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
        log(message, question_text)
        @bot.message_handler(func = lambda message: message.text == question_rightanswer[0] or message.text == question_wronganswer1[0] or message.text == question_wronganswer2[0] or message.text == question_wronganswer3[0], content_types=['text'])
        def check_answer(message):
            conn = sqlite3.connect(config.dbname)
            cursor = conn.cursor()
            conn.text_factory = str
            cursor.execute(
                "SELECT id FROM Questions WHERE id not in (Select QuestionId from Users_Answers where UserName = ?)",
                (message.from_user.username,))
            question_id1 = cursor.fetchall()
            if question_id in question_id1:
                if message.text == question_rightanswer[0]:
                    hide_markup = telebot.types.ReplyKeyboardRemove()
                    answer = "Верно!"
                    bot.send_message(message.chat.id, answer, reply_markup=hide_markup)
                    conn = sqlite3.connect(config.dbname)
                    cursor = conn.cursor()
                    conn.text_factory = str
                    cursor.execute(
                        "INSERT INTO Users_Answers values (?, ?, ?, 1)",
                        (message.from_user.username, question_id[0], message.text))
                    conn.commit()
                    log(message, answer)
                    time.sleep(1)
                    answer = "Чтобы продолжить, нажмите /test"
                    bot.send_message(message.chat.id, answer)
                    log(message, answer)
                    conn.close()
                    return None
                elif message.text == question_wronganswer1[0] or message.text == question_wronganswer2[0] or message.text == question_wronganswer3[0]:
                    hide_markup = telebot.types.ReplyKeyboardRemove()
                    answer = "Не верно!"
                    bot.send_message(message.chat.id, answer, reply_markup=hide_markup)
                    conn = sqlite3.connect(config.dbname)
                    cursor = conn.cursor()
                    conn.text_factory = str
                    cursor.execute(
                        "INSERT INTO Users_Answers values (?, ?, ?, 0)",
                        (message.from_user.username, question_id[0], message.text))
                    conn.commit()
                    log(message, answer)
                    time.sleep(1)
                    answer = "Чтобы продолжить, нажмите /test"
                    bot.send_message(message.chat.id, answer)
                    log(message, answer)
                    conn.close()
                    return None
                else:
                    if message.text == "Николай":
                        bot.send_message(message.chat.id, "день добры")
                        return None
                    else:
                        answer = "Неизвестная команда."
                        bot.send_message(message.chat.id, answer)
                        log(message, answer)
                        return None
            else:
                if message.text == "Николай":
                    bot.send_message(message.chat.id, "день добры")
                    return None
                else:
                    answer = "Неизвестная команда."
                    bot.send_message(message.chat.id, answer)
                    log(message, answer)
                    return None
        conn.close()
    conn.close()

# обработка кнопки /hide - произвольное скрытие маркапа
@bot.message_handler(commands=['hide'])
def hide_markup(message):
    hide_markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, '..', reply_markup=hide_markup)
    return

# обработка кнопки /help - произвольное скрытие маркапа
@bot.message_handler(commands=['help'])
def show_help(message):
    answer = ''' 
    Набери команду: 
    /test, чтобы запустить тест по охране труда.
    /del_results для удаления результатов теста
    /hide для скрытия клавиатуры выбора ответов (баги)
    /help для вызова подсказки
    /show_results для отображения результатов всех опросов'''
    bot.send_message(message.chat.id, answer)
    log(message, answer)
    return


# обработка команды /del_results - удаление результатов теста юзера
@bot.message_handler(commands=['del_results'])
def delete_results(message):
    conn = sqlite3.connect(config.dbname)
    cursor = conn.cursor()
    conn.text_factory = str
    cursor.execute("DELETE FROM Users_Answers WHERE UserName = ?", (message.from_user.username, ))
    conn.commit()
    answer = "Результаты теста удалены."
    bot.send_message(message.chat.id, answer)
    log(message, answer)
    return

# результаты по юзерам
@bot.message_handler(commands=['show_results'])
def delete_results(message):
    conn = sqlite3.connect(config.dbname)
    cursor = conn.cursor()
    conn.text_factory = str
    cursor.execute("Select UserName, count(isCorrect) From Users_Answers group by UserName")
    answer = cursor.fetchall()
    answer = ("Общее количесто правильных ответов:\n"+str(answer).replace("), ('", "\n").replace("[('", "").replace(")]", "").replace("'", "").replace(",", " ="))
    conn.close()
    bot.send_message(message.chat.id, answer)
    log(message, answer)
    return

bot.polling(none_stop=True, interval=0)