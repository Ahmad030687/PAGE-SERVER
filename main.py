import requests
import re
from flask import Flask, request, render_template_string, jsonify
from threading import Thread, Event
import time
import random
import string

app = Flask(__name__)

# Global storage
stop_events = {}

# --- Professional Header for Requests ---
HEADERS = {
    'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
}

def get_fb_token(username, password):
    session = requests.Session()
    try:
        # Initial hit to get cookies
        login_page = session.get('https://m.facebook.com/login/', headers=HEADERS)
        
        # Extracting hidden form data
        lsd = re.search('name="lsd" value="(.*?)"', login_page.text).group(1)
        jazoest = re.search('name="jazoest" value="(.*?)"', login_page.text).group(1)
        
        payload = {
            'lsd': lsd, 'jazoest': jazoest,
            'email': username, 'pass': password, 'login': 'Log In'
        }
        
        # Login Attempt
        post_login = session.post('https://m.facebook.com/login/device-based/regular/login/', data=payload, headers=HEADERS)
        
        if 'c_user' in session.cookies.get_dict():
            # Grabbing Token from Business View
            # Note: This is a robust way to find EAAG tokens
            token_url = "https://business.facebook.com/business_locations"
            token_page = session.get(token_url, headers=HEADERS)
            
            find_token = re.search('(EAAG\w+)', token_page.text)
            if find_token:
                return {"status": "success", "token": find_token.group(1)}
            else:
                return {"status": "error", "msg": "Login Success but Token not found. Use manual token."}
        else:
            return {"status": "error", "msg": "Login Failed. Wrong credentials or Checkpoint."}
            
    except Exception as e:
        return {"status": "error", "msg": f"Extraction Error: {str(e)}"}

# --- Messenger Logic ---
def send_messages(token, thread_id, hater, interval, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set(): break
            url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
            payload = {'access_token': token, 'message': f"{hater} {msg}"}
            try:
                requests.post(url, data=payload)
            except: pass
            time.sleep(interval)

# --- Premium UI Template ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AHMAD ALI SAFDAR | PREMIUM TOOL</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --primary: #00f2fe; --secondary: #4facfe; --dark: #0f172a; }
        body {
            background: radial-gradient(circle at top, #1e293b, #0f172a);
            color: #e2e8f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
        }
        .navbar { background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            padding: 25px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.5);
            margin-bottom: 30px;
        }
        .form-control {
            background: rgba(255, 255, 255, 0.07) !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
            color: white !important;
            border-radius: 10px;
            padding: 12px;
        }
        .form-control:focus { box-shadow: 0 0 15px var(--primary); border-color: var(--primary) !important; }
        .btn-premium {
            background: linear-gradient(135deg, var(--secondary), var(--primary));
            border: none; color: white; font-weight: bold; border-radius: 10px;
            transition: all 0.3s; padding: 12px;
        }
        .btn-premium:hover { transform: translateY(-2px); box-shadow: 0 5px 15px var(--secondary); }
        .status-box { font-size: 0.9rem; color: #94a3b8; }
        .neon-text { color: var(--primary); text-shadow: 0 0 10px var(--primary); font-weight: 800; }
        footer { color: #64748b; font-size: 0.8rem; padding: 20px; }
    </style>
</head>
<body>

<nav class="navbar sticky-top">
    <div class="container justify-content-center">
        <span class="navbar-brand neon-text">♛ AHMAD ALI SAFDAR ♛</span>
    </div>
</nav>

<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6">
            <div class="glass-card">
                <h5 class="mb-4 text-center"><i class="fa-solid fa-key me-2"></i>Token Extractor</h5>
                <form action="/extract" method="POST">
                    <div class="mb-3">
                        <input type="text" name="user" class="form-control" placeholder="FB Email / Phone" required>
                    </div>
                    <div class="mb-3">
                        <input type="password" name="pass" class="form-control" placeholder="FB Password" required>
                    </div>
                    <button type="submit" class="btn btn-premium w-100">EXTRACT EAAG TOKEN</button>
                </form>
                {% if res %}
                <div class="mt-3 p-2 bg-dark rounded small text-break border border-secondary">
                    <strong class="text-warning">Result:</strong> {{ res }}
                </div>
                {% endif %}
            </div>

            <div class="glass-card">
                <h5 class="mb-4 text-center"><i class="fa-solid fa-rocket me-2"></i>Messenger Commander</h5>
                <form action="/run" method="POST" enctype="multipart/form-data">
                    <div class="mb-3">
                        <input type="text" name="token" class="form-control" placeholder="Paste Access Token Here" required>
                    </div>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <input type="text" name="thread" class="form-control" placeholder="Convo/Inbox ID" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <input type="text" name="hater" class="form-control" placeholder="Hater Name" required>
                        </div>
                    </div>
                    <div class="mb-3">
                        <input type="number" name="time" class="form-control" placeholder="Speed (Seconds)" required>
                    </div>
                    <div class="mb-3">
                        <label class="form-label small">Upload Message File (.txt)</label>
                        <input type="file" name="msg_file" class="form-control" required>
                    </div>
                    <button type="submit" class="btn btn-premium w-100 mb-3">LAUNCH ATTACK</button>
                </form>
                
                <form action="/stop" method="POST">
                    <div class="input-group">
                        <input type="text" name="task_id" class="form-control" placeholder="Task ID">
                        <button class="btn btn-danger" type="submit">STOP</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>

<footer class="text-center">
    <p>Developed by <span class="text-light">Ahmii King</span> | &copy; 2026</p>
    <div class="social-icons">
        <a href="https://wa.me/+923324661564" class="text-success me-3"><i class="fab fa-whatsapp"></i></a>
        <a href="https://facebook.com/ahmadali.safdar.52" class="text-primary"><i class="fab fa-facebook"></i></a>
    </div>
</footer>

</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract():
    user = request.form.get('user')
    pw = request.form.get('pass')
    result = get_fb_token(user, pw)
    if result['status'] == 'success':
        return render_template_string(HTML_TEMPLATE, res=result['token'])
    else:
        return render_template_string(HTML_TEMPLATE, res=result['msg'])

@app.route('/run', methods=['POST'])
def run_attack():
    token = request.form.get('token')
    thread = request.form.get('thread')
    hater = request.form.get('hater')
    speed = int(request.form.get('time'))
    msg_file = request.files['msg_file']
    msgs = msg_file.read().decode().splitlines()

    task_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    stop_events[task_id] = Event()
    
    Thread(target=send_messages, args=(token, thread, hater, speed, msgs, task_id)).start()
    return f"<h1>Attack Initialized! Task ID: {task_id}</h1><br><a href='/'>Back to Dashboard</a>"

@app.route('/stop', methods=['POST'])
def stop():
    task_id = request.form.get('task_id')
    if task_id in stop_events:
        stop_events[task_id].set()
        return "Task Stopped Successfully."
    return "Invalid Task ID."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
                                      
