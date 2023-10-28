import requests
import json

# テキスト類似度関数
def text_pair_similarity(app_id, text1, text2, request_id=None):
    # APIのエンドポイントURL
    url = "https://labs.goo.ne.jp/api/textpair"
    
    # リクエストボディの作成
    payload = {
        "app_id": app_id,
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
    points = data["score"]

    return points


# ひらがな化関数
def hiragana_conversion(app_id, sentence, output_type="hiragana", request_id=None):
    # APIのエンドポイントURL
    url = "https://labs.goo.ne.jp/api/hiragana"
    
    # リクエストボディの作成
    payload = {
        "app_id": app_id,
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

# キーワード抽出関数
def extract_keywords(app_id, title, body, request_id=None, max_num=3, focus=None):
    # APIのエンドポイントURL
    url = "https://labs.goo.ne.jp/api/keyword"
    
    # リクエストヘッダーの設定
    headers = {
        'Content-Type': 'application/json',
    }
    
    # リクエストボディの設定
    data = {
        'app_id': app_id,
        'title': title,
        'body': body,
        'max_num': max_num,
    }
    if request_id:
        data['request_id'] = request_id
    if focus:
        data['focus'] = focus
    
    # APIリクエストの実行
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    # レスポンスの解析と結果の返却
    if response.status_code == 200:
        resp_data = response.json()
        print(resp_data)
        if 'error' not in resp_data:
            return resp_data['keywords']
        else:
            return []
    else:
        return []
    
# キーワードポイントを決定する関数
def get_key_word_points(app_id, theme_title, theme_text, ai_text):
    keywords_with_points = extract_keywords(app_id, theme_title, theme_text)
    
    key_word_points = 0
    for kw_dict in keywords_with_points:
        keyword, value = list(kw_dict.items())[0]
        if keyword not in ai_text:
            key_word_points -= value/10
    
    return key_word_points

# 得点決定関数
def determine_points(app_id, theme_title, theme_text, ai_text):
    # 2つのテキストをひらがな化して、スペースと読点を削除
    hiragana_theme_text = hiragana_conversion(app_id , theme_text).replace(" ", "").replace("、", "")
    hiragana_ai_text = hiragana_conversion(app_id, ai_text).replace(" ", "").replace("、", "")

    # 完全一致するかを判定し、完全一致しなければ類似度を得点にする
    if hiragana_theme_text in hiragana_ai_text:
        points = 1
    # 完全一致していなければ、類似度とキーワードによる減点を加味して得点を決定する
    else:
        points = text_pair_similarity(app_id, theme_text, ai_text)
        points = points + get_key_word_points(app_id, theme_title, theme_text, ai_text)
    points = round(points * 100, 1)
    
    return points
