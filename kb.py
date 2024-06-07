from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

import re
from config import Config

config = Config()


class Pagination:
    def __init__(self):
        self.max_items_on_page = 30
        self.buttons_in_one_row = 2

    async def append_list_as_buttons(self, prepared_data, kb):
        buttons_in_one_row = self.buttons_in_one_row
        prepared_data = [prepared_data[i:i+buttons_in_one_row]
                         for i in range(0, len(prepared_data),  buttons_in_one_row)]
        for item in prepared_data:
            buttons = [InlineKeyboardButton(
                text=el["text"], callback_data=el["callback_data"]) for el in item]
            kb.row(*buttons)
        kb.adjust(1)
        return kb

    async def append_pagination_buttons(self, callback_data, is_last_page, page, kb):
        pagination_buttons = []
        if page != 0:
            pagination_buttons.append(InlineKeyboardButton(
                text='<<', callback_data=f'{callback_data}@page{page-1}@'))
            pagination_buttons.append(InlineKeyboardButton(
                text=f"{page}", callback_data="*"))
        if not is_last_page:
            if not len(pagination_buttons):
                pagination_buttons.append(InlineKeyboardButton(
                    text=f"{page}", callback_data="*"))
            pagination_buttons.append(InlineKeyboardButton(
                text='>>', callback_data=f'{callback_data}@page{page+1}@'))
        if len(pagination_buttons):
            kb.row(*pagination_buttons)
            kb.adjust(1)
        return kb

    async def pagination_get_offsets(self, lines, current_page):
        is_last_page = True
        max_items_on_page = self.max_items_on_page
        start_offset = max_items_on_page * current_page
        end_offset = start_offset+max_items_on_page if start_offset + \
            max_items_on_page < len(lines) else len(lines) - 1
        if end_offset != len(lines)-1:
            is_last_page = False
        return start_offset, end_offset, is_last_page

    async def find_current_page(self, callback_data):
        page = 0
        found_page = re.findall(r"@page[0-9]+@", callback_data)
        found_page = found_page[0] if found_page else ""
        if found_page:
            page = int(found_page.replace("@", "").replace("page", ""))
            callback_data = callback_data.replace(found_page, "")
        return callback_data, page

    async def get_last_word_without_page_word(self, callback_data):
        target = callback_data.split('_')[-1]
        found_page = re.findall(r"@page[0-9]+@", target)
        found_page = found_page[0] if found_page else ""
        if found_page:
            target = target.replace(found_page, "")
        return target


async def create_buttons_1(clbck, state):
    pagination = Pagination()
    await state.update_data({"target": await pagination.get_last_word_without_page_word(clbck.data)})
    callback_data, page = await pagination.find_current_page(clbck.data)
    data = config.get_config()
    lines = config.get_lines()
    start_offset, end_offset, is_last_page = await pagination.pagination_get_offsets(
        lines, page)
    kb = InlineKeyboardBuilder()
    prepared_data = [
        {
            "text": data["lines"][line["goip_line"]][0],
            "callback_data": 'send2_' + line['goip_line']
        }
        for line in lines[start_offset:end_offset]
        if data['lines'][line['goip_line']][1] == 1 and str(clbck.message.chat.id) in data
        ['lines'][line['goip_line']][2]]
    kb = await pagination.append_list_as_buttons(prepared_data, kb)
    kb = await pagination.append_pagination_buttons(
        callback_data, is_last_page, page, kb)
    kb.row(InlineKeyboardButton(text='В меню', callback_data='main_menu'))
    return kb.as_markup()


kb_no_user_main_menu = [
    [InlineKeyboardButton(text='Связаться с разработчиком', url=config.get_config()['developerchat']),
     InlineKeyboardButton(text='Узнать ваш chat id', callback_data='show_chat_id')],
]
kb_no_user_main_menu = InlineKeyboardMarkup(inline_keyboard=kb_no_user_main_menu)

kb_menu = [
    [InlineKeyboardButton(text='Отправить SMS', callback_data='send1_sms'),
     InlineKeyboardButton(text='Отправить USSD', callback_data='send1_ussd')],
    [InlineKeyboardButton(text='Узнать ваш chat_id', callback_data='show_chat_id')]
]
kb_menu = InlineKeyboardMarkup(inline_keyboard=kb_menu)

kb_admin_menu = [
    [InlineKeyboardButton(text='Отправить SMS', callback_data='send1_sms'),
     InlineKeyboardButton(text='Отправить USSD', callback_data='send1_ussd')],
    [InlineKeyboardButton(text='Узнать ваш chat_id', callback_data='show_chat_id')],
    [InlineKeyboardButton(text='Администрирование', callback_data='admin_panel')]
]
kb_admin_menu = InlineKeyboardMarkup(inline_keyboard=kb_admin_menu)

kb_ussd_answer = [
    [InlineKeyboardButton(text='Отправить ответ', callback_data='ussd_answer')],
    [InlineKeyboardButton(text='Назад', callback_data='main_menu')]
]
kb_ussd_answer = InlineKeyboardMarkup(inline_keyboard=kb_ussd_answer)

back_to_menu = [
    [InlineKeyboardButton(text='Назад', callback_data='main_menu')]
]
back_to_menu = InlineKeyboardMarkup(inline_keyboard=back_to_menu)

back_to_admin_menu = [
    [InlineKeyboardButton(text='Вернуться в предыдущее меню', callback_data='admin_panel')]
]
back_to_admin_menu = InlineKeyboardMarkup(inline_keyboard=back_to_admin_menu)

kb_admin_panel = [
    [InlineKeyboardButton(text='URL SMS сервера', callback_data='confchange_url')],
    [InlineKeyboardButton(text='Логин SMS сервера', callback_data='confchange_login'),
     InlineKeyboardButton(text='Пароль SMS сервера', callback_data='confchange_password')],
    [InlineKeyboardButton(text='Ссылка на разработчика', callback_data='confchange_developerchat')],
    [InlineKeyboardButton(text='Задать названия линий', callback_data='confchange_lines'),
     InlineKeyboardButton(text='Задать видимость линий', callback_data='confchange_linesstatus')],
    [InlineKeyboardButton(text='Задать доступ пользователя к линиям', callback_data='users_access')],
    [InlineKeyboardButton(text='Задать текстовое приветствие бота', callback_data='confchange_hellomessages')],
    [InlineKeyboardButton(text='Спискок пользователей бота', callback_data='confchange_whitelist'),
     InlineKeyboardButton(text='Список админов бота', callback_data='confchange_adminlist')],
    [InlineKeyboardButton(text='Назад', callback_data='main_menu')]
]
kb_admin_panel = InlineKeyboardMarkup(inline_keyboard=kb_admin_panel)

kb_change_config_hellomessage = [
    [InlineKeyboardButton(text='Текст для пользователей без доступа',
                          callback_data='hellochange_non-users'),
     InlineKeyboardButton(text='Текст для пользователей с доступом',
                          callback_data='hellochange_users')],
    [InlineKeyboardButton(text='Текст для админов',
                          callback_data='hellochange_admins')],
    [InlineKeyboardButton(text='Вернуться в предыдущее меню',
                          callback_data='admin_panel')]
]
kb_change_config_hellomessage = InlineKeyboardMarkup(inline_keyboard=kb_change_config_hellomessage)

kb_change_config_whitelist = [
    [InlineKeyboardButton(text='Добавить в список', callback_data='add_whitelist'),
     InlineKeyboardButton(text='Удалить из списка', callback_data='remove_whitelist')],
    [InlineKeyboardButton(text='Посмотреть список', callback_data=f'check_whitelist')],
    [InlineKeyboardButton(text='Вернуться в предыдущее меню', callback_data='admin_panel')]
]
kb_change_config_whitelist = InlineKeyboardMarkup(inline_keyboard=kb_change_config_whitelist)


async def create_buttons_change_access(clbck, bot):
    kb = InlineKeyboardBuilder()
    for id in config.get_config()['whitelist']:
        try:
            username = await bot.get_chat(int(id))
            username = username.username
        except Exception as e:
            username = None
        kb.row(InlineKeyboardButton(
            text=f'{username} - {id}', callback_data=f'changeaccess_{id}'))
    kb.row(InlineKeyboardButton(
        text='Вернуться в предыдущее меню', callback_data='admin_panel'))
    return kb.as_markup()


async def create_buttons_show_list_change_access(state, callback_data):
    pagination = Pagination()
    id = await pagination.get_last_word_without_page_word(callback_data)
    callback_data, page = await pagination.find_current_page(
        callback_data)
    data = config.get_config()
    lines = config.get_lines()
    start_offset, end_offset, is_last_page = await pagination.pagination_get_offsets(
        lines, page)
    await state.update_data({'id': id})
    kb = InlineKeyboardBuilder()
    statusdict = {True: "ON", False: "OFF"}
    prepared_data = [{
        "text": f'{statusdict[id in data["lines"][line["goip_line"]][2]]} - {data["lines"][line["goip_line"]][0]}',
        "callback_data": f'switchstatus_{line["goip_line"]}'} for line in
        lines[start_offset:end_offset + 1 + 1]]

    kb = await pagination.append_list_as_buttons(prepared_data, kb)
    kb = await pagination.append_pagination_buttons(
        callback_data, is_last_page, page, kb)
    kb.row(InlineKeyboardButton(
        text='Вернуться в предыдущее меню', callback_data='users_access'))
    return kb.as_markup()


async def create_buttons_show_list_change_lines_status(callback_data):
    pagination = Pagination()
    callback_data, page = await pagination.find_current_page(
        callback_data)
    data = config.get_config()
    lines = config.get_lines()
    start_offset, end_offset, is_last_page = await pagination.pagination_get_offsets(
        lines, page)
    kb = InlineKeyboardBuilder()
    status_dict = {0: 'OFF', 1: 'ON'}
    prepared_data = [{
                         "text": f'{status_dict[data["lines"][line["goip_line"]][1]]} - {line["goip_line"]} : {data["lines"][line["goip_line"]][0]}',
                         "callback_data": f'linestatus-change_{line["goip_line"]}'} for line in
                     lines[start_offset:end_offset + 1 + 1]]
    kb = await pagination.append_list_as_buttons(prepared_data, kb)
    kb = await pagination.append_pagination_buttons(
        callback_data, is_last_page, page, kb)
    kb.row(InlineKeyboardButton(
        text='Вернуться в предыдущее меню', callback_data='admin_panel'))
    return kb.as_markup()


async def create_buttons_show_list_change_lines(clbck):
    pagination = Pagination()
    callback_data, page = await pagination.find_current_page(
        clbck.data)
    data = config.get_config()
    lines = config.get_lines()
    start_offset, end_offset, is_last_page = await pagination.pagination_get_offsets(
        lines, page)
    kb = InlineKeyboardBuilder()
    prepared_data = [{"text": f'{line["goip_line"]} : {data["lines"][line["goip_line"]][0]}',
                      "callback_data": f'linename-change_{line["goip_line"]}'} for line in
                     lines[start_offset:end_offset + 1 + 1]]
    kb = await pagination.append_list_as_buttons(prepared_data, kb)
    kb = await pagination.append_pagination_buttons(
        callback_data, is_last_page, page, kb)
    kb.row(InlineKeyboardButton(
        text='Вернуться в предыдущее меню', callback_data='admin_panel'))
    return kb.as_markup()
