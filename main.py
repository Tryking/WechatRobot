import json

import requests

from wxpy import *

TULING_URL = 'http://openapi.tuling123.com/openapi/api/v2'
API_KEY = 'd498ae5d6bcf4adbb5e9ccf23d161fe1'
USERID = 'cd6c54cc75c834cb'
perception = {'text': None}
request_params = {'req_type': 0, 'userInfo': {'apiKey': API_KEY, 'userId': USERID}, 'perception': perception}
request_sess = requests.session()

bot = Bot(cache_path=True, console_qr=True)

Bot.enable_puid(bot)


def get_reply(text):
    try:
        request_params['perception'] = {'inputText': {'text': str(text).replace('小小\u2005', '')}}
        print(request_params)
        result = request_sess.post(url=TULING_URL, data=json.dumps(request_params))
        result = json.loads(result.text)
        print(result)
        result = result['results'][0]['values']['text']
    except Exception as e:
        print(str(e))
        result = '我接口调不通啦~'
    if result == '如果你什么都不说，我也不知道怎么回答你呀':
        result = text
    return result


# 回复 my_friend 发送的消息
@bot.register(msg_types=TEXT)
def reply_group(msg):
    print(msg)
    msg.reply(get_reply(msg.text))


# 堵塞线程，并进入 Python 命令行
embed()
