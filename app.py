from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# 讀取 Render 設定的環境變數
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


# 處理 LINE 訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # ==================================================
    # 匯率查詢功能（完整無錯誤）
    # ==================================================
    if user_text.startswith("匯率") or 
user_text.lower().startswith("rate"):
        parts = user_text.split()

        # 正確格式：匯率 USD TWD
        if len(parts) == 3:
            base = parts[1].upper()
            target = parts[2].upper()

            try:
                url = f"https://api.exchangerate-api.com/v4/latest/{base}"
                response = requests.get(url)
                data = response.json()

                if "rates" in data and target in data["rates"]:
                    rate = data["rates"][target]
                    reply = f"📈 {base} → {target} 匯率： {rate}"
                else:
                    reply = "❌ 查不到這個貨幣的匯率，可能代碼錯誤"

            except Exception:
                reply = "⚠️ 查詢匯率失敗，可能 API 暫時無法使用"

        else:
            reply = (
                "格式錯誤！請用以下格式：\n"
                "匯率 USD TWD\n"
                "或：rate usd jpy"
            )

    else:
        # 一般回覆
        reply = f"你說：{user_text}"

    # 回覆使用者
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    app.run(port=5000)


