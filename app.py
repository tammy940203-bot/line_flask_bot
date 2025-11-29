from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# 從 Render Environment 讀取金鑰
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# 處理 LINE 傳來的訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # =============================
    #  匯率功能
    # =============================
    if user_text.startswith("匯率") or 
user_text.lower().startswith("rate"):
        parts = user_text.split()

        # 格式應為：匯率 USD TWD
        if len(parts) == 3:
            base = parts[1].upper()      # 例如 USD
            target = parts[2].upper()    # 例如 TWD

            try:
                url = f"https://api.exchangerate-api.com/v4/latest/{base}"
                res = requests.get(url)
                data = res.json()

                if "rates" in data and target in data["rates"]:
                    rate = data["rates"][target]
                    reply = f"📈 {base} → {target} 的匯率是 {rate}"
                else:
                    reply = "找不到這個幣別的匯率喔～"

            except Exception:
                reply = "查詢匯率時發生錯誤，請稍後再試～"

        else:
            # 多行字串，保證語法不會壞
            reply = """格式錯誤～ 正確用法：
匯率 USD TWD
或：rate usd jpy"""

    else:
        # 一般回覆
        reply = f"你說：{user_text}"

    # 回傳訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    app.run(port=5000)


