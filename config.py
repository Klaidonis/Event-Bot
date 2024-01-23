import psycopg2
import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.dispatcher.filters.state import State, StatesGroup
from apscheduler.schedulers.asyncio import AsyncIOScheduler

token = 'your_token'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
loop = asyncio.get_event_loop()
scheduler = AsyncIOScheduler()

try:
    connect = psycopg2.connect(user="postgres", password="WorldWar1945", host="localhost", port="5432", database="Answer")
    cursor = connect.cursor()
    connect.commit()
    print("Успешное подключение к бд")
except Exception as ex:
    print(f"Ошибка подключения к бд:\n{ex}")

try:
    cursor.execute("CREATE TABLE IF NOT EXISTS people (Id BIGINT Primary Key, Pernr TEXT, First_name TEXT, Surname TEXT, Relations TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS survey (Id Serial Primary key, "
                   "Id_group BIGINT,"
                   "TxT TEXT,"
                   "answ1 TEXT,"
                   "answ2 TEXT,"
                   "answ3 TEXT,"
                   "Regularity TEXT,"
                   "Day_week TEXT,"
                   "Time_send TEXT,"
                   "Max_people BIGINT,"
                   "Cancel TEXT,"
                   "Time_maybe TEXT,"
                   "Status_send TEXT,"
                   "Status_week INTEGER)")
    cursor.execute("CREATE TABLE IF NOT EXISTS event (Id Serial primary key, Id_event BIGINT, "
                   "Time_date TEXT, Name_FI TEXT, Id_tg BIGINT,"
                   "Maybe TEXT, Waiting TEXT, Num_waiting BIGINT, Num_external BIGINT, Status_send TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS Admins (Id BIGINT PRIMARY KEY, User_name TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS message (message_id INTEGER)")
    connect.commit()
    print("Успешное создание таблиц в бд")
except Exception as ex:
    print(f"Ошибка создания таблиц в бд: {ex}")