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

