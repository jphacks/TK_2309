import json
import openai
import requests
import os
import logging
import yaml

logger = logging.getLogger()
logger.setLevel(logging.INFO)
openai.api_key = os.environ["OPENAI_SECRETKEY"]

# yamlからモデルを設定
with open("configs.yml", "r") as f:
    configs = yaml.safe_load(f)
gpt_model = configs["openai"]["gpt_model"]

# ChatGPTから取得したテキストを返す関数
def send_to_openai(chat_history):
    logger.info(chat_history)
    payload = {
        "model": gpt_model,
        "messages": chat_history
    }
    headers = {
        "Content-Type": "application/json",
        'Authorization': 'Bearer ' + openai.api_key
    }
    openai_api_url = "https://api.openai.com/v1/chat/completions"

    try:
        response = requests.post(openai_api_url, headers=headers, data=json.dumps(payload))
        response_json = response.json()

        # ChatGPTモデルと会話履歴をセット
        response_from_gpt = openai.ChatCompletion.create(
            model=gpt_model,
            messages=chat_history,
        )
        answer_from_gpt = response_from_gpt.choices[0]["message"]["content"]
        text = answer_from_gpt
    # 例外処理
    except Exception as e:
        logger.warning(e)
        text = "error"
    return text
