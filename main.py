import requests
import re
from flask import Flask, request, render_template_string
from threading import Thread, Event
import time
import random
import string

app = Flask(__name__)

# Storage
stop_events = {}

# --- Token Extraction Function ---
def get_fb_token(username, password):
    try:
        session = requests.Session()
        # Headers for mobile login
        headers = {
            'authority': 'free.facebook.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://free.facebook.com',
            'referer': 'https://free.facebook.com/login/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; Mi 9T Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.153 Mobile Safari/537.36',
        }
        
        # Step 1: Get login page
        response = session.get('https://free.facebook.com/login/', headers=headers)
        
        # Step 2: Post login data
        payload = {
            'lsd': re.search('name="lsd" value="(.*?)"', response.text).group(1),
            'jazoest': re.search('name="jazoest" value="(.*?)"', response.text).group(1),
            'm_ts': re.search('name="m_ts" value="(.*?)"', response.text).group(1),
            'li': re.search('name="li" value="(.*?)"', response.text).group(1),
            'email': username,
            'pass': password,
            'login': 'Log In'
        }
        
        login_post = session.post('https://free.facebook.com/login/device-based/regular/login/', data=payload, headers=headers)
        
        if 'c_user' in session.cookies.get_dict():
            # Step 3: Get EAAG Token from Business Manager
            token_page = session.get('https://business.facebook.com/business_locations', headers=headers)
            token = re.search('(EAAG\w+)', token_page.text).group(1)
            return {"status": "success", "token": token}
        else:
            return {"status": "error", "msg": "Login Failed / Checkpoint"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

# --- Messaging Logic ---
def send_messages(access_tokens, thread_id, hater_name, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set(): break
            for token in access_tokens:
                url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                payload = {'access_token': token, 'message': f"{hater_name} {msg}"}
                try:
                    requests.post(url, data=payload)
                except: pass
                time.sleep(time_interval)

# --- UI Template ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>AHMAD KING TOOL</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0e0e0e; color: #00ff00; font-family: sans-serif; text-align: center; }
        .box { border: 1px solid #00ff00; padding: 20px; border-radius: 15px; margin: 20px auto; max-width: 400px; background: #1a1a1a; }
        input, select { background: #000 !important; color: #00ff00 !important; border: 1px solid #00ff00 !important; margin-bottom: 10px; }
        .btn-extract { background: #ff9800; color: white; width: 100%; margin-bottom: 20px; }
        .btn-start { background: #00ff00; color: #000; font-weight: bold; width: 100%; }
    </style>
</head>
<body>
    <h2 class="mt-4">♛ AHMAD ALI SAFDAR ♛</h2>
    
    <div class="box">
        <h4>1. Extract Token (ID/PASS)</h4>
        <form action="/extract" method="POST">
            <input type="text" name="user" class="form-control" placeholder="Email/Number" required>
            <input type="password" name="pass" class="form-control" placeholder="Password" required>
            <button type="submit" class="btn btn-extract">Get Token</button>
        </form>
        {% if token_result %}
            <p style="word-wrap: break-word; color: yellow;">Result: {{ token_result }}</p>
        {% endif %}
    </div>

    <div class="box">
        <h4>2. Run Tool</h4>
        <form method="POST" action="/run" enctype="multipart/form-data">
            <input type="text" name="token" class="form-control" placeholder="Enter Token (Extracted or Manual)" required>
            <input type="text" name="thread" class="form-control" placeholder="Convo ID" required>
            <input type="text" name="hater" class="form-control" placeholder="Hater Name" required>
            <input type="number" name="time" class="form-control" placeholder="Time (Seconds)" required>
            <input type="file" name="msg_file" class="form-control" required>
            <button type="submit" class="btn btn-start">START ATTACK</button>
        </form>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract', methods=['POST'])
def extract():
    u = request.form.get('user')
    p = request.form.get('pass')
    res = get_fb_token(u, p)
    if res['status'] == 'success':
        return render_template_string(HTML_TEMPLATE, token_result=res['token'])
    else:
        return render_template_string(HTML_TEMPLATE, token_result=res['msg'])

@app.route('/run', methods=['POST'])
def run_tool():
    token = request.form.get('token')
    thread = request.form.get('thread')
    hater = request.form.get('hater')
    interval = int(request.form.get('time'))
    msg_file = request.files['msg_file']
    messages = msg_file.read().decode().splitlines()

    task_id = ''.join(random.choices(string.digits, k=4))
    stop_events[task_id] = Event()
    
    Thread(target=send_messages, args=([token], thread, hater, interval, messages, task_id)).start()
    return f"Task Started! ID: {task_id}. Keep it running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
 
