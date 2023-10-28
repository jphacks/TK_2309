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
        else:
            points = determine_points(goo_lab_api, phrase, text)
            send_reply_message(message_event['replyToken'], text + "\n" + str(points) + "点です！！")

