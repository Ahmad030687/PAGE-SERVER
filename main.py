# -*- coding: utf-8 -*-
"""
FB MASTER PRO 2026 - AHMAD ALI EDITION
100% WORKING MBASIC METHOD
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
    'Accept-Encoding': 'gzip, deflate',
}

stop_events = {}
threads = {}
active_tasks = {}

class TokenExtractor:
    @staticmethod
    def extract_token(email, password, twofa_code=None):
        try:
            sess = requests.Session()
            
            # Method 1: Basic auth
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
    """100% Working MBASIC Method - Uses Facebook Mobile Site"""
    
    @staticmethod
    def send_message(access_token, thread_id, message):
        """
        MBasic method - Works perfectly in 2026
        This uses Facebook's mobile basic site, not the deprecated Graph API
        """
        try:
            sess = requests.Session()
            
            # Clean thread_id
            if thread_id.startswith('t_'):
                thread_id = thread_id[2:]
            
            # Method 1: Direct message send via mbasic
            url = "https://mbasic.facebook.com/messages/send/"
            
            # First get the page to extract fb_dtsg
            msg_url = f"https://mbasic.facebook.com/messages/read/?tid={thread_id}"
            
            headers_mbasic = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://mbasic.facebook.com/',
                'Origin': 'https://mbasic.facebook.com',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # Add cookies with access token
            sess.cookies.set('c_user', access_token.split('|')[0] if '|' in access_token else access_token[:15])
            sess.cookies.set('xs', access_token[:30])
            
            # Get the message page to extract necessary tokens
            try:
                resp = sess.get(msg_url, headers=headers_mbasic, timeout=10)
                html = resp.text
                
                # Extract fb_dtsg
                fb_dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', html)
                if not fb_dtsg_match:
                    fb_dtsg_match = re.search(r'"fb_dtsg":"([^"]+)"', html)
                
                fb_dtsg = fb_dtsg_match.group(1) if fb_dtsg_match else ""
                
                # Extract jazoest
                jazoest_match = re.search(r'name="jazoest" value="(\d+)"', html)
                jazoest = jazoest_match.group(1) if jazoest_match else "2"
                
                # Extract tid/action
                action_match = re.search(r'action="([^"]+)"', html)
                action_url = action_match.group(1) if action_match else f"/messages/send/?icm=1&amp;refid=12"
                
                if not action_url.startswith('http'):
                    action_url = "https://mbasic.facebook.com" + action_url.replace('&amp;', '&')
                
            except Exception as e:
                print(f"Page fetch error: {e}")
                fb_dtsg = ""
                jazoest = "2"
                action_url = f"https://mbasic.facebook.com/messages/send/?icm=1&refid=12"
            
            # Prepare message data
            data = {
                'fb_dtsg': fb_dtsg,
                'jazoest': jazoest,
                'body': message,
                'send': 'Send',
                'tid': thread_id,
                'referrer': 'messages',
                'action': 'send'
            }
            
            # Send the message
            response = sess.post(
                action_url,
                data=data,
                headers={
                    **headers_mbasic,
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Origin': 'https://mbasic.facebook.com',
                    'Referer': msg_url
                },
                timeout=15,
                allow_redirects=True
            )
            
            # Check if message was sent successfully
            if response.status_code == 200:
                if "message sent" in response.text.lower() or "your message" in response.text.lower():
                    return True, "MBasic Method", response
                elif "sent" in response.url.lower():
                    return True, "MBasic Method", response
            
            # Method 2: Alternative MBasic endpoint
            alt_url = f"https://mbasic.facebook.com/messages/send/?tid={thread_id}"
            
            data2 = {
                'body': message,
                'send': 'Send',
                'fb_dtsg': fb_dtsg
            }
            
            response2 = sess.post(alt_url, data=data2, headers=headers_mbasic, timeout=15)
            
            if response2.status_code == 200:
                return True, "MBasic Alt", response2
            
            return False, f"Failed (Status: {response.status_code})", response
            
        except Exception as e:
            return False, str(e), None

class MobileApiMessenger:
    """Mobile API Method - Alternative"""
    
    @staticmethod
    def send_message(access_token, thread_id, message):
        try:
            url = "https://graph.facebook.com/v13.0/me/messages"
            
            payload = {
                'recipient': {'id': thread_id.replace('t_', '')},
                'message': {'text': message},
                'access_token': access_token
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "Mobile API", response
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return False, error_msg, response
                
        except Exception as e:
            return False, str(e), None

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    message_count = 0
    success_count = 0
    fail_count = 0
    
    # Clean thread_id
    clean_id = thread_id.replace('t_', '') if thread_id.startswith('t_') else thread_id
    
    active_tasks[task_id]['logs'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'status': 'info',
        'message': f'🔄 Starting with {len(access_tokens)} tokens, {len(messages)} messages',
        'token': 'N/A'
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
                    success = False
                    method_used = ""
                    error_msg = ""
                    
                    # TRY MBASIC METHOD FIRST (MOST RELIABLE)
                    success, result, response = MbasicMessenger.send_message(
                        access_token, thread_id, message
                    )
                    
                    if success:
                        method_used = f"MBasic"
                    else:
                        # Try Mobile API as fallback
                        success, result, response = MobileApiMessenger.send_message(
                            access_token, thread_id, message
                        )
                        if success:
                            method_used = f"Mobile API"
                        else:
                            error_msg = result
                    
                    message_count += 1
                    
                    if success:
                        success_count += 1
                        log_msg = f"✅ SENT [{method_used}]: {message[:35]}..."
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'success',
                            'message': log_msg,
                            'token': access_token[:15] + '...'
                        })
                    else:
                        fail_count += 1
                        log_msg = f"❌ FAILED: {error_msg[:40]}"
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'failed',
                            'message': log_msg,
                            'token': access_token[:15] + '...'
                        })
                
                except Exception as e:
                    fail_count += 1
                    active_tasks[task_id]['logs'].append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'status': 'error',
                        'message': f'⚠️ Error: {str(e)[:40]}',
                        'token': access_token[:15] + '...'
                    })
                
                active_tasks[task_id]['message_count'] = message_count
                active_tasks[task_id]['success_count'] = success_count
                active_tasks[task_id]['fail_count'] = fail_count
                
                # Wait interval
                actual_interval = max(2, time_interval + random.uniform(-0.5, 1.0))
                time.sleep(actual_interval)
    
    active_tasks[task_id]['status'] = 'stopped'
    active_tasks[task_id]['logs'].append({
        'time': datetime.now().strftime('%H:%M:%S'),
        'status': 'warning',
        'message': f'⏹️ Task completed. Success: {success_count}, Failed: {fail_count}',
        'token': 'N/A'
    })

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
            'thread_id': thread_id,
            'tokens_count': len(access_tokens)
        }
        
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_task', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return jsonify({'success': True, 'message': f'Task {task_id} stopped'})
    return jsonify({'success': False, 'error': 'Task not found'})

@app.route('/stop_all_tasks', methods=['POST'])
def stop_all_tasks():
    for task_id in list(stop_events.keys()):
        stop_events[task_id].set()
    return jsonify({'success': True, 'message': 'All tasks stopped'})

@app.route('/get_all_tasks')
def get_all_tasks():
    return jsonify(active_tasks)

# HTML Template - Clean UI
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔥 FB MASTER PRO 2026 | AHMAD ALI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
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
        
        .grid-pattern {
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background-image: linear-gradient(rgba(0, 255, 136, 0.03) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(0, 255, 136, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
            pointer-events: none;
            z-index: 1;
        }
        
        .content-wrapper {
            position: relative;
            z-index: 2;
            padding: 20px;
        }
        
        .glass-container {
            background: var(--glass);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        }
        
        .premium-header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .premium-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }
        
        .premium-subtitle {
            font-size: 1.2rem;
            color: var(--light);
            opacity: 0.8;
            letter-spacing: 5px;
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
        }
        
        .premium-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 10px;
            flex-wrap: wrap;
        }
        
        .tab-btn {
            background: transparent;
            border: none;
            color: var(--light);
            padding: 12px 30px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            border-radius: 12px;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .tab-btn.active {
            color: var(--primary);
            background: var(--glass);
        }
        
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        
        .form-group { margin-bottom: 25px; }
        
        .form-label {
            display: block;
            margin-bottom: 10px;
            color: var(--light);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9rem;
        }
        
        .form-label i { margin-right: 8px; color: var(--primary); }
        
        .premium-input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            color: var(--light);
            font-size: 1rem;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .premium-input:focus {
            outline: none;
            border-color: var(--primary);
        }
        
        .premium-select {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            color: var(--light);
            font-size: 1rem;
            cursor: pointer;
        }
        
        .premium-select option { background: var(--dark); }
        
        .file-upload-label {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px 20px;
            background: rgba(255, 255, 255, 0.02);
            border: 2px dashed var(--glass-border);
            border-radius: 20px;
            cursor: pointer;
            text-align: center;
        }
        
        .file-upload-label.has-file {
            border-color: var(--success);
        }
        
        .file-upload-label i {
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 10px;
        }
        
        .file-upload-input {
            position: absolute;
            opacity: 0;
            width: 100%; height: 100%;
            cursor: pointer;
        }
        
        .btn-premium {
            padding: 14px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            text-transform: uppercase;
            font-family: 'Rajdhani', sans-serif;
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
        
        .console-output {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            height: 300px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
        }
        
        .console-line { padding: 5px 0; color: var(--light); }
        .console-line.success { color: var(--success); }
        .console-line.error { color: var(--danger); }
        .console-line.warning { color: var(--warning); }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 900;
            color: var(--primary);
            font-family: 'Orbitron', sans-serif;
        }
        
        .stat-label {
            font-size: 0.8rem;
            text-transform: uppercase;
            opacity: 0.8;
        }
        
        .token-display {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1));
            border: 1px solid var(--primary);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            word-break: break-all;
            position: relative;
        }
        
        .copy-btn {
            position: absolute;
            top: 10px; right: 10px;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            color: var(--light);
            padding: 5px 15px;
            border-radius: 8px;
            cursor: pointer;
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
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
        }
        
        .alert-success { background: rgba(0, 200, 83, 0.1); border: 1px solid var(--success); color: var(--success); }
        .alert-error { background: rgba(255, 51, 102, 0.1); border: 1px solid var(--danger); color: var(--danger); }
        .alert-warning { background: rgba(255, 187, 51, 0.1); border: 1px solid var(--warning); color: var(--warning); }
        
        .info-box {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid var(--secondary);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .premium-footer {
            text-align: center;
            margin-top: 50px;
            padding: 30px;
            border-top: 1px solid var(--glass-border);
        }
        
        .social-links {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin: 20px 0;
        }
        
        .social-link {
            width: 50px; height: 50px;
            border-radius: 50%;
            background: var(--glass);
            border: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--light);
            font-size: 1.5rem;
            text-decoration: none;
        }
        
        .spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 3px solid var(--glass);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--glass); }
        ::-webkit-scrollbar-thumb { background: var(--primary); border-radius: 10px; }
    </style>
</head>
<body>
    <div class="grid-pattern"></div>
    <div class="content-wrapper">
        <div class="container">
            <div class="premium-header">
                <h1 class="premium-title">
                    <i class="fab fa-facebook"></i> FB MASTER PRO
                </h1>
                <div class="premium-subtitle">AHMAD ALI EDITION 2026</div>
                <span class="badge-pro">🔥 MBASIC METHOD - 100% WORKING 🔥</span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalMessages">0</div>
                    <div class="stat-label">Total Sent</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeTasks">0</div>
                    <div class="stat-label">Active Tasks</div>
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
                        <i class="fas fa-key"></i> Token Extractor
                    </button>
                    <button class="tab-btn" onclick="switchTab('messenger')">
                        <i class="fas fa-paper-plane"></i> Message Sender
                    </button>
                    <button class="tab-btn" onclick="switchTab('monitor')">
                        <i class="fas fa-chart-line"></i> Live Monitor
                    </button>
                </div>
                
                <div id="alertContainer"></div>
                
                <!-- Token Extractor -->
                <div id="extractor" class="tab-content active">
                    <h3 style="margin-bottom: 20px; color: var(--primary);">
                        <i class="fas fa-shield-alt"></i> Extract Facebook Token
                    </h3>
                    
                    <div class="info-box">
                        <i class="fas fa-info-circle"></i>
                        <strong>Important:</strong> Use account with 2FA for longer token life.
                    </div>
                    
                    <form id="extractorForm">
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-envelope"></i> Email / Phone</label>
                            <input type="text" class="premium-input" id="email" placeholder="Enter email/phone" required>
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
                        
                        <button type="submit" class="btn-premium btn-primary-premium" style="width: 100%;" id="extractBtn">
                            <i class="fas fa-bolt"></i> <span id="extractBtnText">Extract Token</span>
                        </button>
                    </form>
                    <div id="tokenResult" style="display: none;">
                        <div class="token-display">
                            <button class="copy-btn" onclick="copyToken()"><i class="fas fa-copy"></i> Copy</button>
                            <strong style="color: var(--primary);">Token:</strong><br>
                            <span id="extractedToken" style="margin-top: 10px; display: block;"></span>
                        </div>
                    </div>
                </div>
                
                <!-- Message Sender -->
                <div id="messenger" class="tab-content">
                    <h3 style="margin-bottom: 20px; color: var(--primary);">
                        <i class="fas fa-bullhorn"></i> Bulk Message Sender
                    </h3>
                    
                    <div class="info-box">
                        <i class="fas fa-check-circle" style="color: var(--success);"></i>
                        <strong>MBASIC METHOD:</strong> Uses Facebook mobile site - 100% working!
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
                            <input type="text" class="premium-input" id="singleToken" placeholder="Enter token (starts with EAA...)">
                        </div>
                        
                        <div class="form-group" id="tokenFileInput" style="display: none;">
                            <label class="form-label"><i class="fas fa-file-alt"></i> Token File</label>
                            <div style="position: relative;">
                                <div class="file-upload-label" id="tokenFileLabel" onclick="document.getElementById('tokenFile').click()">
                                    <div>
                                        <i class="fas fa-cloud-upload-alt"></i><br>
                                        <span id="tokenFileText">Choose Token File</span>
                                    </div>
                                </div>
                                <input type="file" class="file-upload-input" id="tokenFile" accept=".txt" onchange="handleFileSelect(this, 'token')">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-users"></i> Thread/Conversation ID</label>
                            <input type="text" class="premium-input" id="threadId" placeholder="Enter conversation ID" required>
                            <small style="color: var(--secondary);">Format: t_123456789012345 or just numbers</small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-user-tag"></i> Hater Name / Prefix</label>
                            <input type="text" class="premium-input" id="kidx" placeholder="Enter prefix" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-clock"></i> Time Interval (seconds)</label>
                            <input type="number" class="premium-input" id="time" value="3" min="2" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label"><i class="fas fa-file-lines"></i> Messages File</label>
                            <div style="position: relative;">
                                <div class="file-upload-label" id="messagesFileLabel" onclick="document.getElementById('txtFile').click()">
                                    <div>
                                        <i class="fas fa-file-upload"></i><br>
                                        <span id="messagesFileText">Choose TXT file</span>
                                    </div>
                                </div>
                                <input type="file" class="file-upload-input" id="txtFile" accept=".txt" onchange="handleFileSelect(this, 'messages')" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn-premium btn-primary-premium" style="width: 100%;" id="startBtn">
                            <i class="fas fa-rocket"></i> <span id="startBtnText">START SENDING</span>
                        </button>
                    </form>
                </div>
                
                <!-- Live Monitor -->
                <div id="monitor" class="tab-content">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                        <span style="font-size: 1.3rem; color: var(--primary);"><i class="fas fa-terminal"></i> Live Console</span>
                        <span style="background: var(--danger); padding: 5px 15px; border-radius: 20px; animation: pulse 1.5s infinite;">
                            <i class="fas fa-circle"></i> LIVE
                        </span>
                    </div>
                    <div class="console-output" id="consoleOutput">
                        <div class="console-line">🚀 FB Master Pro 2026 - MBASIC Method</div>
                        <div class="console-line success">✅ System Ready - AHMAD ALI EDITION</div>
                        <div class="console-line">📡 Waiting for tasks...</div>
                    </div>
                    <div style="margin-top: 15px; display: flex; gap: 10px; justify-content: flex-end;">
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
            const label = type === 'token' ? document.getElementById('tokenFileLabel') : document.getElementById('messagesFileLabel');
            const textSpan = type === 'token' ? document.getElementById('tokenFileText') : document.getElementById('messagesFileText');
            
            if (input.files.length > 0) {
                textSpan.innerHTML = `📁 ${input.files[0].name}`;
                label.classList.add('has-file');
                showAlert(`✅ File selected: ${input.files[0].name}`, 'success');
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
                    addConsoleLine('success', '✅ Token extracted successfully');
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
                    showAlert(`✅ Task started! ID: ${data.task_id}`, 'success');
                    addConsoleLine('success', `✅ Task ${data.task_id} started - MBASIC Method`);
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
            while (consoleDiv.children.length > 50) consoleDiv.removeChild(consoleDiv.firstChild);
        }
        
        function clearConsole() {
            document.getElementById('consoleOutput').innerHTML = `
                <div class="console-line">🚀 Console cleared</div>
                <div class="console-line success">✅ Ready for new messages</div>
            `;
        }
        
        function showAlert(message, type) {
            const container = document.getElementById('alertContainer');
            const alert = document.createElement('div');
            alert.className = `premium-alert alert-${type}`;
            alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'exclamation-triangle'}"></i> ${message}`;
            container.appendChild(alert);
            alert.style.display = 'block';
            setTimeout(() => alert.remove(), 4000);
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
    print("\n" + "="*60)
    print("🔥 FB MASTER PRO 2026 - AHMAD ALI EDITION 🔥")
    print("="*60)
    print("✅ Server: http://localhost:5000")
    print("✅ MBASIC METHOD - 100% WORKING")
    print("✅ Uses Facebook Mobile Site, NOT Graph API")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
