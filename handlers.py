from aiogram import F, Router, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import requests

from config import Config
import kb
from kb import Pagination
import states

router = Router()
config = Config()
pagination = Pagination()


@router.message(Command('start'))
async def start(msg: Message, state: FSMContext):
    await show_main_menu(msg, state)


@router.callback_query(F.data == 'main_menu')
async def main_menu(clbck: CallbackQuery, state: FSMContext):
    await clbck.message.delete()
    await menu(clbck.message, state)


async def show_main_menu(msg: Message, state: FSMContext):
    await state.clear()
    await msg.delete()
    if str(msg.chat.id) not in (config.get_config()['whitelist']):
        text = config.get_config()['hellomessages']['non-users']
        await msg.answer(text, reply_markup=kb.kb_no_user_main_menu)
    else:
        await menu(msg, state)


async def menu(msg: Message, state: FSMContext):
    await state.clear()
    if str(msg.chat.id) in config.get_config()['adminlist']:
        await msg.answer(text='Выберите что хотите сделать:', reply_markup=kb.kb_admin_menu)
    else:
        await msg.answer(text='Выберите, что хотите сделать:', reply_markup=kb.kb_menu)


@router.callback_query(F.data == 'admin_panel')
async def admin_panel(clbck: CallbackQuery, state: FSMContext):
    await state.clear()
    if str(clbck.message.chat.id) in config.get_config()['adminlist']:
        await clbck.message.edit_text(config.get_config()['hellomessages']['admins'], reply_markup=kb.kb_admin_panel)
    else:
        await clbck.message.edit_text('Вы не являетесь админом!')


def send_sms(line_id, number, content):
    data = config.get_config()
    params = {
        'auth': {
            'username': data["login"],
            'password': data["password"]
        },
        'goip_line': line_id,
        'number': number,
        'content': content
    }
    response = requests.post(
        f'https://{data["url"]}/goip/sendsms/', json=params)
    print(response.reason)
    print(response.text)
    return response.text + response.reason


def send_ussd(line_id, comand):
    data = config.get_config()
    response = requests.get(
        f'https://{data["url"]}/goip/en/ussd.php?USERNAME={data["login"]}&PASSWORD={data["password"]}&TERMID={line_id}'
        f'&USSDMSG={comand.replace("*", "%2A").replace("#", "%23")}')
    return response.text


@router.callback_query(F.data == 'show_chat_id')
async def show_chat_id(clbck: CallbackQuery):
    await clbck.message.edit_text(text=f'Ваш chat id: {clbck.message.chat.id}', reply_markup=kb.back_to_menu)


@router.callback_query(F.data.startswith('send1_'))
async def send1(clbck: CallbackQuery, state: FSMContext):
    await clbck.message.edit_text(text='Выберите линию:', reply_markup=await kb.create_buttons_1(clbck, state))


@router.callback_query(F.data.startswith('send2_'))
async def send2(clbck: CallbackQuery, state: FSMContext):
    await state.update_data({
        "line_id": clbck.data.split('_')[-1]
    })

    data = await state.get_data()
    target = data.get("target")
    if target == 'sms':
        await clbck.message.edit_text(text='Введите номер телефона, на который будет отправлено SMS:',
                                      reply_markup=kb.back_to_menu)
        await state.set_state(states.GetPhoneNumber.get_phone_number)
    elif target == 'ussd':
        await clbck.message.edit_text(text='Введите команду:',
                                      reply_markup=kb.back_to_menu)
        await state.set_state(states.GetCommandSms.get_command_sms)


@router.message(states.GetPhoneNumber.get_phone_number)
async def get_phone_number(msg: Message, state: FSMContext):
    # allowed_characters = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '#']
    if len(msg.text.strip()) <= 18 and msg.text.strip()[0] == '+' and (msg.text.strip()[1:].isdigit() or '*' in msg.text.strip()[1:] or
                                       '#' in msg.text.strip()[1:]):
        await state.update_data({
            "phone_number": msg.text,
        })
        await msg.delete()
        await msg.answer(text='Введите текст SMS:',
                         reply_markup=kb.back_to_menu)
        await state.set_state(states.GetCommandSms.get_command_sms)
    else:
        await msg.delete()
        await msg.answer(text='Неверный формат для номера телефона.',
                         reply_markup=kb.back_to_menu)


@router.callback_query(F.data == 'ussd_answer', states.GetCommandSms.get_command_sms)
async def answer_ussd(clbck: CallbackQuery, state: FSMContext):
    await state.set_state(states.GetCommandSms.get_command_sms)
    await clbck.message.edit_text(text='Введите команду:',
                                  reply_markup=kb.back_to_menu)


@router.message(states.GetCommandSms.get_command_sms)
async def get_comand_sms(msg: Message, state: FSMContext):
    data = await state.get_data()
    target = data['target']
    line_id = data['line_id']
    if target == 'sms':
        phone_number = data['phone_number']
        response = send_sms(line_id, phone_number, msg.text)
        await msg.answer(text='Ответ сервера:\n' + response, reply_markup=kb.back_to_menu)
        await state.clear()
    elif target == 'ussd':
        response = send_ussd(line_id, msg.text)
        await msg.answer(text=f'Ваша команда: {msg.text}')
        await msg.answer(text='Ответ сервера:\n' + response, reply_markup=kb.kb_ussd_answer)


@router.callback_query(F.data.startswith('users_access'))
async def change_access(clbck: CallbackQuery, bot: Bot):
    await clbck.message.edit_text(text='Выберите пользователя, для которого хотите изменить разрешённые линии',
                                  reply_markup=await kb.create_buttons_change_access(clbck, bot))


@router.callback_query(F.data.startswith('changeaccess_'))
async def switch_access(clbck: CallbackQuery, state: FSMContext):
    await show_list_change_access(clbck, state, clbck.data)


async def show_list_change_access(clbck: CallbackQuery, state: FSMContext, callback_data):
    await clbck.message.edit_text(text='Выберите линию, для которой хотите изменить значение',
                                  reply_markup=await kb.create_buttons_show_list_change_access(state, callback_data))


@router.callback_query(F.data.startswith('switchstatus_'))
async def switch_status(clbck: CallbackQuery, state: FSMContext):
    line = await pagination.get_last_word_without_page_word(clbck.data)
    data = await state.get_data()
    id = data['id']
    data = config.get_config()
    status = id in data["lines"][line][2]
    if status:
        data['lines'][line][2].remove(id)
    else:
        data['lines'][line][2].append(id)
    config.change_config(data)
    callback_data = f"changeaccess_{id}"
    await show_list_change_access(clbck, state, callback_data)


async def show_list_change_lines_status(clbck: CallbackQuery, callback_data):
    await clbck.message.edit_text(text='Выберите линию, для которой хотите изменить статус:',
                                  reply_markup=await kb.create_buttons_show_list_change_lines_status(callback_data))


async def show_list_change_lines(clbck: CallbackQuery):
    await clbck.message.edit_text(text='Выберите линию, для которой хотите изменить название:',
                                  reply_markup=await kb.create_buttons_show_list_change_lines(clbck))


@router.callback_query(F.data.startswith('confchange_'))
async def config_change(clbck: CallbackQuery, state: FSMContext):
    target = await pagination.get_last_word_without_page_word(clbck.data)
    print(target)
    if target in ['url', 'login', 'password', 'developerchat']:
        await state.update_data({'target': target})
        if target == 'password':
            await clbck.message.edit_text(text='Введите новое значения для переменной конфига:',
                                          reply_markup=kb.back_to_admin_menu)
        else:
            await clbck.message.edit_text(text=f'Введите новое значения для переменной конфига: \n'
                                          f'Текущее значение <code>{config.get_config()[target]}</code>',
                                          reply_markup=kb.back_to_admin_menu)
        await state.set_state(states.ConfigChange.config_change)
    elif target == 'lines':
        await show_list_change_lines(clbck)
    elif target == 'linesstatus':
        await show_list_change_lines_status(clbck, clbck.data)
    elif target == 'hellomessages':
        await clbck.message.edit_text(text='Выберите действие:',
                                      reply_markup=kb.kb_change_config_hellomessage)
    elif target == 'whitelist' or target == 'adminlist':
        await state.update_data({'target': target})
        await clbck.message.edit_text(text='Выберите действие:',
                                      reply_markup=kb.kb_change_config_whitelist)


@router.callback_query(F.data.startswith('linestatus-change_'))
async def linestatus_change(clbck: CallbackQuery):
    print('line_status')
    target = clbck.data.split('_')[-1]
    data = config.get_config()
    data['lines'][target][1] = int(not (data['lines'][target][1]))
    config.change_config(data)
    callback_data = "confchange_linesstatus"
    await show_list_change_lines_status(clbck, callback_data)


@router.callback_query(F.data.startswith('add_'))
async def add_to_list(clbck: CallbackQuery, state: FSMContext):
    target = clbck.data.split('_')[-1]
    data = await state.get_data()
    data['target'] = target
    data['subtarget'] = 'add'
    await state.update_data(data=data)
    await clbck.message.edit_text(text='Введите chat_id:',
                                  reply_markup=kb.back_to_admin_menu)
    await state.set_state(states.ConfigChange.config_change)


@router.callback_query(F.data.startswith('remove_'))
async def remove_from_list(clbck: CallbackQuery, state: FSMContext):
    target = clbck.data.split('_')[-1]
    data = await state.get_data()
    data['target'] = target
    data['subtarget'] = 'remove'
    await state.update_data(data=data)
    await clbck.message.edit_text(text='Введите chat_id:',
                                  reply_markup=kb.back_to_admin_menu)
    await state.set_state(states.ConfigChange.config_change)


@router.callback_query(F.data.startswith('check_'))
async def check_list(clbck: CallbackQuery, bot: Bot):
    target = clbck.data.split('_')[-1]
    data = config.get_config()[target]
    for i in range(len(data)):
        try:
            username = await bot.get_chat(int(data[i]))
            username = username.username
        except:
            username = None
        data[i] = f'{username} - {data[i]}'
    ans = {'whitelist': 'пользователей', 'adminlist': 'админов'}
    await clbck.message.edit_text(f'Список {ans[target]}:\n' + "\n".join(data), reply_markup=kb.back_to_admin_menu)


@router.callback_query(F.data.startswith('hellochange_'))
async def hello_change(clbck: CallbackQuery, state: FSMContext):
    target = clbck.data.split('_')[-1]
    data = await state.get_data()
    data['target'] = 'hellomessages'
    data['subtarget'] = target
    await state.update_data(data)
    await clbck.message.edit_text(text=f'Пришлите новое значение для переменной: \n'
                                       f'Текущее значение: <code>{config.get_config()["hellomessages"][target]}</code>',
                                  reply_markup=kb.back_to_admin_menu)
    await state.set_state(states.ConfigChange.config_change)


@router.callback_query(F.data.startswith('linename-change_'))
async def linename_change(clbck: CallbackQuery, state: FSMContext):
    target = clbck.data.split('_')[-1]
    await clbck.message.edit_text(text=f'Введите новое название для выбранной линии: \n'
                                       f'Текущее значение: {config.get_config()["lines"][target][0]}',
                                  reply_markup=kb.back_to_admin_menu)
    data = await state.get_data()
    data['target'] = 'lines'
    data['subtarget'] = target
    await state.update_data(data)
    await state.set_state(states.ConfigChange.config_change)


@router.message(states.ConfigChange.config_change)
async def changing_config(msg: Message, state: FSMContext):
    data = await state.get_data()
    target = data['target']
    subtarget = data.get('subtarget')
    conf = config.get_config()
    print(target, subtarget)
    if subtarget:
        if target == 'whitelist' or target == 'adminlist':
            if subtarget == 'add':
                if msg.text not in conf[target]:
                    conf[target].append(msg.text)
                    for line in conf['lines']:
                        if msg.text not in conf['lines'][line][2]:
                            conf['lines'][line][2].append(msg.text)
            elif subtarget == 'remove':
                if msg.text in conf[target]:
                    conf[target].remove(msg.text)
                    for line in conf['lines']:
                        if msg.text in conf['lines'][line][2]:
                            conf['lines'][line][2].remove(msg.text)
            await state.clear()
            print(f'confchange_{target}')
            config.change_config(conf)
            return await msg.answer('Успешно применены изменения.', reply_markup=kb.back_to_admin_menu)
        elif target == 'lines':
            conf[target][subtarget][0] = msg.text
        elif target == 'hellomessages':
            conf[target][subtarget] = msg.text
    else:
        conf[target] = msg.text
    config.change_config(conf)
    data = await state.update_data({
        "subtarget": False
    })
    await msg.answer('Успешно применены изменения.', reply_markup=kb.back_to_admin_menu)
    await state.clear()
