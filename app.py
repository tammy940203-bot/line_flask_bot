import os
from flask import Flask, request, abort

source venv/bin/activate   # 前面已經有 (venv) 就可以略過

cat > app.py << 'EOF'
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests

# 從環境變數讀 LINE 的金鑰（Render 上已經設好了）
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")

app = Flask(__name__)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


@app.route("/")
def index():
    return "LINE bot is running."


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ---------- 匯率查詢相關 ----------

def get_rate_from_api(base: str, target: str):
    """
    用 exchangerate.host 查匯率，1 base 會換成幾 target
    """
    url = "https://api.exchangerate.host/convert"
    try:
        resp = requests.get(
            url,
            params={"from": base, "to": target, "amount": 1},
            timeout=5,
        )
        data = resp.json()
        if not data.get("success"):
            return None
        result = data.get("result")
        if result is None:
            return None
        return float(result)
    except Exception:
        return None


def build_rate_reply(base: str, target: str) -> str:
    rate = get_rate_from_api(base, target)
    if rate is None:
        return f"查不到 {base} 對 {target} 的匯率 QQ\n試試別的貨幣看看～"
    return f"1 {base} ≈ {rate:.4f} {target}"


# ---------- 天氣查詢相關 ----------

# 簡單內建幾個常用城市的座標（Open-Meteo 不用註冊）
CITY_COORDS = {
    "台北": (25.04, 121.56),
    "臺北": (25.04, 121.56),
    "新北": (25.01, 121.46),
    "桃園": (24.99, 121.30),
    "新竹": (24.80, 120.97),
    "台中": (24.14, 120.68),
    "臺中": (24.14, 120.68),
    "台南": (22.99, 120.21),
    "高雄": (22.63, 120.30),
    "基隆": (25.13, 121.74),
    "花蓮": (23.98, 121.61),
    "台東": (22.76, 121.14),
    "嘉義": (23.48, 120.44),
    "屏東": (22.67, 120.49),
}


def weathercode_to_text(code: int) -> str:
    if code is None:
        return "天氣狀況不明"

    if code == 0:
        return "晴朗無雲"
    elif 1 <= code <= 3:
        return "多雲"
    elif code in (45, 48):
        return "有霧"
    elif 51 <= code <= 57:
        return "毛毛雨"
    elif 61 <= code <= 65:
        return "降雨"
    elif 66 <= code <= 67:
        return "凍雨"
    elif 71 <= code <= 77:
        return "降雪"
    elif 80 <= code <= 82:
        return "驟雨"
    elif 95 <= code <= 99:
        return "雷雨 / 暴風雨"
    else:
        return "天氣狀況不明"


def get_weather_reply(city: str) -> str:
    city = city.strip()
    coords = CITY_COORDS.get(city)
    if not coords:
        return (
            f"找不到「{city}」這個城市 QQ\n"
            
"可以試試：台北、新北、桃園、新竹、台中、台南、高雄、基隆、花蓮、台東…"
        )

    lat, lon = coords
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "timezone": "Asia/Taipei",
    }

    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        cw = data.get("current_weather")
        if not cw:
            return "查不到現在天氣，等等再試試～"

        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        code = cw.get("weathercode")
        desc = weathercode_to_text(code)

        return (
            f"{city}目前天氣：\n"
            f"溫度：{temp}°C\n"
            f"風速：{wind} m/s\n"
            f"狀況：{desc}"
        )
    except Exception:
        return "查不到現在天氣，可能 API 暫時壞掉了，等等再試試～"


# ---------- LINE 訊息處理 ----------

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    # 1) 匯率查詢：匯率 USD TWD 或 rate usd jpy
    if user_text.startswith("匯率") or 
user_text.lower().startswith("rate"):
        parts = user_text.split()
        if len(parts) == 3:
            base = parts[1].upper()
            target = parts[2].upper()
            reply = build_rate_reply(base, target)
        else:
            reply = (
                "匯率查詢用法：\n"
                "匯率 USD TWD\n"
                "或：rate usd jpy"
            )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply),
        )
        return

    # 2) 天氣查詢：天氣 台北 或 weather taipei
    if user_text.startswith("天氣") or 
user_text.lower().startswith("weather"):
        parts = user_text.split()
        if len(parts) >= 2:
            city = parts[1]
            reply = get_weather_reply(city)
        else:
            reply = (
                "天氣查詢用法：\n"
                "天氣 台北\n"
                "或：weather taipei"
            )

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply),
        )
        return

    # 3) 其他訊息：原本的 echo
    reply = f"你說：{user_text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply),
    )


if __name__ == "__main__":
    # 本地開發用；在 Render 上會由 gunicorn 啟動
    app.run(port=5000, debug=True)
EOF

