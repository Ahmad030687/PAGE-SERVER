#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FB MASTER CORE - 100% WORKING TOKEN EXTRACTOR + BULK CONVO SERVER
OWNER: AHMAD ALI (RDX)
"""

import os
import sys
import time
import json
import uuid
import random
import threading
import re
import base64
import hashlib
import hmac
from datetime import datetime
from urllib.parse import urlencode, quote_plus

try:
    import requests
    from flask import Flask, render_template_string, request, jsonify
except ImportError:
    os.system("pip install requests flask --quiet")
    import requests
    from flask import Flask, render_template_string, request, jsonify

# ==================== GLOBAL VARIABLES ====================
app = Flask(__name__)
server_thread = None
server_running = False
stored_token = ""
stored_cookie = ""
messages_sent = 0
total_threads_count = 0
log_messages = []
current_access_token = ""
current_uid = ""

# ==================== COLORS ====================
G = '\033[38;5;46m'
Y = '\033[38;5;220m'
R = '\033[38;5;196m'
W = '\033[1;37m'
B = '\033[38;5;45m'
P = '\033[38;5;201m'
C = '\033[38;5;51m'
RESET = '\033[0m'

# ==================== FACEBOOK API CONSTANTS ====================
FB_API_KEY = "882a8490361da98702bf97a021ddc14d"
FB_CLIENT_TOKEN = "62f8ce9f74b12f84c123cc23437a4a32"
FB_APP_ID = "350685531728"
FB_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Dalvik/2.1.0 (Linux; U; Android 13; SM-G998B Build/TP1A.220624.014) [FBAN/FB4A;FBAV/494.0.0.55.73;]"
]

def banner_termux():
    os.system('clear 2>/dev/null || cls 2>/dev/null')
    print(f"""{C}
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  █████╗ ██╗  ██╗███╗   ███╗██╗██╗    ███╗   ███╗ █████╗ ███████╗
║ ██╔══██╗██║  ██║████╗ ████║██║██║    ████╗ ████║██╔══██╗██╔════╝
║ ███████║███████║██╔████╔██║██║██║    ██╔████╔██║███████║███████╗
║ ██╔══██║██╔══██║██║╚██╔╝██║██║██║    ██║╚██╔╝██║██╔══██║╚════██║
║ ██║  ██║██║  ██║██║ ╚═╝ ██║██║██║    ██║ ╚═╝ ██║██║  ██║███████║
║ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝    ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝
║                                                                  ║
║                    {G}🔥 FACEBOOK MASTER CORE 🔥{C}                    ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  {Y}OWNER    : {W}AHMAD ALI (RDX){C}                                         ║
║  {Y}VERSION  : {W}4.0 ULTIMATE{C}                                            ║
║  {Y}STATUS   : {G}✅ 100% WORKING ✅{C}                                      ║
╚══════════════════════════════════════════════════════════════════╝{RESET}""")

def log(message, color=W):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {"timestamp": timestamp, "message": message, "color": color}
    log_messages.append(log_entry)
    if len(log_messages) > 200:
        log_messages.pop(0)
    print(f"{color}[{timestamp}] {message}{RESET}")

def generate_device_data():
    """Generate realistic device data for Facebook"""
    device_id = str(uuid.uuid4()).replace('-', '')[:16]
    adid = str(uuid.uuid4()).upper()
    machine_id = base64.b64encode(os.urandom(16)).decode('utf-8')[:32]
    
    return {
        "device_id": device_id,
        "adid": adid,
        "machine_id": machine_id,
        "client_id": hashlib.md5(device_id.encode()).hexdigest()[:32],
    }

def generate_signature(data_dict, api_key):
    """Generate Facebook API signature"""
    sorted_keys = sorted(data_dict.keys())
    sig_string = ''.join(f"{k}={data_dict[k]}" for k in sorted_keys if k != 'sig')
    sig = hashlib.md5((sig_string + api_key).encode()).hexdigest()
    return sig

# ==================== 100% WORKING TOKEN EXTRACTION ====================

def facebook_login_api(email, password):
    """Method 1: b-api.facebook.com (MOST RELIABLE)"""
    try:
        sess = requests.Session()
        device = generate_device_data()
        
        log(f"[📱] Device: {device['device_id'][:8]}...", B)
        
        headers = {
            "User-Agent": random.choice(FB_USER_AGENTS),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "X-FB-Connection-Type": "WIFI",
            "X-FB-Net-HNI": "45005",
            "X-FB-SIM-HNI": "45005",
            "X-FB-HTTP-Engine": "Liger",
            "X-FB-Connection-Quality": "EXCELLENT",
        }
        
        # Prepare data with signature
        data = {
            "format": "json",
            "email": email,
            "password": password,
            "credentials_type": "password",
            "generate_session_cookies": "1",
            "generate_machine_id": "1",
            "source": "login",
            "machine_id": device["machine_id"],
            "meta_inf_fbmeta": "",
            "adid": device["adid"],
            "device_id": device["device_id"],
            "family_device_id": device["device_id"],
            "cpl": "true",
            "currently_logged_in_userid": "0",
            "locale": "en_US",
            "client_country_code": "US",
            "method": "auth.login",
            "api_key": FB_API_KEY,
            "fb_api_req_friendly_name": "authenticate",
        }
        
        # Add signature
        data["sig"] = generate_signature(data, FB_API_KEY)
        
        log(f"[🔐] Authenticating with Facebook...", B)
        
        resp = sess.post(
            "https://b-api.facebook.com/method/auth.login",
            data=data,
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            try:
                result = resp.json()
                
                # Check for access token
                if "access_token" in result:
                    token = result["access_token"]
                    uid = result.get("uid", "0")
                    log(f"[✅] LOGIN SUCCESSFUL!", G)
                    log(f"[👤] UID: {uid}", G)
                    log(f"[🔑] TOKEN: {token[:50]}...", G)
                    
                    # Save to file
                    save_token(token, uid)
                    return token, uid
                    
                elif "session_key" in result:
                    token = result["session_key"]
                    uid = result.get("uid", "0")
                    log(f"[✅] Session key extracted!", G)
                    save_token(token, uid)
                    return token, uid
                    
                elif "error" in result:
                    error = result["error"]
                    error_msg = error.get("message", "Unknown error")
                    error_code = error.get("code", 0)
                    
                    log(f"[❌] Error {error_code}: {error_msg}", R)
                    
                    if error_code == 405:
                        log(f"[⚠️] CHECKPOINT REQUIRED - Verify login on phone!", Y)
                    elif "password" in error_msg.lower():
                        log(f"[❌] Incorrect password!", R)
                        
                else:
                    log(f"[⚠️] Unknown response: {list(result.keys())}", Y)
                    
            except json.JSONDecodeError:
                log(f"[❌] Invalid JSON response", R)
        else:
            log(f"[❌] HTTP Error: {resp.status_code}", R)
            
    except Exception as e:
        log(f"[❌] Exception: {str(e)}", R)
    
    return None, None

def facebook_login_graph(email, password):
    """Method 2: graph.facebook.com (BACKUP)"""
    try:
        sess = requests.Session()
        device = generate_device_data()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Host": "graph.facebook.com",
            "Authorization": f"OAuth {FB_APP_ID}|{FB_CLIENT_TOKEN}",
            "X-FB-Connection-Type": "WIFI",
            "X-FB-Net-HNI": "45005",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data = {
            "adid": device["adid"],
            "email": email,
            "password": password,
            "format": "json",
            "device_id": device["device_id"],
            "cpl": "true",
            "family_device_id": device["device_id"],
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
        
        log(f"[🔄] Trying alternative method...", B)
        
        resp = sess.post(
            "https://graph.facebook.com/auth/login",
            data=data,
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            result = resp.json()
            
            if "access_token" in result:
                token = result["access_token"]
                uid = result.get("uid", "0")
                log(f"[✅] Token extracted via Graph API!", G)
                save_token(token, uid)
                return token, uid
            elif "error" in result:
                error = result["error"]
                log(f"[❌] Graph Error: {error.get('message', 'Unknown')}", R)
                
    except Exception as e:
        log(f"[❌] Graph method failed: {str(e)}", R)
    
    return None, None

def facebook_login_mbasic(email, password):
    """Method 3: mbasic.facebook.com (FALLBACK)"""
    try:
        sess = requests.Session()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        # Get login page
        log(f"[🌐] Accessing mbasic login page...", B)
        login_page = sess.get("https://mbasic.facebook.com/login", headers=headers)
        
        # Extract hidden inputs
        lsd_match = re.search(r'name="lsd" value="([^"]+)"', login_page.text)
        jazoest_match = re.search(r'name="jazoest" value="([^"]+)"', login_page.text)
        
        if not lsd_match:
            log(f"[❌] Could not extract lsd token", R)
            return None, None
            
        lsd = lsd_match.group(1)
        jazoest = jazoest_match.group(1) if jazoest_match else "1"
        
        log(f"[🔑] Got login tokens...", B)
        
        # Submit login
        login_data = {
            "lsd": lsd,
            "jazoest": jazoest,
            "email": email,
            "pass": password,
            "login": "Log In",
            "default_persistent": "1",
        }
        
        resp = sess.post(
            "https://mbasic.facebook.com/login/device-based/regular/login/",
            data=login_data,
            headers=headers,
            allow_redirects=True
        )
        
        if "checkpoint" in resp.url.lower():
            log(f"[⚠️] Account needs verification (Checkpoint)", Y)
            return None, None
            
        # Extract cookies
        cookies = sess.cookies.get_dict()
        
        if "c_user" in cookies:
            uid = cookies["c_user"]
            
            # Try to get access token
            token_resp = sess.get(
                "https://mbasic.facebook.com/composer/ocelot/async_loader/?publisher=feed",
                headers=headers
            )
            
            # Extract access token from page source
            token_match = re.search(r'"accessToken":"(EAA[^"]+)"', token_resp.text)
            if not token_match:
                token_match = re.search(r'access_token=([^"&\s]+)', token_resp.text)
                
            if token_match:
                token = token_match.group(1)
                log(f"[✅] Token extracted via mbasic!", G)
                save_token(token, uid)
                return token, uid
                
        elif "login" in resp.url.lower():
            log(f"[❌] Login failed - Check credentials", R)
            
    except Exception as e:
        log(f"[❌] Mbasic method failed: {str(e)}", R)
    
    return None, None

def extract_token_full(email, password):
    """Complete token extraction with all methods"""
    global current_access_token, current_uid
    
    log(f"{Y}{'='*60}{RESET}")
    log(f"[🎯] TARGET: {email}", C)
    log(f"{Y}{'='*60}{RESET}")
    
    # Try Method 1: b-api (Most Reliable)
    log(f"[1/3] Trying b-api.facebook.com method...", B)
    token, uid = facebook_login_api(email, password)
    if token:
        current_access_token = token
        current_uid = uid
        return token
    
    # Try Method 2: Graph API
    log(f"[2/3] Trying graph.facebook.com method...", B)
    token, uid = facebook_login_graph(email, password)
    if token:
        current_access_token = token
        current_uid = uid
        return token
    
    # Try Method 3: mbasic
    log(f"[3/3] Trying mbasic.facebook.com method...", B)
    token, uid = facebook_login_mbasic(email, password)
    if token:
        current_access_token = token
        current_uid = uid
        return token
    
    log(f"{R}{'='*60}{RESET}")
    log(f"[💀] ALL METHODS FAILED", R)
    log(f"{R}{'='*60}{RESET}")
    log(f"[💡] TROUBLESHOOTING TIPS:", Y)
    log(f"   1. Disable 2FA temporarily", Y)
    log(f"   2. Login on phone app first", Y)
    log(f"   3. Try app password from FB settings", Y)
    log(f"   4. Wait 5 mins and try again", Y)
    
    return None

def save_token(token, uid="0"):
    """Save token to multiple locations"""
    try:
        # Save to /sdcard/
        with open("/sdcard/ahmii_token.txt", "w") as f:
            f.write(f"{uid}|{token}")
        log(f"[💾] Saved to /sdcard/ahmii_token.txt", G)
    except:
        pass
    
    try:
        # Save to current directory
        with open("token.txt", "w") as f:
            f.write(f"{uid}|{token}")
        log(f"[💾] Saved to token.txt", G)
    except:
        pass
    
    global stored_token
    stored_token = token

# ==================== BULK MESSAGE SENDER ====================

def send_message(token, thread_id, message):
    """Send single message"""
    try:
        headers = {
            "User-Agent": random.choice(FB_USER_AGENTS),
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        url = f"https://graph.facebook.com/v18.0/{thread_id}/messages"
        payload = {"message": message}
        
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            return True, "Sent"
        else:
            try:
                error = resp.json().get('error', {}).get('message', 'Unknown')[:50]
            except:
                error = f"HTTP {resp.status_code}"
            return False, error
            
    except Exception as e:
        return False, str(e)[:40]

def bulk_message_worker(token, thread_ids, message, delay):
    """Worker thread for bulk messaging"""
    global messages_sent, server_running, total_threads_count
    
    total_threads_count = len(thread_ids)
    success = 0
    failed = 0
    
    log(f"{G}{'='*50}{RESET}")
    log(f"[🚀] CONVO SERVER STARTED", G)
    log(f"[📊] Total Threads: {total_threads_count}", C)
    log(f"[💬] Message: {message[:50]}...", C)
    log(f"[⏱️] Delay: {delay}s", C)
    log(f"{G}{'='*50}{RESET}")
    
    for i, tid in enumerate(thread_ids, 1):
        if not server_running:
            log(f"[🛑] Server stopped by user", Y)
            break
            
        tid = tid.strip()
        if not tid:
            continue
        
        status, msg = send_message(token, tid, message)
        
        if status:
            success += 1
            messages_sent += 1
            log(f"[✅] [{i}/{total_threads_count}] Sent to {tid}", G)
        else:
            failed += 1
            log(f"[❌] [{i}/{total_threads_count}] Failed: {tid} | {msg}", R)
        
        if i < len(thread_ids) and server_running:
            time.sleep(delay)
    
    log(f"{Y}{'='*50}{RESET}")
    log(f"[📈] COMPLETED: {success} Success | {failed} Failed", C)
    log(f"{Y}{'='*50}{RESET}")
    
    server_running = False

def start_convo_server(token, thread_ids, message, delay):
    global server_running, server_thread
    
    if server_running:
        return False
    
    server_running = True
    server_thread = threading.Thread(
        target=bulk_message_worker,
        args=(token, thread_ids, message, delay)
    )
    server_thread.daemon = True
    server_thread.start()
    return True

def stop_convo_server():
    global server_running
    server_running = False
    log(f"[🛑] Stopping server...", Y)
    return True

# ==================== TOKEN CHECKER ====================

def check_token_validity(token):
    """Check if token is valid and get user info"""
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": random.choice(FB_USER_AGENTS)
        }
        
        resp = requests.get(
            "https://graph.facebook.com/me?fields=id,name,email",
            headers=headers,
            timeout=10
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return True, data.get("name", "Unknown"), data.get("id", "0")
        else:
            return False, "Invalid", "0"
            
    except:
        return False, "Error", "0"

# ==================== FLASK WEB UI ====================

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#0a0f1e">
    <title>⚡ AHMII FB MASTER CORE ⚡</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{
            font-family:'Plus Jakarta Sans',sans-serif;
            background:linear-gradient(135deg,#0a0f1e 0%,#0d1428 50%,#0a0f1e 100%);
            min-height:100vh;
            color:#fff;
            padding:16px;
            position:relative;
            overflow-x:hidden;
        }
        body::before{
            content:'';
            position:fixed;
            top:0;left:0;right:0;bottom:0;
            background:radial-gradient(circle at 20% 80%,rgba(0,255,136,0.05) 0%,transparent 50%),
                      radial-gradient(circle at 80% 20%,rgba(0,200,255,0.05) 0%,transparent 50%),
                      radial-gradient(circle at 40% 40%,rgba(255,0,212,0.03) 0%,transparent 50%);
            pointer-events:none;z-index:0;
        }
        .container{max-width:600px;margin:0 auto;position:relative;z-index:1;}
        .header{text-align:center;padding:20px 0 15px;}
        .glow-text{font-size:12px;letter-spacing:3px;text-transform:uppercase;background:linear-gradient(135deg,#00ff88,#00ccff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:600;}
        .main-title{font-size:32px;font-weight:800;background:linear-gradient(135deg,#fff,#00ff88,#00ccff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:0 0 40px rgba(0,255,136,0.3);}
        .vip-badge{background:linear-gradient(135deg,#ffd700,#ff8c00);padding:4px 12px;border-radius:20px;font-size:11px;font-weight:700;color:#000;box-shadow:0 0 20px rgba(255,215,0,0.4);}
        .glass-card{
            background:rgba(15,25,45,0.7);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
            border:1px solid rgba(0,255,136,0.15);border-radius:24px;padding:24px 20px;margin-bottom:16px;
            box-shadow:0 20px 40px rgba(0,0,0,0.4),0 0 0 1px rgba(0,255,136,0.05) inset,0 0 30px rgba(0,255,136,0.1);
        }
        .card-title{font-size:18px;font-weight:600;margin-bottom:20px;display:flex;align-items:center;gap:10px;}
        .card-title i{color:#00ff88;text-shadow:0 0 15px #00ff88;}
        .input-group{margin-bottom:18px;}
        .input-label{display:block;font-size:13px;font-weight:500;margin-bottom:8px;color:rgba(255,255,255,0.7);}
        .premium-input{
            width:100%;background:rgba(0,0,0,0.3);border:1.5px solid rgba(255,255,255,0.08);
            border-radius:16px;padding:14px 18px;color:#fff;font-size:14px;outline:none;
            transition:all 0.3s ease;font-family:'Plus Jakarta Sans',sans-serif;
        }
        .premium-input:focus{border-color:#00ff88;background:rgba(0,255,136,0.05);box-shadow:0 0 25px rgba(0,255,136,0.2);}
        .premium-input::placeholder{color:rgba(255,255,255,0.3);}
        textarea.premium-input{resize:vertical;min-height:100px;}
        .button-group{display:flex;gap:12px;flex-wrap:wrap;}
        .btn{
            flex:1;min-width:120px;padding:14px 20px;border:none;border-radius:16px;
            font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;
            justify-content:center;gap:8px;transition:all 0.3s ease;text-transform:uppercase;
            letter-spacing:0.5px;font-family:'Plus Jakarta Sans',sans-serif;
        }
        .btn-primary{background:linear-gradient(135deg,#00ff88,#00cc6a);color:#000;box-shadow:0 8px 20px rgba(0,255,136,0.3);}
        .btn-primary:hover{transform:translateY(-3px);box-shadow:0 15px 30px rgba(0,255,136,0.4);}
        .btn-danger{background:linear-gradient(135deg,#ff4757,#ff3344);color:#fff;box-shadow:0 8px 20px rgba(255,71,87,0.3);}
        .btn-danger:hover{transform:translateY(-3px);box-shadow:0 15px 30px rgba(255,71,87,0.4);}
        .btn-secondary{background:linear-gradient(135deg,#2d3a5e,#1a2744);color:#fff;border:1px solid rgba(255,255,255,0.1);}
        .btn:disabled{opacity:0.5;cursor:not-allowed;transform:none;}
        .token-display{
            background:rgba(0,0,0,0.4);border-radius:12px;padding:12px 16px;margin:15px 0;
            border:1px dashed rgba(0,255,136,0.3);word-break:break-all;font-family:monospace;
            font-size:12px;color:#00ff88;max-height:80px;overflow-y:auto;
        }
        .log-console{
            background:rgba(0,0,0,0.5);border-radius:16px;padding:16px;max-height:250px;
            overflow-y:auto;font-family:monospace;font-size:11px;border:1px solid rgba(255,255,255,0.05);
        }
        .log-entry{padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.03);color:rgba(255,255,255,0.8);}
        .status-indicator{display:flex;align-items:center;gap:8px;margin-bottom:15px;}
        .status-dot{width:12px;height:12px;border-radius:50%;background:#ff4757;box-shadow:0 0 15px #ff4757;animation:pulse-red 2s infinite;}
        .status-dot.active{background:#00ff88;box-shadow:0 0 20px #00ff88;animation:pulse-green 1.5s infinite;}
        @keyframes pulse-green{0%,100%{opacity:1}50%{opacity:0.5}}
        @keyframes pulse-red{0%,100%{opacity:0.8}50%{opacity:0.4}}
        .stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:15px 0;}
        .stat-card{background:rgba(0,0,0,0.3);border-radius:14px;padding:12px;text-align:center;border:1px solid rgba(255,255,255,0.05);}
        .stat-value{font-size:28px;font-weight:700;color:#00ff88;text-shadow:0 0 20px #00ff88;}
        .stat-label{font-size:11px;color:rgba(255,255,255,0.5);text-transform:uppercase;letter-spacing:1px;}
        .footer{text-align:center;padding:20px;color:rgba(255,255,255,0.4);font-size:12px;}
        .footer a{color:#00ccff;text-decoration:none;}
        ::-webkit-scrollbar{width:4px;}
        ::-webkit-scrollbar-track{background:rgba(0,0,0,0.2);}
        ::-webkit-scrollbar-thumb{background:#00ff88;border-radius:10px;}
        .notification{
            position:fixed;top:20px;right:20px;background:rgba(0,255,136,0.9);color:#000;
            padding:12px 20px;border-radius:50px;font-weight:600;font-size:14px;
            box-shadow:0 10px 30px rgba(0,255,136,0.4);transform:translateX(400px);
            transition:transform 0.3s ease;z-index:1000;
        }
        .notification.show{transform:translateX(0);}
    </style>
</head>
<body>
    <div class="notification" id="notification">✓ Message</div>
    
    <div class="container">
        <div class="header">
            <div class="glow-text">⚡ 100% WORKING ⚡</div>
            <div class="main-title">AHMII FB MASTER</div>
            <div style="display:flex;justify-content:center;gap:10px;margin-top:10px;">
                <span><i class="fas fa-crown" style="color:#ffd700;"></i> AHMAD ALI (RDX)</span>
                <span class="vip-badge"><i class="fas fa-check-circle"></i> VIP ACCESS</span>
            </div>
        </div>
        
        <!-- TOKEN EXTRACTOR -->
        <div class="glass-card">
            <div class="card-title"><i class="fas fa-key"></i> TOKEN EXTRACTOR</div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-envelope"></i> EMAIL / PHONE</label>
                <input type="text" id="email" class="premium-input" placeholder="example@email.com">
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-lock"></i> PASSWORD</label>
                <input type="password" id="password" class="premium-input" placeholder="••••••••">
            </div>
            <div class="button-group">
                <button class="btn btn-primary" onclick="extractToken()"><i class="fas fa-unlock-alt"></i> EXTRACT</button>
                <button class="btn btn-secondary" onclick="checkToken()"><i class="fas fa-search"></i> CHECK</button>
            </div>
            <div id="tokenDisplay" class="token-display" style="display:none;">
                <i class="fas fa-check-circle" style="color:#00ff88;"></i>
                <span id="tokenText"></span>
            </div>
        </div>
        
        <!-- CONVO SERVER -->
        <div class="glass-card">
            <div class="card-title"><i class="fas fa-server"></i> BULK CONVO SERVER</div>
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">SERVER OFFLINE</span>
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-users"></i> THREAD IDs (One per line)</label>
                <textarea id="threadIds" class="premium-input" placeholder="1000123456789&#10;1000987654321"></textarea>
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-comment"></i> MESSAGE</label>
                <textarea id="message" class="premium-input" placeholder="Type your message..."></textarea>
            </div>
            <div class="input-group">
                <label class="input-label"><i class="fas fa-clock"></i> DELAY (Seconds)</label>
                <input type="number" id="delay" class="premium-input" value="2" min="1" max="60">
            </div>
            <div class="button-group">
                <button class="btn btn-primary" id="startBtn" onclick="startServer()"><i class="fas fa-play"></i> START</button>
                <button class="btn btn-danger" id="stopBtn" onclick="stopServer()" disabled><i class="fas fa-stop"></i> STOP</button>
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="msgSent">0</div>
                    <div class="stat-label">SENT</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="threadCount">0</div>
                    <div class="stat-label">THREADS</div>
                </div>
            </div>
        </div>
        
        <!-- CONSOLE -->
        <div class="glass-card">
            <div class="card-title"><i class="fas fa-terminal"></i> LIVE CONSOLE</div>
            <div class="log-console" id="logConsole">
                <div class="log-entry">🟢 System ready...</div>
            </div>
        </div>
        
        <div class="footer">
            <i class="fas fa-heart" style="color:#ff4757;"></i>
            <a href="https://wa.me/+923277348009" target="_blank">CONTACT OWNER</a>
            | AHMAD ALI (RDX) © 2024
        </div>
    </div>
    
    <script>
        let serverRunning = false;
        let token = "";
        let updateInterval = null;
        
        function showNotification(msg, isError=false){
            const n=document.getElementById('notification');
            n.innerHTML=msg;
            n.style.background=isError?'rgba(255,71,87,0.9)':'rgba(0,255,136,0.9)';
            n.classList.add('show');
            setTimeout(()=>n.classList.remove('show'),3000);
        }
        
        function addLog(msg,color='#fff'){
            const c=document.getElementById('logConsole');
            const e=document.createElement('div');
            e.className='log-entry';
            e.innerHTML=`<i class="fas fa-circle" style="color:${color};font-size:8px;"></i> ${msg}`;
            c.appendChild(e);
            c.scrollTop=c.scrollHeight;
            if(c.children.length>30) c.removeChild(c.children[0]);
        }
        
        async function extractToken(){
            const email=document.getElementById('email').value;
            const password=document.getElementById('password').value;
            if(!email||!password){showNotification('Enter email and password',true);return;}
            addLog('🔐 Extracting token...','#00ccff');
            showNotification('Extracting...');
            try{
                const r=await fetch('/extract_token',{
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({email,password})
                });
                const d=await r.json();
                if(d.success){
                    token=d.token;
                    document.getElementById('tokenDisplay').style.display='block';
                    document.getElementById('tokenText').textContent=token.substring(0,60)+'...';
                    addLog('✅ Token extracted!','#00ff88');
                    showNotification('Success!');
                }else{
                    addLog('❌ Failed: '+d.error,'#ff4757');
                    showNotification(d.error,true);
                }
            }catch(e){addLog('❌ Error','#ff4757');}
        }
        
        async function checkToken(){
            if(!token){showNotification('Extract token first!',true);return;}
            try{
                const r=await fetch('/check_token',{
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({token})
                });
                const d=await r.json();
                if(d.valid){
                    addLog(`✅ Valid! Owner: ${d.name}`,'#00ff88');
                    showNotification(`Valid - ${d.name}`);
                }else{
                    addLog('❌ Invalid token','#ff4757');
                    showNotification('Invalid',true);
                }
            }catch(e){}
        }
        
        async function startServer(){
            const threadIds=document.getElementById('threadIds').value.split('\\n').filter(id=>id.trim());
            const message=document.getElementById('message').value;
            const delay=parseInt(document.getElementById('delay').value);
            if(!token){showNotification('Extract token first!',true);return;}
            if(!threadIds.length||!message){showNotification('Enter threads and message',true);return;}
            try{
                const r=await fetch('/start_server',{
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({token,threadIds,message,delay})
                });
                const d=await r.json();
                if(d.success){
                    serverRunning=true;
                    updateUI();
                    addLog('🚀 Server started!','#00ff88');
                    showNotification('Server started!');
                    startStatusUpdate();
                }
            }catch(e){}
        }
        
        async function stopServer(){
            try{
                await fetch('/stop_server',{method:'POST'});
                serverRunning=false;
                updateUI();
                addLog('🛑 Server stopped','#ffcc00');
                showNotification('Stopped');
                if(updateInterval){clearInterval(updateInterval);updateInterval=null;}
            }catch(e){}
        }
        
        function updateUI(){
            const dot=document.getElementById('statusDot');
            const status=document.getElementById('statusText');
            const start=document.getElementById('startBtn');
            const stop=document.getElementById('stopBtn');
            if(serverRunning){
                dot.classList.add('active');
                status.textContent='SERVER ONLINE ●';
                start.disabled=true;
                stop.disabled=false;
            }else{
                dot.classList.remove('active');
                status.textContent='SERVER OFFLINE';
                start.disabled=false;
                stop.disabled=true;
            }
        }
        
        async function updateStats(){
            try{
                const r=await fetch('/stats');
                const d=await r.json();
                document.getElementById('msgSent').textContent=d.messages_sent;
                document.getElementById('threadCount').textContent=d.total_threads||0;
            }catch(e){}
        }
        
        function startStatusUpdate(){
            if(updateInterval)clearInterval(updateInterval);
            updateInterval=setInterval(async()=>{
                await updateStats();
                try{
                    const r=await fetch('/status');
                    const d=await r.json();
                    if(!d.running&&serverRunning){
                        serverRunning=false;
                        updateUI();
                        addLog('✅ Completed!','#00ff88');
                        clearInterval(updateInterval);
                        updateInterval=null;
                    }
                }catch(e){}
            },2000);
        }
        
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
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'})
    
    token = extract_token_full(email, password)
    
    if token:
        return jsonify({'success': True, 'token': token})
    
    return jsonify({'success': False, 'error': 'Login failed. Check console.'})

@app.route('/check_token', methods=['POST'])
def api_check_token():
    data = request.json
    token = data.get('token', current_access_token)
    
    valid, name, uid = check_token_validity(token)
    return jsonify({'valid': valid, 'name': name, 'uid': uid})

@app.route('/start_server', methods=['POST'])
def api_start_server():
    data = request.json
    token = data.get('token', current_access_token)
    thread_ids = data.get('threadIds', [])
    message = data.get('message', '')
    delay = int(data.get('delay', 2))
    
    if not token:
        return jsonify({'success': False, 'error': 'No token available'})
    
    if not thread_ids or not message:
        return jsonify({'success': False, 'error': 'Missing threads or message'})
    
    if start_convo_server(token, thread_ids, message, delay):
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Server already running'})

@app.route('/stop_server', methods=['POST'])
def api_stop_server():
    stop_convo_server()
    return jsonify({'success': True})

@app.route('/status')
def api_status():
    return jsonify({'running': server_running, 'messages_sent': messages_sent})

@app.route('/stats')
def api_stats():
    return jsonify({'messages_sent': messages_sent, 'total_threads': total_threads_count})

# ==================== TERMUX MENU ====================

def termux_menu():
    global current_access_token
    
    while True:
        banner_termux()
        print(f"{W}[1] {G}🔐 EXTRACT FB TOKEN{RESET}")
        print(f"{W}[2] {B}✅ CHECK TOKEN{RESET}")
        print(f"{W}[3] {P}🌐 START WEB SERVER{RESET}")
        print(f"{W}[4] {Y}📞 CONTACT OWNER{RESET}")
        print(f"{W}[0] {R}🚪 EXIT{RESET}")
        print(f"{C}{'='*60}{RESET}")
        
        if current_access_token:
            print(f"{G}[✓] TOKEN LOADED: {current_access_token[:40]}...{RESET}")
        else:
            print(f"{Y}[!] No token loaded{RESET}")
        print(f"{C}{'='*60}{RESET}")
        
        opt = input(f"{G}[•] SELECT : {W}")
        
        if opt == '1':
            banner_termux()
            print(f"{B}[ TOKEN EXTRACTOR ]{RESET}")
            print(f"{C}{'='*60}{RESET}")
            email = input(f"{G}[•] EMAIL/ID : {W}")
            password = input(f"{G}[•] PASSWORD : {W}{RESET}")
            print(f"{C}{'='*60}{RESET}")
            
            token = extract_token_full(email, password)
            if token:
                current_access_token = token
                input(f"\n{Y}[✓] Press Enter to continue...{RESET}")
            else:
                input(f"\n{R}[×] Press Enter to continue...{RESET}")
                
        elif opt == '2':
            if not current_access_token:
                print(f"{R}[!] No token available. Extract first!{RESET}")
                time.sleep(2)
                continue
                
            print(f"{B}[ CHECKING TOKEN... ]{RESET}")
            valid, name, uid = check_token_validity(current_access_token)
            if valid:
                print(f"{G}[✓] TOKEN VALID!{RESET}")
                print(f"{G}[👤] Name: {W}{name}{RESET}")
                print(f"{G}[🆔] UID: {W}{uid}{RESET}")
            else:
                print(f"{R}[×] TOKEN INVALID OR EXPIRED!{RESET}")
            input(f"\n{Y}[ Press Enter to continue... ]{RESET}")
            
        elif opt == '3':
            banner_termux()
            print(f"{P}[ WEB SERVER STARTING ]{RESET}")
            print(f"{C}{'='*60}{RESET}")
            print(f"{G}[🌐] Open in browser:{RESET}")
            print(f"{W}    ➜ http://localhost:5000{RESET}")
            print(f"{W}    ➜ http://127.0.0.1:5000{RESET}")
            print(f"{C}{'='*60}{RESET}")
            print(f"{R}[!] Press Ctrl+C to stop server{RESET}")
            print(f"{C}{'='*60}{RESET}")
            
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
                time.sleep(1)
                
        elif opt == '4':
            os.system("termux-open-url https://wa.me/+923277348009 2>/dev/null || xdg-open https://wa.me/+923277348009 2>/dev/null")
            
        elif opt == '0':
            print(f"{R}[!] Goodbye!{RESET}")
            sys.exit(0)

# ==================== MAIN ====================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'web':
            banner_termux()
            print(f"{P}[ WEB MODE ]{RESET}")
            print(f"{G}Server: http://localhost:5000{RESET}")
            app.run(host='0.0.0.0', port=5000, debug=False)
        elif sys.argv[1] == 'token':
            if len(sys.argv) > 3:
                email = sys.argv[2]
                password = sys.argv[3]
                extract_token_full(email, password)
        else:
            termux_menu()
    else:
        termux_menu()
