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
