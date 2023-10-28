import os
import boto3
from datetime import datetime, timedelta, timezone


# 現在の日付と時刻を取得
japan_tz = timezone(timedelta(hours=9))
now = datetime.now(japan_tz)
# 日の部分だけを文字列として取得
day_str = now.strftime("%d")

# 今月のポイント2倍デー
double_days = ["1", "6", "12", "21", "2"]

class Users:

    USER_TABLE_NAME = os.getenv("USER_TABLE_NAME")
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(USER_TABLE_NAME)
    line_user_id = ''

    data = {}
  
    def __init__(self, line_user_id):
        self.line_user_id = line_user_id

        # ユーザ情報を取得
        user = self.get_user()

        # 新規ユーザの場合はデータベースに登録
        if not 'Item' in user:
            self.__create_user()

        # 登録済みの場合
        else:
            self.data = user['Item']
