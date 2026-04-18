#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os, sys, time, json, uuid, random, threading, re
import requests
from flask import Flask, render_template_string, request, jsonify
from datetime import datetime

# ==================== GLOBAL VARIABLES ====================
app = Flask(__name__)
server_thread = None
server_running = False
stored_token = ""
messages_sent = 0
log_messages = []

# ==================== COLORS (TERMUX SUPPORT) ====================
G = '\033[38;5;46m'
Y = '\033[38;5;220m'
R = '\033[38;5;196m'
W = '\033[1;37m'
B = '\033[38;5;45m'
P = '\033[38;5;201m'
C = '\033[38;5;51m'
RESET = '\033[0m'

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

def log(message, color=W):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    log_messages.append(log_entry)
    if len(log_messages) > 50:
        log_messages.pop(0)
    print(f"{color}{log_entry}{RESET}")

def extract_token_termux():
    banner_termux()
    print(f"{B}[ FB TOKEN EXTRACTOR ]{RESET}")
    print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    uid = input(f"{G}[•] EMAIL/ID : {W}")
    pas = input(f"{G}[•] PASSWORD : {W}{RESET}")
    print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{G}[!] LOGGING IN... PLEASE WAIT{RESET}")
    
    token = extract_token_core(uid, pas)
    if token:
        global stored_token
        stored_token = token
        print(f"{G}[✓] TOKEN SAVED SUCCESSFULLY!{RESET}")
    input(f"\n{Y}[ Press Enter To Back ]{RESET}")

def extract_token_core(email, password):
    try:
        sess = requests.Session()
        ua = "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
        head = {
            "User-Agent": ua,
            "Host": "graph.facebook.com",
            "Authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
            "X-FB-Connection-Type": "WIFI",
            "X-FB-Net-HNI": "45005",
            "X-FB-SIM-HNI": "45005",
        }
        data = {
            "adid": str(uuid.uuid4()).upper(),
            "email": email,
            "password": password,
            "format": "json",
            "device_id": str(uuid.uuid4()).upper(),
            "cpl": "true",
            "family_device_id": str(uuid.uuid4()).upper(),
            "credentials_type": "device_based_login_password",
            "generate_session_cookies": "1",
            "error_detail_type": "button_with_disabled",
            "source": "login",
            "method": "auth.login",
            "meta_inf_fbmeta": "",
            "currently_logged_in_userid": "0",
            "locale": "en_US",
            "client_country_code": "US",
        }
        
        res = sess.post("https://graph.facebook.com/auth/login", data=data, headers=head)
        
        if res.status_code == 200:
            resp_json = res.json()
            if "access_token" in resp_json:
                token = resp_json["access_token"]
                try:
                    with open("/sdcard/ahmii_token.txt", "w") as f:
                        f.write(token)
                except:
                    with open("ahmii_token.txt", "w") as f:
                        f.write(token)
                log(f"TOKEN: {token[:50]}...", G)
                return token
            elif "error" in resp_json:
                log(f"ERROR: {resp_json['error'].get('message', 'Unknown')}", R)
            else:
                log(f"RESPONSE: {resp_json}", R)
        else:
            log(f"HTTP ERROR: {res.status_code}", R)
    except Exception as e:
        log(f"EXCEPTION: {str(e)}", R)
    return None

def send_bulk_message(token, thread_ids, message, hater_name="", delay=2):
    global messages_sent
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    
    success_count = 0
    fail_count = 0
    
    for tid in thread_ids:
        if not server_running:
            log(f"[STOPPED] Server stopped by user", Y)
            break
            
        tid = tid.strip()
        if not tid:
            continue
            
        url = f"https://graph.facebook.com/v18.0/{tid}/messages"
        payload = {"message": message}
        
        try:
            resp = requests.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                success_count += 1
                messages_sent += 1
                log(f"[✓] SENT → {tid} ({success_count}/{len(thread_ids)})", G)
            else:
                fail_count += 1
                try:
                    err = resp.json().get('error', {}).get('message', 'Unknown')[:50]
                except:
                    err = "Unknown error"
                log(f"[×] FAILED → {tid} | {err}", R)
        except Exception as e:
            fail_count += 1
            log(f"[×] ERROR → {tid} | {str(e)[:40]}", R)
        
        time.sleep(delay)
    
    log(f"[✓] COMPLETED | Success: {success_count} | Failed: {fail_count}", Y)
    return success_count, fail_count

def start_convo_server(token, thread_ids, message, delay):
    global server_running, server_thread
    if server_running:
        log("[!] Server already running!", Y)
        return False
    
    server_running = True
    server_thread = threading.Thread(target=send_bulk_message, args=(token, thread_ids, message, "", delay))
    server_thread.daemon = True
    server_thread.start()
    log("[✓] CONVO SERVER STARTED!", G)
    return True

def stop_convo_server():
    global server_running
    server_running = False
    log("[!] CONVO SERVER STOPPED!", Y)
    return True

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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
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
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: 
                radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(0, 200, 255, 0.03) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(255, 0, 212, 0.02) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            position: relative;
            z-index: 1;
        }
        
        /* PREMIUM HEADER */
        .header {
            text-align: center;
            padding: 20px 0 15px;
            position: relative;
        }
        
        .glow-text {
            font-size: 12px;
            letter-spacing: 3px;
            text-transform: uppercase;
            background: linear-gradient(135deg, #00ff88, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .main-title {
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #00ff88, #00ccff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(0, 255, 136, 0.3);
            letter-spacing: -0.5px;
            margin-bottom: 5px;
        }
        
        .subtitle {
            font-size: 14px;
            color: rgba(255,255,255,0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-top: 8px;
        }
        
        .vip-badge {
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            color: #000;
            letter-spacing: 1px;
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
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(0, 255, 136, 0.05) inset,
                0 0 30px rgba(0, 255, 136, 0.1);
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(0, 255, 136, 0.3);
            box-shadow: 
                0 25px 50px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(0, 255, 136, 0.1) inset,
                0 0 40px rgba(0, 255, 136, 0.15);
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #fff;
            letter-spacing: -0.3px;
        }
        
        .card-title i {
            color: #00ff88;
            font-size: 20px;
            text-shadow: 0 0 15px #00ff88;
        }
        
        /* INPUT GROUPS */
        .input-group {
            margin-bottom: 18px;
        }
        
        .input-label {
            display: block;
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 8px;
            color: rgba(255,255,255,0.7);
            letter-spacing: 0.3px;
        }
        
        .input-label i {
            color: #00ccff;
            margin-right: 6px;
            font-size: 12px;
        }
        
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
        
        .premium-input::placeholder {
            color: rgba(255,255,255,0.3);
            font-weight: 300;
        }
        
        textarea.premium-input {
            resize: vertical;
            min-height: 100px;
        }
        
        /* BUTTONS */
        .button-group {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        
        .btn {
            flex: 1;
            min-width: 120px;
            padding: 14px 20px;
            border: none;
            border-radius: 16px;
            font-size: 14px;
            font-weight: 600;
            font-family: 'Plus Jakarta Sans', sans-serif;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #00ff88, #00cc6a);
            color: #000;
            box-shadow: 0 8px 20px rgba(0, 255, 136, 0.3);
        }
        
        .btn-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(0, 255, 136, 0.4);
            background: linear-gradient(135deg, #33ff9a, #00ff88);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff4757, #ff3344);
            color: #fff;
            box-shadow: 0 8px 20px rgba(255, 71, 87, 0.3);
        }
        
        .btn-danger:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(255, 71, 87, 0.4);
            background: linear-gradient(135deg, #ff5e6e, #ff4757);
        }
        
        .btn-secondary {
            background: linear-gradient(135deg, #2d3a5e, #1a2744);
            color: #fff;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .btn-secondary:hover {
            background: linear-gradient(135deg, #3d4a6e, #2d3a5e);
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* TOKEN DISPLAY */
        .token-display {
            background: rgba(0, 0, 0, 0.4);
            border-radius: 12px;
            padding: 12px 16px;
            margin: 15px 0;
            border: 1px dashed rgba(0, 255, 136, 0.3);
            word-break: break-all;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            color: #00ff88;
            max-height: 80px;
            overflow-y: auto;
        }
        
        /* LOG CONSOLE */
        .log-console {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 16px;
            padding: 16px;
            max-height: 250px;
            overflow-y: auto;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 11px;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.03);
            color: rgba(255,255,255,0.8);
        }
        
        .log-entry:last-child {
            border-bottom: none;
        }
        
        /* STATUS INDICATOR */
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 15px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ff4757;
            box-shadow: 0 0 15px #ff4757;
            animation: pulse-red 2s infinite;
        }
        
        .status-dot.active {
            background: #00ff88;
            box-shadow: 0 0 20px #00ff88;
            animation: pulse-green 1.5s infinite;
        }
        
        @keyframes pulse-green {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes pulse-red {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 0.4; }
        }
        
        /* STATS */
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin: 15px 0;
        }
        
        .stat-card {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 14px;
            padding: 12px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: #00ff88;
            text-shadow: 0 0 20px #00ff88;
        }
        
        .stat-label {
            font-size: 11px;
            color: rgba(255,255,255,0.5);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 5px;
        }
        
        /* FOOTER */
        .footer {
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.4);
            font-size: 12px;
        }
        
        .footer a {
            color: #00ccff;
            text-decoration: none;
        }
        
        /* SCROLLBAR */
        ::-webkit-scrollbar {
            width: 4px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #00ff88;
            border-radius: 10px;
        }
        
        /* NOTIFICATION */
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0, 255, 136, 0.9);
            color: #000;
            padding: 12px 20px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 14px;
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.4);
            transform: translateX(400px);
            transition: transform 0.3s ease;
            z-index: 1000;
        }
        
        .notification.show {
            transform: translateX(0);
        }
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
        
        <!-- TOKEN EXTRACTOR CARD -->
        <div class="glass-card">
            <div class="card-title">
                <i class="fas fa-key"></i>
                <span>FACEBOOK TOKEN EXTRACTOR</span>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-envelope"></i> EMAIL / PHONE</label>
                <input type="text" id="email" class="premium-input" placeholder="example@email.com" value="">
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-lock"></i> PASSWORD</label>
                <input type="password" id="password" class="premium-input" placeholder="••••••••">
            </div>
            
            <div class="button-group">
                <button class="btn btn-primary" onclick="extractToken()">
                    <i class="fas fa-unlock-alt"></i> EXTRACT TOKEN
                </button>
                <button class="btn btn-secondary" onclick="checkToken()">
                    <i class="fas fa-search"></i> CHECK
                </button>
            </div>
            
            <div id="tokenDisplay" class="token-display" style="display: none;">
                <i class="fas fa-check-circle" style="color: #00ff88;"></i> 
                <span id="tokenText">No token extracted yet</span>
            </div>
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
                <textarea id="threadIds" class="premium-input" placeholder="1000123456789&#10;1000987654321&#10;..."></textarea>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-comment"></i> MESSAGE</label>
                <textarea id="message" class="premium-input" placeholder="Type your message here..."></textarea>
            </div>
            
            <div class="input-group">
                <label class="input-label"><i class="fas fa-clock"></i> DELAY (Seconds)</label>
                <input type="number" id="delay" class="premium-input" value="2" min="1" max="60">
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
                    <div class="stat-label"><i class="fas fa-paper-plane"></i> MESSAGES SENT</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="threadCount">0</div>
                    <div class="stat-label"><i class="fas fa-user"></i> TOTAL THREADS</div>
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
                <div class="log-entry"><i class="fas fa-circle" style="color: #00ccff; font-size: 8px;"></i> Waiting for commands</div>
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
            
            if (consoleDiv.children.length > 30) {
                consoleDiv.removeChild(consoleDiv.children[0]);
            }
        }
        
        async function extractToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                showNotification('Please enter email and password', true);
                return;
            }
            
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
                    document.getElementById('tokenText').textContent = token.substring(0, 80) + '...';
                    addLog('✅ Token extracted successfully!', '#00ff88');
                    showNotification('Token extracted successfully!');
                } else {
                    addLog('❌ Failed: ' + data.error, '#ff4757');
                    showNotification('Extraction failed: ' + data.error, true);
                }
            } catch (e) {
                addLog('❌ Error: ' + e.message, '#ff4757');
                showNotification('Network error', true);
            }
        }
        
        async function checkToken() {
            if (!token) {
                showNotification('No token available. Extract first!', true);
                return;
            }
            
            addLog('🔍 Checking token...', '#00ccff');
            
            try {
                const response = await fetch('/check_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token})
                });
                
                const data = await response.json();
                
                if (data.valid) {
                    addLog(`✅ Token valid! Owner: ${data.name}`, '#00ff88');
                    showNotification(`Token valid - ${data.name}`);
                } else {
                    addLog('❌ Token invalid or expired', '#ff4757');
                    showNotification('Token invalid', true);
                }
            } catch (e) {
                addLog('❌ Error checking token', '#ff4757');
            }
        }
        
        async function startServer() {
            const threadIdsText = document.getElementById('threadIds').value;
            const message = document.getElementById('message').value;
            const delay = parseInt(document.getElementById('delay').value);
            
            if (!token) {
                showNotification('Extract token first!', true);
                return;
            }
            
            if (!threadIdsText || !message) {
                showNotification('Enter thread IDs and message', true);
                return;
            }
            
            const threadIds = threadIdsText.split('\\n').filter(id => id.trim());
            document.getElementById('threadCount').textContent = threadIds.length;
            
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
                    showNotification('Server started successfully!');
                    startStatusUpdate();
                }
            } catch (e) {
                addLog('❌ Failed to start server', '#ff4757');
            }
        }
        
        async function stopServer() {
            try {
                const response = await fetch('/stop_server', {method: 'POST'});
                const data = await response.json();
                
                if (data.success) {
                    serverRunning = false;
                    updateUI();
                    addLog('🛑 Convo Server Stopped!', '#ffcc00');
                    showNotification('Server stopped');
                    if (updateInterval) {
                        clearInterval(updateInterval);
                        updateInterval = null;
                    }
                }
            } catch (e) {
                addLog('❌ Failed to stop server', '#ff4757');
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
                const response = await fetch('/stats');
                const data = await response.json();
                document.getElementById('msgSent').textContent = data.messages_sent;
                document.getElementById('threadCount').textContent = data.total_threads || 0;
            } catch (e) {}
        }
        
        function startStatusUpdate() {
            if (updateInterval) clearInterval(updateInterval);
            updateInterval = setInterval(async () => {
                await updateStats();
                
                try {
                    const response = await fetch('/status');
                    const data = await response.json();
                    
                    if (!data.running && serverRunning) {
                        serverRunning = false;
                        updateUI();
                        addLog('✅ Server task completed!', '#00ff88');
                        clearInterval(updateInterval);
                        updateInterval = null;
                    }
                    
                    if (data.logs) {
                        const consoleDiv = document.getElementById('logConsole');
                        data.logs.slice(-10).forEach(log => {
                            if (!log.shown) {
                                addLog(log.message, log.color || '#fff');
                                log.shown = true;
                            }
                        });
                    }
                } catch (e) {}
            }, 2000);
        }
        
        // Initial load
        updateStats();
    </script>
</body>
</html>
'''

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract_token', methods=['POST'])
def api_extract_token():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    token = extract_token_core(email, password)
    if token:
        global stored_token
        stored_token = token
        return jsonify({'success': True, 'token': token})
    return jsonify({'success': False, 'error': 'Login failed'})

@app.route('/check_token', methods=['POST'])
def api_check_token():
    data = request.json
    token = data.get('token')
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        resp = requests.get('https://graph.facebook.com/me?fields=name', headers=headers)
        if resp.status_code == 200:
            name = resp.json().get('name', 'Unknown')
            return jsonify({'valid': True, 'name': name})
    except:
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
    return jsonify({'success': False, 'error': 'Server already running'})

@app.route('/stop_server', methods=['POST'])
def api_stop_server():
    stop_convo_server()
    return jsonify({'success': True})

@app.route('/status')
def api_status():
    return jsonify({
        'running': server_running,
        'messages_sent': messages_sent,
    })

@app.route('/stats')
def api_stats():
    return jsonify({
        'messages_sent': messages_sent,
        'total_threads': 0,
        'success_rate': 0
    })

# ==================== TERMUX MENU ====================
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
            print(f"{W}    OR http://127.0.0.1:5000{RESET}")
            print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            print(f"{R}[!] Press Ctrl+C to stop server{RESET}")
            print(f"{Y}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
            
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

# ==================== MAIN ====================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'web':
            banner_termux()
            print(f"{B}[ WEB MODE ]{RESET}")
            print(f"{G}Server running at: http://localhost:5000{RESET}")
            app.run(host='0.0.0.0', port=5000, debug=False)
        else:
            termux_menu()
    else:
        termux_menu()
