from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# 從 Render 的環境變數讀 KEY
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/")
def home():
    return "LINE Bot running!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# =========================================================
#                 處理收到的文字訊息
# =========================================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # ===== 匯率功能 =====
    # 用法：
    #   匯率 USD TWD
    #   rate USD JPY
    if user_text.startswith("匯率") or 
user_text.lower().startswith("rate"):
        parts = user_text.split()

        if len(parts) == 3:
            base = parts[1].upper()     # 例如 USD
            target = parts[2].upper()   # 例如 TWD

            try:
                api_url = 
f"https://api.exchangerate-api.com/v4/latest/{base}"
                res = requests.get(api_url)
                data = res.json()

                if "rates" in data and target in data["rates"]:
                    rate = data["rates"][target]
                    reply_text = f"📈 {base} → {target} 的匯率是：{rate}"
                else:
                    reply_text = f"查不到 {base} 對 {target} 的匯率喔～"
            except:
                reply_text = "查匯率時出錯了，請稍後再試！"

        else:
            reply_text = "用法：\n匯率 USD TWD\n或：rate USD JPY"

    # ===== 一般聊天 =====
    else:
        reply_text = f"你說：{user_text}"

    # 回傳訊息
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# =========================================================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

