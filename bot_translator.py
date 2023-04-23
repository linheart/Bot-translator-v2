import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from translatepy.translators.deepl import DeeplTranslate as deepl
from translatepy.translators.yandex import YandexTranslate as yandex
from translatepy.translators.deepl import DeeplTranslate as deepl
from translatepy.translators.google import GoogleTranslate as google
from translatepy.translators.reverso import ReversoTranslate as reverso
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

API_TOKEN = '6062915875:AAEN77tMyekgNEO6hwgosYDHZyN5-EtgJqA'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

dictionary = {'from_lang' : None, 'to_lang' : None, 'state_del': 0}

# Tab menu
commands = [
        types.BotCommand("/start", "Start the bot"),
        types.BotCommand("/add", "Adds text to the dictionary"),
        types.BotCommand("/dictionary", "Output the list of saved words"),
        types.BotCommand("/check", "Translation check"),
        types.BotCommand("/swap", "Swap the languages"),
        types.BotCommand("/delete", "Removes text from the dictionary"),
        types.BotCommand("/select", "Translator selection"),
        types.BotCommand("/reminder", "Set a reminder"),
]

async def set_commands(commands):
    await dp.bot.set_my_commands(commands)

# Buttons for selecting language
EnglishButton = InlineKeyboardButton(text='English', callback_data='English')
RussianButton = InlineKeyboardButton(text='Russian', callback_data='Russian')

keyboard = InlineKeyboardMarkup(row_width=2).add(EnglishButton, RussianButton)

# dictionary keyboard 
dict_keyboard = InlineKeyboardMarkup(row_width=2)

# Buttons to choose translator
YandexButton = InlineKeyboardButton(text='Yandex', callback_data='yandex')
DeeplButton = InlineKeyboardButton(text='Deepl', callback_data='deepl')
GoogleButton = InlineKeyboardButton("Google", callback_data='google')
ReversoButton = InlineKeyboardButton("Reverso", callback_data='reverso')

translator_keyboard = InlineKeyboardMarkup(row_width=1).add(YandexButton, DeeplButton, GoogleButton, ReversoButton)

# class for FSMContext
class AddItem(StatesGroup):
    waiting_for_lang = State()
    waiting_for_key = State()
    waiting_for_value = State()
    waiting_for_translator = State()
    waiting_for_deleting = State()

#handler to start chat bot
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await set_commands(commands)
    await message.answer("Hi\nI'm Bot translator v2.0. Select the language you wish to translate from:", reply_markup=keyboard)
    await AddItem.waiting_for_lang.set()

#handler to select language
@dp.callback_query_handler(state=AddItem.waiting_for_lang)
async def select_language(call: types.CallbackQuery, state: FSMContext):
    inline_keyboard = call.message.reply_markup.inline_keyboard[0]
    button_index = 0 if call.data == 'English' else 1
    dictionary['from_lang'] = call.data
    dictionary['to_lang'] = inline_keyboard[1 - button_index]
    await call.answer()
    keyboard.inline_keyboard[0][button_index].text = f"✅{call.data}"
    if "✅" in keyboard.inline_keyboard[0][1 - button_index].text:
        keyboard.inline_keyboard[0][1 - button_index].text = f"{inline_keyboard[1 - button_index].text[1:]}"
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=keyboard)

#handler to swap languages
@dp.message_handler(commands=['swap'], state='*')
async def cmp_swap(message: types.Message, state: FSMContext):
    await state.finish()
    if dictionary['from_lang']:
        to_lang = dictionary['to_lang']
        dictionary['to_lang'] = dictionary['from_lang']
        dictionary['from_lang'] = to_lang
        await message.answer(f"Selected {to_lang.upper()} language")
    else:
        await AddItem.waiting_for_lang.set()
        await message.answer("Please, select the language first", reply_markup=keyboard)

#handler to print list of saved words
@dp.message_handler(commands=['dictionary'], state='*')
async def cmd_dictionary(message: types.Message, state: FSMContext):
    await state.finish()
    if len(dict_keyboard.inline_keyboard) > 0:
        await message.answer(text="words", reply_markup=dict_keyboard)
    else:
        await message.answer("The dictionary is empty.")

@dp.callback_query_handler(lambda call: True)
async def words(call: types.CallbackQuery):
    await call.answer()


#handler for deleting text
@dp.message_handler(commands=['delete'], state='*')
async def cmd_delete(message: types.Message, state: FSMContext):
    await state.finish()
    if len(dict_keyboard.inline_keyboard) > 0:
        await AddItem.waiting_for_deleting.set()
        await message.answer('choose word to delete', reply_markup=dict_keyboard)
    else:
        await message.answer('Dictionary is empty')

@dp.callback_query_handler(state=AddItem.waiting_for_deleting)
async def proccess_key_and_value(call: types.CallbackQuery):
    inline_keyboard = call.message.reply_markup.inline_keyboard
    for row in inline_keyboard:
        for button in range(2):
            if row[button].text == call.data:
                inline_keyboard.remove(row)
                break
    dict_keyboard.inline_keyboard = inline_keyboard
    await bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=dict_keyboard)
    await call.answer()

#handler gor chosing translator
@dp.message_handler(commands=['select'], state='*')
async def cmd_select(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("Please, select the translator you wish", reply_markup=translator_keyboard)
    await AddItem.waiting_for_translator.set()
    

@dp.callback_query_handler(state=AddItem.waiting_for_translator)
async def proccess_selection(call: types.CallbackQuery):
    dictionary['translator'] = call.data
    await bot.send_message(call.message.chat.id, f'{call.data} has been selected')
    await call.answer()

#handler to add text to the dictionary
@dp.message_handler(commands=['add'], state='*')
async def cmd_add(message: types.Message):
    if dictionary['from_lang']:
       await message.answer("Enter text:")
       await AddItem.waiting_for_key.set()
    else:
        await AddItem.waiting_for_lang.set()
        await message.answer("Please, select the language first", reply_markup=keyboard)

@dp.message_handler(state=AddItem.waiting_for_key)
async def process_key(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['key'] = message.text
    await AddItem.next()
    await message.answer("Enter description")

@dp.message_handler(state=AddItem.waiting_for_value)
async def process_value(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['value'] = message.text
    word = InlineKeyboardButton(text=data['key'], callback_data=data['key'])
    translate = InlineKeyboardButton(text=data['value'], callback_data=data['value'])
    dict_keyboard.add(word, translate)
    await message.answer("Text saved successfully")
    await state.finish()

#handler to translate
@dp.message_handler(state='*')
async def translate_text(message: types.Message, state: FSMContext):
    await state.finish()
    src = dictionary['from_lang']
    dst = dictionary['to_lang']
    if not 'translator' in dictionary or dictionary['translator'] == 'yandex':
        translator = yandex()
    elif dictionary['translator'] == 'deepl':
        translator = deepl()
    elif dictionary['translator'] == 'google':
        translator = google()
    else:
        translator = reverso()
    try:
        await message.reply(str(translator.translate(message.text, dst, src)))
    except Exception:
        await message.answer("Translation failed. Please try again later.")

async def main():
    await dp.start_polling()

if __name__ == '__main__':
    asyncio.run(main())
