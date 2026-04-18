# FB_PRO_2026_FINAL.py
# 100% Working with Page Access Token

from flask import Flask, request, render_template_string, jsonify
import requests
import threading
import time
import random
import string
from datetime import datetime

app = Flask(__name__)

active_tasks = {}
stop_events = {}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Content-Type': 'application/json'
}

# ==================== TOKEN EXTRACTOR ====================
def extract_fb_token(email, password):
    try:
        sess = requests.Session()
        url = "https://b-api.facebook.com/method/auth.login"
        params = {
            'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32',
            'format': 'json',
            'email': email,
            'password': password,
            'generate_session_cookies': '1',
            'credentials_type': 'password',
            'source': 'login',
        }
        
        resp = sess.post(url, data=params, headers={'User-Agent': HEADERS['User-Agent']})
        data = resp.json()
        
        if "access_token" in data:
            return True, data["access_token"]
        elif "session_key" in data:
            return True, data["session_key"]
        else:
            error = data.get('error', {}).get('message', 'Login failed')
            return False, error
    except Exception as e:
        return False, str(e)

# ==================== PAGE ID EXTRACTOR ====================
def get_page_id(access_token):
    """Get Page ID from Page Access Token"""
    try:
        url = f"https://graph.facebook.com/v21.0/me/accounts"
        params = {'access_token': access_token}
        resp = requests.get(url, params=params, headers=HEADERS)
        data = resp.json()
        
        if 'data' in data and len(data['data']) > 0:
            return True, data['data'][0]['id'], data['data'][0].get('name', 'Unknown')
        else:
            return False, None, "No pages found"
    except Exception as e:
        return False, None, str(e)

# ==================== MESSAGE SENDER (OFFICIAL API) ====================
def send_via_page_api(page_id, access_token, thread_id, message):
    """Official Facebook Graph API v21.0"""
    try:
        url = f"https://graph.facebook.com/v21.0/{page_id}/messages"
        
        payload = {
            'recipient': {'id': thread_id},
            'message': {'text': message},
            'messaging_type': 'RESPONSE',
            'access_token': access_token
        }
        
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        
        if resp.status_code == 200:
            return True, "API v21.0"
        else:
            error_data = resp.json() if resp.text else {}
            error_msg = error_data.get('error', {}).get('message', f'HTTP {resp.status_code}')
            return False, error_msg
    except Exception as e:
        return False, str(e)

def send_messages_worker(task_id, tokens, thread_id, prefix, delay, messages):
    stop_event = stop_events[task_id]
    count = 0
    success = 0
    
    # Clean thread ID
    clean_tid = thread_id.replace('t_', '') if thread_id.startswith('t_') else thread_id
    
    for token in tokens:
        token = token.strip()
        if not token:
            continue
            
        # Get Page ID
        ok, page_id, page_name = get_page_id(token)
        
        if ok:
            active_tasks[task_id]['logs'].append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'msg': f'✅ Page found: {page_name} ({page_id})',
                'status': 'success'
            })
            
            # Send messages using this page
            while not stop_event.is_set():
                for msg in messages:
                    if stop_event.is_set():
                        break
                    
                    full_msg = f"{prefix} {msg}"
                    
                    ok_send, result = send_via_page_api(page_id, token, clean_tid, full_msg)
                    count += 1
                    
                    if ok_send:
                        success += 1
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'msg': f'✅ SENT: {full_msg[:30]}...',
                            'status': 'success'
                        })
                    else:
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'msg': f'❌ FAILED: {result[:40]}',
                            'status': 'error'
                        })
                    
                    active_tasks[task_id]['total'] = count
                    active_tasks[task_id]['success'] = success
                    
                    time.sleep(delay)
        else:
            active_tasks[task_id]['logs'].append({
                'time': datetime.now().strftime('%H:%M:%S'),
                'msg': f'❌ Invalid/No Page: {page_name}',
                'status': 'error'
            })
    
    active_tasks[task_id]['status'] = 'stopped'

# ==================== FLASK ROUTES ====================
@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/extract', methods=['POST'])
def api_extract():
    email = request.form.get('email', '')
    password = request.form.get('password', '')
    
    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email and password required'})
    
    ok, result = extract_fb_token(email, password)
    return jsonify({'ok': ok, 'token': result if ok else None, 'error': result if not ok else None})

@app.route('/api/start', methods=['POST'])
def api_start():
    try:
        token_type = request.form.get('token_type', 'single')
        
        if token_type == 'single':
            token = request.form.get('token', '').strip()
            if not token:
                return jsonify({'ok': False, 'error': 'Token is required'})
            tokens = [token]
        else:
            if 'token_file' not in request.files:
                return jsonify({'ok': False, 'error': 'Token file is required'})
            
            file = request.files['token_file']
            if file.filename == '':
                return jsonify({'ok': False, 'error': 'No file selected'})
            
            content = file.read().decode('utf-8', errors='ignore')
            tokens = [t.strip() for t in content.split('\n') if t.strip()]
            
            if not tokens:
                return jsonify({'ok': False, 'error': 'No tokens found'})
        
        thread_id = request.form.get('thread_id', '').strip()
        prefix = request.form.get('prefix', '').strip()
        delay = int(request.form.get('delay', 3))
        
        if 'msg_file' not in request.files:
            return jsonify({'ok': False, 'error': 'Messages file is required'})
        
        msg_file = request.files['msg_file']
        if msg_file.filename == '':
            return jsonify({'ok': False, 'error': 'No messages file selected'})
        
        content = msg_file.read().decode('utf-8', errors='ignore')
        messages = [m.strip() for m in content.split('\n') if m.strip()]
        
        if not messages:
            return jsonify({'ok': False, 'error': 'No messages found'})
        
        if not thread_id:
            return jsonify({'ok': False, 'error': 'Thread ID is required'})
        
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        stop_events[task_id] = threading.Event()
        active_tasks[task_id] = {
            'status': 'running',
            'total': 0,
            'success': 0,
            'logs': [],
            'start': datetime.now().strftime('%H:%M:%S')
        }
        
        thread = threading.Thread(
            target=send_messages_worker,
            args=(task_id, tokens, thread_id, prefix, delay, messages)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'ok': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)})

@app.route('/api/stop_all', methods=['POST'])
def api_stop_all():
    for task_id in stop_events:
        stop_events[task_id].set()
    return jsonify({'ok': True})

@app.route('/api/status')
def api_status():
    return jsonify(active_tasks)

# ==================== HTML PAGE ====================
HTML_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB MASTER PRO 2026 | AHMAD ALI</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a0a2e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 500px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        h1 {
            font-size: 26px;
            background: linear-gradient(45deg, #00ff88, #00d4ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 5px;
        }
        .sub { color: #aaa; font-size: 13px; letter-spacing: 2px; }
        .badge {
            background: linear-gradient(45deg, #00ff88, #00d4ff);
            color: #0a0e27;
            padding: 3px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            display: inline-block;
            margin-top: 8px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 20px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 10px;
        }
        .tab {
            flex: 1;
            padding: 12px;
            background: transparent;
            border: none;
            color: #fff;
            font-size: 14px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 10px;
        }
        .tab.active {
            background: rgba(0,255,136,0.1);
            color: #00ff88;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { margin-bottom: 18px; }
        label {
            display: block;
            margin-bottom: 8px;
            color: #ccc;
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
        }
        input, select {
            width: 100%;
            padding: 14px 16px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            outline: none;
        }
        input:focus, select:focus { border-color: #00ff88; }
        .file-box {
            background: rgba(255,255,255,0.03);
            border: 2px dashed rgba(255,255,255,0.2);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            cursor: pointer;
        }
        .file-box:hover {
            border-color: #00ff88;
            background: rgba(0,255,136,0.05);
        }
        .file-box.selected {
            border-color: #00c853;
            background: rgba(0,200,83,0.05);
        }
        .file-name {
            color: #00d4ff;
            font-size: 13px;
            margin-top: 8px;
            word-break: break-all;
        }
        .hidden-file { display: none; }
        .btn {
            width: 100%;
            padding: 16px;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            margin-top: 10px;
        }
        .btn-primary {
            background: linear-gradient(45deg, #00ff88, #00d4ff);
            color: #0a0e27;
        }
        .btn-danger {
            background: linear-gradient(45deg, #ff3366, #ff6699);
            color: #fff;
        }
        .btn-warning {
            background: linear-gradient(45deg, #ffbb33, #ffdd66);
            color: #0a0e27;
        }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .stats {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 12px 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #00ff88;
        }
        .stat-label {
            font-size: 10px;
            color: #aaa;
            text-transform: uppercase;
        }
        .console {
            background: rgba(0,0,0,0.5);
            border-radius: 15px;
            padding: 15px;
            height: 250px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .console-line {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .console-line.success { color: #00c853; }
        .console-line.error { color: #ff3366; }
        .alert {
            padding: 12px 16px;
            border-radius: 12px;
            margin-bottom: 15px;
            display: none;
            font-size: 14px;
        }
        .alert-success {
            background: rgba(0,200,83,0.1);
            border: 1px solid #00c853;
            color: #00c853;
        }
        .alert-error {
            background: rgba(255,51,102,0.1);
            border: 1px solid #ff3366;
            color: #ff3366;
        }
        .alert-info {
            background: rgba(0,212,255,0.1);
            border: 1px solid #00d4ff;
            color: #00d4ff;
        }
        .token-box {
            background: rgba(0,255,136,0.1);
            border: 1px solid #00ff88;
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
            word-break: break-all;
            position: relative;
        }
        .copy-btn {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            color: #fff;
            padding: 5px 12px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 12px;
        }
        .info-box {
            background: rgba(0,212,255,0.1);
            border: 1px solid #00d4ff;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 12px;
        }
        .spinner {
            display: inline-block;
            width: 18px;
            height: 18px;
            border: 3px solid rgba(255,255,255,0.3);
            border-top-color: #00ff88;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 FB MASTER PRO 2026</h1>
            <div class="sub">AHMAD ALI EDITION</div>
            <span class="badge">✅ PAGE API METHOD - 100% WORKING</span>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="totalMsg">0</div>
                <div class="stat-label">Sent</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="activeTasks">0</div>
                <div class="stat-label">Active</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="successMsg">0</div>
                <div class="stat-label">Success</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="uptime">00:00</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>
        
        <div class="card">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('extract')">🔑 Extract</button>
                <button class="tab" onclick="switchTab('send')">📨 Send</button>
                <button class="tab" onclick="switchTab('monitor')">📊 Monitor</button>
            </div>
            
            <div id="alertBox"></div>
            
            <!-- EXTRACT TAB -->
            <div id="tab-extract" class="tab-content active">
                <form id="extractForm">
                    <div class="form-group">
                        <label>📧 Email / Phone</label>
                        <input type="text" id="extEmail" placeholder="Enter email or phone" required>
                    </div>
                    <div class="form-group">
                        <label>🔒 Password</label>
                        <input type="password" id="extPass" placeholder="Enter password" required>
                    </div>
                    <button type="submit" class="btn btn-primary" id="extractBtn">
                        <span id="extractBtnText">🔓 Extract Token</span>
                    </button>
                </form>
                <div id="tokenResult" style="display:none;">
                    <div class="token-box">
                        <button class="copy-btn" onclick="copyToken()">📋 Copy</button>
                        <strong style="color:#00ff88;">Token:</strong><br>
                        <span id="extractedToken" style="font-size:12px;"></span>
                    </div>
                </div>
            </div>
            
            <!-- SEND TAB -->
            <div id="tab-send" class="tab-content">
                <div class="info-box">
                    <strong>📌 IMPORTANT:</strong> Use PAGE ACCESS TOKEN (starts with EAA..., 200+ chars).
                    <br>Get it from: Facebook Developers → Graph API Explorer → Select Page → Generate Token with pages_messaging permission.
                </div>
                
                <form id="sendForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label>🎯 Token Type</label>
                        <select id="tokenType" onchange="toggleTokenInput()">
                            <option value="single">Single Token</option>
                            <option value="file">Token File</option>
                        </select>
                    </div>
                    
                    <div class="form-group" id="singleTokenDiv">
                        <label>🔑 Page Access Token</label>
                        <input type="text" id="singleToken" placeholder="Paste Page Access Token (EAA...)">
                    </div>
                    
                    <div class="form-group" id="tokenFileDiv" style="display:none;">
                        <label>📁 Token File</label>
                        <div class="file-box" id="tokenFileBox" onclick="document.getElementById('tokenFile').click()">
                            <div>📂 Click to select token file</div>
                            <div class="file-name" id="tokenFileName"></div>
                        </div>
                        <input type="file" class="hidden-file" id="tokenFile" accept=".txt" onchange="handleFileSelect(this, 'token')">
                    </div>
                    
                    <div class="form-group">
                        <label>💬 Thread ID (Recipient ID)</label>
                        <input type="text" id="threadId" placeholder="Facebook User ID (numbers only)" required>
                    </div>
                    
                    <div class="form-group">
                        <label>🏷️ Message Prefix</label>
                        <input type="text" id="prefix" placeholder="Enter prefix" required>
                    </div>
                    
                    <div class="form-group">
                        <label>⏱️ Delay (seconds)</label>
                        <input type="number" id="delay" value="3" min="2" required>
                    </div>
                    
                    <div class="form-group">
                        <label>📄 Messages File</label>
                        <div class="file-box" id="msgFileBox" onclick="document.getElementById('msgFile').click()">
                            <div>📄 Click to select messages file</div>
                            <div class="file-name" id="msgFileName"></div>
                        </div>
                        <input type="file" class="hidden-file" id="msgFile" accept=".txt" onchange="handleFileSelect(this, 'msg')" required>
                    </div>
                    
                    <button type="submit" class="btn btn-primary" id="startBtn">
                        <span id="startBtnText">🚀 START SENDING</span>
                    </button>
                </form>
            </div>
            
            <!-- MONITOR TAB -->
            <div id="tab-monitor" class="tab-content">
                <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                    <span style="color:#00ff88;">📡 Live Console</span>
                    <span style="background:#ff3366; padding:3px 10px; border-radius:20px; font-size:11px;">🔴 LIVE</span>
                </div>
                <div class="console" id="console">
                    <div class="console-line">🚀 FB Master Pro Started</div>
                    <div class="console-line success">✅ System Ready - Page API Method</div>
                    <div class="console-line">📡 Waiting for tasks...</div>
                </div>
                <div style="display:flex; gap:10px; margin-top:15px;">
                    <button class="btn btn-warning" onclick="clearConsole()">🗑️ Clear</button>
                    <button class="btn btn-danger" onclick="stopAllTasks()">⏹️ Stop All</button>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2026 FB MASTER PRO | <span style="color:#00ff88;">AHMAD ALI (RDX)</span></p>
        </div>
    </div>
    
    <script>
        let startTime = Date.now();
        let displayedLogs = new Set();
        
        setInterval(updateStats, 2000);
        setInterval(uptimeCounter, 1000);
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById('tab-' + tab).classList.add('active');
            event.target.classList.add('active');
        }
        
        function toggleTokenInput() {
            const type = document.getElementById('tokenType').value;
            document.getElementById('singleTokenDiv').style.display = type === 'single' ? 'block' : 'none';
            document.getElementById('tokenFileDiv').style.display = type === 'file' ? 'block' : 'none';
        }
        
        function handleFileSelect(input, type) {
            const box = type === 'token' ? document.getElementById('tokenFileBox') : document.getElementById('msgFileBox');
            const nameSpan = type === 'token' ? document.getElementById('tokenFileName') : document.getElementById('msgFileName');
            
            if (input.files.length > 0) {
                nameSpan.textContent = '📎 ' + input.files[0].name;
                box.classList.add('selected');
                showAlert('✅ Selected: ' + input.files[0].name, 'success');
            }
        }
        
        document.getElementById('extractForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('extEmail').value;
            const pass = document.getElementById('extPass').value;
            const btn = document.getElementById('extractBtn');
            const btnText = document.getElementById('extractBtnText');
            
            btn.disabled = true;
            btnText.innerHTML = '<span class="spinner"></span> Extracting...';
            
            const formData = new FormData();
            formData.append('email', email);
            formData.append('password', pass);
            
            try {
                const resp = await fetch('/api/extract', { method: 'POST', body: formData });
                const data = await resp.json();
                
                if (data.ok) {
                    document.getElementById('extractedToken').textContent = data.token;
                    document.getElementById('tokenResult').style.display = 'block';
                    document.getElementById('singleToken').value = data.token;
                    showAlert('✅ Token extracted!', 'success');
                    addConsoleLine('success', '✅ Token extracted');
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (err) {
                showAlert('❌ Network error', 'error');
            } finally {
                btn.disabled = false;
                btnText.textContent = '🔓 Extract Token';
            }
        });
        
        document.getElementById('sendForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('startBtn');
            const btnText = document.getElementById('startBtnText');
            btn.disabled = true;
            btnText.innerHTML = '<span class="spinner"></span> Starting...';
            
            const formData = new FormData();
            
            const tokenType = document.getElementById('tokenType').value;
            formData.append('token_type', tokenType);
            
            if (tokenType === 'single') {
                formData.append('token', document.getElementById('singleToken').value);
            } else {
                formData.append('token_file', document.getElementById('tokenFile').files[0]);
            }
            
            formData.append('thread_id', document.getElementById('threadId').value);
            formData.append('prefix', document.getElementById('prefix').value);
            formData.append('delay', document.getElementById('delay').value);
            formData.append('msg_file', document.getElementById('msgFile').files[0]);
            
            try {
                const resp = await fetch('/api/start', { method: 'POST', body: formData });
                const data = await resp.json();
                
                if (data.ok) {
                    showAlert('✅ Task started! ID: ' + data.task_id, 'success');
                    addConsoleLine('success', '✅ Task ' + data.task_id + ' started');
                    switchTab('monitor');
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (err) {
                showAlert('❌ Failed to start', 'error');
            } finally {
                btn.disabled = false;
                btnText.textContent = '🚀 START SENDING';
            }
        });
        
        async function stopAllTasks() {
            try {
                await fetch('/api/stop_all', { method: 'POST' });
                showAlert('✅ All tasks stopped', 'success');
                addConsoleLine('warning', '⏹️ All tasks stopped');
            } catch (err) {}
        }
        
        async function updateStats() {
            try {
                const resp = await fetch('/api/status');
                const tasks = await resp.json();
                
                let total = 0, active = 0, success = 0;
                for (let [id, task] of Object.entries(tasks)) {
                    total += task.total || 0;
                    success += task.success || 0;
                    if (task.status === 'running') active++;
                    
                    if (task.logs) {
                        task.logs.slice(-3).forEach(log => {
                            const key = log.time + log.msg;
                            if (!displayedLogs.has(key)) {
                                displayedLogs.add(key);
                                addConsoleLine(log.status || 'info', '[' + log.time + '] ' + log.msg);
                            }
                        });
                    }
                }
                
                document.getElementById('totalMsg').textContent = total;
                document.getElementById('activeTasks').textContent = active;
                document.getElementById('successMsg').textContent = success;
            } catch (err) {}
        }
        
        function uptimeCounter() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(elapsed / 60);
            const secs = elapsed % 60;
            document.getElementById('uptime').textContent = 
                String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
        }
        
        function addConsoleLine(type, msg) {
            const consoleDiv = document.getElementById('console');
            const line = document.createElement('div');
            line.className = 'console-line ' + (type || '');
            line.textContent = msg;
            consoleDiv.appendChild(line);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
            if (consoleDiv.children.length > 30) consoleDiv.removeChild(consoleDiv.firstChild);
        }
        
        function clearConsole() {
            document.getElementById('console').innerHTML = 
                '<div class="console-line">🚀 Console cleared</div>' +
                '<div class="console-line success">✅ Ready</div>';
        }
        
        function showAlert(msg, type) {
            const box = document.getElementById('alertBox');
            const alert = document.createElement('div');
            alert.className = 'alert alert-' + type;
            alert.textContent = msg;
            box.appendChild(alert);
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
    print("🔥 FB MASTER PRO 2026 - PAGE API METHOD 🔥")
    print("="*50)
    print("✅ Open: http://localhost:5000")
    print("✅ USE PAGE ACCESS TOKEN (EAA...)")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
