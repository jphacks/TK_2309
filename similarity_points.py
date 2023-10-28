import requests
import json
import os

# テキスト類似度関数
def text_pair_similarity(goo_lab_api, text1, text2, request_id=None):
    # APIのエンドポイントURL
    url = "https://labs.goo.ne.jp/api/textpair"
    
    # リクエストボディの作成
    payload = {
        "app_id": goo_lab_api,
        "text1": text1,
        "text2": text2
    }
    if request_id:
        payload["request_id"] = request_id
    
    # APIをコール
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    # レスポンスから得点を抽出
    data = response.json()
    score = data["score"]
    points = round(score * 100, 1)

    return points


# ひらがな化関数
def hiragana_conversion(goo_lab_api, sentence, output_type="hiragana", request_id=None):
    # APIのエンドポイントURL
    url = "https://labs.goo.ne.jp/api/hiragana"
    
    # リクエストボディの作成
    payload = {
        "app_id": goo_lab_api,
        "sentence": sentence,
        "output_type": output_type
    }
    if request_id:
        payload["request_id"] = request_id
    
    # APIをコール
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    
    # レスポンスからひらがな化結果を抽出
    data = response.json()
    result = data["converted"]
    
    return result
