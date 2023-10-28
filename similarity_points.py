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

# 得点決定関数
def determine_points(app_id, theme_text, ai_text):
    # 2つのテキストをひらがな化して、スペースと読点を削除
    hiragana_theme_text = hiragana_conversion(app_id , theme_text).replace(" ", "").replace("、", "")
    hiragana_ai_text = hiragana_conversion(app_id, ai_text).replace(" ", "").replace("、", "")

    # 完全一致するかを判定し、完全一致しなければ類似度を得点にする
    if hiragana_theme_text in hiragana_ai_text:
        print(hiragana_theme_text)
    else:
        points = text_pair_similarity(app_id, theme_text, ai_text)
    
    return points
