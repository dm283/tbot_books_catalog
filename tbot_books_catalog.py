import asyncio, logging, sys
from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Filter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from aiogram.utils.callback_answer import CallbackQuery, CallbackAnswer

import os, configparser
from pathlib import Path
from lib_db_manager import db_connection, db_read_data, db_insert_data, db_execute


config = configparser.ConfigParser()
config_file = os.path.join(Path(__file__).resolve().parent, 'config.ini')   
if os.path.exists(config_file):
  config.read(config_file, encoding='utf-8')
else:
  print("error! config file doesn't exist"); sys.exit()
TOKEN = config['bot']['bot_token']
DB_TYPE = config['db']['db_type']
DB_CONNECTION_STRING = config['db']['db_connection_string']
DB_USER = config['db']['db_user']
DB_PASSWORD = config['db']['db_password']
DB_TABLE = 'books_catalog'
if DB_TYPE == '-m' and 'DSN' in DB_CONNECTION_STRING:
  DB_CONNECTION_STRING += (';UID='+DB_USER+';PWD='+DB_PASSWORD)


conn, cursor = db_connection(DB_CONNECTION_STRING, DB_TYPE)

INPUT_STATUS = 'start'  #
UPDATE_BOOK_DATA = tuple()
ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO = '', '', ''
dp = Dispatcher()

builder = InlineKeyboardBuilder()
builder.button(text="books catalog", callback_data="catalog")
builder.button(text="my books", callback_data="my_books")
builder.button(text="add book", callback_data="add_book")
    
builder_add_book = InlineKeyboardBuilder()
builder_add_book.button(text="confirm", callback_data="add_book_confirm")
builder_add_book.button(text="cancel", callback_data="add_book_cancel")

builder_update_book = InlineKeyboardBuilder()
builder_update_book.button(text="confirm", callback_data="update_book_confirm")
builder_update_book.button(text="cancel", callback_data="update_book_cancel")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    #
    await message.answer(f'Hello, {hbold(message.from_user.full_name)}!')
    await message.answer(text='Select an action:', reply_markup=builder.as_markup())
    # await message.answer(text='add photo')
    

@dp.message()
async def message_handling(message: types.Message):
    #
    global INPUT_STATUS, ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO

    if INPUT_STATUS == 'input_title':
        ADD_BOOK_TITLE = message.text
        INPUT_STATUS = 'input_author'
        await message.answer(text='input author')
        return 0
    if INPUT_STATUS == 'input_author':
        ADD_BOOK_AUTHOR = message.text
        INPUT_STATUS = 'input_photo'
        await message.answer(text='add photo')
        return 0
    if INPUT_STATUS == 'input_photo':
        file_id = message.photo[0].file_id
        ADD_BOOK_PHOTO = file_id
        INPUT_STATUS = 'input_answer_add_book'
        caption = f'{ADD_BOOK_TITLE}\n{ADD_BOOK_AUTHOR}'
        chat_id = message.chat.id
        await message.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption)
        await message.answer(text='Add this book?', reply_markup=builder_add_book.as_markup())
        return 0
    
    if INPUT_STATUS == 'update_title':
        ADD_BOOK_TITLE = message.text
        INPUT_STATUS = 'update_author'
        await message.answer(text=f"update author '{UPDATE_BOOK_DATA[2]}'")
        return 0
    if INPUT_STATUS == 'update_author':
        ADD_BOOK_AUTHOR = message.text
        INPUT_STATUS = 'update_photo'
        await message.answer(text=f"change photo '{UPDATE_BOOK_DATA[3]}'")
        return 0
    if INPUT_STATUS == 'update_photo':
        file_id = message.photo[0].file_id
        ADD_BOOK_PHOTO = file_id
        INPUT_STATUS = 'input_answer_update_book'
        caption = f'{ADD_BOOK_TITLE}\n{ADD_BOOK_AUTHOR}'
        chat_id = message.chat.id
        await message.bot.send_photo(chat_id=chat_id, photo=file_id, caption=caption)
        await message.answer(text='Save updates?', reply_markup=builder_update_book.as_markup())
        return 0


@dp.callback_query(F.data == 'update_book_confirm')
async def btn_update_book_confirm_handler(callback: CallbackQuery):
    # update_book_confirm
    global INPUT_STATUS, ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO

    query = f"""update {DB_TABLE} set 
        title='{ADD_BOOK_TITLE}', 
        author='{ADD_BOOK_AUTHOR}', 
        photo='{ADD_BOOK_PHOTO}', 
        update_date=now() 
        where id = {UPDATE_BOOK_DATA[0]}"""
    print('QUERY =', query)
    db_execute(conn, cursor, query)

    await callback.message.answer(text='book updated successfully!')
    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())

    INPUT_STATUS = 'start'
    ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO = '', '', ''


@dp.callback_query(F.data == 'update_book_cancel')
async def btn_update_book_cancel_handler(callback: CallbackQuery):
    # add_book_confirm
    global INPUT_STATUS, ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO
    INPUT_STATUS = 'start'
    ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO = '', '', ''

    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())


@dp.callback_query(F.data == 'add_book_confirm')
async def btn_add_book_confirm_handler(callback: CallbackQuery):
    # add_book_confirm
    global INPUT_STATUS, ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO

    data_set = [(ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO, f'@{callback.from_user.username}'), ]
    columns = 'title, author, photo, book_owner'
    db_insert_data(conn, cursor, data_set, DB_TYPE, DB_TABLE, columns)

    await callback.message.answer(text='book added successfully!')
    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())

    INPUT_STATUS = 'start'
    ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO = '', '', ''


@dp.callback_query(F.data == 'add_book_cancel')
async def btn_add_book_cancel_handler(callback: CallbackQuery):
    # add_book_confirm
    global INPUT_STATUS, ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO
    INPUT_STATUS = 'start'
    ADD_BOOK_TITLE, ADD_BOOK_AUTHOR, ADD_BOOK_PHOTO = '', '', ''

    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())


def load_catalog_from_db(range, user):
    #
    books = list()
    if range == 'all':
        query = f'select * from {DB_TABLE}'
    elif range == 'my':
        query = f"select * from {DB_TABLE} where book_owner='@{user}'"
    catalog = db_read_data(cursor, query)

    for book in catalog:
        id = book[0]
        title = book[1]
        author = book[2]
        file_id = book[3]
        book_owner = book[4]
        books.append((id, file_id, f'<b>{title}</b>\n{author}\n{book_owner}'))
    return books


@dp.callback_query(F.data == 'catalog')
async def btn1_handler(callback: CallbackQuery):
    # books catalog
    books = load_catalog_from_db(range='all', user=callback.from_user.username)
    chat_id = callback.message.chat.id

    for book in books:
        await callback.message.bot.send_photo(chat_id=chat_id, photo=book[1], caption=book[2])
        #await callback.message.answer(text=msg)

    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())


@dp.callback_query(F.data == 'my_books')
async def btn2_handler(callback: CallbackQuery):
    # my books catalog
    books = load_catalog_from_db(range='my', user=callback.from_user.username)
    chat_id = callback.message.chat.id

    builder_my_book = {}

    for book in books:
        builder_my_book[book[0]] = InlineKeyboardBuilder()
        builder_my_book[book[0]].button(text="update", callback_data=f"my_book_update_{book[0]}")
        builder_my_book[book[0]].button(text="delete", callback_data=f"my_book_delete_{book[0]}")

        await callback.message.bot.send_photo(chat_id=chat_id, 
                                              photo=book[1], 
                                              caption=book[2],
                                              reply_markup=builder_my_book[book[0]].as_markup())

    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())    


@dp.callback_query(F.data == 'add_book')
async def btn3_handler(callback: CallbackQuery):
    # add book
    global INPUT_STATUS
    INPUT_STATUS = 'input_title'
    await callback.message.answer(text='input title')


@dp.callback_query(F.data.contains('my_book_update'))
async def btn_my_book_update(callback: CallbackQuery):
    # update book
    global INPUT_STATUS, UPDATE_BOOK_DATA
    update_book_id = int(callback.data.rpartition('_')[2])
    INPUT_STATUS = 'update_title'
    query = f'select id, title, author, photo from {DB_TABLE} where id = {update_book_id}'
    UPDATE_BOOK_DATA = db_read_data(cursor, query)[0]

    await callback.message.answer(text=f"update title '{UPDATE_BOOK_DATA[1]}'")



@dp.callback_query(F.data.contains('my_book_delete'))
async def btn_my_book_delete(callback: CallbackQuery):
    # delete book from database
    book_id = int(callback.data.rpartition('_')[2])
    print(book_id)

    query = f'select title from {DB_TABLE} where id = {book_id}'
    book_title = db_read_data(cursor, query)[0][0]

    builder_delete_book = InlineKeyboardBuilder()
    builder_delete_book.button(text="confirm", callback_data=f"confirm_delete_book_{book_id}")
    builder_delete_book.button(text="cancel", callback_data=f"cancel_delete_book_{book_id}")

    await callback.message.answer(text=f"Are you sure to delete your book '{book_title}'?",
                                  reply_markup=builder_delete_book.as_markup())


@dp.callback_query(F.data.contains('confirm_delete_book_'))
async def btn_my_book_delete_confirm(callback: CallbackQuery):
    #
    book_id = int(callback.data.rpartition('_')[2])
    query = f'delete from {DB_TABLE} where id = {book_id}'
    db_execute(conn, cursor, query)
    await callback.message.answer(text='book deleted')
    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())


@dp.callback_query(F.data.contains('cancel_delete_book_'))
async def btn_my_book_delete_cancel(callback: CallbackQuery):
    #
    await callback.message.answer(text='Select an action:', reply_markup=builder.as_markup())


#*********************************************************
async def main() -> None:
    bot = Bot(TOKEN, parse_mode=ParseMode.HTML)
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
