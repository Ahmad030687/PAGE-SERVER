#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, json, uuid, random, threading, re, base64, string
import requests
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

# ==================== FLASK SETUP ====================
app = Flask(__name__)
app.debug = False

# ==================== GLOBAL VARIABLES ====================
server_running = False
server_thread = None
stop_event = threading.Event()
log_messages = []
stats = {"sent": 0, "success": 0, "fail": 0}

# ==================== COLORS (TERMUX SUPPORT) ====================
G = '\033[38;5;46m'
Y = '\033[38;5;220m'
R = '\033[38;5;196m'
W = '\033[1;37m'
B = '\033[38;5;45m'
P = '\033[38;5;201m'
C = '\033[38;5;51m'
RESET = '\033[0m'

def log(message, color=W):
    timestamp = datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    log_messages.append({"msg": entry, "color": color})
    if len(log_messages) > 100:
        log_messages.pop(0)
    print(f"{color}{entry}{RESET}")

# ==================== TOKEN EXTRACTION (AAPKA ORIGINAL LOGIC) ====================
def extract_token_core(email, password):
    """Aapka original token extraction logic"""
    try:
        sess = requests.Session()
        ua = "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
        head = {
            "User-Agent": ua,
            "Host": "graph.facebook.com",
            "Authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32"
        }
        data = {
            "adid": str(uuid.uuid4()),
            "email": email,
            "password": password,
            "format": "json",
            "device_id": str(uuid.uuid4()),
            "cpl": "true",
            "family_device_id": str(uuid.uuid4()),
            "credentials_type": "device_based_login_password",
            "generate_session_cookies": "1",
            "error_detail_type": "button_with_disabled",
            "source": "login",
            "method": "auth.login"
        }
        
        res = sess.post("https://graph.facebook.com/auth/login", data=data, headers=head, timeout=30)
        
        if res.status_code == 200:
            resp_json = res.json()
            if "access_token" in resp_json:
                token = resp_json["access_token"]
                # Save token
                try:
                    open("/sdcard/ahmii_token.txt", "w").write(token)
                except:
                    open("ahmii_token.txt", "w").write(token)
                return token, None
            elif "error" in resp_json:
                return None, resp_json["error"].get("message", "Unknown error")
        return None, "Login failed"
    except Exception as e:
        return None, str(e)

def check_token_validity(token):
    """Check if token is valid and get user info"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get("https://graph.facebook.com/me?fields=name,id", headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return True, data.get("name", "Unknown"), data.get("id", "Unknown")
    except:
        pass
    return False, None, None

# ==================== MESSAGE SENDER (TOKEN BASED) ====================
def send_message_fb(token, thread_id, message):
    """Send message using Facebook Graph API with token"""
    try:
        # Clean thread ID
        clean_tid = thread_id.strip()
        
        # Try multiple endpoints
        endpoints = [
            f"https://graph.facebook.com/v18.0/{clean_tid}/messages",
            f"https://graph.facebook.com/v17.0/{clean_tid}/messages",
            f"https://graph.facebook.com/v16.0/{clean_tid}/messages",
            f"https://graph.facebook.com/v15.0/{clean_tid}/messages",
        ]
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        }
        
        payload = {"message": message}
        
        for url in endpoints:
            try:
                resp = requests.post(url, json=payload, headers=headers, timeout=15)
                if resp.status_code == 200:
                    return True, "Sent"
                else:
                    error_data = resp.json() if resp.text else {}
                    error_msg = error_data.get('error', {}).get('message', 'Unknown')[:50]
                    if "permission" in error_msg.lower():
                        continue  # Try next endpoint
                    else:
                        return False, error_msg
            except:
                continue
        
        return False, "All endpoints failed"
        
    except Exception as e:
        return False, str(e)[:40]

def convo_worker(token, thread_ids, hater_name, delay, messages_list):
    """Background worker for sending messages"""
    global stats, server_running, stop_event
    
    stats = {"sent": 0, "success": 0, "fail": 0}
    stop_event.clear()
    
    log(f"[🚀] Convo Server Started!", G)
    log(f"[📊] Threads: {len(thread_ids)} | Messages: {len(messages_list)} | Delay: {delay}s", B)
    
    for tid in thread_ids:
        if stop_event.is_set():
            log(f"[⏹️] Server stopped by user", Y)
            break
        
        tid = tid.strip()
        if not tid:
            continue
        
        # Get thread name if possible
        thread_display = tid
        
        for msg in messages_list:
            if stop_event.is_set():
                break
            
            msg = msg.strip()
            if not msg:
                continue
            
            full_msg = f"{hater_name} {msg}" if hater_name else msg
            
            success, status = send_message_fb(token, tid, full_msg)
            stats["sent"] += 1
            
            if success:
                stats["success"] += 1
                log(f"[✓] SENT → {thread_display[:20]}... | {full_msg[:30]}...", G)
            else:
                stats["fail"] += 1
                log(f"[×] FAILED → {thread_display[:20]}... | {status}", R)
            
            time.sleep(delay)
    
    log(f"[🏁] TASK COMPLETED | Sent: {stats['sent']} | Success: {stats['success']} | Failed: {stats['fail']}", Y)
    server_running = False

def start_convo_server(token, thread_ids, hater_name, delay, messages_list):
    """Start the convo server thread"""
    global server_running, server_thread
    
    if server_running:
        return False, "Server already running"
    
    if not token:
        return False, "No token provided"
    
    if not thread_ids:
        return False, "No thread IDs provided"
    
    server_running = True
    server_thread = threading.Thread(
        target=convo_worker,
        args=(token, thread_ids, hater_name, delay, messages_list)
    )
    server_thread.daemon = True
    server_thread.start()
    
    return True, "Server started"

def stop_convo_server():
    """Stop the convo server"""
    global server_running, stop_event
    if server_running:
        stop_event.set()
        server_running = False
        return True
    return False

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract_token', methods=['POST'])
def api_extract_token():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'})
    
    token, error = extract_token_core(email, password)
    
    if token:
        # Check token validity
        valid, name, uid = check_token_validity(token)
        return jsonify({
            'success': True,
            'token': token,
            'valid': valid,
            'name': name,
            'uid': uid
        })
    else:
        return jsonify({'success': False, 'error': error or 'Extraction failed'})

@app.route('/check_token', methods=['POST'])
def api_check_token():
    data = request.json
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'valid': False, 'error': 'No token provided'})
    
    valid, name, uid = check_token_validity(token)
    
    if valid:
        return jsonify({'valid': True, 'name': name, 'uid': uid})
    else:
        return jsonify({'valid': False, 'error': 'Token invalid or expired'})

@app.route('/start_server', methods=['POST'])
def api_start_server():
    data = request.json
    token = data.get('token', '').strip()
    thread_ids_text = data.get('thread_ids', '')
    hater_name = data.get('hater_name', '')
    delay = int(data.get('delay', 2))
    messages_text = data.get('messages', '')
    
    if not token:
        return jsonify({'success': False, 'error': 'Token required'})
    
    # Parse thread IDs
    thread_ids = [t.strip() for t in thread_ids_text.split('\n') if t.strip()]
    
    # Parse messages
    messages_list = [m.strip() for m in messages_text.split('\n') if m.strip()]
    
    if not thread_ids:
        return jsonify({'success': False, 'error': 'No thread IDs provided'})
    
    if not messages_list:
        return jsonify({'success': False, 'error': 'No messages provided'})
    
    success, msg = start_convo_server(token, thread_ids, hater_name, delay, messages_list)
    
    return jsonify({'success': success, 'message': msg})

@app.route('/stop_server', methods=['POST'])
def api_stop_server():
    if stop_convo_server():
        log(f"[⏹️] Server stopped via API", Y)
        return jsonify({'success': True, 'message': 'Server stopped'})
    return jsonify({'success': False, 'message': 'No server running'})

@app.route('/status')
def api_status():
    return jsonify({
        'running': server_running,
        'stats': stats,
        'logs': log_messages[-20:]
    })

# ==================== PREMIUM HTML UI ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>⚡ AHMII FB MASTER CORE ⚡</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: linear-gradient(135deg, #0a0f1e 0%, #0f1629 50%, #0a0f1e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 16px;
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.03) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(0, 200, 255, 0.03) 0%, transparent 50%),
                        radial-gradient(circle at 40% 40%, rgba(255, 0, 212, 0.02) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .container { max-width: 650px; margin: 0 auto; position: relative; z-index: 1; }
        
        /* PREMIUM HEADER */
        .header { text-align: center; padding: 20px 0 15px; }
        .glow-text {
            font-size: 12px; letter-spacing: 3px; text-transform: uppercase;
            background: linear-gradient(135deg, #00ff88, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-weight: 600; margin-bottom: 5px;
        }
        .main-title {
            font-size: 32px; font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #00ff88, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 40px rgba(0, 255, 136, 0.3);
            letter-spacing: -0.5px; margin-bottom: 5px;
        }
        .subtitle {
            font-size: 14px; color: rgba(255,255,255,0.6);
            display: flex; align-items: center; justify-content: center; gap: 15px; margin-top: 8px;
        }
        .vip-badge {
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            padding: 4px 12px; border-radius: 20px; font-size: 11px;
            font-weight: 700; color: #000; letter-spacing: 1px;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
        }
        
        /* GLASS CARD */
        .glass-card {
            background: rgba(15, 25, 45, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 255, 136, 0.15);
            border-radius: 24px;
            padding: 24px 20px;
            margin-bottom: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(0, 255, 136, 0.05) inset, 0 0 30px rgba(0, 255, 136, 0.1);
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(0, 255, 136, 0.3);
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 255, 136, 0.1) inset, 0 0 40px rgba(0, 255, 136, 0.15);
        }
        
        .card-title {
            font-size: 18px; font-weight: 600; margin-bottom: 20px;
            display: flex; align-items: center; gap: 10px; color: #fff;
        }
        .card-title i { color: #00ff88; font-size: 20px; text-shadow: 0 0 15px #00ff88; }
        
        /* INPUT GROUPS */
        .input-group { margin-bottom: 18px; }
        .input-label {
            display: block; font-size: 13px; font-weight: 500; margin-bottom: 8px;
            color: rgba(255,255,255,0.7); letter-spacing: 0.3px;
        }
        .input-label i { color: #00ccff; margin-right: 6px; font-size: 12px; }
        
        .premium-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1.5px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 14px 18px;
            color: #fff;
            font-size: 14px;
            font-family: 'Plus Jakarta Sans', sans-serif;
            transition: all 0.3s ease;
            outline: none;
        }
        
        .premium-input:focus {
            border-color: #00ff88;
            background: rgba(0, 255, 136, 0.05);
            box-shadow: 0 0 25px rgba(0, 255, 136, 0.2);
        }
        
        .premium-input::placeholder { color: rgba(255,255,255,0.3); }
        textarea.premium-input { resize: vertical; min-height: 100px; }
        
        /* BUTTONS */
        .button-group { display: flex; gap: 12px; flex-wrap: wrap; }
        .btn {
            flex: 1; min-width: 120px; padding: 14px 20px; border: none;
            border-radius: 16px; font-size: 14px; font-weight: 600;
            font-family: 'Plus Jakarta Sans', sans-serif; cursor: pointer;
            display: flex; align-items: center; justify-content: center;
            gap: 8px; transition: all 0.3s ease; text-transform: uppercase;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #00ff88, #00cc6a);
            color: #000; box-shadow: 0 8px 20px rgba(0, 255, 136, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(0, 255, 136, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff4757, #ff3344);
            color: #fff; box-shadow: 0 8px 20px rgba(255, 71, 87, 0.3);
        }
        
        .btn-danger:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(255, 71, 87, 0.4);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #2d3a5e, #1a2744);
            color: #fff; border: 1px solid rgba(255,255,255,0.1);
        }
        
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        
        /* TOKEN DISPLAY */
        .token-display {
            background: rgba(0, 0, 0, 0.4); border-radius: 12px; padding: 12px 16px;
            margin: 15px 0; border: 1px dashed rgba(0, 255, 136, 0.3);
            word-break: break-all; font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px; color: #00ff88; max-height: 80px; overflow-y: auto;
        }
        
        /* LOG CONSOLE */
        .log-console {
            background: rgba(0, 0, 0, 0.5); border-radius: 16px; padding: 16px;
            max-height: 250px; overflow-y: auto; font-family: 'Monaco', 'Menlo', monospace;
            font-size: 11px; border: 1px solid rgba(255,255,255,0.05);
        }
        
        .log-entry {
            padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.03);
            color: rgba(255,255,255,0.8);
        }
        
        /* STATUS INDICATOR */
        .status-indicator { display: flex; align-items: center; gap: 8px; margin-bottom: 15px; }
        .status-dot {
            width: 12px; height: 12px; border-radius: 50%; background: #ff4757;
            box-shadow: 0 0 15px #ff4757; animation: pulse-red 2s infinite;
        }
        .status-dot.active { background: #00ff88; box-shadow: 0 0 20px #00ff88; animation: pulse-green 1.5s infinite; }
        
        @keyframes pulse-green { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes pulse-red { 0%, 100% { opacity: 0.8; } 50% { opacity: 0.4; } }
        
        /* STATS */
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 15px 0; }
        .stat-card { background: rgba(0, 0, 0, 0.3); border-radius: 14px; padding: 12px; text-align: center; }
        .stat-value { font-size: 28px; font-weight: 700; color: #00ff88; text-shadow: 0 0 20px #00ff88; }
        .stat-label { font-size: 11px; color: rgba(255,255,255,0.5); text-transform: uppercase; }
        
        /* USER INFO */
        .user-info {
            background: linear-gradient(135deg, #00ff8822, #00ccff22);
            border-radius: 12px; padding: 10px 15px; margin-top: 10px;
            border: 1px solid #00ff8844; display: flex; align-items: center; gap: 10px;
        }
        .user-info i { color: #00ff88; font-size: 24px; }
        
        /* FOOTER */
        .footer { text-align: center; padding: 20px; color: rgba(255,255,255,0.4); font-size: 12px; }
        .footer a { color: #00ccff; text-decoration: none; }
        
        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
        ::-webkit-scrollbar-thumb { background: #00ff88; border-radius: 10px; }
        
        /* NOTIFICATION */
        .notification {
            position: fixed; top: 20px; right: 20px; background: rgba(0, 255, 136, 0.9);
            color: #000; padding: 12px 20px; border-radius: 50px; font-weight: 600;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.4);
            transform: translateX(400px); transition: transform 0.3s ease; z-index: 1000;
        }
        .notification.show { transform: translateX(0); }
        .notification.error { background: rgba(255, 71, 87, 0.9); }
        
        .tabs { display: flex; gap: 10px; margin-bottom: 15px; }
        .tab {
            padding: 10px 20px; background: rgba(0,0,0,0.3); border-radius: 30px;
            cursor: pointer; border: 1px solid transparent; transition: 0.3s;
        }
        .tab.active { border-color: #00ff88; background: #00ff8822; }
        .tab:hover { border-color: #00ff8844; }
    </style>
</head>
<body>
    <div class="notification" id="notification">✓ Message</div>
    
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <div class="glow-text">⚡ PREMIUM EDITION ⚡</div>
            <div class="main-title">AHMII FB MASTER</div>
            <div class="subtitle">
                <span><i class="fas fa-crown" style="color: #ffd700;"></i> AHMAD ALI (RDX)</span>
                <span class="vip-badge"><i class="fas fa-check-circle"></i> VIP ACCESS</span>
            </div>
        </div>
        
        <!-- TABS -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('extract')"><i class="fas fa-key"></i> Token Extract</div>
            <div class="tab" onclick="switchTab('manual')"><i class="fas fa-paste"></i> Manual Token</div>
        </div>
        
        <!-- TOKEN EXTRACTOR SECTION -->
        <div id="extractSection" class="glass-card">
            <div class="card-title">
                <i class="fas fa-key"></i>
                <span>FACEBOOK TOKEN EXTRACTOR</span>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-envelope"></i> EMAIL / PHONE</label>
                <input type="text" id="email" class="premium-input" placeholder="example@email.com">
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-lock"></i> PASSWORD</label>
                <input type="password" id="password" class="premium-input" placeholder="••••••••">
            </div>
            
            <button class="btn btn-primary" onclick="extractToken()" style="width: 100%;">
                <i class="fas fa-unlock-alt"></i> EXTRACT TOKEN
            </button>
            
            <div id="extractResult" style="margin-top: 15px;"></div>
        </div>
        
        <!-- MANUAL TOKEN SECTION -->
        <div id="manualSection" class="glass-card" style="display: none;">
            <div class="card-title">
                <i class="fas fa-paste"></i>
                <span>MANUAL TOKEN INPUT</span>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-key"></i> FACEBOOK TOKEN</label>
                <textarea id="manualToken" class="premium-input" placeholder="Paste your Facebook token here..." rows="3"></textarea>
            </div>
            
            <button class="btn btn-primary" onclick="checkManualToken()" style="width: 100%;">
                <i class="fas fa-check-circle"></i> VERIFY & USE TOKEN
            </button>
            
            <div id="manualResult" style="margin-top: 15px;"></div>
        </div>
        
        <!-- CURRENT TOKEN INFO -->
        <div id="tokenInfoCard" class="glass-card" style="display: none;">
            <div class="card-title">
                <i class="fas fa-user-check"></i>
                <span>ACTIVE TOKEN</span>
            </div>
            <div id="tokenInfoContent"></div>
        </div>
        
        <!-- CONVO SERVER CARD -->
        <div class="glass-card">
            <div class="card-title">
                <i class="fas fa-server"></i>
                <span>CONVO BULK SERVER</span>
            </div>
            
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">SERVER OFFLINE</span>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-users"></i> THREAD IDs (One per line)</label>
                <textarea id="threadIds" class="premium-input" placeholder="t_123456789012345 (for GC)&#10;1000123456789 (for User)&#10;..."></textarea>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-tag"></i> HATER NAME / PREFIX (Optional)</label>
                <input type="text" id="haterName" class="premium-input" placeholder="AHMAD: ">
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-clock"></i> DELAY (Seconds)</label>
                <input type="number" id="delay" class="premium-input" value="2" min="1" max="60">
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-comment-dots"></i> MESSAGES (One per line)</label>
                <textarea id="messages" class="premium-input" placeholder="Hello!&#10;How are you?&#10;Third message..."></textarea>
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" id="startBtn" onclick="startServer()">
                    <i class="fas fa-play"></i> START SERVER
                </button>
                <button class="btn btn-danger" id="stopBtn" onclick="stopServer()" disabled>
                    <i class="fas fa-stop"></i> STOP SERVER
                </button>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="msgSent">0</div>
                    <div class="stat-label"><i class="fas fa-paper-plane"></i> SENT</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="msgSuccess">0</div>
                    <div class="stat-label"><i class="fas fa-check"></i> SUCCESS</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="msgFail">0</div>
                    <div class="stat-label"><i class="fas fa-times"></i> FAILED</div>
                </div>
            </div>
        </div>
        
        <!-- LOG CONSOLE -->
        <div class="glass-card">
            <div class="card-title">
                <i class="fas fa-terminal"></i>
                <span>LIVE CONSOLE</span>
            </div>
            <div class="log-console" id="logConsole">
                <div class="log-entry"><i class="fas fa-circle" style="color: #00ff88; font-size: 8px;"></i> System ready...</div>
            </div>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            <i class="fas fa-heart" style="color: #ff4757;"></i> 
            <a href="https://wa.me/+923277348009" target="_blank">CONTACT OWNER</a> 
            | AHMAD ALI (RDX) © 2024
        </div>
    </div>
    
    <script>
        let currentToken = '';
        let serverRunning = false;
        let updateInterval = null;
        
        function showNotification(msg, isError = false) {
            const notif = document.getElementById('notification');
            notif.innerHTML = msg;
            notif.className = 'notification' + (isError ? ' error' : '');
            notif.classList.add('show');
            setTimeout(() => notif.classList.remove('show'), 3000);
        }
        
        function addLog(message, color = '#fff') {
            const consoleDiv = document.getElementById('logConsole');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            entry.innerHTML = `<i class="fas fa-circle" style="color: ${color}; font-size: 8px;"></i> ${message}`;
            consoleDiv.appendChild(entry);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
            if (consoleDiv.children.length > 30) consoleDiv.removeChild(consoleDiv.children[0]);
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            
            if (tab === 'extract') {
                document.getElementById('extractSection').style.display = 'block';
                document.getElementById('manualSection').style.display = 'none';
            } else {
                document.getElementById('extractSection').style.display = 'none';
                document.getElementById('manualSection').style.display = 'block';
            }
        }
        
        function showTokenInfo(token, name, uid) {
            currentToken = token;
            document.getElementById('tokenInfoCard').style.display = 'block';
            document.getElementById('tokenInfoContent').innerHTML = `
                <div class="user-info">
                    <i class="fas fa-user-circle"></i>
                    <div>
                        <strong>${name || 'Unknown'}</strong><br>
                        <small>UID: ${uid || 'N/A'}</small>
                    </div>
                </div>
                <div class="token-display" style="margin-top: 10px;">
                    <i class="fas fa-key"></i> ${token.substring(0, 50)}...
                </div>
            `;
        }
        
        async function extractToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                showNotification('Enter email and password', true);
                return;
            }
            
            addLog('🔐 Extracting token...', '#00ccff');
            showNotification('Extracting token...');
            
            try {
                const res = await fetch('/extract_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await res.json();
                
                if (data.success) {
                    addLog('✅ Token extracted successfully!', '#00ff88');
                    showNotification('Token extracted!');
                    showTokenInfo(data.token, data.name, data.uid);
                    document.getElementById('extractResult').innerHTML = `
                        <div style="color: #00ff88;"><i class="fas fa-check-circle"></i> Token Ready!</div>
                    `;
                } else {
                    addLog('❌ Failed: ' + data.error, '#ff4757');
                    showNotification('Extraction failed', true);
                    document.getElementById('extractResult').innerHTML = `
                        <div style="color: #ff4757;"><i class="fas fa-times-circle"></i> ${data.error}</div>
                    `;
                }
            } catch (e) {
                addLog('❌ Error: ' + e.message, '#ff4757');
            }
        }
        
        async function checkManualToken() {
            const token = document.getElementById('manualToken').value.trim();
            
            if (!token) {
                showNotification('Paste a token first', true);
                return;
            }
            
            addLog('🔍 Verifying token...', '#00ccff');
            
            try {
                const res = await fetch('/check_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token})
                });
                const data = await res.json();
                
                if (data.valid) {
                    addLog('✅ Token valid!', '#00ff88');
                    showNotification(`Valid - ${data.name}`);
                    showTokenInfo(token, data.name, data.uid);
                    document.getElementById('manualResult').innerHTML = `
                        <div style="color: #00ff88;"><i class="fas fa-check-circle"></i> Token Valid!</div>
                    `;
                } else {
                    addLog('❌ Invalid token', '#ff4757');
                    showNotification('Invalid token', true);
                    document.getElementById('manualResult').innerHTML = `
                        <div style="color: #ff4757;"><i class="fas fa-times-circle"></i> Invalid Token</div>
                    `;
                }
            } catch (e) {
                addLog('❌ Error checking token', '#ff4757');
            }
        }
        
        async function startServer() {
            if (!currentToken) {
                showNotification('No token available. Extract or paste token first!', true);
                return;
            }
            
            const threadIds = document.getElementById('threadIds').value;
            const haterName = document.getElementById('haterName').value;
            const delay = document.getElementById('delay').value;
            const messages = document.getElementById('messages').value;
            
            if (!threadIds || !messages) {
                showNotification('Enter thread IDs and messages', true);
                return;
            }
            
            addLog('🚀 Starting Convo Server...', '#00ccff');
            
            try {
                const res = await fetch('/start_server', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        token: currentToken,
                        thread_ids: threadIds,
                        hater_name: haterName,
                        delay: parseInt(delay),
                        messages: messages
                    })
                });
                const data = await res.json();
                
                if (data.success) {
                    serverRunning = true;
                    updateUI();
                    addLog('🟢 Convo Server Started!', '#00ff88');
                    showNotification('Server started!');
                    startStatusUpdate();
                } else {
                    addLog('❌ Failed: ' + data.message, '#ff4757');
                    showNotification(data.message, true);
                }
            } catch (e) {
                addLog('❌ Error: ' + e.message, '#ff4757');
            }
        }
        
        async function stopServer() {
            try {
                const res = await fetch('/stop_server', {method: 'POST'});
                const data = await res.json();
                
                if (data.success) {
                    serverRunning = false;
                    updateUI();
                    addLog('🔴 Server Stopped!', '#ffcc00');
                    showNotification('Server stopped');
                    if (updateInterval) {
                        clearInterval(updateInterval);
                        updateInterval = null;
                    }
                }
            } catch (e) {
                addLog('❌ Error stopping server', '#ff4757');
            }
        }
        
        function updateUI() {
            const dot = document.getElementById('statusDot');
            const status = document.getElementById('statusText');
            const startBtn = document.getElementById('startBtn');
            const stopBtn = document.getElementById('stopBtn');
            
            if (serverRunning) {
                dot.classList.add('active');
                status.textContent = 'SERVER ONLINE ●';
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                dot.classList.remove('active');
                status.textContent = 'SERVER OFFLINE';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        }
        
        async function updateStats() {
            try {
                const res = await fetch('/status');
                const data = await res.json();
                
                document.getElementById('msgSent').textContent = data.stats.sent || 0;
                document.getElementById('msgSuccess').textContent = data.stats.success || 0;
                document.getElementById('msgFail').textContent = data.stats.fail || 0;
                
                // Update logs
                if (data.logs) {
                    const consoleDiv = document.getElementById('logConsole');
                    consoleDiv.innerHTML = '';
                    data.logs.forEach(log => {
                        const entry = document.createElement('div');
                        entry.className = 'log-entry';
                        entry.innerHTML = `<i class="fas fa-circle" style="color: ${log.color || '#fff'}; font-size: 8px;"></i> ${log.msg}`;
                        consoleDiv.appendChild(entry);
                    });
                    consoleDiv.scrollTop = consoleDiv.scrollHeight;
                }
                
                // Check if server stopped
                if (!data.running && serverRunning) {
                    serverRunning = false;
                    updateUI();
                    addLog('✅ Server task completed!', '#00ff88');
                }
                serverRunning = data.running;
                updateUI();
            } catch (e) {}
        }
        
        function startStatusUpdate() {
            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(updateStats, 2000);
        }
        
        // Initial load
        updateStats();
    </script>
</body>
</html>
'''

# ==================== TERMUX MENU ====================
def banner_termux():
    os.system('clear')
    print(f"""{G}
 █████╗ ██╗  ██╗███╗   ███╗██╗██╗
██╔══██╗██║  ██║████╗ ████║██║██║
███████║███████║██╔████╔██║██║██║
██╔══██║██╔══██║██║╚██╔╝██║██║██║
██║  ██║██║  ██║██║ ╚═╝ ██║██║██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝
{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{G} [•] {W}OWNER    : {Y}AHMAD ALI (RDX)
{G} [•] {W}TOOL     : {Y}FB MASTER CORE WEB
{G} [•] {W}STATUS   : {Y}VIP ACCESS ✅
{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}""")

def extract_token_termux():
    banner_termux()
    print(f"{B}[ FB TOKEN EXTRACTOR ]{RESET}")
    print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    uid = input(f"{G}[•] EMAIL/ID : {W}")
    pas = input(f"{G}[•] PASSWORD : {W}{RESET}")
    print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{G}[!] LOGGING IN... PLEASE WAIT{RESET}")
    
    token, error = extract_token_core(uid, pas)
    if token:
        print(f"{G}[✓] TOKEN EXTRACTED!{RESET}")
        print(f"{G}[>] {token}{RESET}")
    else:
        print(f"{R}[×] FAILED: {error}{RESET}")
    input(f"\n{Y}[ Press Enter To Back ]{RESET}")

def termux_menu():
    while True:
        banner_termux()
        print(f"{W}[1] {G}GET FB TOKEN{RESET}")
        print(f"{W}[2] {B}START WEB SERVER{RESET}")
        print(f"{W}[3] {Y}CONTACT OWNER{RESET}")
        print(f"{W}[0] {R}EXIT{RESET}")
        print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
        opt = input(f"{G}[•] SELECT : {W}")
        
        if opt == '1':
            extract_token_termux()
        elif opt == '2':
            banner_termux()
            print(f"{B}[ WEB SERVER STARTING ]{RESET}")
            print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print(f"{G}[✓] Open browser and go to:{RESET}")
            print(f"{W}    http://localhost:5000{RESET}")
            print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print(f"{R}[!] Press Ctrl+C to stop server{RESET}")
            
            def run_flask():
                app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            
            flask_thread = threading.Thread(target=run_flask)
            flask_thread.daemon = True
            flask_thread.start()
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n{R}[!] Server stopped{RESET}")
        elif opt == '3':
            os.system("termux-open-url https://wa.me/+923277348009")
        elif opt == '0':
            print(f"{R}[!] Goodbye!{RESET}")
            sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'web':
        banner_termux()
        print(f"{B}[ WEB MODE ]{RESET}")
        print(f"{G}Server running at: http://localhost:5000{RESET}")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        termux_menu()