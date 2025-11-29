from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    return "ROOT OK", 200

@app.route("/callback", methods=["GET", "POST"])
def callback():
    # 這裡單純印出 body 看看有沒有東西進來
    print("Callback body:", request.get_data())
    # 不管收到什麼，一律回 200 OK
    return "OK", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)

