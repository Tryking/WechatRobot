import os
import datetime
import pymongo

from libs.config import MONGODB_HOST, MONGODB_PORT, MONGODB_USER, MONGODB_PWD, MONGODB_DB

# 成语接龙实例
IDIOM_RECORD = 'idiom_record'
# 成语对照表
IDIOM = 'idiom'


class MongoClient(object):

    def __init__(self):
        host = MONGODB_HOST
        port = MONGODB_PORT
        user = MONGODB_USER
        pwd = MONGODB_PWD
        db_name = MONGODB_DB
        self.client = pymongo.MongoClient(host=host, port=port)
        self.db = self.client[db_name]
        if user and user != '':
            self.db.authenticate(name=user, password=pwd)

    def get_idiom_status(self, puid, init=True):
        """
        获取成语接龙实例(已经在进行的并且更新在5分钟之前的，如果没有正在进行的，需要new一个实例)
        :return:
        """
        instance = self.db[IDIOM_RECORD].find_one(filter={'wechat_group': puid, 'status': 'open', 'update_time': {
            '$gte': datetime.datetime.now() - datetime.timedelta(minutes=5)}})
        if instance is None and init:
            self.db[IDIOM_RECORD].insert_one(
                {'wechat_group': puid, 'status': 'open', 'play_times': 0, 'update_time': datetime.datetime.now()})
            instance = self.db[IDIOM_RECORD].find_one(filter={'wechat_group': puid, 'status': 'open', 'play_times': 0})
        return instance

    def idiom_status_times_auto_grow(self, puid):
        """
        游戏接龙游戏次数自增1
        :param puid:
        :return:
        """
        self.db[IDIOM_RECORD].update_one(filter={'wechat_group': puid, 'status': 'open'},
                                         update={'$inc': {'play_times': 1},
                                                 '$set': {'update_time': datetime.datetime.now()}})

    def idiom_status_close_game(self, puid):
        """
        关闭游戏
        :param puid:
        :return:
        """
        self.db[IDIOM_RECORD].update_one(filter={'wechat_group': puid, 'status': 'open'},
                                         update={'$set': {'status': 'close', 'update_time': datetime.datetime.now()}})

    def idiom_status_update_game(self, puid, answer):
        """
        更新游戏及答案，并且次数加1
        :param puid:
        :return:
        """
        self.db[IDIOM_RECORD].update_one(filter={'wechat_group': puid, 'status': 'open'},
                                         update={'$inc': {'play_times': 1},
                                                 '$set': {'answer': answer, 'update_time': datetime.datetime.now()}})

    def save_idiom(self, file_path, idiom):
        """
        保存成语
        :return:
        """
        self.db[IDIOM].update_one(filter={'idiom': idiom}, update={'$set': {'file_path': file_path}}, upsert=True)

    def get_idiom(self, file_path):
        """
        获取成语
        :param file_path: 成语路径
        :return:
        """
        instance = self.db[IDIOM].find_one(filter={'file_path': file_path})
        return instance


if __name__ == '__main__':
    client = MongoClient()
    IDIOT_FILES = [os.path.join('datas', f) for f in os.listdir('datas') if os.path.isfile(os.path.join('datas', f))]
    for file in IDIOT_FILES:
        print(file)
