from bs4 import BeautifulSoup
import asyncio
import requests
import pandas as pd
import openpyxl
import os
from openpyxl import load_workbook
import conf as cnf
from aiogram import F, Router, types, Dispatcher, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup, default_state
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
bot = Bot(token=cnf.TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dict_diary = {}

del_sumbol = ['{', '}', '[', ']', '~', '@', '#', '$', '%', '^', '&', '*', '=', '+', '<', '>', '"', '_', '/', '|']

class Write_mess(StatesGroup):
    write_city = State()
    write_age = State()
    write_emotion = State()
    write_sleep = State()
    write_sleep_time = State()
    write_health = State()
    write_only_txt = State()
    write_error = State()



def error_check(mess):
    for i in del_sumbol:
        if i in mess:
            return False
    return True
            


@dp.message(Command('start'))
async def start(message: types.Message):
    name_user = message.from_user.id
    if os.path.exists(f'diary_{name_user}.xlsx'):
        kb = InlineKeyboardBuilder()
        kb.add(types.InlineKeyboardButton(
            text = 'Добавить запись',
            callback_data = 'city'))
        await message.answer(f'Здравствуй, {message.from_user.first_name}', reply_markup=kb.as_markup())
    else:
        kb = InlineKeyboardBuilder()
        kb.add(types.InlineKeyboardButton(
            text = 'Начать вести дневник',
            callback_data = 'to_start'))
        await message.answer(f'''Здравствуй, {message.from_user.first_name} 
        Я твой персональный помошник
        по отслеживанию твоего ментального
        состояния. Здесь ты можешь 
        зафиксировать своё самочувствие,
        сон, а так же погоду для
        того чтобы отследить её влияние 
        на твоё эмоциональное и 
        физическое состояние.''', reply_markup=kb.as_markup()) #разобраться с кнопкой
    
    
@dp.callback_query(F.data == 'to_start')
async def to_creat_diary(callback: types.CallbackQuery):
    name_user = callback.from_user.id
    if os.path.exists(f'diary_{name_user}.xlsx'):
        pass
    else:
        kb = InlineKeyboardBuilder()
        kb.add(types.InlineKeyboardButton(
        text = 'Задай мне вопрос',
        callback_data = 'city'))
        df = pd.DataFrame(columns=['age', 'emotion', 'sleep', 'sleep_time', 'health', 'city', 'time', 'precipitation', 'weather'])
        df.to_excel(f'diary_{name_user}.xlsx')
        
        await callback.message.answer('''Хорошо, тогда приступим
        я задам тебе несколько вопросов
        и занесу их в таблицу. Ты сможешь 
        скачать её написав команду: 
            
        /download_diary''', reply_markup=kb.as_markup())

#вопрос по городу
@dp.callback_query(F.data == 'city', StateFilter(None))
async def city_check(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.answer(text = 'Введи название населённого пункта, в котором ты сейчас находишься')
    await state.set_state(Write_mess.write_city)


#получение ответа по городу
@dp.message(StateFilter(Write_mess.write_city))
async def weather_checking(message: types.Message, state: FSMContext):
    city = message.text.lower()
    if error_check(city):
        
        print(city)
        headers = {
            'User-Agent': ''
        }

        res = requests.get(
            f'https://www.google.com/search?q=погода+{city}',
            headers=headers
        )

        soup = BeautifulSoup(res.text, 'html.parser')

        time = soup.select('#wob_dts')[0].getText().strip()
        precipitation = soup.select('#wob_dc')[0].getText().strip()
        weather = soup.select('#wob_tm')[0].getText().strip()

        d_wather = {'G': city, 'H': time, 'I': precipitation, 'J': weather}
        dict_diary.update(d_wather)

        await state.update_data(write_city=message.text.lower())
        await message.answer(text = 'Спасибо, теперь введите свой возраст')
        await state.set_state(Write_mess.write_age)
    else:
        await state.set_state(Write_mess.write_city)
        await message.answer(text = 'Что-то пошло не так. Пожалуйста попробуй снова.')


age_list = [str(i) for i in range(101)]

@dp.message(
    Write_mess.write_age,
    F.text.in_(age_list)
)
async def age_checking(message: types.Message, state: FSMContext):
    age = message.text.lower()
    dict_diary['B'] = age
    await state.update_data(write_age = message.text.lower())
    await message.answer('Спасибо, теперь опиши свои эмоции кратко')
    await state.set_state(Write_mess.write_emotion)


@dp.message(Write_mess.write_emotion)
async def emotion_check(message: types.Message, state: FSMContext):
    emotion = message.text
    if error_check(emotion):
        dict_diary['C'] = emotion
        await state.update_data(write_emotion=message.text.lower())
        await message.answer(text = 'Спасибо, теперь напиши количество часов сегодняшнего сна')
        await state.set_state(Write_mess.write_sleep)
    else:
        await state.set_state(Write_mess.write_emotion)
        await message.answer('Что-то пошло не так. Пожалуйста попробуй ещё раз')



@dp.message(Write_mess.write_sleep)
async def sleep_check(message: types.Message, state: FSMContext):
    sleep1 = message.text
    if str(sleep1).isdigit() and int(sleep1) <= 48:
        dict_diary['D'] = sleep1
        await state.update_data(write_sleep=message.text.lower())
        await message.answer('Спасибо, теперь введи время когда вы легли и время когда проснулись строго в формате 00.00 - 00.00')
        await state.set_state(Write_mess.write_sleep_time)
    else:
        await message.answer('Что-то поло не так. Пожалуйста попробуйте ещё раз')
        await state.set_state(Write_mess.write_sleep)


@dp.message(Write_mess.write_sleep_time)
async def write_time_check(message: types.Message, state: FSMContext):
    sleep_tim = message.text.strip()
    prov = '00.00 - 00.00'.strip()
    if len(sleep_tim) == len(prov):
        dict_diary['E'] = sleep_tim
        await state.update_data(write_sleep_time=message.text.lower())
        await message.answer('Спасибо, теперь кратко опиши ваше самочувствие и возможные болезни')
        await state.set_state(Write_mess.write_health)
    else: 
        await message.answer('Введите время когда вы легли и время когда проснулись строго в формате 00.00 - 00.00')
        await state.set_state(Write_mess.write_sleep_time)


@dp.message(Write_mess.write_health)
async def health_check(message: types.Message, state: FSMContext):
    healthd = message.text
    newdate = datetime.now()
    if error_check(healthd):
        newdate = newdate.strftime('%d.%m.%Y')
        dict_diary['F'] = healthd
        dict_diary['A'] = newdate
        name_user = message.from_user.id
        fn = f'diary_{name_user}.xlsx'
        wb = load_workbook(fn)
        ws = wb['Sheet1']
        ws.append(dict_diary)
        wb.save(f'diary_{name_user}.xlsx')
        wb.close
        await state.update_data(write_health=message.text.lower())
        await state.clear()
        await message.answer('Спасибо, данные занесены в таблицу. Ты сможешь скачать её написав команду: /download_diary или удалить прописав команду: /del_diary') 
    else:
        await message.answer('Что-то пошло не так. Пожалуйста попробуйте ещё раз')
        await state.set_state(Write_mess.write_health)


@dp.message(Command('download_diary'))
async def download_diary_tabel(message: types.Message):
    name_user = message.from_user.id
    tebl = FSInputFile(f'diary_{name_user}.xlsx')
    await message.answer_document(tebl)


@dp.message(Command('del_diary'))
async def delete_diary(message: types.Message):
    name_user = message.from_user.id
    os.remove(f'diary_{name_user}.xlsx')
    await message.answer('Файл удалён')
    

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
