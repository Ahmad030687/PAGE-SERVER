# requirements.txt
"""
flask==2.3.3
flask-socketio==5.3.4
requests==2.31.0
beautifulsoup4==4.12.2
pyqt5==5.15.9
qdarkstyle==3.2.3
python-socketio==5.9.0
eventlet==0.33.3
colorama==0.4.6
"""

# fb_server_core.py - Main Server File
import os
import sys
import time
import json
import uuid
import random
import hashlib
import requests
import threading
import queue
from datetime import datetime
from typing import Dict, List, Optional

# Flask & SocketIO for Server
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import eventlet
eventlet.monkey_patch()

# Beautiful UI Colors
class Colors:
    DARK_BG = "#0A0E27"
    CARD_BG = "#1A1F3A"
    ACCENT = "#00D2FF"
    ACCENT_GRADIENT = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
    SUCCESS = "#00F2FE"
    WARNING = "#F2994A"
    ERROR = "#EB5757"
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#8892B0"
    BORDER = "#2A2F4A"

class FacebookConvoServer:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'fb-convo-server-secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='eventlet')
        self.active_tokens = {}
        self.message_queue = queue.Queue()
        self.server_running = False
        self.thread_pool = []
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.route('/')
        def index():
            return render_template('index.html')
            
        @self.app.route('/api/extract_token', methods=['POST'])
        def extract_token_endpoint():
            data = request.json
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return jsonify({'success': False, 'error': 'Email and password required'})
                
            token_info = self.extract_facebook_token(email, password)
            return jsonify(token_info)
            
        @self.app.route('/api/start_server', methods=['POST'])
        def start_server_endpoint():
            data = request.json
            token = data.get('token')
            thread_count = data.get('threads', 5)
            
            if not token:
                return jsonify({'success': False, 'error': 'Token required'})
                
            result = self.start_convo_server(token, thread_count)
            return jsonify(result)
            
        @self.app.route('/api/stop_server', methods=['POST'])
        def stop_server_endpoint():
            result = self.stop_convo_server()
            return jsonify(result)
            
        @self.app.route('/api/send_bulk', methods=['POST'])
        def send_bulk_endpoint():
            data = request.json
            token = data.get('token')
            thread_ids = data.get('thread_ids', [])
            message = data.get('message')
            
            if not all([token, thread_ids, message]):
                return jsonify({'success': False, 'error': 'Missing parameters'})
                
            result = self.send_bulk_messages(token, thread_ids, message)
            return jsonify(result)
            
        @self.app.route('/api/get_conversations', methods=['POST'])
        def get_conversations_endpoint():
            data = request.json
            token = data.get('token')
            limit = data.get('limit', 50)
            
            if not token:
                return jsonify({'success': False, 'error': 'Token required'})
                
            conversations = self.get_conversations(token, limit)
            return jsonify(conversations)
            
        @self.socketio.on('connect')
        def handle_connect():
            emit('connected', {'status': 'Connected to FB Convo Server'})
            
        @self.socketio.on('server_status')
        def handle_status_request():
            emit('status_update', {
                'running': self.server_running,
                'active_tokens': len(self.active_tokens),
                'queue_size': self.message_queue.qsize()
            })
    
    def extract_facebook_token(self, email: str, password: str) -> Dict:
        """Extract Facebook access token from credentials"""
        try:
            session = requests.Session()
            
            # Generate device identifiers
            device_id = str(uuid.uuid4())
            adid = str(uuid.uuid4())
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
                "Host": "graph.facebook.com",
                "Authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
                "X-FB-Connection-Type": "WIFI"
            }
            
            data = {
                "adid": adid,
                "email": email,
                "password": password,
                "format": "json",
                "device_id": device_id,
                "cpl": "true",
                "family_device_id": str(uuid.uuid4()),
                "credentials_type": "device_based_login_password",
                "generate_session_cookies": "1",
                "error_detail_type": "button_with_disabled",
                "source": "login",
                "method": "auth.login",
                "generate_machine_id": "1",
                "meta_inf_fbmeta": ""
            }
            
            response = session.post(
                "https://graph.facebook.com/auth/login",
                data=data,
                headers=headers,
                timeout=30
            )
            
            result = response.json()
            
            if "access_token" in result:
                token = result["access_token"]
                
                # Get user info with token
                user_info = self.get_user_info(token)
                
                return {
                    'success': True,
                    'token': token,
                    'user_info': user_info,
                    'expires': result.get('expires', 0)
                }
            elif "error" in result:
                return {
                    'success': False,
                    'error': result['error'].get('message', 'Unknown error')
                }
            else:
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_info(self, token: str) -> Dict:
        """Get user information using token"""
        try:
            response = requests.get(
                "https://graph.facebook.com/me",
                params={
                    'access_token': token,
                    'fields': 'id,name,email,picture'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'id': data.get('id'),
                    'name': data.get('name'),
                    'email': data.get('email'),
                    'picture': data.get('picture', {}).get('data', {}).get('url')
                }
        except:
            pass
            
        return {'id': 'Unknown', 'name': 'Unknown'}
    
    def get_conversations(self, token: str, limit: int = 50) -> Dict:
        """Get Facebook conversations"""
        try:
            response = requests.get(
                "https://graph.facebook.com/v18.0/me/conversations",
                params={
                    'access_token': token,
                    'fields': 'participants,messages.limit(1){message,created_time},unread_count,updated_time',
                    'limit': limit
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                conversations = []
                
                for conv in data.get('data', []):
                    participants = conv.get('participants', {}).get('data', [])
                    other_participants = [p for p in participants if p.get('id') != 'me']
                    
                    conversations.append({
                        'id': conv.get('id'),
                        'updated_time': conv.get('updated_time'),
                        'unread_count': conv.get('unread_count', 0),
                        'participants': other_participants[:3],
                        'snippet': conv.get('messages', {}).get('data', [{}])[0].get('message', '')
                    })
                
                return {
                    'success': True,
                    'conversations': conversations,
                    'total': len(conversations)
                }
            else:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_bulk_messages(self, token: str, thread_ids: List[str], message: str) -> Dict:
        """Send bulk messages to multiple conversations"""
        results = {
            'success': True,
            'sent': 0,
            'failed': 0,
            'details': []
        }
        
        for thread_id in thread_ids:
            try:
                response = requests.post(
                    f"https://graph.facebook.com/v18.0/{thread_id}/messages",
                    data={
                        'access_token': token,
                        'message': message
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    results['sent'] += 1
                    results['details'].append({
                        'thread_id': thread_id,
                        'status': 'success'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'thread_id': thread_id,
                        'status': 'failed',
                        'error': response.text
                    })
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'thread_id': thread_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results
    
    def start_convo_server(self, token: str, thread_count: int = 5) -> Dict:
        """Start the conversation server"""
        if self.server_running:
            return {'success': False, 'error': 'Server already running'}
        
        self.server_running = True
        session_id = str(uuid.uuid4())
        
        self.active_tokens[session_id] = {
            'token': token,
            'threads': thread_count,
            'started_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Start worker threads
        for i in range(thread_count):
            thread = threading.Thread(
                target=self.convo_worker,
                args=(session_id, i),
                daemon=True
            )
            thread.start()
            self.thread_pool.append(thread)
        
        self.socketio.emit('server_started', {
            'session_id': session_id,
            'thread_count': thread_count
        })
        
        return {
            'success': True,
            'session_id': session_id,
            'message': f'Server started with {thread_count} threads'
        }
    
    def stop_convo_server(self) -> Dict:
        """Stop the conversation server"""
        if not self.server_running:
            return {'success': False, 'error': 'Server not running'}
        
        self.server_running = False
        
        # Clear active tokens
        self.active_tokens.clear()
        
        # Wait for threads to finish
        for thread in self.thread_pool:
            thread.join(timeout=2)
        
        self.thread_pool.clear()
        
        self.socketio.emit('server_stopped', {
            'message': 'Server stopped successfully'
        })
        
        return {
            'success': True,
            'message': 'Server stopped successfully'
        }
    
    def convo_worker(self, session_id: str, worker_id: int):
        """Worker thread for processing conversations"""
        while self.server_running and session_id in self.active_tokens:
            try:
                # Process message queue
                if not self.message_queue.empty():
                    task = self.message_queue.get(timeout=1)
                    
                    # Emit progress update
                    self.socketio.emit('worker_update', {
                        'worker_id': worker_id,
                        'task': task
                    })
                
                time.sleep(0.1)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    def run(self, host='0.0.0.0', port=5000):
        """Run the Flask server"""
        print(f"\033[92m[+] Facebook Convo Server starting on http://{host}:{port}\033[0m")
        self.socketio.run(self.app, host=host, port=port, debug=False)

# HTML Template for Frontend
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AHMII FB CONVO SERVER • PREMIUM</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', sans-serif;
            background: #0A0E27;
            color: #FFFFFF;
            overflow-x: hidden;
        }
        
        /* Animated Gradient Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            background: linear-gradient(45deg, #0A0E27, #1A1F3A, #0F1433, #1A1F3A);
            background-size: 400% 400%;
            animation: gradientBG 15s ease infinite;
        }
        
        @keyframes gradientBG {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* Glassmorphism Effect */
        .glass {
            background: rgba(26, 31, 58, 0.7);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 210, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        .header {
            text-align: center;
            padding: 30px 0;
            position: relative;
        }
        
        .glowing-text {
            font-size: 48px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #00D2FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: glow 3s ease-in-out infinite alternate;
        }
        
        @keyframes glow {
            from { filter: drop-shadow(0 0 10px rgba(102, 126, 234, 0.5)); }
            to { filter: drop-shadow(0 0 20px rgba(0, 210, 255, 0.8)); }
        }
        
        .subtitle {
            color: #8892B0;
            margin-top: 10px;
            font-size: 16px;
            letter-spacing: 2px;
        }
        
        /* Status Bar */
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 25px;
            margin-bottom: 25px;
        }
        
        .server-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .pulse {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #EB5757;
            box-shadow: 0 0 10px #EB5757;
            animation: pulse-animation 2s infinite;
        }
        
        .pulse.active {
            background: #00F2FE;
            box-shadow: 0 0 20px #00F2FE;
        }
        
        @keyframes pulse-animation {
            0% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.1); }
            100% { opacity: 1; transform: scale(1); }
        }
        
        /* Cards */
        .card-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .card {
            padding: 25px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 210, 255, 0.2);
        }
        
        .card-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-title i {
            color: #00D2FF;
        }
        
        /* Form Elements */
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-label {
            display: block;
            margin-bottom: 8px;
            color: #8892B0;
            font-size: 14px;
        }
        
        .input-field {
            width: 100%;
            padding: 12px 15px;
            background: rgba(10, 14, 39, 0.5);
            border: 1px solid #2A2F4A;
            border-radius: 10px;
            color: #FFFFFF;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .input-field:focus {
            outline: none;
            border-color: #00D2FF;
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.3);
        }
        
        .input-field::placeholder {
            color: #4A5073;
        }
        
        /* Buttons */
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        
        .btn-success {
            background: linear-gradient(135deg, #00F2FE 0%, #4FACFE 100%);
            color: white;
        }
        
        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 242, 254, 0.4);
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #EB5757 0%, #F2994A 100%);
            color: white;
        }
        
        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(235, 87, 87, 0.4);
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        /* Token Display */
        .token-box {
            background: rgba(10, 14, 39, 0.5);
            border: 1px solid #2A2F4A;
            border-radius: 10px;
            padding: 15px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            word-break: break-all;
            margin-top: 15px;
            max-height: 100px;
            overflow-y: auto;
        }
        
        /* Conversations List */
        .conv-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .conv-item {
            padding: 12px;
            border-bottom: 1px solid #2A2F4A;
            cursor: pointer;
            transition: background 0.3s ease;
        }
        
        .conv-item:hover {
            background: rgba(0, 210, 255, 0.1);
        }
        
        .conv-item.selected {
            background: rgba(0, 210, 255, 0.2);
            border-left: 3px solid #00D2FF;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .stat-card {
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 32px;
            font-weight: 700;
            color: #00D2FF;
        }
        
        .stat-label {
            color: #8892B0;
            font-size: 14px;
            margin-top: 5px;
        }
        
        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin-top: 15px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #00F2FE 0%, #4FACFE 100%);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 3px;
        }
        
        /* Log Console */
        .log-console {
            background: rgba(10, 14, 39, 0.8);
            border-radius: 10px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            margin-top: 20px;
        }
        
        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .log-time {
            color: #4A5073;
            margin-right: 10px;
        }
        
        .log-info { color: #00D2FF; }
        .log-success { color: #00F2FE; }
        .log-error { color: #EB5757; }
        .log-warning { color: #F2994A; }
        
        /* Responsive */
        @media (max-width: 768px) {
            .card-grid {
                grid-template-columns: 1fr;
            }
            
            .glowing-text {
                font-size: 32px;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(26, 31, 58, 0.5);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
        
        /* Loading Spinner */
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #00D2FF;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Owner Badge */
        .owner-badge {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 10px 20px;
            background: rgba(26, 31, 58, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 50px;
            border: 1px solid rgba(0, 210, 255, 0.3);
            color: #00D2FF;
            font-weight: 600;
            z-index: 1000;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.3);
        }
        
        .owner-badge i {
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1 class="glowing-text">AHMII FB CONVO SERVER</h1>
            <p class="subtitle">PREMIUM • PROFESSIONAL • POWERFUL</p>
        </div>
        
        <!-- Status Bar -->
        <div class="status-bar glass">
            <div class="server-indicator">
                <div class="pulse" id="serverPulse"></div>
                <span id="serverStatusText">Server Offline</span>
            </div>
            <div>
                <span style="color: #8892B0;">OWNER:</span>
                <span style="color: #00D2FF; margin-left: 8px;">AHMAD ALI (RDX)</span>
            </div>
        </div>
        
        <!-- Stats Grid -->
        <div class="stats-grid">
            <div class="stat-card glass">
                <div class="stat-value" id="activeTokens">0</div>
                <div class="stat-label">Active Tokens</div>
            </div>
            <div class="stat-card glass">
                <div class="stat-value" id="messagesSent">0</div>
                <div class="stat-label">Messages Sent</div>
            </div>
            <div class="stat-card glass">
                <div class="stat-value" id="queueSize">0</div>
                <div class="stat-label">Queue Size</div>
            </div>
        </div>
        
        <!-- Main Card Grid -->
        <div class="card-grid">
            <!-- Token Extractor Card -->
            <div class="card glass">
                <div class="card-title">
                    <span>🔐 TOKEN EXTRACTOR</span>
                </div>
                <div class="input-group">
                    <label class="input-label">Email / Phone</label>
                    <input type="text" class="input-field" id="emailInput" placeholder="example@email.com">
                </div>
                <div class="input-group">
                    <label class="input-label">Password</label>
                    <input type="password" class="input-field" id="passwordInput" placeholder="••••••••">
                </div>
                <button class="btn btn-primary" onclick="extractToken()">
                    <span id="extractBtnText">Extract Token</span>
                </button>
                <div class="token-box" id="tokenDisplay" style="display: none;"></div>
            </div>
            
            <!-- Server Control Card -->
            <div class="card glass">
                <div class="card-title">
                    <span>⚡ SERVER CONTROL</span>
                </div>
                <div class="input-group">
                    <label class="input-label">Access Token</label>
                    <input type="text" class="input-field" id="serverTokenInput" placeholder="Paste your FB token">
                </div>
                <div class="input-group">
                    <label class="input-label">Thread Count</label>
                    <input type="number" class="input-field" id="threadCountInput" value="5" min="1" max="20">
                </div>
                <div class="btn-group">
                    <button class="btn btn-success" onclick="startServer()" id="startServerBtn">
                        ▶ START SERVER
                    </button>
                    <button class="btn btn-danger" onclick="stopServer()" id="stopServerBtn" disabled>
                        ⏹ STOP SERVER
                    </button>
                </div>
                <div class="progress-bar" id="serverProgress" style="display: none;">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
            </div>
        </div>
        
        <!-- Bulk Messaging Card -->
        <div class="card glass" style="margin-bottom: 25px;">
            <div class="card-title">
                <span>💬 BULK MESSAGING</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                <div>
                    <label class="input-label">Select Conversations</label>
                    <button class="btn btn-primary" onclick="loadConversations()" style="margin-bottom: 10px;">
                        📋 Load Conversations
                    </button>
                    <div class="conv-list" id="conversationsList">
                        <div style="padding: 20px; text-align: center; color: #4A5073;">
                            Click "Load Conversations" to fetch
                        </div>
                    </div>
                </div>
                <div>
                    <label class="input-label">Message</label>
                    <textarea class="input-field" id="bulkMessage" rows="4" placeholder="Type your message here..."></textarea>
                    <button class="btn btn-success" onclick="sendBulkMessages()" style="margin-top: 15px; width: 100%;">
                        🚀 SEND BULK MESSAGES
                    </button>
                </div>
            </div>
        </div>
        
        <!-- Log Console -->
        <div class="card glass">
            <div class="card-title">
                <span>📊 SERVER LOGS</span>
            </div>
            <div class="log-console" id="logConsole">
                <div class="log-entry">
                    <span class="log-time">[SYSTEM]</span>
                    <span class="log-info">Facebook Convo Server initialized</span>
                </div>
                <div class="log-entry">
                    <span class="log-time">[SYSTEM]</span>
                    <span class="log-info">Ready for operations...</span>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Owner Badge -->
    <div class="owner-badge">
        <span>👑 AHMAD ALI (RDX) • PREMIUM VIP</span>
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const socket = io();
        let currentToken = '';
        let selectedConversations = new Set();
        let messagesSent = 0;
        
        // Socket Events
        socket.on('connect', () => {
            addLog('Connected to server', 'success');
        });
        
        socket.on('server_started', (data) => {
            addLog(`Server started with ${data.thread_count} threads`, 'success');
            updateServerStatus(true);
        });
        
        socket.on('server_stopped', (data) => {
            addLog('Server stopped', 'warning');
            updateServerStatus(false);
        });
        
        socket.on('worker_update', (data) => {
            addLog(`Worker ${data.worker_id} processing task`, 'info');
        });
        
        socket.on('status_update', (data) => {
            document.getElementById('activeTokens').textContent = data.active_tokens || 0;
            document.getElementById('queueSize').textContent = data.queue_size || 0;
        });
        
        // Helper Functions
        function addLog(message, type = 'info') {
            const console = document.getElementById('logConsole');
            const entry = document.createElement('div');
            entry.className = 'log-entry';
            
            const time = new Date().toLocaleTimeString();
            entry.innerHTML = `
                <span class="log-time">[${time}]</span>
                <span class="log-${type}">${message}</span>
            `;
            
            console.appendChild(entry);
            console.scrollTop = console.scrollHeight;
            
            // Keep only last 50 logs
            if (console.children.length > 50) {
                console.removeChild(console.firstChild);
            }
        }
        
        function updateServerStatus(running) {
            const pulse = document.getElementById('serverPulse');
            const statusText = document.getElementById('serverStatusText');
            const startBtn = document.getElementById('startServerBtn');
            const stopBtn = document.getElementById('stopServerBtn');
            
            if (running) {
                pulse.classList.add('active');
                statusText.textContent = 'Server Online';
                startBtn.disabled = true;
                stopBtn.disabled = false;
            } else {
                pulse.classList.remove('active');
                statusText.textContent = 'Server Offline';
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        }
        
        function updateMessagesSent(count) {
            messagesSent += count;
            document.getElementById('messagesSent').textContent = messagesSent;
        }
        
        // API Functions
        async function extractToken() {
            const email = document.getElementById('emailInput').value;
            const password = document.getElementById('passwordInput').value;
            const btn = document.getElementById('extractBtnText');
            
            if (!email || !password) {
                addLog('Please enter email and password', 'error');
                return;
            }
            
            btn.innerHTML = '<span class="spinner"></span> Extracting...';
            addLog('Extracting token...', 'info');
            
            try {
                const response = await fetch('/api/extract_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    currentToken = data.token;
                    document.getElementById('tokenDisplay').style.display = 'block';
                    document.getElementById('tokenDisplay').textContent = data.token;
                    document.getElementById('serverTokenInput').value = data.token;
                    addLog(`Token extracted successfully for ${data.user_info.name}`, 'success');
                } else {
                    addLog(`Token extraction failed: ${data.error}`, 'error');
                }
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
            } finally {
                btn.textContent = 'Extract Token';
            }
        }
        
        async function startServer() {
            const token = document.getElementById('serverTokenInput').value;
            const threads = parseInt(document.getElementById('threadCountInput').value);
            
            if (!token) {
                addLog('Please enter an access token', 'error');
                return;
            }
            
            addLog('Starting server...', 'info');
            document.getElementById('serverProgress').style.display = 'block';
            
            try {
                const response = await fetch('/api/start_server', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token, threads})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addLog(`Server started: ${data.message}`, 'success');
                    currentToken = token;
                } else {
                    addLog(`Failed to start server: ${data.error}`, 'error');
                }
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
            } finally {
                document.getElementById('serverProgress').style.display = 'none';
            }
        }
        
        async function stopServer() {
            addLog('Stopping server...', 'warning');
            
            try {
                const response = await fetch('/api/stop_server', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addLog(data.message, 'success');
                } else {
                    addLog(`Failed to stop server: ${data.error}`, 'error');
                }
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
            }
        }
        
        async function loadConversations() {
            if (!currentToken) {
                addLog('Please extract or enter a token first', 'error');
                return;
            }
            
            addLog('Loading conversations...', 'info');
            
            try {
                const response = await fetch('/api/get_conversations', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: currentToken, limit: 50})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    displayConversations(data.conversations);
                    addLog(`Loaded ${data.total} conversations`, 'success');
                } else {
                    addLog(`Failed to load conversations: ${data.error}`, 'error');
                }
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
            }
        }
        
        function displayConversations(conversations) {
            const container = document.getElementById('conversationsList');
            container.innerHTML = '';
            
            conversations.forEach(conv => {
                const div = document.createElement('div');
                div.className = 'conv-item';
                div.onclick = () => toggleConversation(conv.id, div);
                
                const participants = conv.participants.map(p => p.name).join(', ');
                div.innerHTML = `
                    <div style="font-weight: 600; margin-bottom: 5px;">${participants}</div>
                    <div style="font-size: 12px; color: #8892B0;">${conv.snippet || 'No messages'}</div>
                `;
                
                container.appendChild(div);
            });
        }
        
        function toggleConversation(id, element) {
            if (selectedConversations.has(id)) {
                selectedConversations.delete(id);
                element.classList.remove('selected');
            } else {
                selectedConversations.add(id);
                element.classList.add('selected');
            }
        }
        
        async function sendBulkMessages() {
            const message = document.getElementById('bulkMessage').value;
            
            if (!currentToken) {
                addLog('Please extract or enter a token first', 'error');
                return;
            }
            
            if (selectedConversations.size === 0) {
                addLog('Please select at least one conversation', 'error');
                return;
            }
            
            if (!message) {
                addLog('Please enter a message', 'error');
                return;
            }
            
            const threadIds = Array.from(selectedConversations);
            addLog(`Sending bulk messages to ${threadIds.length} conversations...`, 'info');
            
            try {
                const response = await fetch('/api/send_bulk', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        token: currentToken,
                        thread_ids: threadIds,
                        message: message
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    addLog(`Messages sent: ${data.sent} successful, ${data.failed} failed`, 'success');
                    updateMessagesSent(data.sent);
                    selectedConversations.clear();
                    document.querySelectorAll('.conv-item').forEach(el => el.classList.remove('selected'));
                } else {
                    addLog(`Failed to send messages: ${data.error}`, 'error');
                }
            } catch (error) {
                addLog(`Error: ${error.message}`, 'error');
            }
        }
        
        // Initialize
        addLog('Welcome to AHMII FB Convo Server', 'success');
        addLog('Premium VIP Edition • Owner: AHMAD ALI (RDX)', 'info');
    </script>
</body>
</html>
'''

# Main execution
if __name__ == "__main__":
    # Create templates directory and save HTML
    os.makedirs('templates', exist_ok=True)
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)
    
    # Start server
    server = FacebookConvoServer()
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     █████╗ ██╗  ██╗███╗   ███╗██╗██╗                    ║
    ║    ██╔══██╗██║  ██║████╗ ████║██║██║                    ║
    ║    ███████║███████║██╔████╔██║██║██║                    ║
    ║    ██╔══██║██╔══██║██║╚██╔╝██║██║██║                    ║
    ║    ██║  ██║██║  ██║██║ ╚═╝ ██║██║██║                    ║
    ║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝                    ║
    ║                                                          ║
    ║           FB CONVO SERVER • PREMIUM EDITION              ║
    ║                    OWNER: AHMAD ALI (RDX)                ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    🌐 Server running at: http://localhost:5000
    📱 Open your browser to access the web interface
    
    Press Ctrl+C to stop the server
    """)
    
    try:
        server.run(host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n\n\033[91m[!] Server stopped by user\033[0m")
        sys.exit(0)
