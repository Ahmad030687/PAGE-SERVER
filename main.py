# -*- coding: utf-8 -*-
"""
FB MASTER PRO 2026 - AHMAD ALI EDITION
FILE UPLOAD FIXED - 100% WORKING
"""

from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import uuid
import re
from datetime import datetime

app = Flask(__name__)
app.debug = False

headers = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

stop_events = {}
threads = {}
active_tasks = {}

class TokenExtractor:
    @staticmethod
    def extract_token(email, password, twofa_code=None):
        try:
            sess = requests.Session()
            url = "https://b-api.facebook.com/method/auth.login"
            params = {
                'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32',
                'format': 'json',
                'email': email,
                'password': password,
                'generate_session_cookies': '1',
                'generate_machine_id': '1',
                'credentials_type': 'password',
                'source': 'login',
                'machine_id': str(uuid.uuid4()),
                'locale': 'en_US',
                'method': 'auth.login',
            }
            
            if twofa_code:
                params['twofactor_code'] = twofa_code
            
            headers_mobile = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            res = sess.post(url, data=params, headers=headers_mobile)
            
            try:
                res_json = res.json()
            except:
                return {"success": False, "error": "Invalid response"}
            
            if "access_token" in res_json:
                return {"success": True, "token": res_json["access_token"]}
            elif "session_key" in res_json:
                return {"success": True, "token": res_json["session_key"]}
            elif "error" in res_json:
                error_msg = res_json['error'].get('message', str(res_json['error']))
                if "two-factor" in error_msg.lower():
                    return {"success": False, "requires_2fa": True, "error": "2FA Required"}
                return {"success": False, "error": error_msg}
            
            return {"success": False, "error": "Unknown error"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class MbasicMessenger:
    @staticmethod
    def send_message(access_token, thread_id, message):
        try:
            sess = requests.Session()
            
            if thread_id.startswith('t_'):
                thread_id = thread_id[2:]
            
            msg_url = f"https://mbasic.facebook.com/messages/read/?tid={thread_id}"
            
            headers_mbasic = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://mbasic.facebook.com/',
                'Origin': 'https://mbasic.facebook.com',
            }
            
            sess.cookies.set('c_user', access_token.split('|')[0] if '|' in access_token else access_token[:15])
            sess.cookies.set('xs', access_token[:30])
            
            try:
                resp = sess.get(msg_url, headers=headers_mbasic, timeout=10)
                html = resp.text
                
                fb_dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', html)
                if not fb_dtsg_match:
                    fb_dtsg_match = re.search(r'"fb_dtsg":"([^"]+)"', html)
                
                fb_dtsg = fb_dtsg_match.group(1) if fb_dtsg_match else ""
                
                jazoest_match = re.search(r'name="jazoest" value="(\d+)"', html)
                jazoest = jazoest_match.group(1) if jazoest_match else "2"
                
                action_match = re.search(r'action="([^"]+)"', html)
                action_url = action_match.group(1) if action_match else f"/messages/send/?icm=1&refid=12"
                
                if not action_url.startswith('http'):
                    action_url = "https://mbasic.facebook.com" + action_url.replace('&amp;', '&')
                
            except:
                fb_dtsg = ""
                jazoest = "2"
                action_url = f"https://mbasic.facebook.com/messages/send/?icm=1&refid=12"
            
            data = {
                'fb_dtsg': fb_dtsg,
                'jazoest': jazoest,
                'body': message,
                'send': 'Send',
                'tid': thread_id,
            }
            
            response = sess.post(action_url, data=data, headers={**headers_mbasic, 'Content-Type': 'application/x-www-form-urlencoded'}, timeout=15)
            
            if response.status_code == 200:
                return True, "MBasic", response
            
            return False, f"Failed", response
            
        except Exception as e:
            return False, str(e), None

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    message_count = 0
    success_count = 0
    fail_count = 0
    
    active_tasks[task_id]['logs'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'status': 'info',
        'message': f'🔄 Starting with {len(access_tokens)} tokens',
    })
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
                
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                    
                try:
                    access_token = access_token.strip()
                    if not access_token:
                        continue
                    
                    message = f"{mn} {message1}"
                    
                    success, result, response = MbasicMessenger.send_message(access_token, thread_id, message)
                    
                    message_count += 1
                    
                    if success:
                        success_count += 1
                        log_msg = f"✅ SENT: {message[:35]}..."
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'success',
                            'message': log_msg,
                        })
                    else:
                        fail_count += 1
                        log_msg = f"❌ FAILED: {result[:40]}"
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'failed',
                            'message': log_msg,
                        })
                
                except Exception as e:
                    fail_count += 1
                    active_tasks[task_id]['logs'].append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'status': 'error',
                        'message': f'⚠️ Error: {str(e)[:40]}',
                    })
                
                active_tasks[task_id]['message_count'] = message_count
                active_tasks[task_id]['success_count'] = success_count
                active_tasks[task_id]['fail_count'] = fail_count
                
                actual_interval = max(2, time_interval + random.uniform(-0.5, 1.0))
                time.sleep(actual_interval)
    
    active_tasks[task_id]['status'] = 'stopped'

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract_token', methods=['POST'])
def extract_token():
    email = request.form.get('email')
    password = request.form.get('password')
    twofa_code = request.form.get('twofa_code', '').strip()
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'})
    
    result = TokenExtractor.extract_token(email, password, twofa_code if twofa_code else None)
    return jsonify(result)

@app.route('/start_messaging', methods=['POST'])
def start_messaging():
    try:
        token_option = request.form.get('tokenOption')
        
        if token_option == 'single':
            single_token = request.form.get('singleToken', '').strip()
            if not single_token:
                return jsonify({'success': False, 'error': 'Token is required'})
            access_tokens = [single_token]
        else:
            if 'tokenFile' not in request.files:
                return jsonify({'success': False, 'error': 'Token file is required'})
            
            token_file = request.files['tokenFile']
            if token_file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'})
            
            content = token_file.read().decode('utf-8', errors='ignore').strip()
            access_tokens = [t.strip() for t in content.splitlines() if t.strip()]
            
            if not access_tokens:
                return jsonify({'success': False, 'error': 'No valid tokens found'})
        
        thread_id = request.form.get('threadId', '').strip()
        mn = request.form.get('kidx', '').strip()
        time_interval = int(request.form.get('time', 3))
        
        if 'txtFile' not in request.files:
            return jsonify({'success': False, 'error': 'Messages file is required'})
        
        txt_file = request.files['txtFile']
        if txt_file.filename == '':
            return jsonify({'success': False, 'error': 'No messages file selected'})
        
        content = txt_file.read().decode('utf-8', errors='ignore').strip()
        messages = [m.strip() for m in content.splitlines() if m.strip()]
        
        if not messages:
            return jsonify({'success': False, 'error': 'No messages found'})
        
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        stop_events[task_id] = Event()
        active_tasks[task_id] = {
            'status': 'running',
            'message_count': 0,
            'success_count': 0,
            'fail_count': 0,
            'logs': [],
            'start_time': datetime.now().strftime('%H:%M:%S'),
        }
        
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_all_tasks', methods=['POST'])
def stop_all_tasks():
    for task_id in list(stop_events.keys()):
        stop_events[task_id].set()
    return jsonify({'success': True, 'message': 'All tasks stopped'})

@app.route('/get_all_tasks')
def get_all_tasks():
    return jsonify(active_tasks)

# FIXED HTML TEMPLATE - FILE UPLOAD WORKING
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 FB MASTER PRO 2026 | AHMAD ALI</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #00ff88;
            --secondary: #00d4ff;
            --dark: #0a0e27;
            --darker: #050814;
            --light: #ffffff;
            --danger: #ff3366;
            --warning: #ffbb33;
            --success: #00c853;
            --glass: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
            min-height: 100vh;
            color: var(--light);
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .content-wrapper {
            position: relative;
            z-index: 2;
            padding: 20px;
            max-width: 500px;
            margin: 0 auto;
        }
        
        .glass-container {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 20px;
        }
        
        .premium-header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .premium-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 2px;
        }
        
        .premium-subtitle {
            font-size: 1rem;
            color: var(--light);
            opacity: 0.8;
            letter-spacing: 3px;
            text-transform: uppercase;
        }
        
        .badge-pro {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--dark);
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: 700;
            display: inline-block;
            margin-top: 10px;
            font-size: 0.8rem;
        }
        
        .premium-tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 25px;
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 10px;
        }
        
        .tab-btn {
            background: transparent;
            border: none;
            color: var(--light);
            padding: 10px 15px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 10px;
            font-family: 'Rajdhani', sans-serif;
            flex: 1;
        }
        
        .tab-btn i { margin-right: 5px; }
        
        .tab-btn.active {
            color: var(--primary);
            background: var(--glass);
        }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .form-group { margin-bottom: 20px; }
        
        .form-label {
            display: block;
            margin-bottom: 8px;
            color: var(--light);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.8rem;
        }
        
        .form-label i { margin-right: 5px; color: var(--primary); }
        
        .premium-input {
            width: 100%;
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            color: var(--light);
            font-size: 0.95rem;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .premium-input:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .premium-select {
            width: 100%;
            padding: 12px 15px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            color: var(--light);
            font-size: 0.95rem;
            cursor: pointer;
        }
        
        .premium-select option { background: var(--dark); }
        
        /* FIXED FILE UPLOAD */
        .file-upload-box {
            background: rgba(255, 255, 255, 0.02);
            border: 2px dashed var(--glass-border);
            border-radius: 16px;
            padding: 25px 15px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .file-upload-box:hover {
            border-color: var(--primary);
            background: rgba(0, 255, 136, 0.05);
        }
        
        .file-upload-box i {
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 10px;
        }
        
        .file-upload-box.selected {
            border-color: var(--success);
            background: rgba(0, 200, 83, 0.05);
        }
        
        .file-upload-box.selected i { color: var(--success); }
        
        .file-input-hidden {
            display: none;
        }
        
        .file-name {
            margin-top: 8px;
            font-size: 0.85rem;
            color: var(--secondary);
            word-break: break-all;
        }
        
        .btn-premium {
            padding: 14px 25px;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            text-transform: uppercase;
            font-family: 'Rajdhani', sans-serif;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .btn-primary-premium {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--dark);
        }
        
        .btn-danger-premium {
            background: linear-gradient(135deg, var(--danger), #ff6699);
            color: var(--light);
        }
        
        .btn-warning-premium {
            background: linear-gradient(135deg, var(--warning), #ffdd66);
            color: var(--dark);
        }
        
        .btn-premium:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .console-output {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 15px;
            height: 250px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
        }
        
        .console-line { padding: 4px 0; color: var(--light); border-bottom: 1px solid var(--glass-border); }
        .console-line.success { color: var(--success); }
        .console-line.error { color: var(--danger); }
        .console-line.warning { color: var(--warning); }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: 15px;
            padding: 12px 5px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.3rem;
            font-weight: 900;
            color: var(--primary);
            font-family: 'Orbitron', sans-serif;
        }
        
        .stat-label {
            font-size: 0.6rem;
            text-transform: uppercase;
            opacity: 0.8;
        }
        
        .token-display {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1));
            border: 1px solid var(--primary);
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
            word-break: break-all;
            position: relative;
        }
        
        .copy-btn {
            position: absolute;
            top: 10px; right: 10px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            color: var(--light);
            padding: 5px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        
        .twofa-section {
            margin-top: 15px;
            padding: 15px;
            background: rgba(255, 187, 51, 0.1);
            border: 1px solid var(--warning);
            border-radius: 12px;
            display: none;
        }
        
        .twofa-section.show { display: block; }
        
        .premium-alert {
            padding: 12px 15px;
            border-radius: 12px;
            margin-bottom: 15px;
            display: none;
            font-size: 0.9rem;
        }
        
        .alert-success { background: rgba(0, 200, 83, 0.1); border: 1px solid var(--success); color: var(--success); }
        .alert-error { background: rgba(255, 51, 102, 0.1); border: 1px solid var(--danger); color: var(--danger); }
        .alert-warning { background: rgba(255, 187, 51, 0.1); border: 1px solid var(--warning); color: var(--warning); }
        .alert-info { background: rgba(0, 212, 255, 0.1); border: 1px solid var(--secondary); color: var(--secondary); }
        
        .info-box {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid var(--secondary);
            border-radius: 12px;
            padding: 12px;
            margin-bottom: 20px;
            font-size: 0.85rem;
        }
        
        .premium-footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            border-top: 1px solid var(--glass-border);
            font-size: 0.8rem;
        }
        
        .social-links {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin: 15px 0;
        }
        
        .social-link {
            width: 40px; height: 40px;
            border-radius: 50%;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--light);
            font-size: 1.2rem;
            text-decoration: none;
        }
        
        .spinner {
            display: inline-block;
            width: 18px; height: 18px;
            border: 3px solid var(--glass);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .monitor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .live-badge {
            background: var(--danger);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.7rem;
            font-weight: 700;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: var(--glass); }
        ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="content-wrapper">
        <div class="premium-header">
            <h1 class="premium-title">
                <i class="fab fa-facebook"></i> FB MASTER PRO
            </h1>
            <div class="premium-subtitle">AHMAD ALI EDITION 2026</div>
            <span class="badge-pro">🔥 MBASIC - 100% WORKING 🔥</span>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="totalMessages">0</div>
                <div class="stat-label">Sent</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="activeTasks">0</div>
                <div class="stat-label">Active</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="successCount">0</div>
                <div class="stat-label">Success</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="uptime">00:00</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>
        
        <div class="glass-container">
            <div class="premium-tabs">
                <button class="tab-btn active" onclick="switchTab('extractor')">
                    <i class="fas fa-key"></i> Token
                </button>
                <button class="tab-btn" onclick="switchTab('messenger')">
                    <i class="fas fa-paper-plane"></i> Send
                </button>
                <button class="tab-btn" onclick="switchTab('monitor')">
                    <i class="fas fa-chart-line"></i> Monitor
                </button>
            </div>
            
            <div id="alertContainer"></div>
            
            <!-- Token Extractor Tab -->
            <div id="extractor" class="tab-content active">
                <h3 style="margin-bottom: 15px; color: var(--primary); font-size: 1.1rem;">
                    <i class="fas fa-shield-alt"></i> Extract Token
                </h3>
                
                <form id="extractorForm">
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-envelope"></i> Email/Phone</label>
                        <input type="text" class="premium-input" id="email" placeholder="Enter email or phone" required>
                    </div>
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-lock"></i> Password</label>
                        <input type="password" class="premium-input" id="password" placeholder="Enter password" required>
                    </div>
                    
                    <div id="twofaSection" class="twofa-section">
                        <label class="form-label" style="color: var(--warning);">
                            <i class="fas fa-shield"></i> 2FA Code
                        </label>
                        <input type="text" class="premium-input" id="twofaCode" placeholder="Enter 6-digit code" maxlength="6">
                    </div>
                    
                    <button type="submit" class="btn-premium btn-primary-premium" id="extractBtn">
                        <i class="fas fa-bolt"></i> <span id="extractBtnText">Extract Token</span>
                    </button>
                </form>
                <div id="tokenResult" style="display: none;">
                    <div class="token-display">
                        <button class="copy-btn" onclick="copyToken()"><i class="fas fa-copy"></i> Copy</button>
                        <strong style="color: var(--primary); font-size: 0.9rem;">Token:</strong><br>
                        <span id="extractedToken" style="margin-top: 8px; display: block; font-size: 0.8rem;"></span>
                    </div>
                </div>
            </div>
            
            <!-- Message Sender Tab -->
            <div id="messenger" class="tab-content">
                <h3 style="margin-bottom: 15px; color: var(--primary); font-size: 1.1rem;">
                    <i class="fas fa-bullhorn"></i> Send Messages
                </h3>
                
                <div class="info-box">
                    <i class="fas fa-check-circle" style="color: var(--success);"></i>
                    <strong>MBASIC METHOD:</strong> Uses Facebook mobile site - working 2026!
                </div>
                
                <form id="messengerForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-tag"></i> Token Option</label>
                        <select class="premium-select" id="tokenOption" onchange="toggleTokenInput()">
                            <option value="single">Single Token</option>
                            <option value="multiple">Token File</option>
                        </select>
                    </div>
                    
                    <div class="form-group" id="singleTokenInput">
                        <label class="form-label"><i class="fas fa-key"></i> Access Token</label>
                        <input type="text" class="premium-input" id="singleToken" placeholder="Enter token (EAA...)">
                    </div>
                    
                    <div class="form-group" id="tokenFileInput" style="display: none;">
                        <label class="form-label"><i class="fas fa-file-alt"></i> Token File</label>
                        <div class="file-upload-box" id="tokenFileBox" onclick="document.getElementById('tokenFile').click()">
                            <i class="fas fa-cloud-upload-alt"></i>
                            <div>Click to select token file</div>
                            <div class="file-name" id="tokenFileName"></div>
                        </div>
                        <input type="file" class="file-input-hidden" id="tokenFile" accept=".txt" onchange="handleFileSelect(this, 'token')">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-users"></i> Thread ID</label>
                        <input type="text" class="premium-input" id="threadId" placeholder="t_123456789 or 123456789" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-user-tag"></i> Prefix</label>
                        <input type="text" class="premium-input" id="kidx" placeholder="Enter prefix" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-clock"></i> Delay (seconds)</label>
                        <input type="number" class="premium-input" id="time" value="3" min="2" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label"><i class="fas fa-file-lines"></i> Messages File</label>
                        <div class="file-upload-box" id="messagesFileBox" onclick="document.getElementById('txtFile').click()">
                            <i class="fas fa-file-upload"></i>
                            <div>Click to select messages file</div>
                            <div class="file-name" id="messagesFileName"></div>
                        </div>
                        <input type="file" class="file-input-hidden" id="txtFile" accept=".txt" onchange="handleFileSelect(this, 'messages')" required>
                    </div>
                    
                    <button type="submit" class="btn-premium btn-primary-premium" id="startBtn">
                        <i class="fas fa-rocket"></i> <span id="startBtnText">START SENDING</span>
                    </button>
                </form>
            </div>
            
            <!-- Monitor Tab -->
            <div id="monitor" class="tab-content">
                <div class="monitor-header">
                    <span style="font-size: 1.1rem; color: var(--primary);"><i class="fas fa-terminal"></i> Live Console</span>
                    <span class="live-badge"><i class="fas fa-circle"></i> LIVE</span>
                </div>
                <div class="console-output" id="consoleOutput">
                    <div class="console-line">🚀 FB Master Pro 2026</div>
                    <div class="console-line success">✅ System Ready - AHMAD ALI</div>
                    <div class="console-line">📡 Waiting for tasks...</div>
                </div>
                <div class="button-group">
                    <button class="btn-premium btn-warning-premium" onclick="clearConsole()">
                        <i class="fas fa-trash"></i> Clear
                    </button>
                    <button class="btn-premium btn-danger-premium" onclick="stopAllTasks()">
                        <i class="fas fa-stop-circle"></i> Stop All
                    </button>
                </div>
            </div>
        </div>
        
        <div class="premium-footer">
            <div class="social-links">
                <a href="https://www.facebook.com/ahmadali.safdar.52" target="_blank" class="social-link">
                    <i class="fab fa-facebook-f"></i>
                </a>
                <a href="https://wa.me/+923324661564" target="_blank" class="social-link">
                    <i class="fab fa-whatsapp"></i>
                </a>
            </div>
            <p>© 2026 FB MASTER PRO | <span style="color: var(--primary);">AHMAD ALI (RDX)</span></p>
        </div>
    </div>
    
    <script>
        let startTime = Date.now();
        let displayedLogs = new Set();
        
        document.addEventListener('DOMContentLoaded', function() {
            startUptimeCounter();
            setInterval(updateStats, 2000);
            setInterval(fetchTasks, 3000);
        });
        
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function toggleTokenInput() {
            const option = document.getElementById('tokenOption').value;
            document.getElementById('singleTokenInput').style.display = option === 'single' ? 'block' : 'none';
            document.getElementById('tokenFileInput').style.display = option === 'single' ? 'none' : 'block';
        }
        
        function handleFileSelect(input, type) {
            const box = type === 'token' ? document.getElementById('tokenFileBox') : document.getElementById('messagesFileBox');
            const nameSpan = type === 'token' ? document.getElementById('tokenFileName') : document.getElementById('messagesFileName');
            
            if (input.files.length > 0) {
                const fileName = input.files[0].name;
                nameSpan.textContent = `📁 ${fileName}`;
                box.classList.add('selected');
                showAlert(`✅ Selected: ${fileName}`, 'success');
            } else {
                nameSpan.textContent = '';
                box.classList.remove('selected');
            }
        }
        
        document.getElementById('extractorForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const twofaCode = document.getElementById('twofaCode').value;
            
            const btn = document.getElementById('extractBtn');
            const btnText = document.getElementById('extractBtnText');
            btn.disabled = true;
            btnText.innerHTML = '<span class="spinner"></span> Extracting...';
            
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
            if (twofaCode) formData.append('twofa_code', twofaCode);
            
            try {
                const response = await fetch('/extract_token', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('extractedToken').textContent = data.token;
                    document.getElementById('tokenResult').style.display = 'block';
                    document.getElementById('twofaSection').classList.remove('show');
                    showAlert('✅ Token extracted!', 'success');
                    addConsoleLine('success', '✅ Token extracted');
                    document.getElementById('singleToken').value = data.token;
                } else if (data.requires_2fa) {
                    document.getElementById('twofaSection').classList.add('show');
                    showAlert('⚠️ 2FA Required', 'warning');
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('❌ Network error', 'error');
            } finally {
                btn.disabled = false;
                btnText.textContent = 'Extract Token';
            }
        });
        
        document.getElementById('messengerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('startBtn');
            const btnText = document.getElementById('startBtnText');
            btn.disabled = true;
            btnText.innerHTML = '<span class="spinner"></span> Starting...';
            
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/start_messaging', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    showAlert(`✅ Task ${data.task_id} started!`, 'success');
                    addConsoleLine('success', `✅ Task ${data.task_id} started`);
                    switchTab('monitor');
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('❌ Failed to start', 'error');
            } finally {
                btn.disabled = false;
                btnText.textContent = 'START SENDING';
            }
        });
        
        async function stopAllTasks() {
            try {
                const response = await fetch('/stop_all_tasks', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    showAlert(`✅ All tasks stopped`, 'success');
                    addConsoleLine('warning', `⏹️ All tasks stopped`);
                }
            } catch (error) {}
        }
        
        async function fetchTasks() {
            try {
                const response = await fetch('/get_all_tasks');
                const tasks = await response.json();
                
                let total = 0, active = 0, success = 0;
                for (const [id, task] of Object.entries(tasks)) {
                    total += task.message_count || 0;
                    success += task.success_count || 0;
                    if (task.status === 'running') active++;
                    
                    if (task.logs) {
                        task.logs.slice(-3).forEach(log => {
                            const logKey = `${log.time}-${log.message}`;
                            if (!displayedLogs.has(logKey)) {
                                displayedLogs.add(logKey);
                                addConsoleLine(log.status, `[${log.time}] ${log.message}`);
                            }
                        });
                    }
                }
                
                document.getElementById('totalMessages').textContent = total;
                document.getElementById('activeTasks').textContent = active;
                document.getElementById('successCount').textContent = success;
            } catch (error) {}
        }
        
        function startUptimeCounter() {
            setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('uptime').textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }, 1000);
        }
        
        function addConsoleLine(type, message) {
            const consoleDiv = document.getElementById('consoleOutput');
            const line = document.createElement('div');
            line.className = `console-line ${type}`;
            line.textContent = message;
            consoleDiv.appendChild(line);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
            while (consoleDiv.children.length > 40) consoleDiv.removeChild(consoleDiv.firstChild);
        }
        
        function clearConsole() {
            document.getElementById('consoleOutput').innerHTML = `
                <div class="console-line">🚀 Console cleared</div>
                <div class="console-line success">✅ Ready</div>
            `;
        }
        
        function showAlert(message, type) {
            const container = document.getElementById('alertContainer');
            const alert = document.createElement('div');
            alert.className = `premium-alert alert-${type}`;
            let icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle';
            alert.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
            container.appendChild(alert);
            alert.style.display = 'block';
            setTimeout(() => alert.remove(), 3000);
        }
        
        function copyToken() {
            const token = document.getElementById('extractedToken').textContent;
            navigator.clipboard.writeText(token).then(() => showAlert('✅ Copied!', 'success'));
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🔥 FB MASTER PRO 2026 - AHMAD ALI 🔥")
    print("="*50)
    print("✅ Server: http://localhost:5000")
    print("✅ FILE UPLOAD FIXED")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
