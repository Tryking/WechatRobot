import datetime
import os
import time
import pypinyin
from libs.mongodb import MongoClient

client = MongoClient()

game = client.idiom_status_close_game(puid='default')
print(game)
