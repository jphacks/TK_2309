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

    def __create_user(self):
        """ LINEユーザテーブルに新規ユーザを登録する """

        self.data = {
            'line_user_id': self.line_user_id,
            'name': '',
            'last_sended_on': self.__get_adjusted_date_str(),
            'last_pointed_month':self.__get_adjusted_month_str(),
            'last_pointed_date': 0,
            'point_count': 0,
            'api_count_total': 0,
            'created_at': self.__get_date_time_str()
        }
        self.__save()

    
    def __save(self):
        self.table.put_item(Item=self.data)

    def get_user(self):
        """ LINEユーザテーブルからデータを取得 """
        return self.table.get_item(Key={'line_user_id': self.line_user_id})

    def reset_count(self):
        """ 本日のカウントをリセットする """
        self.data['last_sended_on'] = self.__get_adjusted_date_str()
        self.data['api_count_total'] = 0
        self.__save()

    def get_usage(self):
        """ 現在の使用回数を取得する """
        if self.data['last_sended_on'] == self.__get_adjusted_date_str():
            return self.data['api_count_total']
        else:
            self.reset_count()
            return 0

    def get_point(self):
        """ 現在のポイントを取得する """
        if self.data['last_pointed_month'] == self.__get_adjusted_month_str():
            return self.data['point_count']
        else:
            return 0

    def add_point(self):
        # 本日初正解ならポイントを追加して、最終ポイント獲得日を更新
        if self.data['last_pointed_month'] == self.__get_adjusted_month_str() and self.data["last_pointed_date"] != self.__get_adjusted_date_str():
            if day_str in double_days:
                self.data['point_count'] += 2
            else:
                self.data['point_count'] += 1
            self.data["last_pointed_date"] = self.__get_adjusted_date_str()
        elif self.data["last_pointed_date"] == self.__get_adjusted_date_str():
            self.__save()
        # 新しい月ならば、ポイントを１にして最終ポイント獲得月を更新
        else:
            self.data['last_pointed_month'] = self.__get_adjusted_month_str()
            self.data['point_count'] = 1
        self.__save()

    def add_usage(self):
        self.data['api_count_total'] += 1
        self.__save()
