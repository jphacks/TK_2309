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
