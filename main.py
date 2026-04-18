#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, json, uuid, random, threading, re, base64, hashlib
import requests
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

# ==================== GLOBAL VARIABLES ====================
app = Flask(__name__)
server_thread = None
server_running = False
stored_token = ""
messages_sent = 0
success_count = 0
fail_count = 0
log_messages = []

# ==================== COLORS ====================
G = '\033[38;5;46m'
Y = '\033[38;5;220m'
R = '\033[38;5;196m'
W = '\033[1;37m'
B = '\033[38;5;45m'
RESET = '\033[0m'

def log(message, color=W):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    log_messages.append({"message": log_entry, "color": color})
    if len(log_messages) > 100:
        log_messages.pop(0)
    print(f"{color}{log_entry}{RESET}")

# ==================== WORKING MESSAGE SENDER ====================
def send_message_v1(token, thread_id, message):
    """Method 1: Graph API v18.0"""
    try:
        url = f"https://graph.facebook.com/v18.0/{thread_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        }
        payload = {"message": message}
        
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            return True, "Sent"
        else:
            error = resp.json().get('error', {}).get('message', 'Unknown')[:50]
            return False, error
    except Exception as e:
        return False, str(e)[:30]

def send_message_v2(token, thread_id, message):
    """Method 2: Facebook Mobile API"""
    try:
        url = "https://graph.facebook.com/me/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            "X-FB-Friendly-Name": "send_message",
            "X-FB-Connection-Type": "WIFI",
        }
        payload = {
            "recipient": {"thread_key": thread_id},
            "message": {"text": message},
            "messaging_type": "RESPONSE"
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            return True, "Sent (v2)"
        else:
            error = resp.json().get('error', {}).get('message', 'Unknown')[:50]
            return False, error
    except Exception as e:
        return False, str(e)[:30]

def send_message_v3(token, thread_id, message):
    """Method 3: Edge Chat API"""
    try:
        url = f"https://graph.facebook.com/v16.0/{thread_id}/messages"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Origin": "https://www.facebook.com",
            "Referer": "https://www.facebook.com/",
        }
        payload = {
            "message": message,
            "messaging_type": "MESSAGE_TAG",
            "tag": "ACCOUNT_UPDATE"
        }
        
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            return True, "Sent (v3)"
        else:
            error = resp.json().get('error', {}).get('message', 'Unknown')[:50]
            return False, error
    except Exception as e:
        return False, str(e)[:30]

def send_message_v4(token, thread_id, message):
    """Method 4: Legacy API"""
    try:
        url = "https://graph.facebook.com/v2.6/me/messages"
        params = {"access_token": token}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        }
        payload = {
            "recipient": {"id": thread_id},
            "message": {"text": message}
        }
        
        resp = requests.post(url, params=params, json=payload, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            return True, "Sent (v4)"
        else:
            error = resp.json().get('error', {}).get('message', 'Unknown')[:50]
            return False, error
    except Exception as e:
        return False, str(e)[:30]

def send_message_smart(token, thread_id, message):
    """Try all methods until one works"""
    methods = [
        send_message_v1,
        send_message_v2,
        send_message_v3,
        send_message_v4,
    ]
    
    for method in methods:
        success, msg = method(token, thread_id, message)
        if success:
            return True, msg
        time.sleep(0.5)
    
    return False, "All methods failed"

def check_token_permissions(token):
    """Check what permissions token has"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get("https://graph.facebook.com/me/permissions", headers=headers)
        if resp.status_code == 200:
            data = resp.json().get('data', [])
            perms = [p['permission'] for p in data if p.get('status') == 'granted']
            return perms
    except:
        pass
    return []

def get_thread_info(token, thread_id):
    """Get thread/user info"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(f"https://graph.facebook.com/{thread_id}", headers=headers)
        if resp.status_code == 200:
            return resp.json().get('name', 'Unknown')
    except:
        pass
    return thread_id

def send_bulk_message_worker(token, thread_ids, message, delay):
    """Worker function for bulk messaging"""
    global messages_sent, success_count, fail_count, server_running
    
    success_count = 0
    fail_count = 0
    total = len(thread_ids)
    
    log(f"[🚀] Starting bulk message to {total} threads", G)
    log(f"[💬] Message: {message[:50]}...", B)
    
    # Check token permissions first
    perms = check_token_permissions(token)
    if perms:
        log(f"[🔑] Token permissions: {', '.join(perms[:5])}", B)
    else:
        log(f"[⚠️] Could not verify token permissions", Y)
    
    for idx, tid in enumerate(thread_ids, 1):
        if not server_running:
            log(f"[⏹️] Server stopped by user", Y)
            break
        
        tid = tid.strip()
        if not tid:
            continue
        
        # Clean thread ID
        tid = re.sub(r'[^0-9]', '', tid)
        if not tid:
            continue
        
        # Get thread name for better logging
        thread_name = get_thread_info(token, tid)
        if thread_name != tid:
            display_name = f"{tid} ({thread_name[:15]}...)"
        else:
            display_name = tid
        
        log(f"[📤] [{idx}/{total}] Sending to: {display_name}", B)
        
        success, status_msg = send_message_smart(token, tid, message)
        
        if success:
            success_count += 1
            messages_sent += 1
            log(f"[✅] SUCCESS → {display_name} | {status_msg}", G)
        else:
            fail_count += 1
            log(f"[❌] FAILED → {display_name} | {status_msg}", R)
        
        # Progress update
        if idx % 10 == 0:
            log(f"[📊] Progress: {idx}/{total} | Success: {success_count} | Failed: {fail_count}", Y)
        
        # Delay between messages
        if idx < total and server_running:
            time.sleep(delay)
    
    log(f"[🏁] BULK MESSAGING COMPLETED!", G)
    log(f"[📊] Final Stats: Success: {success_count} | Failed: {fail_count} | Total: {total}", Y)

def start_convo_server(token, thread_ids, message, delay):
    """Start the convo server"""
    global server_running, server_thread
    
    if server_running:
        log("[⚠️] Server already running!", Y)
        return False
    
    if not token:
        log("[❌] No token provided!", R)
        return False
    
    if not thread_ids or not message:
        log("[❌] Thread IDs and message required!", R)
        return False
    
    server_running = True
    server_thread = threading.Thread(
        target=send_bulk_message_worker, 
        args=(token, thread_ids, message, delay)
    )
    server_thread.daemon = True
    server_thread.start()
    
    log("[🟢] CONVO SERVER STARTED!", G)
    return True

def stop_convo_server():
    """Stop the convo server"""
    global server_running
    if server_running:
        server_running = False
        log("[🔴] CONVO SERVER STOPPED!", Y)
    return True

# ==================== TOKEN EXTRACTION (Fixed) ====================
def extract_token_core(email, password):
    """Updated working token extraction"""
    try:
        sess = requests.Session()
        device_id = str(uuid.uuid4()).replace('-', '')[:16]
        adid = str(uuid.uuid4()).upper()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; en-US; Facebook) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/131.0.6778.135 Mobile Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-FB-Connection-Type": "WIFI",
            "X-FB-Net-HNI": "45005",
        }
        
        data = {
            "adid": adid,
            "email": email,
            "password": password,
            "format": "json",
            "device_id": device_id,
            "cpl": "true",
            "family_device_id": device_id,
            "credentials_type": "password",
            "generate_session_cookies": "1",
            "error_detail_type": "button_with_disabled",
            "source": "login",
            "method": "auth.login",
            "meta_inf_fbmeta": "",
            "currently_logged_in_userid": "0",
            "locale": "en_US",
            "client_country_code": "US",
            "machine_id": str(uuid.uuid4()),
            "api_key": "882a8490361da98702bf97a021ddc14d",
        }
        
        log("[*] Authenticating...", B)
        resp = sess.post("https://b-api.facebook.com/method/auth.login", data=data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            try:
                resp_json = resp.json()
            except:
                log("[×] Invalid response format", R)
                return None
            
            if "access_token" in resp_json:
                token = resp_json["access_token"]
                log(f"[✓] TOKEN: {token[:50]}...", G)
                
                # Save token
                try:
                    with open("/sdcard/ahmii_token.txt", "w") as f:
                        f.write(token)
                except:
                    with open("ahmii_token.txt", "w") as f:
                        f.write(token)
                
                return token
            elif "error" in resp_json:
                err = resp_json["error"]
                if isinstance(err, dict):
                    log(f"[×] Error: {err.get('message', 'Unknown')}", R)
                else:
                    log(f"[×] Error: {err}", R)
            else:
                log(f"[×] Unexpected response", R)
                
    except Exception as e:
        log(f"[×] Exception: {str(e)}", R)
    
    return None

def extract_token_with_retry(email, password):
    """Try token extraction"""
    log(f"[*] Attempting login for: {email}", B)
    
    token = extract_token_core(email, password)
    if token:
        return token
    
    log("[×] Extraction failed", R)
    log("[!] Tips:", Y)
    log("  1. Disable 2FA temporarily", Y)
    log("  2. Use App Password from Facebook settings", Y)
    log("  3. Login on browser first to verify", Y)
    
    return None

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
    
    token = extract_token_with_retry(email, password)
    
    if token:
        global stored_token
        stored_token = token
        return jsonify({'success': True, 'token': token})
    
    return jsonify({'success': False, 'error': 'Login failed. Check logs.'})

@app.route('/check_token', methods=['POST'])
def api_check_token():
    data = request.json
    token = data.get('token')
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.get('https://graph.facebook.com/me?fields=name,id', headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            name = data.get('name', 'Unknown')
            uid = data.get('id', 'Unknown')
            
            # Check permissions
            perms_resp = requests.get('https://graph.facebook.com/me/permissions', headers=headers, timeout=10)
            perms = []
            if perms_resp.status_code == 200:
                perms_data = perms_resp.json().get('data', [])
                perms = [p['permission'] for p in perms_data if p.get('status') == 'granted']
            
            return jsonify({
                'valid': True, 
                'name': name, 
                'id': uid,
                'permissions': perms
            })
    except Exception as e:
        pass
    
    return jsonify({'valid': False})

@app.route('/start_server', methods=['POST'])
def api_start_server():
    data = request.json
    token = data.get('token', stored_token)
    thread_ids = data.get('threadIds', [])
    message = data.get('message', '')
    delay = data.get('delay', 2)
    
    if start_convo_server(token, thread_ids, message, delay):
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Could not start server'})

@app.route('/stop_server', methods=['POST'])
def api_stop_server():
    stop_convo_server()
    return jsonify({'success': True})

@app.route('/status')
def api_status():
    return jsonify({
        'running': server_running,
        'messages_sent': messages_sent,
        'success_count': success_count,
        'fail_count': fail_count
    })

@app.route('/stats')
def api_stats():
    return jsonify({
        'messages_sent': messages_sent,
        'success_count': success_count,
        'fail_count': fail_count,
        'running': server_running
    })

@app.route('/logs')
def api_logs():
    return jsonify({'logs': log_messages[-30:]})

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
                        radial-gradient(circle at 80% 20%, rgba(0, 200, 255, 0.03) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .container { max-width: 600px; margin: 0 auto; position: relative; z-index: 1; }
        
        .header { text-align: center; padding: 20px 0 15px; }
        .glow-text { font-size: 12px; letter-spacing: 3px; text-transform: uppercase; background: linear-gradient(135deg, #00ff88, #00ccff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 600; }
        .main-title { font-size: 32px; font-weight: 800; background: linear-gradient(135deg, #ffffff, #00ff88, #00ccff); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: -0.5px; }
        .vip-badge { background: linear-gradient(135deg, #ffd700, #ff8c00); padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 700; color: #000; }
        
        .glass-card {
            background: rgba(15, 25, 45, 0.7);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 255, 136, 0.15);
            border-radius: 24px;
            padding: 24px 20px;
            margin-bottom: 16px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 30px rgba(0, 255, 136, 0.1);
        }
        
        .card-title { font-size: 18px; font-weight: 600; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }
        .card-title i { color: #00ff88; font-size: 20px; }
        
        .input-group { margin-bottom: 18px; }
        .input-label { display: block; font-size: 13px; font-weight: 500; margin-bottom: 8px; color: rgba(255,255,255,0.7); }
        
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
        
        .premium-input:focus { border-color: #00ff88; background: rgba(0, 255, 136, 0.05); box-shadow: 0 0 25px rgba(0, 255, 136, 0.2); }
        textarea.premium-input { resize: vertical; min-height: 100px; }
        
        .button-group { display: flex; gap: 12px; flex-wrap: wrap; }
        .btn {
            flex: 1; min-width: 120px; padding: 14px 20px; border: none;
            border-radius: 16px; font-size: 14px; font-weight: 600;
            cursor: pointer; display: flex; align-items: center; justify-content: center;
            gap: 8px; transition: all 0.3s ease; text-transform: uppercase;
        }
        
        .btn-primary { background: linear-gradient(135deg, #00ff88, #00cc6a); color: #000; box-shadow: 0 8px 20px rgba(0, 255, 136, 0.3); }
        .btn-danger { background: linear-gradient(135deg, #ff4757, #ff3344); color: #fff; box-shadow: 0 8px 20px rgba(255, 71, 87, 0.3); }
        .btn-secondary { background: linear-gradient(135deg, #2d3a5e, #1a2744); color: #fff; border: 1px solid rgba(255,255,255,0.1); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .token-display {
            background: rgba(0, 0, 0, 0.4); border-radius: 12px; padding: 12px 16px;
            margin: 15px 0; border: 1px dashed rgba(0, 255, 136, 0.3);
            word-break: break-all; font-family: monospace; font-size: 12px;
            color: #00ff88; max-height: 80px; overflow-y: auto;
        }
        
        .log-console {
            background: rgba(0, 0, 0, 0.5); border-radius: 16px; padding: 16px;
            max-height: 250px; overflow-y: auto; font-family: monospace; font-size: 11px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .log-entry { padding: 5px 0; border-bottom: 1px solid rgba(255,255,255,0.03); color: rgba(255,255,255,0.8); }
        
        .status-indicator { display: flex; align-items: center; gap: 8px; margin-bottom: 15px; }
        .status-dot {
            width: 12px; height: 12px; border-radius: 50%; background: #ff4757;
            box-shadow: 0 0 15px #ff4757; animation: pulse-red 2s infinite;
        }
        .status-dot.active { background: #00ff88; box-shadow: 0 0 20px #00ff88; animation: pulse-green 1.5s infinite; }
        
        @keyframes pulse-green { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        @keyframes pulse-red { 0%, 100% { opacity: 0.8; } 50% { opacity: 0.4; } }
        
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 15px 0; }
        .stat-card { background: rgba(0, 0, 0, 0.3); border-radius: 14px; padding: 12px; text-align: center; }
        .stat-value { font-size: 24px; font-weight: 700; color: #00ff88; }
        .stat-label { font-size: 10px; color: rgba(255,255,255,0.5); text-transform: uppercase; }
        
        .notification {
            position: fixed; top: 20px; right: 20px; background: rgba(0, 255, 136, 0.9);
            color: #000; padding: 12px 20px; border-radius: 50px; font-weight: 600;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.4);
            transform: translateX(400px); transition: transform 0.3s ease; z-index: 1000;
        }
        .notification.show { transform: translateX(0); }
        
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
        ::-webkit-scrollbar-thumb { background: #00ff88; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="notification" id="notification">✓ Message</div>
    
    <div class="container">
        <div class="header">
            <div class="glow-text">⚡ PREMIUM EDITION ⚡</div>
            <div class="main-title">AHMII FB MASTER</div>
            <div class="subtitle" style="display: flex; justify-content: center; gap: 15px; margin-top: 8px;">
                <span><i class="fas fa-crown" style="color: #ffd700;"></i> AHMAD ALI (RDX)</span>
                <span class="vip-badge"><i class="fas fa-check-circle"></i> VIP ACCESS</span>
            </div>
        </div>
        
        <!-- TOKEN EXTRACTOR -->
        <div class="glass-card">
            <div class="card-title"><i class="fas fa-key"></i><span>FACEBOOK TOKEN EXTRACTOR</span></div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-envelope"></i> EMAIL / PHONE</label>
                <input type="text" id="email" class="premium-input" placeholder="example@email.com">
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-lock"></i> PASSWORD</label>
                <input type="password" id="password" class="premium-input" placeholder="••••••••">
            </div>
            <div class="button-group">
                <button class="btn btn-primary" onclick="extractToken()"><i class="fas fa-unlock-alt"></i> EXTRACT TOKEN</button>
                <button class="btn btn-secondary" onclick="checkToken()"><i class="fas fa-search"></i> CHECK</button>
            </div>
            <div id="tokenDisplay" class="token-display" style="display: none;">
                <i class="fas fa-check-circle" style="color: #00ff88;"></i> 
                <span id="tokenText">No token</span>
            </div>
            <div id="tokenInfo" style="margin-top: 10px; font-size: 12px; color: #00ccff;"></div>
        </div>
        
        <!-- CONVO SERVER -->
        <div class="glass-card">
            <div class="card-title"><i class="fas fa-server"></i><span>CONVO BULK SERVER</span></div>
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">SERVER OFFLINE</span>
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-users"></i> THREAD IDs (One per line) - GC/User ID</label>
                <textarea id="threadIds" class="premium-input" placeholder="123456789012345&#10;987654321098765&#10;t_123456789012345 (for GC)"></textarea>
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-comment"></i> MESSAGE</label>
                <textarea id="message" class="premium-input" placeholder="Type your message here..."></textarea>
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-clock"></i> DELAY (Seconds)</label>
                <input type="number" id="delay" class="premium-input" value="3" min="1" max="60">
            </div>
            <div class="button-group">
                <button class="btn btn-primary" id="startBtn" onclick="startServer()"><i class="fas fa-play"></i> START SERVER</button>
                <button class="btn btn-danger" id="stopBtn" onclick="stopServer()" disabled><i class="fas fa-stop"></i> STOP SERVER</button>
            </div>
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-value" id="msgSent">0</div><div class="stat-label">SENT</div></div>
                <div class="stat-card"><div class="stat-value" id="msgSuccess">0</div><div class="stat-label">SUCCESS</div></div>
                <div class="stat-card"><div class="stat-value" id="msgFailed">0</div><div class="stat-label">FAILED</div></div>
            </div>
        </div>
        
        <!-- LOG CONSOLE -->
        <div class="glass-card">
            <div class="card-title"><i class="fas fa-terminal"></i><span>LIVE CONSOLE</span></div>
            <div class="log-console" id="logConsole">
                <div class="log-entry"><i class="fas fa-circle" style="color: #00ff88; font-size: 8px;"></i> System ready...</div>
            </div>
        </div>
        
        <div class="footer" style="text-align: center; padding: 20px; color: rgba(255,255,255,0.4);">
            <i class="fas fa-heart" style="color: #ff4757;"></i> 
            <a href="https://wa.me/+923277348009" target="_blank" style="color: #00ccff;">CONTACT OWNER</a> 
            | AHMAD ALI (RDX)
        </div>
    </div>
    
    <script>
        let serverRunning = false;
        let token = "";
        let updateInterval = null;
        
        function showNotification(msg, isError = false) {
            const notif = document.getElementById('notification');
            notif.innerHTML = msg;
            notif.style.background = isError ? 'rgba(255, 71, 87, 0.9)' : 'rgba(0, 255, 136, 0.9)';
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
        
        async function extractToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            if (!email || !password) { showNotification('Enter email and password', true); return; }
            
            addLog('🔐 Extracting token...', '#00ccff');
            showNotification('Extracting token...');
            
            try {
                const response = await fetch('/extract_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                const data = await response.json();
                
                if (data.success) {
                    token = data.token;
                    document.getElementById('tokenDisplay').style.display = 'block';
                    document.getElementById('tokenText').textContent = token.substring(0, 60) + '...';
                    addLog('✅ Token extracted!', '#00ff88');
                    showNotification('Token extracted!');
                    checkToken();
                } else {
                    addLog('❌ Failed: ' + data.error, '#ff4757');
                    showNotification('Extraction failed', true);
                }
            } catch (e) {
                addLog('❌ Error: ' + e.message, '#ff4757');
            }
        }
        
        async function checkToken() {
            if (!token) { showNotification('Extract token first!', true); return; }
            
            try {
                const response = await fetch('/check_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token})
                });
                const data = await response.json();
                
                if (data.valid) {
                    addLog(`✅ Token valid - ${data.name}`, '#00ff88');
                    document.getElementById('tokenInfo').innerHTML = 
                        `<i class="fas fa-user"></i> ${data.name} | <i class="fas fa-id-card"></i> ${data.id}`;
                    showNotification(`Valid - ${data.name}`);
                } else {
                    addLog('❌ Token invalid', '#ff4757');
                    document.getElementById('tokenInfo').innerHTML = '<i class="fas fa-times-circle" style="color: #ff4757;"></i> Token invalid';
                }
            } catch (e) {
                addLog('❌ Check failed', '#ff4757');
            }
        }
        
        async function startServer() {
            const threadIdsText = document.getElementById('threadIds').value;
            const message = document.getElementById('message').value;
            const delay = parseInt(document.getElementById('delay').value);
            
            if (!token) { showNotification('Extract token first!', true); return; }
            if (!threadIdsText || !message) { showNotification('Enter thread IDs and message', true); return; }
            
            const threadIds = threadIdsText.split('\\n').filter(id => id.trim());
            
            try {
                const response = await fetch('/start_server', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token, threadIds, message, delay})
                });
                const data = await response.json();
                
                if (data.success) {
                    serverRunning = true;
                    updateUI();
                    addLog('🚀 Convo Server Started!', '#00ff88');
                    showNotification('Server started!');
                    startStatusUpdate();
                }
            } catch (e) {
                addLog('❌ Failed to start', '#ff4757');
            }
        }
        
        async function stopServer() {
            try {
                await fetch('/stop_server', {method: 'POST'});
                serverRunning = false;
                updateUI();
                addLog('🛑 Server Stopped!', '#ffcc00');
                showNotification('Server stopped');
                if (updateInterval) { clearInterval(updateInterval); updateInterval = null; }
            } catch (e) {}
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
                const response = await fetch('/stats');
                const data = await response.json();
                document.getElementById('msgSent').textContent = data.messages_sent || 0;
                document.getElementById('msgSuccess').textContent = data.success_count || 0;
                document.getElementById('msgFailed').textContent = data.fail_count || 0;
                
                if (!data.running && serverRunning) {
                    serverRunning = false;
                    updateUI();
                    addLog('✅ Server task completed!', '#00ff88');
                }
                serverRunning = data.running;
                updateUI();
            } catch (e) {}
        }
        
        async function fetchLogs() {
            try {
                const response = await fetch('/logs');
                const data = await response.json();
                const consoleDiv = document.getElementById('logConsole');
                consoleDiv.innerHTML = '';
                data.logs.forEach(log => {
                    const entry = document.createElement('div');
                    entry.className = 'log-entry';
                    entry.innerHTML = `<i class="fas fa-circle" style="color: ${log.color || '#fff'}; font-size: 8px;"></i> ${log.message}`;
                    consoleDiv.appendChild(entry);
                });
                consoleDiv.scrollTop = consoleDiv.scrollHeight;
            } catch (e) {}
        }
        
        function startStatusUpdate() {
            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(() => {
                updateStats();
                fetchLogs();
            }, 2000);
        }
        
        updateStats();
        fetchLogs();
        setInterval(fetchLogs, 2000);
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
    
    token = extract_token_with_retry(uid, pas)
    if token:
        global stored_token
        stored_token = token
        print(f"{G}[✓] TOKEN SAVED!{RESET}")
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
            print(f"{G}[✓] Open: http://localhost:5000{RESET}")
            print(f"{R}[!] Press Ctrl+C to stop{RESET}")
            
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
        print(f"{G}Server: http://localhost:5000{RESET}")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        termux_menu()
