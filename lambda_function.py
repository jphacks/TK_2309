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

def create_web_tweet_link(tweet_text):
    base_url = "https://twitter.com/intent/tweet"
    tweet_parameters = {"text": tweet_text}
    url_parameters = urllib.parse.urlencode(tweet_parameters)
    tweet_url = base_url + "?" + url_parameters
    return tweet_url

def shorten_url(long_url, bitly_token):
    BITLY_API_URL = "https://api-ssl.bitly.com/v4/shorten"
    headers = {"Authorization": f"Bearer {bitly_token}",
               "Content-Type": "application/json"}
    data = json.dumps({"long_url": long_url})
    response = requests.post(BITLY_API_URL, headers=headers, data=data)
    print(f"Bitly API response: {response.json()}")  # レスポンスのログ出力
    if response.status_code == 200:
        short_url = response.json()["link"]
        print(f"Shortened URL: {short_url}")  # 短縮URLのログ出力
        return short_url
    else:
        return long_url

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
    
    # ニックネームの取得
    # ニックネームが空白の場合
    if user.data['name'] == '':
        user.set_name('user-input-waiting')
        send_reply_message(reply_token, '【チュートリアル】\n4文字以上であなたのニックネームを教えてください！')
        return {'statusCode': 200, 'body': json.dumps('Success!')}
        
    # 　ニックネームがユーザの入力待ちの場合
    elif user.data['name'] == 'user-input-waiting':
        # 文字数が足りなかった場合
        if len(user_message) < 4:
            send_reply_message(reply_token, 'ニックネームは4文字以上でお願いします！\nもう一度あなたのニックネームを教えてください！')
            return {'statusCode': 200, 'body': json.dumps('Success!')}
        else:
            # ユーザの情報を更新
            user.set_name(user_message)
            confirm_nickname(reply_token, user_message+'で名前はあっていますか？')
            return {'statusCode': 200, 'body': json.dumps('Success!')}

    # ユーザが名前の入力のやり直しを選択した場合
    elif user_message == '【ニックネーム-間違え】':
        user.set_name('user-input-waiting')
        send_reply_message(reply_token, 'もう一度名前を教えてください！')
        return {'statusCode': 200, 'body': json.dumps('Success!')}
    
    # テーブルから指定した項目を取得
    response = chat_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('line_user_id').eq(line_user_id)
    )
    
    # 初期設定のシステムプロンプト
    chat_history = []
    
    # チャット履歴を取得
    if 'Items' in response and len(response['Items']) > 0:
        items = response['Items']
        sorted_items = sorted(items, key=lambda x: int(x['created_at']))
        sorted_items = sorted_items[-5:]
        
        for item in sorted_items:
            chat_history.append({"role": "user", "content": item['user_message']})
            chat_history.append({"role": "assistant", "content": item['gpt_response']})

    chat_history.append({"role": "user", "content": user_message})

    # 諦めたかどうかを決める変数
    retreated = False
    
    # 現在の日付と時刻を取得
    japan_tz = timezone(timedelta(hours=9))
    now = datetime.now(japan_tz)
    # 日の部分だけを文字列として取得
    day_str = now.strftime("%d")
    
    # 今月のポイント2倍デー
    double_days = ["1", "6", "12", "21", "29"]
    
    phrase = configs["questions"][int(day_str)]["phrase"]
    explanation = configs["questions"][int(day_str)]["explanation"]
    keywords = ["変換", "変え", "入れ替え", "足す", "+", "引く", "-", "組み合わ", "差し引", "抜く", "置き換え", "削除", "繋げて", "付ける", "漢字に", "ひらがなに", "カタカナに", "逆", "反対"]
    
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
    elif user_message == "【ニックネーム-確定】":
        return {'statusCode': 200, 'body': json.dumps('Success!')}
    elif user_message == "友達2倍":
        user.reset_count()
        text = "秘密のパスワードが使用されました！1日の利用制限がリセットされました。"
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
            base_tweet_text = (phrase + " ")*4 + "!\n\n" +  "Twins Linkの今日のツインズリンクをクリアしました！\n月間ポイントが加算されました。\n\n#Twins Linkー #プレゼント #Amazonギフトカード #懸賞 \n\n気になった方は以下のリンクから追加！\n"
            long_link_url = "https://liff.line.me/1645278921-kWRPP32q/?accountId=478khwxt"
            short_link_url = shorten_url(long_link_url, BITLY_TOKEN)
            if short_link_url is not None:
                base_tweet_text += short_link_url
            else:
                base_tweet_text += long_link_url
        
            # base_tweet_textをエンコードせずにそのまま使用
            long_tweet_url = create_web_tweet_link(base_tweet_text)
            short_tweet_url = shorten_url(long_tweet_url, BITLY_TOKEN)
        
            if short_tweet_url is not None:  
                send_reply_message(message_event['replyToken'], text + "\n\nおめでとうございます！ミッションクリア！\n月間ポイントが加算されました。\n\n-----------\n【今日のライフハック】\n" + explanation + "\n-----------\n\nこの結果をTwitterでシェアしましょう！！以下のリンクから共有しましょう！\n\n(" + short_tweet_url + ")")
            else:
                send_reply_message(message_event['replyToken'], text + "\n\nおめでとうございます！ミッションクリア！\n月間ポイントが加算されました。\n\n-----------\n【今日のライフハック】\n" + explanation + "\n-----------\n\nこの結果をTwitterでシェアする機能は現在利用できません。")
            get_user_point(line_user_id)
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
