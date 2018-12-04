import json
import os
import random
import threading
import time

import requests

from wxpy import *

from libs import mongodb
from libs.config import TULING_REQUEST_PARAMS, TULING_URL, DB_NAME, GUESS_IDIOM_MAX_TIMES, GUESS_IDIOM_HINT_TIME
from libs.sqlite import *

request_sess = requests.session()

bot = Bot(cache_path=True, console_qr=True)

DEFAULT_PUID = 'default'

Bot.enable_puid(bot)
SQLITE = Sqlite(db_name=DB_NAME)
DB_CLIENT = mongodb.MongoClient()

IDIOT_PATH = 'idiots'
# 成语文件
IDIOT_FILES = [os.path.join(IDIOT_PATH, f) for f in os.listdir(IDIOT_PATH) if
               os.path.isfile(os.path.join(IDIOT_PATH, f))]


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
        result = '我想安静一会~'
    if result == '如果你什么都不说，我也不知道怎么回答你呀':
        result = text
    return result


def guess_idiom_thread_hint(msg, puid, times):
    """
    定时判断当前成语是否被猜中，如果没有，则进行提醒
    :return:
    """
    time.sleep(GUESS_IDIOM_HINT_TIME)
    instance = DB_CLIENT.get_idiom_status(puid, init=False)
    if instance and instance['play_times'] == times:
        hint_word = '■■■' + instance['answer'][-1]
        # 说明上次的还没猜对，进行提醒
        msg.reply('这都过去 {} 秒了，还没猜出来？\n提醒一下：{}'.format(GUESS_IDIOM_HINT_TIME, hint_word))


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


def handle_guess_idiom(msg, is_restart=False):
    """
    猜成语
    :return:
    """
    puid = msg.sender.puid
    if msg.is_at and '退出猜成语' in msg.text:
        # 游戏结束，数据库中关闭，聊天对象更新为nothing
        DB_CLIENT.idiom_status_close_game(puid)
        SQLITE.update_wechat_group_status(group_puid=msg.sender.puid, status='nothing')
        msg.reply('本次游戏退出，下次我们继续哦~')
        return
    if puid is None:
        puid = DEFAULT_PUID
    if is_restart:
        instance = DB_CLIENT.get_idiom_status(puid)
    else:
        instance = DB_CLIENT.get_idiom_status(puid, init=False)
        if instance is None:
            msg.reply('看来你不想玩儿猜成语了，我们聊天吧~')
            SQLITE.update_wechat_group_status(group_puid=msg.sender.puid, status='nothing')
            return
    subjuct_index = instance['play_times']
    next_game = False
    if instance['play_times'] > 0:
        # 游戏已经在进行中了，直接判断游戏
        if instance['answer'] == msg.text:
            # 答题正确，给用户返回正确信息
            result = '哇哦~恭喜@{} 猜对咯，正确答案为：「{}」'.format(msg.member.name, instance['answer'])
            msg.reply(result)
            if instance['play_times'] < GUESS_IDIOM_MAX_TIMES:
                next_game = True
            else:
                # 游戏结束，数据库中关闭，聊天对象更新为nothing
                DB_CLIENT.idiom_status_close_game(puid)
                SQLITE.update_wechat_group_status(group_puid=msg.sender.puid, status='nothing')
        else:
            # 答题失败，什么都不做
            pass
    else:
        # 游戏还未开始，需要重新初始化游戏
        next_game = True
        msg.reply('猜成语答题开始')
    if next_game:
        # 继续选择游戏进行
        index = random.randint(0, len(IDIOT_FILES))
        game_file = IDIOT_FILES[index]
        answer = DB_CLIENT.get_idiom(file_path=game_file)
        if answer is not None:
            # 更新游戏及游戏答案
            DB_CLIENT.idiom_status_update_game(puid, answer['idiom'])
            # 提醒答题开始
            msg.reply('请看第{}题'.format(subjuct_index + 1))
            # 将图片发送出去
            msg.reply_image(game_file)
            t = threading.Thread(target=guess_idiom_thread_hint, args=(msg, puid, subjuct_index),
                                 name='guess_idiom_hint_thread')
            t.start()
            t.join()


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
        elif status == 'guess_idiom':
            # 猜成语
            handle_guess_idiom(msg)
            need_send = False
        elif msg.is_at:
            if '猜成语' in msg.text:
                # 更新数据库
                SQLITE.update_wechat_group_status(group_puid=msg.sender.puid, status='guess_idiom')
                handle_guess_idiom(msg, is_restart=True)
                need_send = False
            else:
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
