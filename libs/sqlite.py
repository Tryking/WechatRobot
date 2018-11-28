import sqlite3

from libs.common import get_now_time_str


class Sqlite(object):
    def __init__(self, db_name):
        self.db_name = db_name

    def get_conn(self):
        conn = sqlite3.connect(database=self.db_name)
        return conn

    def create_idioms_solitaire(self):
        conn = self.get_conn()
        cursor = conn.cursor()
        sql = """
        create table idioms_solitaire
        (
          id           INTEGER not null,
          wechat_group TEXT    not null,
          last_idioms  CHAR(20),
          last_time    TEXT default '2018-08-08 00:00:00.000' not null,
          start_time   TEXT default '2018-08-08 00:00:00.000' not null,
          status       int  default 1 not null
        );
        create unique index IdiomsSolitaire_id_uindex on idioms_solitaire (id);
        """
        cursor.execute(sql)

        conn.commit()
        conn.close()

    def update_wechat_group_status(self, group_puid, status):
        conn = self.get_conn()
        cursor = conn.cursor()
        sql = "replace into wechat_group_status (group_puid, status) values ('%s','%s')" % (group_puid, status)
        cursor.execute(sql)
        conn.commit()
        conn.close()

    def get_wechat_group_status(self, group_puid):
        """
        获取群组状态
        :param group_puid:  群组
        :return:
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        select_sql = "select group_puid,status from wechat_group_status where group_puid='%s'" % group_puid
        result = cursor.execute(select_sql).fetchone()
        if result is None:
            # 创建此群的状态表
            sql = "insert into wechat_group_status (group_puid) values ('%s')" % group_puid
            cursor.execute(sql)
            conn.commit()
            result = cursor.execute(select_sql).fetchone()
        data = {'group_puid': result[0], 'status': result[1]}
        print(data)
        conn.close()
        return data

    def get_idioms_solitaire(self, wechat_group):
        """
        查找是否有还在玩儿的游戏，有的话直接返回，没有的话创建一个返回
        :param wechat_group:  给定的微信群组
        :return: 返回游戏信息
        """
        conn = self.get_conn()
        cursor = conn.cursor()
        select_sql = "select id,wechat_group,start_time,last_time,last_idioms,status from idioms_solitaire " \
                     "where wechat_group='%s' and status=1 limit 1" % wechat_group
        print(select_sql)
        result = cursor.execute(select_sql).fetchone()
        if result is None:
            # 创建新的数据项
            sql = "insert into idioms_solitaire (wechat_group,start_time,last_time) values ('%s','%s','%s')" \
                  % (wechat_group, get_now_time_str(), get_now_time_str())
            cursor.execute(sql)
            # 重新选择
            print(sql)
            result = cursor.execute(select_sql).fetchone()
        data = {'wechat_group': result[1], 'start_time': result[2], 'last_time': result[3], 'last_idioms': result[4],
                'status': result[5]}
        print(data)
        print('Operation done successfully')
        conn.close()
        return data


if __name__ == '__main__':
    sqlite = Sqlite(db_name='wechat_robot.db')
    sqlite.get_wechat_group_status('test2')
