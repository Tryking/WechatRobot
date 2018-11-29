import json
import random

import requests

from wxpy import *

from libs.config import TULING_REQUEST_PARAMS, TULING_URL, DB_NAME
from libs.sqlite import *

request_sess = requests.session()

bot = Bot(cache_path=True, console_qr=True)

Bot.enable_puid(bot)
SQLITE = Sqlite(db_name=DB_NAME)


def get_reply(text, puid=None):
    try:
        request_params = TULING_REQUEST_PARAMS.copy()
        if puid is not None:
            request_params['userInfo']['userId'] = puid
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


def handle_friends(msg):
    """
    处理好友请求
    :return:
    """
    # 接受好友 (msg.card 为该请求的用户对象)
    new_friend = bot.accept_friend(msg.card)
    # 或 new_friend = msg.card.accept()
    # 向新的好友发送消息
    new_friend.send('哈哈哈')


def handle_text(msg):
    """
    处理文本消息
    :param msg:
    :return:
    """
    need_send = False
    if isinstance(msg.chat, Friend):
        need_send = True
    else:
        puid = msg.sender.puid
        print(puid)
        status = SQLITE.get_wechat_group_status(group_puid=msg.sender.puid)
        status = status['status']
        if status == 'idioms_solitaire':
            need_send = True
        elif msg.is_at:
            need_send = True
        else:
            if random.randint(1, 5) == 3:
                need_send = True
    if need_send:
        text = get_reply(msg.text, msg.sender.puid)
        if '进入成语接龙模式：' in text:
            # 更新数据库
            SQLITE.update_wechat_group_status(group_puid=msg.sender.puid, status='idioms_solitaire')
        elif '退出成语接龙模式' in text:
            # 更新数据库
            SQLITE.update_wechat_group_status(group_puid=msg.sender.puid, status='nothing')
        msg.reply(text)


@bot.register()
def reply(msg):
    print(msg)
    # 处理好友请求
    if msg.type == FRIENDS:
        handle_friends(msg)
    elif msg.type == TEXT:
        handle_text(msg)
    else:
        pass


# 堵塞线程，并进入 Python 命令行
embed()
