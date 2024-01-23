import config as cg
import time
import psycopg2
import datetime
from config import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, types, bot, dp
from datetime import datetime, timedelta
from threading import Thread

connect = cg.connect
cursor = cg.cursor

import datetime


async def send_survey_event_markup():
    cursor.execute("SELECT * FROM survey WHERE Cancel is NULL AND Status_send is NULL")
    for survey in cursor.fetchall():
        day_week = survey[7]  # дата из бд полностью
        status_week = survey[13]  # день недели в числах
        split_date_week = day_week.split(" ", 1)[0]
        split_day_week = day_week.split(" ", 1)[1]# split_day_week = day_week.split(" ", 1)[1]  - убрать дату, оставить день
        current_date = datetime.datetime.now()
        date_from_db = datetime.datetime.strptime(split_date_week, "%d-%m-%Y")

        if status_week == 0:
            # Вычитаем timedelta из даты
            new_date = date_from_db - datetime.timedelta(days=3)
        elif status_week == 6:
            new_date = date_from_db - datetime.timedelta(days=2)
        else:
            new_date = date_from_db - datetime.timedelta(days=1)

        #Отправка опрос на 1 день раньше.
        current_time = current_date.strftime("%H.%M")
        survey_time = survey[8]

        if datetime.datetime.now() >= new_date:
            if current_time >= survey_time:
                markup = types.InlineKeyboardMarkup(row_width=1)
                string1 = survey[3]
                string2 = survey[4]
                string3 = survey[5]
                result1 = string1.split(" ", 1)[0]
                result2 = string2.split(" ", 1)[0]
                result3 = string3.split(" ", 1)[0]
                Answ1 = types.InlineKeyboardButton(f"{result1}", callback_data=f"answ1_{survey[3]}")
                Answ2 = types.InlineKeyboardButton(f"{result2}", callback_data=f"answ2_{survey[4]}")
                Answ3 = types.InlineKeyboardButton(f"{result3}", callback_data=f"answ3_{survey[5]}")
                markup.add(Answ1, Answ2, Answ3)
                send_message = await bot.send_message(survey[1], f"Дата: {split_date_week} ({split_day_week})\n{survey[2]}", reply_markup=markup)
                message_id = send_message.message_id # Id для удаления сообщения
                cursor.execute("INSERT INTO message (message_id) VALUES (%s);", (message_id, ))
                cursor.execute(f"UPDATE survey SET Status_send = 'send' WHERE Day_week = '{day_week}' AND Id = {survey[0]}")
                connect.commit()

    # отправка сообщений сомневающимся людям
    cursor.execute("SELECT * FROM survey WHERE Cancel is NULL")
    for survey_people in cursor.fetchall():
        day_week_people = survey_people[7]
        split_date = day_week_people.split(" ", 1)[0]
        date_db = datetime.datetime.strptime(split_date, "%d-%m-%Y")
        if datetime.datetime.now() >= date_db:
            cursor.execute(f"SELECT * FROM event WHERE Maybe = '?' and Status_send is NULL")
            for people_survey in cursor.fetchall():
                Name_fi = f"{people_survey[3]}"
                try:
                    cursor.execute(f"UPDATE event SET status_send = 'send' WHERE Name_fi = '{Name_fi}'")
                    await bot.send_message(people_survey[4], f"Дата: {people_survey[2]}\n{Name_fi}\nВаше решение по тренировке влияет на остальных участников, пожалуйста, по возможности уточните в опросе актуальный статус своего присутствия")
                except:
                    await bot.send_message(survey_people[1], f"Дата: {people_survey[2]}\n{Name_fi}\nВаше решение по тренировке влияет на остальных участников, пожалуйста, по возможности уточните в опросе актуальный статус своего присутствия")
        connect.commit()

#привязанные кнопки с сообщениями
async def get_answer():
    @dp.callback_query_handler(lambda c: c.data.startswith('answ1'))
    async def handle_answ1_button(query: types.CallbackQuery):
        survey_id = (query.data.split("_")[1])
        cursor.execute(f"SELECT * FROM survey WHERE Answ1 = '{survey_id}'")
        survey = cursor.fetchone()
        if survey:
            cursor.execute(f"SELECT * FROM people WHERE Id = {query.from_user.id}")
            people = cursor.fetchone()
            if people:
                cursor.execute(f"SELECT * FROM event WHERE Id_event = {survey[0]} AND Id_tg = {query.from_user.id}")
                event = cursor.fetchone()
                if event and people[0] == event[4] and event[5] is None:
                    # await bot.send_message(query.from_user.id, "Ваш голос уже был успешно учтен")
                    await bot.answer_callback_query(query.id, "Ваш голос уже был учтен", show_alert=True)
                elif event and people[0] == event[4] and event[5] is not None:
                    cursor.execute(f"UPDATE event SET maybe = Null WHERE Id_tg = {query.from_user.id} AND Id_event = {survey[0]}")
                    # await bot.send_message(query.from_user.id, "Изменение участия учтено")
                    await bot.answer_callback_query(query.id, "Изменение участия учтено")
                    await bot.send_message(survey[1], f"Имя: {people[3] + ' ' + people[2]}\nточно будет на тренировке\nДата: {event[2]}")
                #ЛИСТ ОЖИДАНИЯ
                else:
                    if people[4] == "outside":
                        cursor.execute(f"SELECT COUNT(*) FROM event WHERE Id_event =  {survey[0]} AND waiting IS NULL")
                        result_count_event = cursor.fetchone()[0]
                        connect.commit()
                        if result_count_event >= survey[9]:
                            cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                            max_num_waiting = cursor.fetchone()[0]
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]}")
                            max_external = cursor.fetchone()[0]
                            if max_num_waiting is None:
                                max_num_waiting = 0
                            new_num_waiting = max_num_waiting + 1
                            if max_external is None:
                                max_external = 0
                                new_max_external = max_external + 1
                            elif max_external is not None:
                                new_max_external = max_external + 1
                            Id_event = survey[0]
                            Id_tg = query.from_user.id
                            Name_fi = f"{people[3] + ' ' + people[2]}"
                            Waiting = "await"
                            time_date = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, waiting, Num_waiting, Num_external, Time_date) VALUES (%s, %s, %s, %s, %s, %s, %s);", (
                                Id_event, Id_tg, Name_fi, Waiting, new_num_waiting, new_max_external, time_date
                            ))
                            connect.commit()
                            # await bot.send_message(query.from_user.id, "Ваш голос успешно учтен, спасибо! (обновлен лист ожидания)")
                            await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен лист ожидания)")
                            #Обычное добавление людей с relations outside
                        elif result_count_event <= survey[9]:
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]}")
                            max_nam_external = cursor.fetchone()[0]
                            if max_nam_external is None:
                                max_nam_external = 1
                            elif max_nam_external is not None:
                                max_nam_external = max_nam_external + 1
                            Id_event = survey[0]
                            Id_tg = query.from_user.id
                            Name_fi = f"{people[3] + ' ' + people[2]}"
                            time_date = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Num_external, Time_date) VALUES (%s, %s, %s, %s, %s);",(
                                Id_event, Id_tg, Name_fi, max_nam_external, time_date
                            ))
                            connect.commit()
                            await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен основной состав)")
                    elif people[4] == "lenta":
                        cursor.execute(f"SELECT COUNT(*) FROM event WHERE Id_event = {survey[0]} AND Waiting IS NULL")
                        count_event = cursor.fetchone()[0]
                        if count_event >= survey[9]:
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]} AND Waiting IS NULL")
                            num_extenal = cursor.fetchone()[0]
                            #Если все люди которые уже в основном составе имеют статус лента
                            if num_extenal is None:
                                num_extenal = 1
                                Id_event = survey[0]
                                Id_tg = query.from_user.id
                                Name_fi = f"{people[3] + ' ' + people[2]}"
                                Waiting = "await"
                                #Взять порядковый номер num_waiting
                                cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                                num_waiting = cursor.fetchone()[0]
                                if num_waiting is None:
                                    num_waiting = 1
                                elif num_waiting is not None:
                                    num_waiting = num_waiting + 1
                                time_date = survey[7]
                                cursor.execute(f"INSERT INTO event (Id_event, Id_tg, Name_fi, Waiting, Num_waiting, Time_date) VALUES (%s, %s, %s, %s, %s, %s);",(
                                    Id_event, Id_tg, Name_fi, Waiting, num_waiting, time_date
                                ))
                                await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен лист ожидания)")
                                connect.commit()
                            elif num_extenal is not None:
                                cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                                num_waiting = cursor.fetchone()[0]
                                if num_waiting is None:
                                    num_waiting = 1
                                elif num_waiting is not None:
                                    num_waiting = num_waiting + 1
                                #Обновить статус у пользователя который с max_external и в лист ожидания его
                                cursor.execute(f"UPDATE event SET Waiting = 'await' WHERE Id_event = {survey[0]} AND Num_External = {num_extenal} AND Waiting is NULL")
                                cursor.execute(f"UPDATE event SET Num_waiting = {num_waiting} WHERE Id_event = {survey[0]} AND Num_External = {num_extenal}")
                                cursor.execute(f"SELECT * FROM event WHERE Id_event = {survey[0]} AND Waiting IS NOT NULL AND Num_External = {num_extenal}")
                                people_change_outside = cursor.fetchone()
                                Id_event = survey[0]
                                Id_tg = query.from_user.id
                                Name_fi = f"{people[3] + ' ' + people[2]}"
                                time_date = survey[7]
                                cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Time_date) VALUES (%s, %s, %s, %s);", (Id_event, Id_tg, Name_fi, time_date))
                                await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен основной состав)")
                                Name_fi_await = people_change_outside[3]
                                await bot.send_message(survey[1], f"{Name_fi_await} перенесен в лист ожидания")
                                connect.commit()
                        elif count_event <= survey[9]:
                            Id_event = survey[0]
                            Id_tg = query.from_user.id
                            Name_fi = f"{people[3] + ' ' + people[2]}"
                            time_date = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, time_date) VALUES (%s, %s, %s, %s);", (Id_event, Id_tg, Name_fi, time_date))
                            await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен основной состав)")
                            connect.commit()
            connect.commit()

    @dp.callback_query_handler(lambda c: c.data.startswith('answ2'))
    async def handle_answ2_button(query: types.CallbackQuery):
        survey_id = (query.data.split("_")[1])
        cursor.execute(f"SELECT * FROM survey WHERE Answ2 = '{survey_id}'")
        survey = cursor.fetchone()
        if survey:
            cursor.execute(f"SELECT * FROM people WHERE Id = {query.from_user.id}")
            people = cursor.fetchone()
            if people:
                cursor.execute(f"SELECT * FROM event WHERE Id_event = {survey[0]} AND Id_tg = {query.from_user.id}")
                event = cursor.fetchone()
                if event and people[0] == event[4] and event[5] is None:
                    cursor.execute(f"UPDATE event SET maybe = '?' WHERE id_event = {survey[0]} AND Id_tg = {query.from_user.id}")
                    await bot.answer_callback_query(query.id, "Изменение участия учтено")
                    await bot.send_message(survey[1], f"{event[3]} возможно не сможет присутствовать на тренировке {event[2]}")
                    connect.commit()
                elif event and people[0] and event[4] and event[5] is not None:
                    await bot.answer_callback_query(query.id, "Ваш голос уже был успешно учтен")
                else:
                    if people[4] == "outside":
                        cursor.execute(f"SELECT COUNT(*) FROM event WHERE Id_event = {survey[0]} AND Waiting is NULL")
                        result_count_event = cursor.fetchone()[0]
                        if result_count_event >= survey[9]:
                            cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                            num_waiting = cursor.fetchone()[0]
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]}")
                            num_external = cursor.fetchone()[0]
                            if num_waiting is None:
                                num_waiting = 1
                            elif num_waiting is not None:
                                num_waiting = num_waiting + 1
                            if num_external is None:
                                num_external = 1
                            elif num_external is not None:
                                num_external = num_external + 1
                            Id_event = survey[0]
                            Id_tg = query.from_user.id
                            Name_fi = f"{people[3] + ' ' + people[2]}"
                            Waiting = "await"
                            Maybe = "?"
                            time_date = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Waiting, Num_waiting, Num_External, Maybe, Time_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (
                                Id_event, Id_tg, Name_fi, Waiting, num_waiting, num_external, Maybe, time_date
                            ))
                            await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (Обновлен лист ожидания)")
                            connect.commit()
                        elif result_count_event <= survey[9]:
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]}")
                            max_nam_external = cursor.fetchone()[0]
                            if max_nam_external is None:
                                max_nam_external = 1
                            elif max_nam_external is not None:
                                max_nam_external = max_nam_external + 1
                            Id_event = survey[0]
                            Id_tg = query.from_user.id
                            Name_fi = f"{people[3] + ' ' + people[2]}"
                            Maybe = "?"
                            time_date = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Num_external, Maybe, Time_date) VALUES (%s, %s, %s, %s, %s, %s);",(
                                Id_event, Id_tg, Name_fi, max_nam_external, Maybe, time_date
                            ))
                            await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен основной состав)")
                    elif people[4] == "lenta":
                            cursor.execute(f"SELECT COUNT(*) FROM event WHERE Id_event = {survey[0]} AND Waiting IS NULL")
                            count_event = cursor.fetchone()[0]
                            if count_event >= survey[9]:
                                cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]} AND Waiting IS NULL")
                                num_extenal = cursor.fetchone()[0]
                                # Если все люди которые уже в основном составе имеют статус лента
                                if num_extenal is None:
                                    num_extenal = 1
                                    Id_event = survey[0]
                                    Id_tg = query.from_user.id
                                    Name_fi = f"{people[3] + ' ' + people[2]}"
                                    Waiting = "await"
                                    Maybe = "?"
                                    # Взять порядковый номер num_waiting
                                    cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                                    num_waiting = cursor.fetchone()[0]
                                    if num_waiting is None:
                                        num_waiting = 1
                                    elif num_waiting is not None:
                                        num_waiting = num_waiting + 1
                                    time_date = survey[7]
                                    cursor.execute(f"INSERT INTO event (Id_event, Id_tg, Name_fi, Waiting, Num_waiting, Maybe, Time_date) VALUES (%s, %s, %s, %s, %s, %s, %s);", (
                                            Id_event, Id_tg, Name_fi, Waiting, num_waiting, Maybe, time_date
                                        ))
                                    await bot.answer_callback_query(query.id,"Ваш голос успешно учтен, спасибо! (обновлен лист ожидания)")
                                    connect.commit()
                                elif num_extenal is not None:
                                    cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                                    num_waiting = cursor.fetchone()[0]
                                    if num_waiting is None:
                                        num_waiting = 1
                                    elif num_waiting is not None:
                                        num_waiting = num_waiting + 1
                                    # Обновить статус у пользователя который с max_external и в лист ожидания его
                                    cursor.execute(f"UPDATE event SET Waiting = 'await' WHERE Id_event = {survey[0]} AND Num_External = {num_extenal} AND Waiting is NULL")
                                    cursor.execute(f"UPDATE event SET Num_waiting = {num_waiting} WHERE Id_event = {survey[0]} AND Num_External = {num_extenal}")
                                    cursor.execute(f"SELECT * FROM event WHERE Id_event = {survey[0]} AND Waiting IS NOT NULL AND Num_External = {num_extenal}")
                                    people_change_outside = cursor.fetchone()
                                    Id_event = survey[0]
                                    Id_tg = query.from_user.id
                                    Name_fi = f"{people[3] + ' ' + people[2]}"
                                    Maybe = "?"
                                    time_date = survey[7]
                                    cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Maybe, Time_date) VALUES (%s, %s, %s, %s, %s);", (Id_event, Id_tg, Name_fi, Maybe, time_date))
                                    await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен основной состав)")
                                    Name_fi_await = people_change_outside[3]
                                    await bot.send_message(survey[1], f"{Name_fi_await} перенесен в лист ожидания")
                                    connect.commit()
                            elif count_event <= survey[9]:
                                Id_event = survey[0]
                                Id_tg = query.from_user.id
                                Name_fi = f"{people[3] + ' ' + people[2]}"
                                Maybe = "?"
                                time_date = survey[7]
                                cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Maybe, Time_date) VALUES (%s, %s, %s, %s, %s);", (Id_event, Id_tg, Name_fi, Maybe, time_date))
                                await bot.answer_callback_query(query.id, "Ваш голос успешно учтен, спасибо! (обновлен основной состав)")
                                connect.commit()
                connect.commit()

    @dp.callback_query_handler(lambda c: c.data.startswith('answ3'))
    async def handle_answ3_button(query: types.CallbackQuery):
        survey_id = (query.data.split("_")[1])
        cursor.execute(f"SELECT * FROM survey WHERE Answ3 = '{survey_id}'")
        survey = cursor.fetchone()
        if survey:
            cursor.execute(f"SELECT * FROM people WHERE Id = {query.from_user.id}")
            people = cursor.fetchone()
            if people:
                cursor.execute(f"SELECT * FROM event WHERE Id_event = {survey[0]} AND Id_tg = {query.from_user.id}")
                event = cursor.fetchone()
                cursor.execute(f"DELETE FROM event WHERE Id_tg = {query.from_user.id} AND Id_event = {survey[0]}")
                cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE ID_event = {survey[0]} AND Waiting is not NULL")
                max_waiting = cursor.fetchone()[0]
                if event and people[0] == event[4] and max_waiting is not None:
                    Name_fi = f"{people[3] + ' ' + people[2]}"
                    await bot.answer_callback_query(query.id, "Изменение участия учтено")
                    await bot.send_message(survey[1], f"{Name_fi} к сожалению не сможет присутствовать на тренировке {event[2]}")
                    cursor.execute(f"UPDATE event SET Waiting = NULL WHERE Num_waiting = {max_waiting} and Id_event = {survey[0]}")
                    cursor.execute(f"UPDATE event SET Num_waiting = NULL WHERE Num_waiting = {max_waiting} and Id_event = {survey[0]}")
                elif max_waiting is None:
                    Name_fi = f"{people[3] + ' ' + people[2]}"
                    await bot.answer_callback_query(query.id, "Спасибо, что предупреждаешь! Будем ждать тебя в следующий раз")
                    await bot.send_message(survey[1],f"{Name_fi} к сожалению не сможет присутствовать на тренировке {event[2]}")
                connect.commit()
        connect.commit()

async def delete():
    # Удаление сообщений и обновления статуса в бд, на следующий день у опросов
    cursor.execute("SELECT * FROM survey")
    time_survey = cursor.fetchall()
    for time_survey in time_survey:
        week_day = time_survey[7]
        split_week_date = week_day.split(" ", 1)[0]
        split_week_day = week_day.split(" ", 1)[1]
        time_db = datetime.datetime.strptime(split_week_date, "%d-%m-%Y")
        new_date_db = time_db + datetime.timedelta(days=1)
        if datetime.datetime.   now() >= new_date_db:
            day_week_db = (time_db + datetime.timedelta(days=7)).strftime("%d-%m-%Y")
            day_week_from_db = f"{day_week_db + ' ' + split_week_day}"
            cursor.execute(f"UPDATE survey SET cancel = 'X' WHERE Day_week = '{week_day}' AND Regularity = 'single'")
            cursor.execute(f"UPDATE survey SET day_week = '{day_week_from_db}' WHERE Day_week = '{week_day}' AND Regularity = 'week' AND Status_send is not NULL")
            cursor.execute(f"UPDATE survey SET Status_send = NULL WHERE Day_week = '{week_day}' AND Regularity = 'week' AND Status_send is not NULL")
            cursor.execute("SELECT * FROM message")
            for delete_message in cursor.fetchall():
                try:
                    await bot.delete_message(time_survey[1], message_id=delete_message[0])
                except:
                    pass
            connect.commit()