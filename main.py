#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AHMAD ALI (RDX) - FB TOKEN EXTRACTOR WITH 2FA (FIXED)

import os, sys, time, uuid, json, requests, re, base64, hashlib, random
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# Store sessions for 2FA flow
sessions = {}

# ==================== FIXED TOKEN EXTRACTOR ====================
def generate_device_data():
    """Generate realistic device data"""
    return {
        "adid": str(uuid.uuid4()).upper(),
        "device_id": str(uuid.uuid4()).replace('-', '')[:16],
        "family_device_id": str(uuid.uuid4()).replace('-', '')[:16],
        "machine_id": str(uuid.uuid4()).upper()
    }

def get_fb_token(email, password, twofa_code=None, session_id=None):
    """
    Working Facebook token extractor with 2FA
    """
    try:
        # Use existing session or create new
        if session_id and session_id in sessions:
            sess = sessions[session_id]['session']
            cookies = sessions[session_id].get('cookies', {})
        else:
            sess = requests.Session()
            session_id = str(uuid.uuid4())
            sessions[session_id] = {'session': sess, 'email': email}
            cookies = {}
        
        device = generate_device_data()
        
        # Updated User Agent
        ua = "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36"
        
        # If 2FA code provided
        if twofa_code and session_id:
            return verify_2fa(sess, session_id, twofa_code, email)
        
        # ==================== METHOD 1: Mobile API ====================
        headers = {
            "User-Agent": ua,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "X-FB-Connection-Type": "WIFI",
            "X-FB-Net-HNI": "45005",
            "X-FB-SIM-HNI": "45005",
        }
        
        data = {
            "adid": device['adid'],
            "email": email,
            "password": password,
            "format": "json",
            "device_id": device['device_id'],
            "cpl": "true",
            "family_device_id": device['family_device_id'],
            "credentials_type": "password",
            "generate_session_cookies": "1",
            "error_detail_type": "button_with_disabled",
            "source": "login",
            "method": "auth.login",
            "meta_inf_fbmeta": "",
            "currently_logged_in_userid": "0",
            "locale": "en_US",
            "client_country_code": "US",
            "machine_id": device['machine_id'],
            "api_key": "882a8490361da98702bf97a021ddc14d",
            "fb_api_req_friendly_name": "authenticate",
        }
        
        # Try primary endpoint
        try:
            resp = sess.post(
                "https://b-api.facebook.com/method/auth.login",
                data=data,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            if resp.status_code == 200:
                try:
                    resp_data = resp.json()
                except:
                    resp_data = {}
                
                # Success - got token
                if "access_token" in resp_data:
                    token = resp_data["access_token"]
                    cookies = sess.cookies.get_dict()
                    sessions[session_id]['cookies'] = cookies
                    return True, {"token": token, "cookies": cookies}, "success", None
                
                # 2FA Required
                elif "error" in resp_data:
                    error = resp_data.get("error", {})
                    error_code = error.get("code", 0)
                    error_msg = error.get("message", "").lower()
                    
                    if error_code == 403 or "two-factor" in error_msg or "login_approval" in error_msg:
                        # Save session for 2FA
                        sessions[session_id]['login_data'] = data
                        sessions[session_id]['headers'] = headers
                        sessions[session_id]['device'] = device
                        return False, "2FA Required - Enter code", "2fa_required", session_id
                    
                    elif "incorrect" in error_msg or "invalid" in error_msg:
                        return False, "Incorrect email or password", "error", None
                    
                    elif "checkpoint" in error_msg:
                        return False, "Account locked - Verify on browser first", "error", None
                    
                    else:
                        return False, error.get("message", "Login failed"), "error", None
        except:
            pass
        
        # ==================== METHOD 2: Graph API ====================
        headers2 = {
            "User-Agent": ua,
            "Host": "graph.facebook.com",
            "Authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        data2 = {
            "adid": device['adid'],
            "email": email,
            "password": password,
            "format": "json",
            "device_id": device['device_id'],
            "cpl": "true",
            "family_device_id": device['family_device_id'],
            "credentials_type": "device_based_login_password",
            "generate_session_cookies": "1",
            "error_detail_type": "button_with_disabled",
            "source": "login",
            "method": "auth.login",
        }
        
        try:
            resp2 = sess.post(
                "https://graph.facebook.com/auth/login",
                data=data2,
                headers=headers2,
                timeout=30
            )
            
            if resp2.status_code == 200:
                resp_data = resp2.json()
                
                if "access_token" in resp_data:
                    token = resp_data["access_token"]
                    return True, {"token": token, "cookies": sess.cookies.get_dict()}, "success", None
                
                elif "error" in resp_data:
                    error = resp_data.get("error", {})
                    error_msg = error.get("message", "").lower()
                    
                    if "two-factor" in error_msg or "login_approval" in error_msg:
                        sessions[session_id]['login_data'] = data2
                        sessions[session_id]['headers'] = headers2
                        return False, "2FA Required - Enter code", "2fa_required", session_id
        except:
            pass
        
        return False, "Network error - Try again", "error", None
        
    except requests.exceptions.ConnectionError:
        return False, "No internet connection", "error", None
    except Exception as e:
        return False, f"Error: {str(e)}", "error", None

def verify_2fa(sess, session_id, code, email):
    """Verify 2FA code and get token"""
    try:
        if session_id not in sessions:
            return False, "Session expired", "error", None
        
        login_data = sessions[session_id].get('login_data', {})
        headers = sessions[session_id].get('headers', {})
        
        # Add 2FA code
        login_data['twofactor_code'] = code
        login_data['machine_id'] = str(uuid.uuid4())
        login_data['confirmed'] = "true"
        
        # Try with 2FA code
        resp = sess.post(
            "https://b-api.facebook.com/method/auth.login",
            data=login_data,
            headers=headers,
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            
            if "access_token" in data:
                token = data["access_token"]
                del sessions[session_id]
                return True, {"token": token}, "success", None
            
            elif "error" in data:
                return False, data["error"].get("message", "Invalid 2FA code"), "error", session_id
        
        # Alternative 2FA endpoint
        twofa_headers = {
            "User-Agent": headers.get("User-Agent", ""),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        twofa_data = {
            "code": code,
            "email": email,
            "method": "authenticator",
            "fb_api_req_friendly_name": "two_factor_verification",
        }
        
        resp2 = sess.post(
            "https://graph.facebook.com/auth/login/twofactor",
            data=twofa_data,
            headers=twofa_headers,
            timeout=30
        )
        
        if resp2.status_code == 200:
            data2 = resp2.json()
            if "access_token" in data2:
                token = data2["access_token"]
                del sessions[session_id]
                return True, {"token": token}, "success", None
        
        return False, "Invalid 2FA code", "error", session_id
        
    except Exception as e:
        return False, f"2FA error: {str(e)}", "error", session_id

def check_token(token):
    """Check token validity and get user info"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get(
            "https://graph.facebook.com/me?fields=name,id",
            headers=headers,
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            return {
                "valid": True,
                "name": data.get("name", "Unknown"),
                "uid": data.get("id", "Unknown")
            }
    except:
        pass
    return {"valid": False, "name": None, "uid": None}

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')
    twofa_code = data.get('twofa_code', '').strip()
    session_id = data.get('session_id', '').strip()
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'})
    
    success, result, status, sid = get_fb_token(email, password, twofa_code if twofa_code else None, session_id if session_id else None)
    
    if success:
        token = result['token'] if isinstance(result, dict) else result
        user = check_token(token)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user,
            'status': 'success'
        })
    
    elif status == "2fa_required":
        return jsonify({
            'success': False,
            'status': '2fa_required',
            'session_id': sid,
            'message': result
        })
    
    else:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': result
        })

@app.route('/api/check', methods=['POST'])
def api_check():
    data = request.json
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'success': False, 'error': 'No token'})
    
    user = check_token(token)
    
    if user['valid']:
        return jsonify({'success': True, 'user': user})
    
    return jsonify({'success': False, 'error': 'Invalid token'})

# ==================== PREMIUM UI ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🔐 AHMAD ALI - TOKEN EXTRACTOR</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: linear-gradient(135deg, #0a0f1e 0%, #0f1629 50%, #0a0f1e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.04) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(0, 200, 255, 0.04) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }
        .container { max-width: 550px; margin: 0 auto; position: relative; z-index: 1; }
        .header { text-align: center; padding: 25px 0 20px; }
        .glow-text {
            font-size: 12px; letter-spacing: 4px; text-transform: uppercase;
            background: linear-gradient(135deg, #00ff88, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-weight: 700; margin-bottom: 8px;
        }
        .main-title {
            font-size: 38px; font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #00ff88, #00ccff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            text-shadow: 0 0 60px rgba(0, 255, 136, 0.5);
            letter-spacing: -1px; margin-bottom: 8px;
        }
        .vip-badge {
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            padding: 5px 15px; border-radius: 30px; font-size: 11px;
            font-weight: 700; color: #000; letter-spacing: 1.5px;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
        }
        .glass-card {
            background: rgba(15, 25, 45, 0.65);
            backdrop-filter: blur(25px);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 28px;
            padding: 28px;
            margin-bottom: 20px;
            box-shadow: 0 25px 50px -10px rgba(0, 0, 0, 0.5);
        }
        .card-title {
            font-size: 20px; font-weight: 600; margin-bottom: 24px;
            display: flex; align-items: center; gap: 12px; color: #fff;
        }
        .card-title i { color: #00ff88; font-size: 24px; }
        .input-group { margin-bottom: 20px; }
        .input-label {
            display: block; font-size: 13px; font-weight: 500;
            margin-bottom: 8px; color: rgba(255,255,255,0.7);
        }
        .premium-input {
            width: 100%;
            background: rgba(0, 0, 0, 0.35);
            border: 1.5px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 15px 18px;
            color: #fff;
            font-size: 15px;
            font-family: 'Plus Jakarta Sans', sans-serif;
            transition: all 0.3s ease;
            outline: none;
        }
        .premium-input:focus {
            border-color: #00ff88;
            background: rgba(0, 255, 136, 0.05);
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.25);
        }
        .btn {
            width: 100%;
            padding: 16px 20px;
            border: none;
            border-radius: 40px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }
        .btn-primary {
            background: linear-gradient(135deg, #00ff88, #00cc6a);
            color: #000;
            box-shadow: 0 10px 25px rgba(0, 255, 136, 0.4);
        }
        .btn-primary:hover {
            transform: translateY(-4px);
            box-shadow: 0 20px 35px rgba(0, 255, 136, 0.5);
        }
        .btn-secondary {
            background: linear-gradient(135deg, #2d3a5e, #1a2744);
            color: #fff;
            margin-top: 12px;
        }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .twofa-section {
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #ffd70015, #ff8c0015);
            border-radius: 20px;
            border: 1px solid #ffd70033;
        }
        .twofa-title { color: #ffd700; font-weight: 600; margin-bottom: 15px; }
        .token-result {
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #00ff8810, #00ccff10);
            border-radius: 20px;
            border: 1px solid #00ff8833;
        }
        .token-display {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 16px;
            padding: 16px;
            margin: 15px 0;
            border: 1px dashed #00ff8866;
            word-break: break-all;
            font-family: monospace;
            font-size: 12px;
            color: #00ff88;
            max-height: 100px;
            overflow-y: auto;
        }
        .user-info {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 15px;
        }
        .user-avatar {
            width: 50px; height: 50px;
            background: linear-gradient(135deg, #00ff88, #00ccff);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            color: #000;
        }
        .copy-btn {
            background: rgba(0, 255, 136, 0.2);
            border: 1px solid #00ff88;
            color: #00ff88;
            padding: 10px 20px;
            border-radius: 30px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            margin-top: 12px;
        }
        .copy-btn:hover { background: #00ff88; color: #000; }
        .loader {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #00ff88;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .toast {
            position: fixed; top: 20px; right: 20px;
            background: linear-gradient(135deg, #00ff88, #00cc6a);
            color: #000; padding: 14px 24px; border-radius: 50px;
            font-weight: 700; box-shadow: 0 15px 40px rgba(0, 255, 136, 0.5);
            transform: translateX(400px); transition: transform 0.4s ease;
            z-index: 1000;
        }
        .toast.show { transform: translateX(0); }
        .toast.error { background: linear-gradient(135deg, #ff4757, #ff1e4d); color: #fff; }
        .footer { text-align: center; padding: 25px; color: rgba(255,255,255,0.35); font-size: 12px; }
        .footer a { color: #00ccff; text-decoration: none; }
        .tab-bar { display: flex; gap: 10px; margin-bottom: 20px; background: rgba(0,0,0,0.2); padding: 6px; border-radius: 40px; }
        .tab {
            flex: 1; padding: 12px 20px; background: transparent;
            border-radius: 40px; cursor: pointer; text-align: center;
            font-weight: 600; font-size: 14px; color: rgba(255,255,255,0.6);
            transition: all 0.3s ease;
        }
        .tab.active { background: linear-gradient(135deg, #00ff8822, #00ccff22); border: 1px solid #00ff88; color: #fff; }
        .section { display: none; }
        .section.active { display: block; }
    </style>
</head>
<body>
    <div class="toast" id="toast"><i class="fas fa-check-circle"></i> <span id="toastMsg"></span></div>
    
    <div class="container">
        <div class="header">
      <div class="glow-text">⚡ PREMIUM VIP EDITION ⚡</div>
            <div class="main-title">AHMAD ALI</div>
            <div style="display: flex; justify-content: center; gap: 15px; margin-top: 5px;">
                <span style="color: rgba(255,255,255,0.7);"><i class="fas fa-crown" style="color: #ffd700;"></i> TOKEN EXTRACTOR</span>
                <span class="vip-badge"><i class="fas fa-shield-alt"></i> 2FA SUPPORT</span>
            </div>
        </div>
        
        <div class="tab-bar">
            <div class="tab active" onclick="switchTab('extract')"><i class="fas fa-key"></i> Extract Token</div>
            <div class="tab" onclick="switchTab('check')"><i class="fas fa-search"></i> Check Token</div>
        </div>
        
        <div id="extractSection" class="section active">
            <div class="glass-card">
                <div class="card-title"><i class="fas fa-unlock-alt"></i> TOKEN EXTRACTOR</div>
                
                <div id="loginForm">
                    <div class="input-group">
                        <label class="input-label"><i class="fas fa-envelope"></i> EMAIL / PHONE</label>
                        <input type="text" id="email" class="premium-input" placeholder="example@email.com">
                    </div>
                    <div class="input-group">
                        <label class="input-label"><i class="fas fa-lock"></i> PASSWORD</label>
                        <input type="password" id="password" class="premium-input" placeholder="••••••••">
                    </div>
                    <button class="btn btn-primary" onclick="extractToken()"><i class="fas fa-bolt"></i> EXTRACT TOKEN</button>
                </div>
                
                <div id="twofaForm" style="display: none;">
                    <div class="twofa-section">
                        <div class="twofa-title"><i class="fas fa-shield-alt"></i> TWO-FACTOR AUTHENTICATION</div>
                        <p style="font-size: 13px; margin-bottom: 15px;">Enter the 6-digit code from Google Authenticator or SMS</p>
                        <div class="input-group">
                            <label class="input-label"><i class="fas fa-key"></i> 2FA CODE</label>
                            <input type="text" id="twofaCode" class="premium-input" placeholder="000000" maxlength="6">
                        </div>
                        <button class="btn btn-primary" onclick="submit2FA()"><i class="fas fa-check"></i> VERIFY 2FA</button>
                        <button class="btn btn-secondary" onclick="resetForm()"><i class="fas fa-arrow-left"></i> BACK</button>
                    </div>
                </div>
                
                <div id="resultSection"></div>
            </div>
        </div>
        
        <div id="checkSection" class="section">
            <div class="glass-card">
                <div class="card-title"><i class="fas fa-search"></i> CHECK TOKEN</div>
                <div class="input-group">
                    <label class="input-label"><i class="fas fa-key"></i> FACEBOOK TOKEN</label>
                    <textarea id="checkTokenInput" class="premium-input" placeholder="Paste token here..." rows="4"></textarea>
                </div>
                <button class="btn btn-primary" onclick="checkToken()"><i class="fas fa-check-circle"></i> VERIFY TOKEN</button>
                <div id="checkResult"></div>
            </div>
        </div>
        
        <div class="footer">
            <i class="fas fa-heart" style="color: #ff4757;"></i> 
            <a href="https://wa.me/+923277348009" target="_blank">AHMAD ALI (RDX)</a> | © 2024
        </div>
    </div>
    
    <script>
        let currentSessionId = null;
        let extractedToken = '';
        
        function showToast(msg, isError = false) {
            const toast = document.getElementById('toast');
            document.getElementById('toastMsg').textContent = msg;
            toast.className = 'toast' + (isError ? ' error' : '');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3500);
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById('extractSection').classList.toggle('active', tab === 'extract');
            document.getElementById('checkSection').classList.toggle('active', tab === 'check');
        }
        
        function resetForm() {
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('twofaForm').style.display = 'none';
            currentSessionId = null;
        }
        
        function showResult(token, user) {
            document.getElementById('resultSection').innerHTML = `
                <div class="token-result">
                    <h4 style="color: #00ff88; margin-bottom: 15px;"><i class="fas fa-check-circle"></i> TOKEN EXTRACTED!</h4>
                    <div class="user-info">
                        <div class="user-avatar"><i class="fas fa-user"></i></div>
                        <div><strong>${user.name}</strong><br><small>UID: ${user.uid}</small></div>
                    </div>
                    <div class="token-display">${token}</div>
                    <button class="copy-btn" onclick="copyToken()"><i class="fas fa-copy"></i> COPY TOKEN</button>
                </div>
            `;
            extractedToken = token;
            document.getElementById('loginForm').style.display = 'none';
            document.getElementById('twofaForm').style.display = 'none';
        }
        
        function copyToken() {
            navigator.clipboard.writeText(extractedToken);
            showToast('Token copied! ✓');
        }
        
        async function extractToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) { showToast('Enter email and password!', true); return; }
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> EXTRACTING...';
            
            try {
                const res = await fetch('/api/extract', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password, session_id: currentSessionId})
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast('Token extracted! ✓');
                    showResult(data.token, data.user);
                } else if (data.status === '2fa_required') {
                    showToast('2FA Required - Enter code');
                    document.getElementById('loginForm').style.display = 'none';
                    document.getElementById('twofaForm').style.display = 'block';
                    currentSessionId = data.session_id;
                } else {
                    showToast(data.error || 'Extraction failed', true);
                }
            } catch (e) {
                showToast('Network error - Try again', true);
            }
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-bolt"></i> EXTRACT TOKEN';
        }
        
        async function submit2FA() {
            const code = document.getElementById('twofaCode').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!code || code.length < 6) { showToast('Enter valid 2FA code!', true); return; }
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> VERIFYING...';
            
            try {
                const res = await fetch('/api/extract', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password, twofa_code: code, session_id: currentSessionId})
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast('2FA Verified! ✓');
                    showResult(data.token, data.user);
                } else {
                    showToast(data.error || 'Invalid 2FA code', true);
                }
            } catch (e) {
                showToast('Verification error', true);
            }
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check"></i> VERIFY 2FA';
        }
        
        async function checkToken() {
            const token = document.getElementById('checkTokenInput').value.trim();
            if (!token) { showToast('Paste a token!', true); return; }
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> CHECKING...';
            
            try {
                const res = await fetch('/api/check', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token})
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast(`Valid - ${data.user.name}`);
                    document.getElementById('checkResult').innerHTML = `
                        <div class="token-result">
                            <h4 style="color: #00ff88;"><i class="fas fa-check-circle"></i> TOKEN VALID</h4>
                            <div class="user-info">
                                <div class="user-avatar"><i class="fas fa-user"></i></div>
                                <div><strong>${data.user.name}</strong><br><small>UID: ${data.user.uid}</small></div>
                            </div>
                        </div>
                    `;
                } else {
                    showToast('Invalid token', true);
                    document.getElementById('checkResult').innerHTML = '<div style="color: #ff4757; margin-top: 20px;"><i class="fas fa-times-circle"></i> Invalid Token</div>';
                }
            } catch (e) {
                showToast('Check error', true);
            }
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-check-circle"></i> VERIFY TOKEN';
        }
    </script>
</body>
</html>
'''

# ==================== MAIN ====================
if __name__ == '__main__':
    print("\033[92m" + "="*50 + "\033[0m")
    print("\033[93m🔐 AHMAD ALI - FB TOKEN EXTRACTOR (2FA FIXED) 🔐\033[0m")
    print("\033[92m" + "="*50 + "\033[0m")
    print("\033[96m✅ Server: http://localhost:5000\033[0m")
    print("\033[92m" + "="*50 + "\033[0m")
    app.run(host='0.0.0.0', port=5000, debug=False)
