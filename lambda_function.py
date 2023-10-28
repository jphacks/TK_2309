import json
import logging
import boto3
import time
import yaml
import random
import stripe
import re
import os
import urllib.parse
import requests
import users

from datetime import datetime, timedelta, timezone
from line_handler import send_reply_message, send_for_count_over
from openai_handler import send_to_openai
from dynamodb_handler import get_usage_count, get_user_point, check_user_point
from line_handler import send_reply_message, send_for_count_over, send_flex_message, confirm_nickname
from similarity_points import determine_points

# loggerの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# configs.ymlファイルの読み込み
with open("configs.yml", "r") as f:
    configs = yaml.safe_load(f)
    
# 環境変数からAPIキーを取得
goo_lab_api = os.environ["goo_lab_api"]
    
# DynamoDB接続
dynamodb = boto3.resource("dynamodb")
chat_table = dynamodb.Table(configs["dynamodb"]["chat_history"])
user_table = dynamodb.Table(configs["dynamodb"]["users"])

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
PRICE_ID_MONTH = os.environ.get('PRICE_ID_MONTH')
PRICE_ID_HALF_YEAR = os.environ.get('PRICE_ID_HALF_YEAR')
BITLY_TOKEN = os.getenv('BITLY_TOKEN')

def handle_payment_request(user_id):
    print("handle_payment_request function called")
    try:
        # Create the Stripe payment sessions
        session_month = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_ID_MONTH,  # set your price ID here
                "quantity": 1,
            }],
            mode="subscription",
            success_url='https://shoma0321.github.io/success/',
            cancel_url='https://shoma0321.github.io/cancel/',
            client_reference_id=user_id
        )
        session_half_year = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_ID_HALF_YEAR,  # set your price ID here
                "quantity": 1,
            }],
            mode="subscription",
            success_url='https://shoma0321.github.io/success/',
            cancel_url='https://shoma0321.github.io/cancel/',
            client_reference_id=user_id
        )
        
        print(f"Stripe session ID for a month: {session_month.id}")
        print(f"Stripe session ID for a half year: {session_half_year.id}")
        
        # Create the Flex Message contents
        contents = {
            "type": "bubble",
            "styles": {
                "body": {
                    "backgroundColor": "#FFFFFF",
                }
            },
            "hero": {
                "type": "image",
                "url": "https://shoma0321.github.io/success/twinds_linker.png",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "使い放題プラン",
                        "weight": "bold",
                        "size": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "baseline",
                        "margin": "md",
                        "contents": [
                            {
                                "type": "text",
                                "text": "月額400円(税込)",
                                "size": "sm",
                                "color": "#999999",
                                "margin": "md",
                                "flex": 0
                            }
                        ]
                    },
                    {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#A9A9A9",
                        "action": {
                            "type": "uri",
                            "label": "プレミアム-1ヶ月(400円)",
                            "uri": session_month.url
                        }
                    },
                 {
                        "type": "separator",
                        "margin": "md"
                    },
                    {
                        "type": "button",
                        "style": "primary",
                        "color": "#A9A9A9",
                        "action": {
                            "type": "uri",
                            "label": "プレミアム-半年(1500円)",
                            "uri": session_half_year.url
                        }
                    }
                ]
            }
        }
        return contents
    except Exception as e:
        logger.error(f"An error occurred: {e}")  # これはエラーメッセージをログに出力します
        return None


def lambda_handler(event, context):
      try:
        body = json.loads(event['body'])
        print(f"Body content: {body}")  # Debug information
        message_event = body['events'][0]
    except KeyError:
        print("'events' or 'data' or 'object' key not found in the event body.")
    
    # メッセージやテキスト以外は返却
    if not body['events'][0]['type'] == 'message':
        return {'statusCode': 200, 'body': json.dumps('Error!')}
    if not body['events'][0]['message']['type'] == 'text':
        text = "メッセージはテキストで送信してください"
        send_reply_message(message_event['replyToken'], text)
        return {'statusCode': 200, 'body': json.dumps('Error!')}

    # 重要な情報を変数に格納
    reply_token = body['events'][0]['replyToken']
    user_message = body['events'][0]['message']['text']
    print(user_message)
    line_user_id = body['events'][0]['source']['userId']
    
    # オブジェクトを生成
    # リクエストを取得
    body = json.loads(event['body'])
    # ユーザ情報
    user = users.Users(body['events'][0]['source']['userId'])

    phrase = configs["questions"][int(day_str)]["phrase"]
    explanation = configs["questions"][int(day_str)]["explanation"]

    # LINE上での処理
    if user_message == "[挑戦]ツインズリンク":
        if day_str in double_days:
            hidden_text = "ツインズリンクに挑戦しよう！\n今日はポイント2倍デー！クリアすると、2ポイントを獲得できます！\n\n-----------\n今日のフレーズ:" + phrase +"\n【" + phrase + "】と私に言わせたらクリア！早速会話を始めましょう！\n-----------"
        else:
            hidden_text = "ツインズリンクに挑戦しよう！\n-----------\n今日のフレーズ:" + phrase +"\n【" + phrase + "】と私に言わせたらクリア！早速会話を始めましょう！\n-----------"
        text = "ツインズリンクに挑戦しよう！今日のフレーズを私に言わせることが出来たら成功！"
        send_reply_message(message_event['replyToken'], hidden_text)
    elif any(keyword in user_message for keyword in keywords) or phrase in user_message:
        text = "フレーズの内容を直接含めたり、不自然に発言を誘導したりする行為は禁止です！"
        send_reply_message(message_event['replyToken'], text)
        user_message = "こんにちは"
    elif user_message == "[確認]お知らせ":
        text = "上記が今月のイベント・アップデート情報になります！！ "
        send_reply_message(message_event['replyToken'], text)
        # 必要な処理
    elif user_message == "[確認]現在の月間ポイント":
        text = "現在の月間ポイントは" + str(user.get_point()) + "ポイントです。"
        send_reply_message(message_event['replyToken'], text)
    elif user_message == "[チュートリアル]使い方の確認":
        text = "上記の画像を参考に使い方を確認してください！"
        send_reply_message(message_event['replyToken'], text)
    elif user_message == "[確認]先月のランキング":
        text = "以下が先月のランキングになります！！"
        send_reply_message(message_event['replyToken'], text)
    else:
        # 利用回数を取得し、カウントを1つ増やす。
        user.add_usage()
        usage_count = user.get_usage()
        if usage_count > configs["limit"]:
            text = "無料版でのチャットは1日あたり" + str(configs["limit"]) + "回までです。制限は午前0時にリセットされます。\n\n公式Twitterに利用制限解除のパスワードがあるかも！？\n秘密のパスワードを送ると、チャット制限をリセットできます！"
            send_for_count_over(message_event['replyToken'], text)
            return {'statusCode': 200, 'body': json.dumps('Error!')}
        else:
            text = send_to_openai(chat_history)
        if phrase in text:
            # ポイントを１つ増やす。
            user.add_point()
        else:
            points = determine_points(goo_lab_api, phrase, text)
            send_reply_message(message_event['replyToken'], text + "\n" + str(points) + "点です！！")

    # 会話履歴のDynamoDB更新
    chat_table.put_item(
        Item={
            "line_user_id": line_user_id,
            "user_message": user_message,
            "gpt_response": text,
            "created_at": str(round(time.time()))
        }
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
