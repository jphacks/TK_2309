from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import FlexSendMessage
import os

from linebot.models import (
    TextSendMessage, QuickReply, QuickReplyButton, MessageAction,
)

# 環境変数からアクセストークンを取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 通常のリプライ
def send_reply_message(reply_token, text):
    try:
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text=text,)
        )
    except LineBotApiError as e:
        print(f"Error: {e}")
