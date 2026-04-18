import requests
import re
import time
import random
import string
from flask import Flask, request, render_template_string
from threading import Thread, Event

app = Flask(__name__)

# Global storage for background tasks
stop_events = {}

def get_fb_token_pro(username, password):
    """
    Improved Token Extractor. 
    Note: If this fails, it's due to FB Checkpoint (2FA/Security).
    """
    session = requests.Session()
    # Modern mobile headers to mimic a real device
    headers = {
        'authority': 'm.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'user-agent': 'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    }
    try:
        # Step 1: Hit Login Page
        res = session.get('https://m.facebook.com/login/', headers=headers)
        lsd = re.search('name="lsd" value="(.*?)"', res.text)
        jazoest = re.search('name="jazoest" value="(.*?)"', res.text)
        
        if not lsd:
            return {"status": "error", "msg": "FB Blocked Access. Try on a different network."}

        # Step 2: Login Data
        data = {
            'lsd': lsd.group(1),
            'jazoest': jazoest.group(1),
            'email': username,
            'pass': password,
            'login': 'Log In'
        }
        
        login_res = session.post('https://m.facebook.com/login/device-based/regular/login/', data=data, headers=headers)
        
        if 'c_user' in session.cookies.get_dict():
            # Step 3: Extracting EAAG Token from Business Manager View
            # This is the 'Premium' way people get high-quality tokens
            token_page = session.get('https://business.facebook.com/business_locations', headers=headers)
            token = re.search('(EAAG\w+)', token_page.text)
            if token:
                return {"status": "success", "token": token.group(1)}
            return {"status": "error", "msg": "Login Success, but Token was hidden by FB security."}
        else:
            return {"status": "error", "msg": "Login Failed. Check for Checkpoint/Wrong Password."}
    except Exception as e:
        return {"status": "error", "msg": f"Extraction Error: {str(e)}"}

def send_messages(token, tid, hater, speed, msgs, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for m in msgs:
            if stop_event.is_set(): break
            url = f'https://graph.facebook.com/v17.0/t_{tid}/'
            params = {'access_token': token, 'message': f"{hater} {m}"}
            try:
                requests.post(url, data=params)
            except: pass
            time.sleep(speed)

# --- ULTRA PREMIUM ATTRACTIVE UI ---
HTML_UI = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AHMAD KING | ELITE COMMANDER</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: #000; color: #fff; font-family: 'Poppins', sans-serif; overflow-x: hidden; }
        .glass-container {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 40px;
            box-shadow: 0 0 50px rgba(0, 242, 254, 0.2);
            margin-top: 50px;
        }
        .neon-text {
            background: linear-gradient(90deg, #00f2fe, #4facfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 900;
            letter-spacing: 5px;
            text-shadow: 0 0 20px rgba(0, 242, 254, 0.5);
        }
        .form-control {
            background: rgba(0,0,0,0.5);
            border: 1px solid #333;
            color: #00f2fe;
            border-radius: 15px;
            padding: 12px;
        }
        .form-control:focus {
            border-color: #00f2fe;
            box-shadow: 0 0 15px #00f2fe;
            background: rgba(0,0,0,0.7);
        }
        .btn-launch {
            background: linear-gradient(45deg, #00f2fe, #4facfe);
            border: none;
            color: #000;
            font-weight: 800;
            border-radius: 15px;
            padding: 15px;
            text-transform: uppercase;
            transition: 0.4s;
        }
        .btn-launch:hover {
            transform: scale(1.03);
            box-shadow: 0 0 30px #00f2fe;
            color: #fff;
        }
        .footer { font-size: 0.8rem; color: #555; margin-top: 30px; }
    </style>
</head>
<body>
    <div class="container" style="max-width: 550px;">
        <div class="glass-container text-center">
            <h2 class="neon-text mb-4">AHMAD ALI SAFDAR</h2>
            
            <div class="mb-5 p-3" style="border: 1px dashed #333; border-radius: 20px;">
                <h6 class="text-info mb-3">TOKEN EXTRACTOR (PRO)</h6>
                <form action="/get_token" method="POST">
                    <input type="text" name="u" class="form-control mb-2" placeholder="Phone/Email" required>
                    <input type="password" name="p" class="form-control mb-3" placeholder="Password" required>
                    <button type="submit" class="btn btn-launch w-100 py-2" style="font-size: 0.8rem;">Extract EAAG</button>
                </form>
                {% if token_res %}
                <div class="mt-3 p-2 bg-dark rounded small text-info border border-info text-break">
                    Result: {{ token_res }}
                </div>
                {% endif %}
            </div>

            <form action="/launch" method="POST" enctype="multipart/form-data">
                <input type="text" name="token" class="form-control mb-3" placeholder="Access Token" required>
                <div class="row">
                    <div class="col-6"><input type="text" name="tid" class="form-control mb-3" placeholder="Convo ID" required></div>
                    <div class="col-6"><input type="text" name="hater" class="form-control mb-3" placeholder="Hater Name" required></div>
                </div>
                <input type="number" name="speed" class="form-control mb-3" placeholder="Delay (Seconds)" required>
                <label class="small text-secondary mb-2">Upload Attack File (.txt)</label>
                <input type="file" name="file" class="form-control mb-4" required>
                <button type="submit" class="btn btn-launch w-100">LAUNCH ATTACK</button>
            </form>

            <form action="/stop" method="POST" class="mt-4">
                <div class="input-group">
                    <input type="text" name="id" class="form-control" placeholder="Task ID">
                    <button type="submit" class="btn btn-danger px-4">STOP</button>
                </div>
            </form>

            <div class="footer">
                <p>DEVELOPED BY <b>AHMAD KING</b> | &copy; 2026</p>
                <a href="https://wa.me/+923324661564" class="text-info me-2"><i class="fab fa-whatsapp"></i></a>
                <a href="#" class="text-info"><i class="fab fa-facebook"></i></a>
            </div>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/get_token', methods=['POST'])
def token_extract():
    u, p = request.form.get('u'), request.form.get('p')
    res = get_fb_token_pro(u, p)
    return render_template_string(HTML_UI, token_res=res.get('token') or res.get('msg'))

@app.route('/launch', methods=['POST'])
def launch():
    token, tid = request.form.get('token'), request.form.get('tid')
    hater, speed = request.form.get('hater'), int(request.form.get('speed'))
    msgs = request.files['file'].read().decode().splitlines()
    
    task_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    stop_events[task_id] = Event()
    
    Thread(target=send_messages, args=(token, tid, hater, speed, msgs, task_id)).start()
    return f"<h1 style='color:cyan;text-align:center;'>Attack Started! ID: {task_id}</h1>"

@app.route('/stop', methods=['POST'])
def stop():
    task_id = request.form.get('id')
    if task_id in stop_events:
        stop_events[task_id].set()
        return "Task Stopped."
    return "Invalid ID."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
        
