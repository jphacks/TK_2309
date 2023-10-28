import boto3
import yaml
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
with open("configs.yml", "r") as f:
    configs = yaml.safe_load(f)
# テーブル作成    
table1 = dynamodb.Table(configs["dynamodb"]["chat_history"])
table2 = dynamodb.Table(configs['dynamodb']['users'])
