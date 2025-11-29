from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# 從 Render 環境變數取得 Token
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot is running"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ------------------------------------------------------
# 文字訊息處理
# ------------------------------------------------------
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    reply = ""

    # === 匯率功能 ===
    if user_text.startswith("匯率") or 
user_text.lower().startswith("rate"):
        parts = user_text.split()

        if len(parts) == 3:
            base = parts[1].upper()      # USD
            target = parts[2].upper()    # TWD

            try:
                url = f"https://api.exchangerate-api.com/v4/latest/{base}"
                res = requests.get(url)
                data = res.json()

                if "rates" in data and target in data["rates"]:
                    rate = data["rates"][target]
                    reply = f"📈 {base} → {target} 的匯率是 {rate}"
                else:
                    reply = "查不到該匯率喔～"
            except:
                reply = "查匯率時發生錯誤，請稍後再試～"
        else:
            reply = "格式錯誤～ 正確用法：\n匯率 USD TWD\n或：rate usd 
jpy"

    else:
        reply = f"你說：{user_text}"

    # 回傳文字
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


# ------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

