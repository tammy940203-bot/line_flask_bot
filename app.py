import os
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境變數（Render 使用）
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running!"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # ---------------------------
    # 匯率查詢
    # ---------------------------
    if user_text.startswith("匯率") or 
user_text.lower().startswith("rate"):
        parts = user_text.split()
        if len(parts) != 3:
            reply = "格式錯誤！請用：\n匯率 USD TWD\n或：rate usd jpy"
        else:
            base = parts[1].upper()
            target = parts[2].upper()

            url = 
f"https://api.exchangerate.host/convert?from={base}&to={target}"
            r = requests.get(url).json()

            if r.get("result"):
                rate = r["result"]
                reply = f"💱 {base} → {target} 匯率：{rate}"
            else:
                reply = "⚠️ 無法取得匯率，請稍後再試～"

        line_bot_api.reply_message(event.reply_token, 
TextSendMessage(text=reply))
        return

    # ---------------------------
    # 天氣查詢
    # ---------------------------
    if user_text.startswith("天氣"):
        city = user_text.replace("天氣", "").strip()
        if not city:
            reply = "請輸入城市，例如：天氣 台北"
        else:
            url = f"https://wttr.in/{city}?format=3"
            result = requests.get(url).text
            reply = f"🌤 天氣查詢：\n{result}"

        line_bot_api.reply_message(event.reply_token, 
TextSendMessage(text=reply))
        return

    # ---------------------------
    # 一般回覆
    # ---------------------------
    reply = f"你說：{user_text}"
    line_bot_api.reply_message(event.reply_token, 
TextSendMessage(text=reply))


if __name__ == "__main__":
    app.run(port=5000, debug=True)

