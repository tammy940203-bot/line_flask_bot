
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# 從環境變數讀取 LINE 的金鑰
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/callback", methods=["POST"])
def callback():
    # 取得 LINE 的簽章
    signature = request.headers.get("X-Line-Signature", "")
    # 取得 body
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # ============================
    #   匯率查詢功能
    # ============================
    if user_text.startswith("匯率") or user_text.lower().startswith("rate"):
        parts = user_text.split()

        # 正確格式：匯率 USD TWD  或  rate usd jpy
        if len(parts) == 3:
            base = parts[1].upper()
            target = parts[2].upper()

            try:
                url = f"https://api.exchangerate-api.com/v4/latest/{base}"
                resp = requests.get(url, timeout=10)
                data = resp.json()

                if "rates" in data and target in data["rates"]:
                    rate = data["rates"][target]
                    reply = f"📈 {base} → {target} 匯率：{rate}"
                else:
                    reply = "❌ 查不到這個貨幣的匯率，請確認貨幣代碼是否正確（例如：USD、TWD、JPY）。"

            except Exception:
                reply = "⚠️ 查詢匯率失敗，可能 API 暫時無法使用，等等再試試看～"

        else:
            reply = (
                "格式錯誤！請用以下格式：\n"
                "匯率 USD TWD\n"
                "或：rate usd jpy"
            )

    else:
        # 一般回覆：把你說的話再回一次
        reply = f"你說：{user_text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


if __name__ == "__main__":
    app.run(port=5000, debug=True)

