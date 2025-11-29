from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    # 給 Render / 健康檢查用
    return "OK", 200


@app.route("/callback", methods=["GET", "POST"])
def callback():
    # 不做任何簽章驗證，先確定 LINE 打得進來
    body = request.get_data(as_text=True)
    print("Got request from LINE:")
    print(body)
    return "OK", 200


if __name__ == "__main__":
    # 在本機開發用，Render 會用 gunicorn 啟動，不會用到這行的 port
    app.run(port=5000, debug=True)

