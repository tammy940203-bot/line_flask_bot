from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 從環境變數讀取金鑰（不要寫死在程式裡）
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/", methods=["GET"])
def index():
    return "LINE Flask bot is running."


@app.route("/callback", methods=["POST"])
def callback():
    # 1. 取得簽章
    signature = request.headers.get("X-Line-Signature", "")

    # 2. 取得 body（事件內容）
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # 3. 驗證 + 交給 handler 處理
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.warning("Invalid signature.")
        abort(400)

    return "OK", 200


# 4. 收到文字訊息時要怎麼回
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    reply_text = f"你說：{user_text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )


if __name__ == "__main__":
    # 本機測試用，Render 會用 gunicorn 啟動
    app.run(host="0.0.0.0", port=5000, debug=True)

