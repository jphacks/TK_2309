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
