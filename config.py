import os
import json
import requests


class Config:
    def __init__(self):
        pass

    def create_config(self):
        if os.path.exists('config.json'):
            return True
        data = {
            'bot_token': '',
            # данные для авторизации на СМС сервере
            'url': '199.247.21.208.sslip.io',
            'login': 'developer',
            'password': 'Y7yAVCexmg86H9br',
            'lines':
                {},
            'hellomessages':
                {
                    'users': 'Главное меню',
                    'non-users': 'Для работы с ботом необходимо получить доступ, чтобы его получить обратитесь к разработчику бота и укажите ваш chat id.',
                    'admins': 'Вы вошли в меню администратора.\nВыберите действие, которое хотите сделать:'
                },
            'whitelist': ['907933015'],  # доступ пользователей. Для нескльких пользователей: ['123', '345']
            'adminlist': ['907933015'],  # доступ админов. Для нескльких админов: ['123', '345']
            'developerchat': 't.me'
        }
        with open('config.json', 'w') as config:
            json.dump(data, config)
        config.close()

    def get_bot_token(self):
        with open('config.json', 'r') as config:
            data = json.load(config)
            BOT_TOKEN = data['bot_token']
        config.close()
        return BOT_TOKEN

    def get_config(self):
        with open('config.json', 'r') as config:
            data = json.load(config)
        config.close()
        return data

    def change_config(self, data):
        with open('config.json', 'w') as config:
            json.dump(data, config)
        config.close()

    def get_lines(self):
        data = self.get_config()
        params = {
            'auth': {
                'username': data['login'],
                'password': data['password']}
        }
        response = requests.post(
            f'https://{data["url"]}/goip/querylines/', json=params)
        print(type(data))
        try:
            data['lines'] = {line['goip_line']: [data['lines'][line['goip_line']][0], data
            ['lines'][line['goip_line']][1], data['lines'][line['goip_line']][2]] for line in response.json()}
        except KeyError:
            data['lines'] = {line['goip_line']: [line['goip_line'], 1,
                                                 data['whitelist']] for line in response.json()}

        self.change_config(data)
        return response.json()

