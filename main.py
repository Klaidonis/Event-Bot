import asyncio
import pandas as pd
import openpyxl
import functions as fn
from datetime import datetime, timedelta
from config import bot, executor, dp, scheduler, connect, cursor, State, StatesGroup, \
    types, FSMContext, ReplyKeyboardMarkup, KeyboardButton

#Ячейки для регистраци
class People(StatesGroup):
    Surname = State()
    First_name = State()
    Pernr = State()

class Admin(StatesGroup):
    Id = State()
    Admin_name = State()

class Survey(StatesGroup):
    Id_group = State()
    Txt = State()
    Answ1 = State()
    Answ2 = State()
    Answ3 = State()
    Regularity = State()
    Day_week = State()
    Max_people = State()
    Time = State()
    Time_maybe = State()

class Mailing(StatesGroup):
    Id_group = State()
    Text_message = State()

class Schedule(StatesGroup):
    Text_schedule = State()

class Doc(StatesGroup):
    Text_doc = State()

class Limit_event(StatesGroup):
    Id_event = State()
    Max_people = State()

class Add_new_people(StatesGroup):
    Id_event = State()
    Id_tg = State()
    Name_fi = State()

class Delete_people(StatesGroup):
    Id_event = State()
    Id_tg = State()
    Name_fi = State()

class Delete_event(StatesGroup):
    Id_event = State()

class start_message(StatesGroup):
    Start_message = State()


markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
button1 = "отмена"
markup.add(button1)

admin_markup = ReplyKeyboardMarkup(resize_keyboard=True)
button1 = KeyboardButton('Добавить админа')
button2 = KeyboardButton('Изменить приветствие')
button3 = KeyboardButton('Запланировать опрос')
button4 = KeyboardButton('Отменить опрос')
button5 = KeyboardButton('Изменить расписание')
button6 = KeyboardButton('Изменить документы')
button7 = KeyboardButton('Рассылка')
button8 = KeyboardButton('Лимит')
button9 = KeyboardButton('Добавить')
button10 = KeyboardButton('Удалить')
button11 = KeyboardButton('Выгрузить Excel')
admin_markup.add(button1, button2, button3, button4, button5, button6, button7, button8, button9, button10, button11)

async def check_admin(user_id):
    cursor.execute("SELECT * FROM Admins WHERE Id = %s", (user_id,))
    return cursor.fetchone() is not None

@dp.message_handler(commands=['Admin' or 'admin'])
async def admin_panel(message: types.Message, state: FSMContext):
    if await check_admin(message.from_user.id):
        await bot.send_message(message.from_user.id, "Добро пожаловать в административную панель", reply_markup=admin_markup)
    else:
        await bot.send_message(message.from_user.id, "Вы не являетесь администратором")
    connect.commit()

async def check_user(user_id):
    cursor.execute("SELECT * FROM people WHERE Id = %s", (user_id, ))
    return cursor.fetchone() is None

@dp.message_handler(commands=['start' or 'Start'])
async def start(message: types.Message):
    await message.answer("Укажите свою Фамилию")
    await People.Surname.set()

@dp.message_handler(commands=['roster'])
async def roster(message: types.Message):
    cursor.execute(f"SELECT * FROM people where Id = {message.from_user.id}")
    people = cursor.fetchone()
    if people[0] == message.from_user.id:
        cursor.execute("SELECT * FROM event")
        events_by_date = {}

        for event in cursor.fetchall():
            day_week = event[2]
            split_date_week = day_week.split(" ", 1)[0]
            date_from_db = datetime.strptime(split_date_week, "%d-%m-%Y")

            if date_from_db >= datetime.now():
                date_key = date_from_db.date()
                if date_key not in events_by_date:
                    events_by_date[date_key] = []

                id = event[0]
                full_name = f"{event[3]}"  # Замените 4 на индекс, где хранится Имя
                maybe = "" if event[5] is None else "?"

                events_by_date[date_key].append((id, full_name, maybe))

        connect.commit()

        # Сортируем события и форматируем записи перед добавлением в сообщение
        for date, names in events_by_date.items():
            sorted_names = sorted(names, key=lambda x: (x[0], x[1]))
            message_text = f"#Дата: {date}\n"
            message_text += "\n".join(f"{name[0]}, {name[1]}{' ' + name[2] if name[2] else ''}" for name in sorted_names)
            await bot.send_message(message.from_user.id, message_text)
    else:
        await bot.send_message(message.from_user.id, "Вы не зарегистрировались в боте")

@dp.message_handler(commands=['schedule'])
async def schedule(message: types.Message):
    cursor.execute(f"SELECT * FROM people where Id = {message.from_user.id}")
    people = cursor.fetchone()
    if people[0] == message.from_user.id:
        file_schedule = open("Text/Schedule.txt", 'r', encoding='UTF-8').read()
        await bot.send_message(message.from_user.id, file_schedule)
    else:
        await bot.send_message(message.from_user.id, "Вы не зарегистрировались в боте")

@dp.message_handler(commands=['doc'])
async def doc(message: types.Message):
    cursor.execute(f"SELECT * FROM people where Id = {message.from_user.id}")
    people = cursor.fetchone()
    if people[0] == message.from_user.id:
        file_doc = open("Text/Doc.txt", 'r', encoding='UTF-8').read()
        await bot.send_message(message.from_user.id, file_doc)
    else:
        await bot.send_message(message.from_user.id, "Вы не зарегистрировались в боте")


@dp.message_handler(content_types=['text'])
async def default_and_admin_user(message: types.Message):
    if await check_admin(message.from_user.id):
        if message.text == 'Добавить админа':
            await message.reply("Укажите Id администратора", reply_markup=markup)
            await Admin.Id.set()
        elif message.text == "Запланировать опрос":
            await message.reply("Укажите Id группы в которой будет проходить опрос", reply_markup=markup)
            await Survey.Id_group.set()
        elif message.text == "Рассылка":
            await message.reply("Укажите id группы в которую хотите отправить сообщение", reply_markup=markup)
            await Mailing.Id_group.set()
        elif message.text == "Изменить расписание":
            await message.reply("Введите текст на который хотите изменить", reply_markup=markup)
            await Schedule.Text_schedule.set()
        elif message.text == "Изменить документы":
            await message.reply("Введите текст на который хотите изменить", reply_markup=markup)
            await Doc.Text_doc.set()
        elif message.text == "Лимит":
            await message.reply("Укажите id мероприятия", reply_markup=markup)
            await Limit_event.Id_event.set()
        elif message.text == "Добавить":
            await message.answer("Укажите id мероприятия", reply_markup=markup)
            await Add_new_people.Id_event.set()
        elif message.text == "Удалить":
            await message.answer("Введите id мероприятия", reply_markup=markup)
            await Delete_people.Id_event.set()
        elif message.text == "Отменить опрос":
            cursor.execute("SELECT * FROM survey WHERE Regularity ='week' AND Cancel is NULL")
            for survey in cursor.fetchall():
                await bot.send_message(message.from_user.id, f"#Id: {survey[0]}\nId группы: {survey[1]}\n#День: {survey[7]}\n#Время: {survey[8]}\n Регулярность: #week")
            connect.commit()
            cursor.execute("SELECT * FROM survey WHERE Regularity ='single' AND Cancel is NULL")
            for survey in cursor.fetchall():
                await bot.send_message(message.from_user.id, f"#Id: {survey[0]}\nId группы: {survey[1]}\n#День: {survey[7]}\n#Время: {survey[8]}\n Регулярность: #single")
            connect.commit()
            await message.reply("Укажите Id мероприятия которое надо отменить", reply_markup=markup)
            await Delete_event.Id_event.set()
        elif message.text == "Изменить приветствие":
            await message.reply("Введите текст приветсвия")
            await start_message.Start_message.set()
        elif message.text == "Выгрузить Excel":
            await message.answer("Это команда выгрзуит сразу три таблицы")
            try:
                people = pd.read_sql("select * from people", connect)
                people.to_excel(fr"Excel/People.xlsx", index=False)
                survey = pd.read_sql("select * from survey", connect)
                survey.to_excel(fr"Excel/Survey.xlsx", index=False)
                event = pd.read_sql("select * from event", connect)
                event.to_excel(fr"Excel/Event.xlsx", index=False)
                with open('Excel/People.xlsx', 'rb') as people:
                    await bot.send_document(message.from_user.id, document=people)
                    with open('Excel/survey.xlsx', 'rb') as survey:
                        await bot.send_document(message.from_user.id, document=survey)
                        with open('Excel/Event.xlsx', 'rb') as event:
                            await bot.send_document(message.from_user.id, document=event)
            except:
                pass

@dp.message_handler(state=start_message.Start_message)
async def write_file_start(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await bot.send_message(message.from_user.id, "Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(write_file_start = message.text)
        data = await state.get_data()
        write_file_start = data['write_file_start']
        file = open("Text/Start.txt", 'w', encoding='UTF-8')
        file.write(f"{write_file_start}")
        file.close()
        await bot.send_message(message.from_user.id, "Вы успешно изменили приветствие")
        await state.finish()


@dp.message_handler(state=Delete_event.Id_event)
async def delete_event(message: types.Message, state: FSMContext):
    await state.update_data(delete_event = message.text)
    data = await state.get_data()
    delete_event = data['delete_event']
    if message.text == "отмена":
        await state.finish()
        await bot.send_message(message.from_user.id, "Вы отменили действие", reply_markup=admin_markup)
    else:
        try:
            cursor.execute(f"Update survey SET Cancel = 'X' WHERE Id = {delete_event}")
            await message.answer("Вы успешно отменили опрос")
        except:
            await message.answer("Такой группы не было найдено")
    connect.commit()
    await state.finish()

@dp.message_handler(state=Delete_people.Id_event)
async def delete_id_from_event(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(delete_id_from_event = message.text)
        await message.answer("Введите Id телеграмма человека, которого хотите удалить")
        await Delete_people.next()

@dp.message_handler(state=Delete_people.Id_tg)
async def delete_tg_from_event(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(delete_tg_from_event = message.text)
        await message.answer("Введите фамилию и имя человека которого хотите удалить", reply_markup=markup)
        await Delete_people.next()

@dp.message_handler(state=Delete_people.Name_fi)
async def delete_name_fi_from_event(message: types.Message, state: FSMContext):
    await state.update_data(delete_name_fi_from_event = message.text)
    data = await state.get_data()
    delete_id_from_event = data['delete_id_from_event']
    delete_tg_from_event = data['delete_tg_from_event']
    delete_name_fi_from_event = data['delete_name_fi_from_event']
    if message.text == "отмена":
        await state.finish()
        await bot.send_message(message.from_user.id, "Вы отменили действие", reply_markup=admin_markup)
    else:
        cursor.execute(f"DELETE FROM event WHERE Id_event = {delete_id_from_event} AND Id_tg = {delete_tg_from_event} AND Name_fi = '{delete_name_fi_from_event}'")
        await bot.send_message(message.from_user.id, "Человек успешно удален из мероприятия")
    connect.commit()
    await state.finish()

@dp.message_handler(state=Add_new_people.Id_event)
async def get_id_event_for_people(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(get_id_event_for_people = message.text)
        await message.answer("Укажите id телеграм человека")
        await Add_new_people.next()

@dp.message_handler(state=Add_new_people.Id_tg)
async def get_id_tg_for_people(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(get_id_tg_for_people = message.text)
        await message.answer("Укажите фамилию и имя человека, которого хотите добавить", reply_markup=admin_markup)
        await Add_new_people.next()

@dp.message_handler(state=Add_new_people.Name_fi)
async def add_new_people_in_event(message: types.Message, state: FSMContext):
    await state.update_data(add_new_people_in_event = message.text)
    data = await state.get_data()
    get_event = data['get_id_event_for_people']
    get_people_id = int(data['get_id_tg_for_people'])
    get_name_fi_people = data['add_new_people_in_event']
    cursor.execute(f"SELECT * FROM survey WHERE Id = {get_event}")
    survey = cursor.fetchone()
    if survey:
        cursor.execute(f"SELECT * FROM people WHERE Id = {get_people_id}")
        people = cursor.fetchone()
        if people:
            cursor.execute(f"SELECT * FROM event WHERE Id_event = {get_event}")
            event = cursor.fetchone()
            if event and people[0] == event[4] and event[5] is None:
                await bot.send_message(message.from_user.id, "Уже добавлен", reply_markup=admin_markup)
            elif event and people[0] == event[4] and event[5] is not None:
                cursor.execute(f"UPDATE event SET maybe = NULL WHERE Id_tg = {get_people_id} AND ID_event = {get_event}")
                await bot.send_message(message.from_user.id, "Точно будет", reply_markup=admin_markup)
            else:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM event WHERE Id_event = {get_event} AND Waiting is NULL")
                    count_people_event = cursor.fetchone()[0]
                    print(count_people_event)
                    if count_people_event >= survey[9]:
                        if people[4] == "outside":
                            cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                            max_waiting = cursor.fetchone()[0]
                            cursor.execute(f"SELECT MAX(Num_External) FROM event WHERE Id_event = {survey[0]}")
                            max_external = cursor.fetchone()[0]
                            if max_waiting is None:
                                max_waiting = 1
                            elif max_waiting is not None:
                                max_waiting = max_waiting + 1
                            if max_external is None:
                                max_external = 1
                            elif max_external is not None:
                                max_external = max_external + 1
                            date_time = survey[7]
                            waiting = 'await'
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Waiting, Num_waiting, Num_external, Time_date) VALUES (%s, %s, %s, %s, %s, %s, %s);", (
                                get_event, get_people_id, get_name_fi_people, waiting, max_waiting, max_external, date_time))
                            await bot.send_message(message.from_user.id, f"{get_name_fi_people} Успешно добавлен (обновлен лист ожидания)", reply_markup=admin_markup)
                        elif people[4] == "lenta":
                            date_time = survey[7]
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]} AND Waiting is NULL")
                            max_external = cursor.fetchone()[0]
                            if max_external is None:
                                cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                                num_waiting = cursor.fetchone()[0]
                                if num_waiting is None:
                                    num_waiting = 1
                                elif num_waiting is not None:
                                    num_waiting = num_waiting + 1
                                waiting = 'await'
                                cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Waiting, Num_waiting, Time_date) VALUES (%s, %s, %s, %s, %s, %s);", (
                                    get_event, get_people_id, get_name_fi_people, waiting, num_waiting, date_time
                                ))
                                await bot.send_message(message.from_user.id, f"{get_name_fi_people} успешно добавлен (обновлен лист ожидания)", reply_markup=admin_markup)
                            elif max_external is not None:
                                cursor.execute(f"SELECT MAX(Num_waiting) FROM event WHERE Id_event = {survey[0]}")
                                num_waiting = cursor.fetchone()[0]
                                if num_waiting is None:
                                    num_waiting = 1
                                elif num_waiting is not None:
                                    num_waiting = num_waiting + 1
                                cursor.execute(f"UPDATE event SET num_waiting = {num_waiting} WHERE Id_event = {survey[0]} and Num_external = {max_external} and Waiting is NULL")
                                cursor.execute(f"UPDATE event SET waiting = 'await' WHERE Id_event = {survey[0]} and Num_external = {max_external} and Waiting is NULL")
                                cursor.execute(f"INSERT INTO event (Id_event, Id_tg, Name_fi, Time_date) VALUES (%s, %s, %s, %s);", (get_event, get_people_id, get_name_fi_people, date_time))
                                await bot.send_message(message.from_user.id, f"{get_name_fi_people} Успешно добавлен (обновлен основной состав)", reply_markup=admin_markup)
                    elif count_people_event <= survey[9]:
                        if people[4] == "outside":
                            cursor.execute(f"SELECT MAX(Num_external) FROM event WHERE Id_event = {survey[0]}")
                            max_external = cursor.fetchone()[0]
                            if max_external is None:
                                max_external = 1
                            elif max_external is not None:
                                max_external = max_external + 1
                            date_time = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Num_external, Time_date) VALUES (%s, %s, %s, %s, %s);", (
                                get_event, get_people_id, get_name_fi_people, max_external, date_time
                            ))
                            await bot.send_message(message.from_user.id, f"{get_name_fi_people} Успешно добавлен (обновлен основной состав)", reply_markup=admin_markup)
                        elif people[4] == "lenta":
                            date_time = survey[7]
                            cursor.execute("INSERT INTO event (Id_event, Id_tg, Name_fi, Time_date) VALUES (%s, %s, %s, %s);", (
                                get_event, get_people_id, get_name_fi_people, date_time
                            ))
                            await bot.send_message(message.from_user.id, f"{get_name_fi_people} Успешно добавлен (обновлен основной состав)", reply_markup=admin_markup)
                except Exception as ex:
                    print(ex)
    await state.finish()
    connect.commit()

@dp.message_handler(state=Limit_event.Id_event)
async def get_id_event_for_max_people(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(get_id_event_for_max_people = message.text)
        await message.answer("Укажите новое максимальное кол-во людей")
        await Limit_event.next()

@dp.message_handler(state=Limit_event.Max_people)
async def update_max_people_for_event(message: types.Message, state: FSMContext):
    await state.update_data(update_max_people_for_event = message.text)
    data = await state.get_data()
    get_id_event_for_max_people = data['get_id_event_for_max_people']
    update_max_people_for_event = int(data['update_max_people_for_event'])
    cursor.execute(f"SELECT COUNT(*) FROM event WHERE Id_event = {get_id_event_for_max_people} AND waiting is NULL")
    get_max_people = cursor.fetchone()[0]
    try:
        if get_max_people is None:
            cursor.execute(f"UPDATE survey SET max_people = {update_max_people_for_event} WHERE Id = {get_id_event_for_max_people}")
            await bot.send_message(message.from_user.id, "Вы успешно обновили максимальное кол-во людей на мероприятие")
        elif get_max_people < update_max_people_for_event:
            cursor.execute(f"UPDATE survey SET max_people = {update_max_people_for_event} WHERE Id = {get_id_event_for_max_people}")
            await bot.send_message(message.from_user.id, "Вы успешно обновили максимальное кол-во людей на мероприятие")
        else:
            await bot.send_message(message.from_user.id, "Вы не можете обновить максимальное значение людей так, как оно превышает значение людей, которые записались на мероприятие")
    except:
        pass
    connect.commit()
    await state.finish()


@dp.message_handler(state=Doc.Text_doc)
async def add_text_doc_doc(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(add_text_doc_doc = message.text)
        data = await state.get_data()
        add_text_doc_doc = data['add_text_doc_doc']
        file = open("Text/Doc.txt", 'w', encoding='UTF-8')
        file.write(f"{add_text_doc_doc}")
        file.close()
        await message.answer("Вы успешно перезаписали файл")
        await state.finish()

@dp.message_handler(state=Schedule.Text_schedule)
async def add_text_schedule_doc(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(add_text_schedule_doc = message.text)
        data = await state.get_data()
        add_text_schedule_doc = data['add_text_schedule_doc']
        file = open("Text/Schedule.txt", 'w', encoding='UTF-8')
        file.write(f"{add_text_schedule_doc}")
        file.close()
        await message.answer("Вы успешно перезаписали файл")
        await state.finish()

@dp.message_handler(state=Mailing.Id_group)
async def add_mailing_id_group(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(add_mailing_id_group = message.text)
        await message.answer("Введите текст рассылки")
        await Mailing.next()

@dp.message_handler(state=Mailing.Text_message)
async def add_text_mailing(message: types.Message, state: FSMContext):
    await state.update_data(add_text_mailing = message.text)
    data = await state.get_data()
    add_mailing_id_group = data['add_mailing_id_group']
    add_text_mailing = data['add_text_mailing']
    try:
        await bot.send_message(add_mailing_id_group, add_text_mailing)
    except:
        await bot.send_message(message.from_user.id, "Неправильно ввели id группы")
    await state.finish()

@dp.message_handler(state=Survey.Id_group)
async def get_id_group(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(get_id_group = message.text)
        await message.answer("Введите текст опроса")
        await Survey.next()

@dp.message_handler(state=Survey.Txt)
async def text_group(message: types.Message, state: FSMContext):
    await state.update_data(text_group = message.text)
    await message.answer("Введите первый ответ(Answ1)")
    await Survey.next()

@dp.message_handler(state=Survey.Answ1)
async def get_answ1(message: types.Message, state: FSMContext):
    await state.update_data(get_answ1 = message.text)
    await message.answer("Введите второй ответ(Answ2)")
    await Survey.next()

@dp.message_handler(state=Survey.Answ2)
async def get_answ2(message: types.Message, state: FSMContext):
    await state.update_data(get_answ2 = message.text)
    await message.answer("Введите третий ответ(Answ3)")
    await Survey.next()

@dp.message_handler(state=Survey.Answ3)
async def get_answ3(message: types.Message, state: FSMContext):
    await state.update_data(get_answ3 = message.text)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    week = KeyboardButton("week")
    single = KeyboardButton("single")
    markup.add(week, single)
    await message.answer("Укажите регулярность опроса (week/single)", reply_markup=markup)
    await Survey.next()

@dp.message_handler(state=Survey.Regularity)
async def get_regularity(message: types.Message, state: FSMContext):
    await state.update_data(get_regularity = message.text)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button0 = types.KeyboardButton('Понедельник')
    button1 = types.KeyboardButton('Вторник')
    button2 = types.KeyboardButton('Среда')
    button3 = types.KeyboardButton('Четверг')
    button4 = types.KeyboardButton('Пятница')
    button5 = types.KeyboardButton('Суббота')
    button6 = types.KeyboardButton('Воскресенье')
    markup.add(button0, button1, button2, button3, button4, button5, button6)
    await message.answer("Укажите день опроса", reply_markup=markup)
    await Survey.next()

@dp.message_handler(state=Survey.Day_week)
async def get_day_week(message: types.Message, state: FSMContext):
    await state.update_data(get_day_week = message.text)
    await message.answer("Укажите кол-во людей", reply_markup=types.ReplyKeyboardRemove())
    await Survey.next()

@dp.message_handler(state=Survey.Max_people)
async def get_max_people(message: types.Message, state: FSMContext):
    await state.update_data(get_max_people = message.text)
    await message.answer("Укажите время рассылки\nФормат времени 12.00")
    await Survey.next()

@dp.message_handler(state=Survey.Time)
async def get_time_send_message(message: types.Message, state: FSMContext):
    await state.update_data(get_time_send_message = message.text)
    await message.answer("Введите время уведомления сомневающихся\nФормат времени 12.00", reply_markup=markup)
    await Survey.next()

@dp.message_handler(state=Survey.Time_maybe)
async def get_time_maybe(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(get_time_maybe = message.text)
        data = await state.get_data()
        get_id_group = data['get_id_group']
        text_group = data['text_group']
        get_regularity = data['get_regularity']
        get_day_week = data['get_day_week']
        get_max_people = data['get_max_people']
        time_send = data['get_time_send_message']
        get_time_maybe = data['get_time_maybe']
        if get_regularity:
            days_of_week = {
                "Понедельник": 0,
                "Вторник": 1,
                "Среда": 2,
                "Четверг": 3,
                "Пятница": 4,
                "Суббота": 5,
                "Воскресенье": 6
            }

            # Получаем текущую дату
            today = datetime.now()

            # Получаем день недели в числовом формате (0 - понедельник, 1 - вторник, и так далее)
            current_day_of_week = today.weekday()

            # Получаем название текущего дня недели
            current_day_name = list(days_of_week.keys())[list(days_of_week.values()).index(current_day_of_week)]

            # Вводим день недели от пользователя
            desired_day = get_day_week

            # Проверяем, был ли уже этот день на этой неделе
            if days_of_week[desired_day] > current_day_of_week:
                # Если день еще не прошел на этой неделе
                days_until_desired_day = days_of_week[desired_day] - current_day_of_week
            else:
                # Если день уже был на этой неделе, добавляем 7 дней для следующей недели
                days_until_desired_day = 7 - (current_day_of_week - days_of_week[desired_day])

            # Вычисляем дату для заданного дня недели
            desired_date = today + timedelta(days=days_until_desired_day)
            # Выводим результат
            day_week = (f"{desired_date.strftime('%d-%m-%Y') + ' ' + desired_day}")
            if desired_day == "Понедельник":
                status_week = 0
            elif desired_day == "Вторник":
                status_week = 1
            elif desired_day == "Среда":
                status_week = 2
            elif desired_day == "Четверг":
                status_week = 3
            elif desired_day == "Пятница":
                status_week = 4
            elif desired_day == "Суббота":
                status_week = 5
            elif desired_day == "Воскресенье":
                status_week = 6

        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = KeyboardButton('Добавить админа')
        button2 = KeyboardButton('Изменить приветствие')
        button3 = KeyboardButton('Запланировать опрос')
        button4 = KeyboardButton('Отменить опрос')
        button5 = KeyboardButton('Изменить расписание')
        button6 = KeyboardButton('Изменить документы')
        button7 = KeyboardButton('Рассылка')
        button8 = KeyboardButton('Лимит')
        button9 = KeyboardButton('Добавить')
        button10 = KeyboardButton('Удалить')
        markup.add(button1, button2, button3, button4, button5, button6, button7, button8, button9, button10)
        try:
            cursor.execute("Insert Into Survey (Id_group, Txt, Regularity, Day_week, Time_send, Max_people, Time_maybe, Status_week)"
                           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", (get_id_group, text_group, get_regularity, day_week, time_send, get_max_people, get_time_maybe, status_week))
            cursor.execute("SELECT * FROM survey ORDER BY Id DESC LIMIT 1")
            for survey in cursor.fetchall():
                get_answ1 = data['get_answ1']
                get_answ2 = data['get_answ2']
                get_answ3 = data['get_answ3']
                cursor.execute(f"UPDATE survey SET Answ1 = '{get_answ1 + ' ' + str(survey[0])}' WHERE Id = {survey[0]}")
                cursor.execute(f"UPDATE survey SET Answ2 = '{get_answ2 + ' ' + str(survey[0])}' WHERE Id = {survey[0]}")
                cursor.execute(f"UPDATE survey SET Answ3 = '{get_answ3 + ' ' + str(survey[0])}' WHERE Id = {survey[0]}")
                connect.commit()
            await bot.send_message(message.from_user.id, "Вы успешно создали новый опрос", reply_markup=markup)
        except Exception as ex:
            await bot.send_message(message.from_user.id, f"При добавлении мероприятия произошла ошибка: {ex}")
        connect.commit()
        await state.finish()

@dp.message_handler(state=Admin.Id)
async def add_new_id_admin(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(add_new_id_admin = message.text)
        await message.answer("Введите имя администратора")
        await Admin.next()

@dp.message_handler(state=Admin.Admin_name)
async def add_new_name_admin(message: types.Message, state: FSMContext):
    await state.update_data(add_new_name_admin = message.text)
    data = await state.get_data()
    add_new_id_admin = data['add_new_id_admin']
    add_new_name_admin = data['add_new_name_admin']
    await state.finish()
    try:
        cursor.execute("Insert Into Admins (Id, User_name) VALUES (%s, %s);", (add_new_id_admin, add_new_name_admin))
        await bot.send_message(message.from_user.id, "Вы успешно добавили нового админа")
    except Exception as ex:
        await bot.send_message(message.from_user.id, f"При добавлении произошла ошибка: {ex}")
    connect.commit()
    await state.finish()
#------------------------------------------------------РЕГИСТРАЦИЯ-----------------------------------------------------#
@dp.message_handler(state=People.Surname)
async def surname(message: types.Message, state: FSMContext):
    await state.update_data(surname = message.text)
    await message.answer("Укажите свое имя")
    await People.next()

@dp.message_handler(state=People.First_name)
async def first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name = message.text)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = KeyboardButton("Нет")
    button2 = KeyboardButton("Не знаю")
    markup.add(button1, button2)
    await message.answer("Укажите свой табельный номер", reply_markup=markup)
    await People.next()

@dp.message_handler(state=People.Pernr)
async def pernr(message: types.Message, state: FSMContext):
    if message.text == "отмена":
        await state.finish()
        await message.answer("Вы отменили действие", reply_markup=admin_markup)
    else:
        await state.update_data(pernr = message.text)
        data = await state.get_data()
        Tg_id = message.from_user.id
        Surname = data['surname']
        First_name = data['first_name']
        Pernr = data['pernr']
        try:
            if Pernr.lower() in {"нет", "не знаю"}:
                Relations = "outside"
            else:
                Relations = "lenta"
            cursor.execute("INSERT INTO People (Id, Surname, First_name, Pernr, Relations) VALUES (%s, %s, %s, %s, %s);", (Tg_id, Surname, First_name, Pernr, Relations))
            await bot.send_message(message.from_user.id, "Вы успешно зарегистрировались", reply_markup=types.ReplyKeyboardRemove())
            # Отправка и закрпление сообщения
            file_start = open('Text/Start.txt', 'r', encoding='UTF-8').read()
            pinned_message = await bot.send_message(message.from_user.id, file_start)
            await bot.pin_chat_message(chat_id=message.chat.id, message_id=pinned_message.message_id)
        except Exception as ex:
            await bot.send_message(message.from_user.id, "Вы уже были зарегистрированы", reply_markup=types.ReplyKeyboardRemove())

        connect.commit()
        await state.finish()

#Запуск бота
if __name__ == "__main__":
    scheduler.add_job(fn.delete, "interval", seconds = 3)
    scheduler.add_job(fn.send_survey_event_markup, "interval", seconds = 3)
    loop = asyncio.get_event_loop()
    loop.create_task(fn.get_answer())
    scheduler.start()
    executor.start_polling(dp, skip_updates=True)
    loop.run_forever()