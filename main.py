# -*- coding: utf-8 -*-
"""
FB MASTER PRO 2026 - AHMAD ALI EDITION
Fixed Version with Token Validation & Proper Error Messages
"""

from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import uuid
import json
import re
import os
from datetime import datetime

app = Flask(__name__)
app.debug = False
app.secret_key = os.urandom(24)

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
}

stop_events = {}
threads = {}
active_tasks = {}

class TokenValidator:
    @staticmethod
    def validate_token(access_token):
        """Check if token is valid and has required permissions"""
        try:
            # Check token info
            url = f"https://graph.facebook.com/me"
            params = {
                'access_token': access_token,
                'fields': 'id,name'
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return True, data.get('name', 'User')
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Invalid token')
                return False, error_msg
        except Exception as e:
            return False, str(e)

class TokenExtractor:
    @staticmethod
    def extract_token(email, password, twofa_code=None):
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
            
            if twofa_code:
                data['twofactor_code'] = twofa_code
                data['method'] = 'auth.login_twofactor'
            
            res = sess.post("https://graph.facebook.com/auth/login", data=data, headers=head)
            
            try:
                res_json = res.json()
            except:
                return {"success": False, "error": "Invalid server response"}
            
            if "error" in res_json:
                error_msg = res_json['error'].get('message', '')
                if "two-factor" in error_msg.lower() or "login_approval" in error_msg.lower():
                    return {"success": False, "requires_2fa": True, "error": "2FA Required"}
                else:
                    return {"success": False, "error": error_msg}
            
            if "access_token" in res_json:
                return {"success": True, "token": res_json["access_token"]}
            elif "session_key" in res_json:
                return {"success": True, "token": res_json["session_key"]}
            else:
                return TokenExtractor.alternative_extraction(email, password, twofa_code)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def alternative_extraction(email, password, twofa_code=None):
        try:
            sess = requests.Session()
            url = "https://b-api.facebook.com/method/auth.login"
            
            params = {
                'access_token': '350685531728|62f8ce9f74b12f84c123cc23437a4a32',
                'format': 'json',
                'sdk_version': '2',
                'email': email,
                'password': password,
                'generate_session_cookies': '1',
                'generate_machine_id': '1',
                'credentials_type': 'password',
                'source': 'login',
                'machine_id': str(uuid.uuid4()),
                'locale': 'en_US',
                'client_country_code': 'US',
                'method': 'auth.login',
                'fb_api_req_friendly_name': 'authenticate',
                'cpl': 'true'
            }
            
            if twofa_code:
                params['twofactor_code'] = twofa_code
                params['method'] = 'auth.login_twofactor'
            
            headers_mobile = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
                'X-FB-Connection-Type': 'WIFI',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            res = sess.post(url, data=params, headers=headers_mobile)
            
            try:
                res_json = res.json()
            except:
                return {"success": False, "error": "Failed to parse response"}
            
            if "access_token" in res_json:
                return {"success": True, "token": res_json["access_token"]}
            elif "session_key" in res_json:
                return {"success": True, "token": res_json["session_key"]}
            elif "error" in res_json:
                error_msg = res_json['error'].get('message', str(res_json['error']))
                if "two-factor" in error_msg.lower():
                    return {"success": False, "requires_2fa": True, "error": "2FA Required"}
                return {"success": False, "error": error_msg}
            
            return {"success": False, "error": "Unknown error occurred"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

class FacebookMessenger:
    @staticmethod
    def send_with_page_token(access_token, thread_id, message):
        """Method for Page Access Token (EAA...)"""
        try:
            url = f"https://graph.facebook.com/v17.0/{thread_id}/messages"
            params = {
                'access_token': access_token,
                'message': message
            }
            response = requests.post(url, data=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "Page Token", response
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return False, error_msg, response
        except Exception as e:
            return False, str(e), None

    @staticmethod
    def send_with_user_token(access_token, thread_id, message):
        """Method for User Access Token (EAA...)"""
        try:
            # Using v19.0 which is more stable
            url = f"https://graph.facebook.com/v19.0/{thread_id}/messages"
            params = {
                'access_token': access_token,
                'message': message
            }
            response = requests.post(url, data=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "User Token", response
            else:
                error_data = response.json() if response.text else {}
                error_msg = error_data.get('error', {}).get('message', f'HTTP {response.status_code}')
                return False, error_msg, response
        except Exception as e:
            return False, str(e), None

    @staticmethod
    def send_legacy_method(access_token, thread_id, message):
        """Legacy method for older tokens"""
        try:
            # Try with t_ prefix
            clean_id = thread_id.replace('t_', '')
            url = f"https://graph.facebook.com/v15.0/t_{clean_id}"
            params = {
                'access_token': access_token,
                'message': message
            }
            response = requests.post(url, data=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True, "Legacy", response
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
    clean_thread_id = thread_id.replace('t_', '') if thread_id.startswith('t_') else thread_id
    
    # First validate all tokens
    valid_tokens = []
    for token in access_tokens:
        token = token.strip()
        if token:
            is_valid, info = TokenValidator.validate_token(token)
            if is_valid:
                valid_tokens.append(token)
                active_tasks[task_id]['logs'].append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'status': 'success',
                    'message': f'✅ Token valid: {info}',
                    'token': token[:15] + '...'
                })
            else:
                active_tasks[task_id]['logs'].append({
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'status': 'error',
                    'message': f'❌ Invalid token: {info}',
                    'token': token[:15] + '...'
                })
    
    if not valid_tokens:
        active_tasks[task_id]['status'] = 'stopped'
        active_tasks[task_id]['logs'].append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'status': 'error',
            'message': '❌ No valid tokens found!',
            'token': 'N/A'
        })
        return
    
    active_tasks[task_id]['valid_tokens'] = len(valid_tokens)
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
                
            for access_token in valid_tokens:
                if stop_event.is_set():
                    break
                    
                try:
                    message = f"{mn} {message1}"
                    success = False
                    method_used = ""
                    error_msg = ""
                    
                    # Try different methods based on token type
                    
                    # Method 1: Page/User Token v19
                    success, result, response = FacebookMessenger.send_with_user_token(
                        access_token, thread_id, message
                    )
                    if success:
                        method_used = f"v19.0 ({result})"
                    else:
                        # Method 2: Page Token v17
                        success, result, response = FacebookMessenger.send_with_page_token(
                            access_token, thread_id, message
                        )
                        if success:
                            method_used = f"v17.0 ({result})"
                        else:
                            # Method 3: Legacy method
                            success, result, response = FacebookMessenger.send_legacy_method(
                                access_token, clean_thread_id, message
                            )
                            if success:
                                method_used = f"Legacy ({result})"
                            else:
                                error_msg = result
                    
                    message_count += 1
                    
                    if success:
                        success_count += 1
                        log_msg = f"✅ Sent [{method_used}]: {message[:30]}..."
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'success',
                            'message': log_msg,
                            'token': access_token[:15] + '...'
                        })
                    else:
                        fail_count += 1
                        
                        # Parse error for better message
                        if "permission" in error_msg.lower():
                            error_msg = "No permission (need pages_messaging)"
                        elif "expired" in error_msg.lower():
                            error_msg = "Token expired"
                        elif "invalid" in error_msg.lower():
                            error_msg = "Invalid token"
                        
                        log_msg = f"❌ Failed: {error_msg[:40]}"
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
                
                actual_interval = time_interval + random.uniform(-0.3, 0.7)
                time.sleep(max(0.5, actual_interval))
    
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

@app.route('/validate_token', methods=['POST'])
def validate_token():
    token = request.form.get('token', '').strip()
    if not token:
        return jsonify({'valid': False, 'message': 'Token required'})
    
    is_valid, info = TokenValidator.validate_token(token)
    return jsonify({'valid': is_valid, 'message': info})

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
        
        if not thread_id:
            return jsonify({'success': False, 'error': 'Thread ID is required'})
        
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        stop_events[task_id] = Event()
        active_tasks[task_id] = {
            'status': 'running',
            'message_count': 0,
            'success_count': 0,
            'fail_count': 0,
            'valid_tokens': 0,
            'logs': [],
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'thread_id': thread_id,
            'tokens_count': len(access_tokens),
            'messages_count': len(messages)
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
        if task_id in active_tasks:
            active_tasks[task_id]['status'] = 'stopped'
        return jsonify({'success': True, 'message': f'Task {task_id} stopped'})
    return jsonify({'success': False, 'error': 'Task not found'})

@app.route('/stop_all_tasks', methods=['POST'])
def stop_all_tasks():
    for task_id in list(stop_events.keys()):
        stop_events[task_id].set()
        if task_id in active_tasks:
            active_tasks[task_id]['status'] = 'stopped'
    return jsonify({'success': True, 'message': 'All tasks stopped'})

@app.route('/get_all_tasks')
def get_all_tasks():
    return jsonify(active_tasks)

# HTML Template - Same premium UI but with added validation
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
            --glow: 0 0 20px rgba(0, 255, 136, 0.3);
        }
        
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
            min-height: 100vh;
            color: var(--light);
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 40% 20%, rgba(255, 51, 102, 0.08) 0%, transparent 50%);
            animation: bgPulse 15s ease-in-out infinite;
            pointer-events: none;
            z-index: 0;
        }
        
        @keyframes bgPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
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
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        }
        
        .glass-container:hover {
            border-color: rgba(0, 255, 136, 0.3);
            box-shadow: var(--glow);
        }
        
        .premium-header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .premium-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 3.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 30px rgba(0, 255, 136, 0.5);
            letter-spacing: 2px;
            margin-bottom: 10px;
            animation: titleGlow 2s ease-in-out infinite;
        }
        
        @keyframes titleGlow {
            0%, 100% { filter: brightness(1); }
            50% { filter: brightness(1.2); }
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
            font-size: 0.9rem;
            letter-spacing: 2px;
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
            position: relative;
            transition: all 0.3s ease;
            border-radius: 12px;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .tab-btn i { margin-right: 8px; }
        
        .tab-btn:hover { background: var(--glass); }
        
        .tab-btn.active {
            color: var(--primary);
            background: var(--glass);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        }
        
        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -11px; left: 0;
            width: 100%; height: 2px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            box-shadow: 0 0 10px var(--primary);
        }
        
        .tab-content { display: none; }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .form-group { margin-bottom: 25px; }
        
        .form-label {
            display: block;
            margin-bottom: 10px;
            color: var(--light);
            font-weight: 600;
            letter-spacing: 1px;
            text-transform: uppercase;
            font-size: 0.9rem;
        }
        
        .form-label i {
            margin-right: 8px;
            color: var(--primary);
        }
        
        .premium-input {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            color: var(--light);
            font-size: 1rem;
            transition: all 0.3s ease;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .premium-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
            background: rgba(255, 255, 255, 0.05);
        }
        
        .premium-input::placeholder { color: rgba(255, 255, 255, 0.4); }
        
        .premium-select {
            width: 100%;
            padding: 14px 18px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            color: var(--light);
            font-size: 1rem;
            cursor: pointer;
            font-family: 'Rajdhani', sans-serif;
        }
        
        .premium-select option {
            background: var(--dark);
            color: var(--light);
        }
        
        .file-upload-wrapper { position: relative; }
        
        .file-upload-label {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 30px 20px;
            background: rgba(255, 255, 255, 0.02);
            border: 2px dashed var(--glass-border);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }
        
        .file-upload-label:hover {
            border-color: var(--primary);
            background: rgba(0, 255, 136, 0.05);
        }
        
        .file-upload-label i {
            font-size: 2.5rem;
            color: var(--primary);
            margin-bottom: 10px;
        }
        
        .file-upload-label.has-file {
            border-color: var(--success);
            background: rgba(0, 200, 83, 0.05);
        }
        
        .file-upload-label.has-file i { color: var(--success); }
        
        .file-upload-input {
            position: absolute;
            opacity: 0;
            width: 100%; height: 100%;
            top: 0; left: 0;
            cursor: pointer;
        }
        
        .btn-premium {
            padding: 14px 30px;
            border: none;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            font-family: 'Rajdhani', sans-serif;
            position: relative;
            overflow: hidden;
        }
        
        .btn-premium::before {
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
        }
        
        .btn-premium:hover::before { left: 100%; }
        
        .btn-primary-premium {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: var(--dark);
            box-shadow: 0 5px 20px rgba(0, 255, 136, 0.3);
        }
        
        .btn-primary-premium:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0, 255, 136, 0.4);
        }
        
        .btn-danger-premium {
            background: linear-gradient(135deg, var(--danger), #ff6699);
            color: var(--light);
            box-shadow: 0 5px 20px rgba(255, 51, 102, 0.3);
        }
        
        .btn-danger-premium:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(255, 51, 102, 0.4);
        }
        
        .btn-warning-premium {
            background: linear-gradient(135deg, var(--warning), #ffdd66);
            color: var(--dark);
        }
        
        .btn-success-premium {
            background: linear-gradient(135deg, var(--success), #69f0ae);
            color: var(--dark);
        }
        
        .live-monitor { margin-top: 30px; }
        
        .monitor-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .monitor-title {
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--primary);
        }
        
        .live-badge {
            background: var(--danger);
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 700;
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
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
        
        .console-line {
            padding: 5px 0;
            border-bottom: 1px solid var(--glass-border);
            color: var(--light);
        }
        
        .console-line.success { color: var(--success); }
        .console-line.error { color: var(--danger); }
        .console-line.warning { color: var(--warning); }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: var(--glass);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 20px;
            text-align: center;
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            border-color: var(--primary);
            transform: translateY(-5px);
        }
        
        .stat-value {
            font-size: 2.5rem;
            font-weight: 900;
            color: var(--primary);
            font-family: 'Orbitron', sans-serif;
        }
        
        .stat-label {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 2px;
            opacity: 0.8;
            margin-top: 5px;
        }
        
        .token-display {
            background: linear-gradient(135deg, rgba(0, 255, 136, 0.1), rgba(0, 212, 255, 0.1));
            border: 1px solid var(--primary);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            word-break: break-all;
            font-family: 'Courier New', monospace;
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
            transition: all 0.3s ease;
        }
        
        .copy-btn:hover {
            background: var(--primary);
            color: var(--dark);
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
            transition: all 0.3s ease;
            text-decoration: none;
        }
        
        .social-link:hover {
            background: var(--primary);
            color: var(--dark);
            transform: translateY(-5px);
            box-shadow: var(--glow);
        }
        
        .twofa-section {
            margin-top: 15px;
            padding: 15px;
            background: rgba(255, 187, 51, 0.1);
            border: 1px solid var(--warning);
            border-radius: 12px;
            display: none;
        }
        
        .twofa-section.show {
            display: block;
            animation: slideDown 0.3s ease;
        }
        
        .token-validation-result {
            margin-top: 10px;
            padding: 10px;
            border-radius: 8px;
            display: none;
        }
        
        .token-validation-result.valid {
            background: rgba(0, 200, 83, 0.1);
            border: 1px solid var(--success);
            color: var(--success);
        }
        
        .token-validation-result.invalid {
            background: rgba(255, 51, 102, 0.1);
            border: 1px solid var(--danger);
            color: var(--danger);
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .premium-alert {
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
            animation: slideDown 0.3s ease;
        }
        
        .alert-success {
            background: rgba(0, 200, 83, 0.1);
            border: 1px solid var(--success);
            color: var(--success);
        }
        
        .alert-error {
            background: rgba(255, 51, 102, 0.1);
            border: 1px solid var(--danger);
            color: var(--danger);
        }
        
        .alert-info {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid var(--secondary);
            color: var(--secondary);
        }
        
        .alert-warning {
            background: rgba(255, 187, 51, 0.1);
            border: 1px solid var(--warning);
            color: var(--warning);
        }
        
        .spinner {
            display: inline-block;
            width: 20px; height: 20px;
            border: 3px solid var(--glass);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .info-box {
            background: rgba(0, 212, 255, 0.1);
            border: 1px solid var(--secondary);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .info-box i {
            color: var(--secondary);
            margin-right: 10px;
        }
        
        @media (max-width: 768px) {
            .premium-title { font-size: 2rem; }
            .premium-tabs { flex-direction: column; }
            .glass-container { padding: 20px; }
        }
        
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--glass); border-radius: 10px; }
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 10px;
        }
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
                <div class="premium-subtitle">AHMAD ALI EDITION</div>
                <span class="badge-pro">🔥 PREMIUM 2026 🔥</span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="totalMessages">0</div>
                    <div class="stat-label">Total Messages</div>
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
                    <button class="tab-btn" onclick="switchTab('tasks')">
                        <i class="fas fa-tasks"></i> Task Manager
                    </button>
                </div>
                
                <div id="alertContainer"></div>
                
                <!-- Token Extractor Tab -->
                <div id="extractor" class="tab-content active">
                    <h3 style="margin-bottom: 20px; color: var(--primary);">
                        <i class="fas fa-shield-alt"></i> Extract Facebook Token
                    </h3>
                    
                    <div class="info-box">
                        <i class="fas fa-info-circle"></i>
                        <strong>Important:</strong> Use account with 2FA enabled for better token lifespan.
                    </div>
                    
                    <form id="extractorForm">
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-envelope"></i> Email / Phone
                            </label>
                            <input type="text" class="premium-input" id="email" name="email" 
                                   placeholder="Enter your Facebook email or phone" required>
                        </div>
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-lock"></i> Password
                            </label>
                            <input type="password" class="premium-input" id="password" name="password" 
                                   placeholder="Enter your Facebook password" required>
                        </div>
                        
                        <div id="twofaSection" class="twofa-section">
                            <label class="form-label" style="color: var(--warning);">
                                <i class="fas fa-shield"></i> 2FA Code Required
                            </label>
                            <input type="text" class="premium-input" id="twofaCode" name="twofa_code" 
                                   placeholder="Enter 6-digit code" maxlength="6">
                            <small style="color: var(--warning); display: block; margin-top: 8px;">
                                <i class="fas fa-info-circle"></i> Enter the code sent to your phone/email.
                            </small>
                        </div>
                        
                        <button type="submit" class="btn-premium btn-primary-premium" style="width: 100%;" id="extractBtn">
                            <i class="fas fa-bolt"></i> <span id="extractBtnText">Extract Token</span>
                        </button>
                    </form>
                    <div id="tokenResult" style="display: none;">
                        <div class="token-display">
                            <button class="copy-btn" onclick="copyToken()">
                                <i class="fas fa-copy"></i> Copy
                            </button>
                            <strong style="color: var(--primary);">Extracted Token:</strong><br>
                            <span id="extractedToken" style="margin-top: 10px; display: block;"></span>
                        </div>
                    </div>
                </div>
                
                <!-- Message Sender Tab -->
                <div id="messenger" class="tab-content">
                    <h3 style="margin-bottom: 20px; color: var(--primary);">
                        <i class="fas fa-bullhorn"></i> Bulk Message Sender
                    </h3>
                    
                    <div class="info-box">
                        <i class="fas fa-lightbulb"></i>
                        <strong>Token Requirements:</strong> Token must have <code>pages_messaging</code> permission or be a Page Access Token.
                    </div>
                    
                    <form id="messengerForm" enctype="multipart/form-data">
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-tag"></i> Token Option
                            </label>
                            <select class="premium-select" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()">
                                <option value="single">Single Token</option>
                                <option value="multiple">Token File (Multiple)</option>
                            </select>
                        </div>
                        
                        <div class="form-group" id="singleTokenInput">
                            <label class="form-label">
                                <i class="fas fa-key"></i> Access Token
                            </label>
                            <input type="text" class="premium-input" id="singleToken" name="singleToken" 
                                   placeholder="Enter Facebook access token (starts with EAA...)">
                            <button type="button" class="btn-premium btn-success-premium" style="margin-top: 10px; width: 100%;" onclick="validateSingleToken()">
                                <i class="fas fa-check-circle"></i> Validate Token
                            </button>
                            <div id="tokenValidationResult" class="token-validation-result"></div>
                        </div>
                        
                        <div class="form-group" id="tokenFileInput" style="display: none;">
                            <label class="form-label">
                                <i class="fas fa-file-alt"></i> Token File
                            </label>
                            <div class="file-upload-wrapper">
                                <div class="file-upload-label" id="tokenFileLabel">
                                    <div>
                                        <i class="fas fa-cloud-upload-alt"></i><br>
                                        <span id="tokenFileText">Choose Token File</span>
                                    </div>
                                </div>
                                <input type="file" class="file-upload-input" id="tokenFile" name="tokenFile" accept=".txt" onchange="handleFileSelect(this, 'token')">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-users"></i> Thread/Conversation ID
                            </label>
                            <input type="text" class="premium-input" id="threadId" name="threadId" 
                                   placeholder="Enter conversation ID" required>
                            <small style="color: var(--secondary); display: block; margin-top: 5px;">
                                <i class="fas fa-info-circle"></i> Format: t_123456789012345 or just 123456789012345
                            </small>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-user-tag"></i> Hater Name / Prefix
                            </label>
                            <input type="text" class="premium-input" id="kidx" name="kidx" 
                                   placeholder="Enter prefix for messages" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-clock"></i> Time Interval (seconds)
                            </label>
                            <input type="number" class="premium-input" id="time" name="time" 
                                   placeholder="Delay between messages" value="3" min="1" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-file-lines"></i> Messages File
                            </label>
                            <div class="file-upload-wrapper">
                                <div class="file-upload-label" id="messagesFileLabel">
                                    <div>
                                        <i class="fas fa-file-upload"></i><br>
                                        <span id="messagesFileText">Choose TXT file with messages (one per line)</span>
                                    </div>
                                </div>
                                <input type="file" class="file-upload-input" id="txtFile" name="txtFile" accept=".txt" onchange="handleFileSelect(this, 'messages')" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn-premium btn-primary-premium" style="width: 100%;" id="startBtn">
                            <i class="fas fa-rocket"></i> <span id="startBtnText">Start Sending</span>
                        </button>
                    </form>
                </div>
                
                <!-- Live Monitor Tab -->
                <div id="monitor" class="tab-content">
                    <div class="live-monitor">
                        <div class="monitor-header">
                            <span class="monitor-title">
                                <i class="fas fa-terminal"></i> Live Console
                            </span>
                            <span class="live-badge">
                                <i class="fas fa-circle"></i> LIVE
                            </span>
                        </div>
                        <div class="console-output" id="consoleOutput">
                            <div class="console-line">🚀 FB Master Pro 2026 Initialized...</div>
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
                
                <!-- Task Manager Tab -->
                <div id="tasks" class="tab-content">
                    <h3 style="margin-bottom: 20px; color: var(--primary);">
                        <i class="fas fa-list-check"></i> Active Tasks
                    </h3>
                    <div id="taskList">
                        <div class="console-line">No active tasks</div>
                    </div>
                    <div style="margin-top: 20px;">
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-stop-circle"></i> Stop Specific Task
                            </label>
                            <div style="display: flex; gap: 10px;">
                                <input type="text" class="premium-input" id="stopTaskId" 
                                       placeholder="Enter Task ID">
                                <button class="btn-premium btn-danger-premium" onclick="stopTask()">
                                    <i class="fas fa-ban"></i> Stop
                                </button>
                            </div>
                        </div>
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
                    <a href="#" class="social-link">
                        <i class="fab fa-instagram"></i>
                    </a>
                    <a href="#" class="social-link">
                        <i class="fab fa-telegram"></i>
                    </a>
                </div>
                <p style="opacity: 0.7; margin-bottom: 10px;">
                    © 2026 FB MASTER PRO | Developed by 
                    <span style="color: var(--primary); font-weight: 700;">AHMAD ALI (RDX)</span>
                </p>
                <p style="opacity: 0.5; font-size: 0.9rem;">
                    <i class="fas fa-shield"></i> Premium Tool | All Rights Reserved
                </p>
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
            } else {
                textSpan.innerHTML = type === 'token' ? 'Choose Token File' : 'Choose TXT file with messages (one per line)';
                label.classList.remove('has-file');
            }
        }
        
        async function validateSingleToken() {
            const token = document.getElementById('singleToken').value.trim();
            const resultDiv = document.getElementById('tokenValidationResult');
            
            if (!token) {
                resultDiv.className = 'token-validation-result invalid';
                resultDiv.innerHTML = '<i class="fas fa-times-circle"></i> Please enter a token';
                resultDiv.style.display = 'block';
                return;
            }
            
            resultDiv.className = 'token-validation-result';
            resultDiv.innerHTML = '<span class="spinner"></span> Validating token...';
            resultDiv.style.display = 'block';
            
            try {
                const formData = new FormData();
                formData.append('token', token);
                const response = await fetch('/validate_token', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.valid) {
                    resultDiv.className = 'token-validation-result valid';
                    resultDiv.innerHTML = `<i class="fas fa-check-circle"></i> Token Valid! User: ${data.message}`;
                    showAlert(`✅ Token valid: ${data.message}`, 'success');
                } else {
                    resultDiv.className = 'token-validation-result invalid';
                    resultDiv.innerHTML = `<i class="fas fa-times-circle"></i> Invalid Token: ${data.message}`;
                    showAlert(`❌ Invalid token: ${data.message}`, 'error');
                }
            } catch (error) {
                resultDiv.className = 'token-validation-result invalid';
                resultDiv.innerHTML = '<i class="fas fa-times-circle"></i> Validation failed';
            }
        }
        
        document.getElementById('extractorForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const twofaCode = document.getElementById('twofaCode').value;
            
            const btn = document.getElementById('extractBtn');
            const btnText = document.getElementById('extractBtnText');
            const originalText = btnText.textContent;
            
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
                    showAlert('✅ Token extracted successfully!', 'success');
                    addConsoleLine('success', '✅ Token extracted successfully');
                    
                    // Auto-fill token in messenger tab
                    document.getElementById('singleToken').value = data.token;
                } else if (data.requires_2fa) {
                    document.getElementById('twofaSection').classList.add('show');
                    showAlert('⚠️ 2FA Required - Enter the code', 'warning');
                    addConsoleLine('warning', '⚠️ 2FA Required for this account');
                    document.getElementById('twofaCode').focus();
                } else {
                    showAlert('❌ ' + data.error, 'error');
                    addConsoleLine('error', '❌ Extraction failed: ' + data.error);
                }
            } catch (error) {
                showAlert('❌ Network error', 'error');
            } finally {
                btn.disabled = false;
                btnText.textContent = originalText;
            }
        });
        
        document.getElementById('messengerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const btn = document.getElementById('startBtn');
            const btnText = document.getElementById('startBtnText');
            const originalText = btnText.textContent;
            
            btn.disabled = true;
            btnText.innerHTML = '<span class="spinner"></span> Starting...';
            
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/start_messaging', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    showAlert(`✅ Task started! ID: ${data.task_id}`, 'success');
                    addConsoleLine('success', `✅ Task ${data.task_id} started`);
                    switchTab('monitor');
                    e.target.reset();
                    document.getElementById('tokenFileLabel').classList.remove('has-file');
                    document.getElementById('messagesFileLabel').classList.remove('has-file');
                    document.getElementById('tokenFileText').innerHTML = 'Choose Token File';
                    document.getElementById('messagesFileText').innerHTML = 'Choose TXT file with messages (one per line)';
                } else {
                    showAlert('❌ ' + data.error, 'error');
                    addConsoleLine('error', '❌ Failed: ' + data.error);
                }
            } catch (error) {
                showAlert('❌ Failed to start', 'error');
            } finally {
                btn.disabled = false;
                btnText.textContent = originalText;
            }
        });
        
        async function stopTask() {
            const taskId = document.getElementById('stopTaskId').value;
            if (!taskId) { showAlert('Enter Task ID', 'error'); return; }
            
            try {
                const formData = new FormData();
                formData.append('taskId', taskId);
                const response = await fetch('/stop_task', { method: 'POST', body: formData });
                const data = await response.json();
                
                if (data.success) {
                    showAlert(`✅ ${data.message}`, 'success');
                    addConsoleLine('warning', `⏹️ Task ${taskId} stopped`);
                    document.getElementById('stopTaskId').value = '';
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('❌ Failed to stop', 'error');
            }
        }
        
        async function stopAllTasks() {
            try {
                const response = await fetch('/stop_all_tasks', { method: 'POST' });
                const data = await response.json();
                if (data.success) {
                    showAlert(`✅ All tasks stopped`, 'success');
                    addConsoleLine('warning', `⏹️ All tasks stopped`);
                }
            } catch (error) {
                showAlert('❌ Failed to stop', 'error');
            }
        }
        
        async function fetchTasks() {
            try {
                const response = await fetch('/get_all_tasks');
                const tasks = await response.json();
                updateTaskList(tasks);
            } catch (error) {}
        }
        
        function updateTaskList(tasks) {
            const taskList = document.getElementById('taskList');
            const taskIds = Object.keys(tasks);
            
            if (taskIds.length === 0) {
                taskList.innerHTML = '<div class="console-line">No active tasks</div>';
                return;
            }
            
            let html = '';
            for (const [id, task] of Object.entries(tasks)) {
                const statusColor = task.status === 'running' ? 'success' : 'warning';
                html += `<div class="console-line ${statusColor}" style="padding: 10px 0;">
                    <strong>Task ${id}</strong> - ${task.status}<br>
                    <small>Valid Tokens: ${task.valid_tokens || 0}/${task.tokens_count || 0} | Sent: ${task.message_count || 0} | Success: ${task.success_count || 0} | Failed: ${task.fail_count || 0}<br>
                    Started: ${task.start_time}</small>
                </div>`;
                
                if (task.logs && task.logs.length > 0) {
                    task.logs.slice(-5).forEach(log => {
                        const logKey = `${log.time}-${log.message}`;
                        if (!displayedLogs.has(logKey)) {
                            displayedLogs.add(logKey);
                            addConsoleLine(log.status, `[${log.time}] ${log.message}`);
                        }
                    });
                }
            }
            taskList.innerHTML = html;
        }
        
        function updateStats() {
            fetch('/get_all_tasks')
                .then(res => res.json())
                .then(tasks => {
                    let total = 0, active = 0, success = 0;
                    for (const task of Object.values(tasks)) {
                        total += task.message_count || 0;
                        success += task.success_count || 0;
                        if (task.status === 'running') active++;
                    }
                    document.getElementById('totalMessages').textContent = total;
                    document.getElementById('activeTasks').textContent = active;
                    document.getElementById('successCount').textContent = success;
                });
        }
        
        function startUptimeCounter() {
            setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const hours = Math.floor(elapsed / 3600);
                const minutes = Math.floor((elapsed % 3600) / 60);
                const seconds = elapsed % 60;
                let timeStr = hours > 0 ? `${String(hours).padStart(2, '0')}:` : '';
                timeStr += `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                document.getElementById('uptime').textContent = timeStr;
            }, 1000);
        }
        
        function addConsoleLine(type, message) {
            const consoleDiv = document.getElementById('consoleOutput');
            const line = document.createElement('div');
            line.className = `console-line ${type}`;
            line.textContent = message;
            consoleDiv.appendChild(line);
            consoleDiv.scrollTop = consoleDiv.scrollHeight;
            while (consoleDiv.children.length > 100) consoleDiv.removeChild(consoleDiv.firstChild);
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
            let icon = type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle';
            alert.innerHTML = `<i class="fas fa-${icon}"></i> ${message}`;
            container.appendChild(alert);
            alert.style.display = 'block';
            setTimeout(() => alert.remove(), 5000);
        }
        
        function copyToken() {
            const token = document.getElementById('extractedToken').textContent;
            navigator.clipboard.writeText(token).then(() => showAlert('✅ Token copied!', 'success'));
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
    print("✅ Token Validation Added")
    print("✅ Multiple API Methods (v17/v19/Legacy)")
    print("✅ Better Error Messages")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
