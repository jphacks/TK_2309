import boto3
import yaml
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
with open("configs.yml", "r") as f:
    configs = yaml.safe_load(f)
# テーブル作成    
table1 = dynamodb.Table(configs["dynamodb"]["chat_history"])
table2 = dynamodb.Table(configs['dynamodb']['users'])

def get_usage_count(line_user_id):
    # ユーザーテーブルからユーザー情報を取得
    response = table2.get_item(Key={"line_user_id": line_user_id})

    # 現在の日付を取得
    # 日本時間に設定+9
    current_date = (datetime.utcnow() + timedelta(hours=9)).date()
    if 'Item' in response:
        is_premium = response['Item'].get('is_premium', False)
        # プレミアム会員の場合、使用回数の上限はない
        if is_premium:
            return 0

        # 以下は非会員の場合の処理
        last_used_date = response['Item'].get('last_used_date', None)

        if str(last_used_date) == str(current_date):
            # 同じ日の場合、使用回数を1増やす
            count = response['Item'].get('usage_count', 0) + 1
        else:
            # 前回の使用日と異なる場合、使用回数を1とする
            count = 1
    else:
        # ユーザーが存在しない場合、使用回数を1とする
        count = 1

    # 使用回数と使用日を更新
    table2.put_item(
        Item={
            'line_user_id': line_user_id,
            'usage_count': count,
            'last_used_date': str(current_date),
            'is_premium': False  # 初回利用者は非会員とする
        }
    )

    return count


# 月間獲得ポイントを追加する関数   
def get_user_point(line_user_id):
    # ユーザーテーブルからユーザー情報を取得
    response = table2.get_item(Key={"line_user_id": line_user_id})

    # 現在の日付を取得
    # 日本時間に設定+9
    current_date = (datetime.utcnow() + timedelta(hours=9)).date()
    print("現在の日にち" + str(current_date))
    
    # 現在の年/月を取得
    now = (datetime.utcnow() + timedelta(hours=9)).now()
    current_year_month = str(now.year) + "-" + str(now.month)
    print("現在年月" + str(current_year_month))
    
    if 'Item' in response:
        # ユーザーが存在する場合、前回の使用年月日と比較
        last_pointed_date = response['Item'].get('last_pointed_date', None)
        last_pointed_year_month = response['Item'].get('last_pointed_year_month', None)
        print("前回の日にち" + str(last_pointed_date))
        print("前回の年月" + str(last_pointed_year_month))
        
        if str(last_pointed_year_month) == str(current_year_month) and str(last_pointed_date) != str(current_date):
            # 同年月で異なる日の場合、ポイントを1追加する。
            point = response['Item'].get('user_point', 0) + 1
        elif str(last_pointed_date) == str(current_date):
            # 同じ日付の場合はポイント変化なし
            point = response['Item'].get('user_point', 0)
        else:
            # 前回のポイント獲得月と異なる場合、ポイントを1とする
            point = 1
    else:
        # ユーザーが存在しない場合、ポイントを1とする
        point = 1
        
    # 使用回数と使用日を更新
    table2.put_item(
        Item={
            'line_user_id': line_user_id,
            'user_point': point,
            'last_pointed_date': str(current_date),
            'last_pointed_year_month':str(current_year_month)
        }
    )
    return point
