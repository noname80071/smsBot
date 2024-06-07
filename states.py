from aiogram.fsm.state import State, StatesGroup


class ConfigChange(StatesGroup):
    config_change = State()


class GetPhoneNumber(StatesGroup):
    get_phone_number = State()


class GetCommandSms(StatesGroup):
    get_command_sms = State()
