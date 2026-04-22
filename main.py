#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AHMAD ALI (RDX) - FB TOKEN EXTRACTOR WITH 2FA SUPPORT
# Vercel Ready Single File

import os, sys, time, uuid, json, requests, re, base64, hashlib
from flask import Flask, request, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)

# ==================== GLOBAL SESSION STORE ====================
sessions = {}  # Store session data for 2FA flow

# ==================== TOKEN EXTRACTOR CORE ====================
def get_facebook_token(email, password, twofa_code=None, session_id=None):
    """
    Extract Facebook token with 2FA support
    Returns: (success, token/cookies/error_message, next_step)
    """
    try:
        # Use existing session or create new
        if session_id and session_id in sessions:
            sess = sessions[session_id]['session']
        else:
            sess = requests.Session()
            session_id = str(uuid.uuid4())
            sessions[session_id] = {'session': sess, 'email': email}
        
        # Headers
        ua = "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36"
        headers = {
            "User-Agent": ua,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-FB-Connection-Type": "WIFI",
            "X-FB-Net-HNI": "45005",
            "X-FB-SIM-HNI": "45005",
        }
        
        device_id = str(uuid.uuid4()).replace('-', '')[:16]
        adid = str(uuid.uuid4()).upper()
        
        # If 2FA code provided, verify it
        if twofa_code:
            return verify_2fa_code(sess, session_id, twofa_code)
        
        # Step 1: Initial Login Attempt
        login_data = {
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
            "api_key": "882a8490361da98702bf97a021ddc14d",
            "fb_api_req_friendly_name": "authenticate",
        }
        
        # Try primary endpoint
        resp = sess.post("https://b-api.facebook.com/method/auth.login", 
                        data=login_data, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            # Try alternative endpoint
            headers["Authorization"] = "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32"
            resp = sess.post("https://graph.facebook.com/auth/login", 
                            data=login_data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            try:
                data = resp.json()
            except:
                return False, "Invalid response from Facebook", None, session_id
            
            # Check for access token (no 2FA)
            if "access_token" in data:
                token = data["access_token"]
                cookies = sess.cookies.get_dict()
                # Clean up session
                if session_id in sessions:
                    del sessions[session_id]
                return True, {"token": token, "cookies": cookies}, "success", None
            
            # Check for 2FA requirement
            elif "error" in data:
                error = data["error"]
                error_code = error.get("code", 0)
                error_msg = error.get("message", "")
                
                # 2FA Required
                if error_code == 403 or "two-factor" in error_msg.lower() or "login_approval" in error_msg.lower():
                    # Store session for 2FA flow
                    sessions[session_id]['login_data'] = login_data
                    sessions[session_id]['headers'] = headers
                    
                    # Try to get 2FA methods
                    twofa_info = get_2fa_methods(sess, session_id)
                    
                    return False, "2FA Required", "2fa_required", session_id
                
                # Wrong password
                elif "incorrect" in error_msg.lower() or error_code == 401:
                    return False, "Incorrect email or password", "error", None
                
                # Checkpoint required
                elif "checkpoint" in error_msg.lower():
                    return False, "Account needs verification. Login on browser first.", "error", None
                
                else:
                    return False, error_msg, "error", None
            
            # Check for session key (older format)
            elif "session_key" in data:
                token = data["session_key"]
                cookies = sess.cookies.get_dict()
                if session_id in sessions:
                    del sessions[session_id]
                return True, {"token": token, "cookies": cookies}, "success", None
        
        return False, f"HTTP Error: {resp.status_code}", "error", None
        
    except requests.exceptions.ConnectionError:
        return False, "Connection error - check internet", "error", None
    except requests.exceptions.Timeout:
        return False, "Request timeout - try again", "error", None
    except Exception as e:
        return False, f"Error: {str(e)}", "error", None

def get_2fa_methods(sess, session_id):
    """Try to get available 2FA methods"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        # Check if we can get 2FA options
        resp = sess.get("https://m.facebook.com/two_factor/authentication/", 
                       headers=headers, allow_redirects=True)
        
        methods = []
        if "authenticator" in resp.text.lower():
            methods.append("authenticator")
        if "sms" in resp.text.lower():
            methods.append("sms")
        if "notification" in resp.text.lower():
            methods.append("notification")
        
        sessions[session_id]['twofa_methods'] = methods
        return methods
    except:
        return ["authenticator", "sms"]

def verify_2fa_code(sess, session_id, twofa_code):
    """Verify 2FA code and complete login"""
    try:
        if session_id not in sessions:
            return False, "Session expired. Login again.", "error", None
        
        login_data = sessions[session_id].get('login_data', {})
        headers = sessions[session_id].get('headers', {})
        
        # Add 2FA code to login data
        login_data['twofactor_code'] = twofa_code
        login_data['machine_id'] = str(uuid.uuid4())
        login_data['confirmed'] = "true"
        login_data['currently_logged_in_userid'] = "0"
        
        # Try to complete login with 2FA
        resp = sess.post("https://b-api.facebook.com/method/auth.login", 
                        data=login_data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            data = resp.json()
            
            if "access_token" in data:
                token = data["access_token"]
                cookies = sess.cookies.get_dict()
                del sessions[session_id]
                return True, {"token": token, "cookies": cookies}, "success", None
            
            elif "session_key" in data:
                token = data["session_key"]
                cookies = sess.cookies.get_dict()
                del sessions[session_id]
                return True, {"token": token, "cookies": cookies}, "success", None
            
            elif "error" in data:
                error_msg = data["error"].get("message", "Invalid 2FA code")
                return False, error_msg, "error", session_id
        
        # Try alternative 2FA verification
        twofa_data = {
            "code": twofa_code,
            "method": "authenticator",
            "fb_api_req_friendly_name": "two_factor_verification",
            "api_key": "882a8490361da98702bf97a021ddc14d",
        }
        
        resp2 = sess.post("https://graph.facebook.com/auth/login/twofactor", 
                         data=twofa_data, headers=headers, timeout=30)
        
        if resp2.status_code == 200:
            data2 = resp2.json()
            if "access_token" in data2:
                token = data2["access_token"]
                cookies = sess.cookies.get_dict()
                del sessions[session_id]
                return True, {"token": token, "cookies": cookies}, "success", None
        
        return False, "Invalid 2FA code. Try again.", "error", session_id
        
    except Exception as e:
        return False, f"2FA verification error: {str(e)}", "error", session_id

def check_token_info(token):
    """Get token owner information"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get("https://graph.facebook.com/me?fields=name,id,email", 
                           headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "name": data.get("name", "Unknown"),
                "uid": data.get("id", "Unknown"),
                "email": data.get("email", "N/A")
            }
    except:
        pass
    return {"name": "Unknown", "uid": "Unknown", "email": "N/A"}

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
    
    success, result, status, new_session_id = get_facebook_token(
        email, password, 
        twofa_code if twofa_code else None,
        session_id if session_id else None
    )
    
    if success:
        token = result['token'] if isinstance(result, dict) else result
        user_info = check_token_info(token)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': user_info,
            'status': 'success'
        })
    
    elif status == "2fa_required":
        return jsonify({
            'success': False,
            'status': '2fa_required',
            'session_id': new_session_id,
            'message': result,
            'methods': ['Google Authenticator', 'SMS', 'Facebook Notification']
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
        return jsonify({'success': False, 'error': 'No token provided'})
    
    user_info = check_token_info(token)
    
    if user_info.get('uid') != "Unknown":
        return jsonify({'success': True, 'user': user_info})
    
    return jsonify({'success': False, 'error': 'Invalid or expired token'})

# ==================== PREMIUM HTML UI ====================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🔐 AHMAD ALI - FB TOKEN EXTRACTOR</title>
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
            position: relative;
            overflow-x: hidden;
        }
        
        body::before {
            content: '';
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: radial-gradient(circle at 20% 80%, rgba(0, 255, 136, 0.04) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(0, 200, 255, 0.04) 0%, transparent 50%),
                        radial-gradient(circle at 50% 50%, rgba(255, 0, 212, 0.02) 0%, transparent 60%);
            pointer-events: none;
            z-index: 0;
            animation: bgPulse 8s ease-in-out infinite;
        }
        
        @keyframes bgPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .container { max-width: 550px; margin: 0 auto; position: relative; z-index: 1; }
        
        /* HEADER */
        .header {
            text-align: center;
            padding: 25px 0 20px;
            position: relative;
        }
        
        .glow-text {
            font-size: 12px;
            letter-spacing: 4px;
            text-transform: uppercase;
            background: linear-gradient(135deg, #00ff88, #00ccff, #ff00d4, #00ff88);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            margin-bottom: 8px;
            animation: gradientShift 4s ease infinite;
        }
        
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        
        .main-title {
            font-size: 38px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff, #00ff88, #00ccff);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-shadow: 0 0 60px rgba(0, 255, 136, 0.5);
            letter-spacing: -1px;
            margin-bottom: 8px;
            animation: titleGlow 3s ease-in-out infinite;
        }
        
        @keyframes titleGlow {
            0%, 100% { filter: drop-shadow(0 0 20px #00ff88); }
            50% { filter: drop-shadow(0 0 40px #00ccff); }
        }
        
        .subtitle {
            font-size: 13px;
            color: rgba(255,255,255,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-top: 5px;
        }
        
        .vip-badge {
            background: linear-gradient(135deg, #ffd700, #ff8c00);
            padding: 5px 15px;
            border-radius: 30px;
            font-size: 11px;
            font-weight: 700;
            color: #000;
            letter-spacing: 1.5px;
            box-shadow: 0 0 30px rgba(255, 215, 0, 0.5);
            animation: badgePulse 2s ease infinite;
        }
        
        @keyframes badgePulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        /* GLASS CARD */
        .glass-card {
            background: rgba(15, 25, 45, 0.65);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid rgba(0, 255, 136, 0.2);
            border-radius: 28px;
            padding: 28px;
            margin-bottom: 20px;
            box-shadow: 0 25px 50px -10px rgba(0, 0, 0, 0.5),
                        0 0 0 1px rgba(0, 255, 136, 0.1) inset,
                        0 0 40px rgba(0, 255, 136, 0.1);
            transition: all 0.4s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(0, 255, 136, 0.4);
            box-shadow: 0 30px 60px -10px rgba(0, 0, 0, 0.6),
                        0 0 0 1px rgba(0, 255, 136, 0.2) inset,
                        0 0 60px rgba(0, 255, 136, 0.2);
            transform: translateY(-3px);
        }
        
        .card-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: #fff;
        }
        
        .card-title i {
            color: #00ff88;
            font-size: 24px;
            text-shadow: 0 0 20px #00ff88;
        }
        
        /* INPUTS */
        .input-group { margin-bottom: 20px; }
        
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
            margin-right: 8px;
            font-size: 12px;
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
        
        .premium-input::placeholder {
            color: rgba(255,255,255,0.25);
            font-weight: 300;
        }
        
        /* BUTTONS */
        .btn {
            width: 100%;
            padding: 16px 20px;
            border: none;
            border-radius: 40px;
            font-size: 15px;
            font-weight: 700;
            font-family: 'Plus Jakarta Sans', sans-serif;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
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
            border: 1px solid rgba(255,255,255,0.1);
            margin-top: 12px;
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        /* 2FA SECTION */
        .twofa-section {
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #ffd70015, #ff8c0015);
            border-radius: 20px;
            border: 1px solid #ffd70033;
        }
        
        .twofa-title {
            color: #ffd700;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        /* TOKEN RESULT */
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
            font-family: 'Monaco', 'Menlo', monospace;
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
            width: 50px;
            height: 50px;
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
            font-size: 13px;
            font-weight: 600;
            transition: all 0.3s;
            margin-top: 12px;
        }
        
        .copy-btn:hover {
            background: #00ff88;
            color: #000;
        }
        
        /* LOADER */
        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #00ff88;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* TOAST */
        .toast {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #00ff88, #00cc6a);
            color: #000;
            padding: 14px 24px;
            border-radius: 50px;
            font-weight: 700;
            box-shadow: 0 15px 40px rgba(0, 255, 136, 0.5);
            transform: translateX(400px);
            transition: transform 0.4s ease;
            z-index: 1000;
        }
        
        .toast.show { transform: translateX(0); }
        .toast.error { background: linear-gradient(135deg, #ff4757, #ff1e4d); color: #fff; }
        
        /* FOOTER */
        .footer {
            text-align: center;
            padding: 25px;
            color: rgba(255,255,255,0.35);
            font-size: 12px;
        }
        
        .footer a {
            color: #00ccff;
            text-decoration: none;
        }
        
        /* TABS */
        .tab-bar {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: rgba(0,0,0,0.2);
            padding: 6px;
            border-radius: 40px;
        }
        
        .tab {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border-radius: 40px;
            cursor: pointer;
            text-align: center;
            font-weight: 600;
            font-size: 14px;
            color: rgba(255,255,255,0.6);
            transition: all 0.3s ease;
            border: 1px solid transparent;
        }
        
        .tab i { margin-right: 8px; }
        
        .tab.active {
            background: linear-gradient(135deg, #00ff8822, #00ccff22);
            border-color: #00ff88;
            color: #fff;
        }
        
        .section { display: none; }
        .section.active { display: block; }
    </style>
</head>
<body>
    <div class="toast" id="toast"><i class="fas fa-check-circle"></i> <span id="toastMsg">Message</span></div>
    
    <div class="container">
        <!-- HEADER -->
        <div class="header">
            <div class="glow-text">⚡ PREMIUM VIP EDITION ⚡</div>
            <div class="main-title">AHMAD ALI</div>
            <div class="subtitle">
                <span><i class="fas fa-crown" style="color: #ffd700;"></i> TOKEN EXTRACTOR PRO</span>
                <span class="vip-badge"><i class="fas fa-shield-alt"></i> 2FA BYPASS</span>
            </div>
        </div>
        
        <!-- TAB BAR -->
        <div class="tab-bar">
            <div class="tab active" onclick="switchTab('extract')"><i class="fas fa-key"></i> Token Extract</div>
            <div class="tab" onclick="switchTab('manual')"><i class="fas fa-paste"></i> Check Token</div>
        </div>
        
        <!-- EXTRACT SECTION -->
        <div id="extractSection" class="section active">
            <div class="glass-card">
                <div class="card-title">
                    <i class="fas fa-unlock-alt"></i>
                    <span>FACEBOOK TOKEN EXTRACTOR</span>
                </div>
                
                <div id="loginForm">
                    <div class="input-group">
                        <label class="input-label"><i class="fas fa-envelope"></i> EMAIL / PHONE</label>
                        <input type="text" id="email" class="premium-input" placeholder="example@email.com">
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label"><i class="fas fa-lock"></i> PASSWORD</label>
                        <input type="password" id="password" class="premium-input" placeholder="••••••••">
                    </div>
                    
                    <button class="btn btn-primary" onclick="extractToken()">
                        <i class="fas fa-bolt"></i> EXTRACT TOKEN
                    </button>
                </div>
                
                <div id="twofaForm" style="display: none;">
                    <div class="twofa-section">
                        <div class="twofa-title">
                            <i class="fas fa-shield-alt"></i> TWO-FACTOR AUTHENTICATION
                        </div>
                        <p style="font-size: 13px; margin-bottom: 15px; color: rgba(255,255,255,0.8);">
                            Enter the 6-digit code from Google Authenticator or SMS
                        </p>
                        <div class="input-group">
                            <label class="input-label"><i class="fas fa-key"></i> 2FA CODE</label>
                            <input type="text" id="twofaCode" class="premium-input" placeholder="000000" maxlength="6">
                        </div>
                        <button class="btn btn-primary" onclick="submit2FA()">
                            <i class="fas fa-check"></i> VERIFY 2FA
                        </button>
                        <button class="btn btn-secondary" onclick="resetForm()">
                            <i class="fas fa-arrow-left"></i> BACK TO LOGIN
                        </button>
                    </div>
                </div>
                
                <div id="resultSection"></div>
            </div>
        </div>
        
        <!-- MANUAL CHECK SECTION -->
        <div id="manualSection" class="section">
            <div class="glass-card">
                <div class="card-title">
                    <i class="fas fa-search"></i>
                    <span>CHECK TOKEN VALIDITY</span>
                </div>
                
                <div class="input-group">
                    <label class="input-label"><i class="fas fa-key"></i> FACEBOOK TOKEN</label>
                    <textarea id="checkToken" class="premium-input" placeholder="Paste your Facebook token here..." rows="4"></textarea>
                </div>
                
                <button class="btn btn-primary" onclick="checkToken()">
                    <i class="fas fa-check-circle"></i> VERIFY TOKEN
                </button>
                
                <div id="checkResult"></div>
            </div>
        </div>
        
        <!-- FOOTER -->
        <div class="footer">
            <i class="fas fa-heart" style="color: #ff4757;"></i> 
            <a href="https://wa.me/+923277348009" target="_blank"><i class="fab fa-whatsapp"></i> AHMAD ALI (RDX)</a> 
            | © 2024 FB TOKEN EXTRACTOR
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
            document.getElementById('manualSection').classList.toggle('active', tab === 'manual');
        }
        
        function resetForm() {
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('twofaForm').style.display = 'none';
            currentSessionId = null;
        }
        
        function showResult(token, user) {
            const html = `
                <div class="token-result">
                    <h4 style="color: #00ff88; margin-bottom: 15px;">
                        <i class="fas fa-check-circle"></i> TOKEN EXTRACTED SUCCESSFULLY!
                    </h4>
                    
                    <div class="user-info">
                        <div class="user-avatar"><i class="fas fa-user"></i></div>
                        <div>
                            <strong>${user.name}</strong><br>
                            <small style="color: rgba(255,255,255,0.6);">UID: ${user.uid}</small>
                        </div>
                    </div>
                    
                    <div class="token-display" id="tokenDisplay">${token}</div>
                    
                    <button class="copy-btn" onclick="copyToken()">
                        <i class="fas fa-copy"></i> COPY TOKEN
                    </button>
                </div>
            `;
            
            document.getElementById('resultSection').innerHTML = html;
            extractedToken = token;
        }
        
        function copyToken() {
            navigator.clipboard.writeText(extractedToken);
            showToast('Token copied to clipboard! ✓');
        }
        
        async function extractToken() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!email || !password) {
                showToast('Enter email and password!', true);
                return;
            }
            
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
                    showToast('Token extracted successfully! ✓');
                    showResult(data.token, data.user);
                    document.getElementById('loginForm').style.display = 'none';
                    document.getElementById('twofaForm').style.display = 'none';
                } else if (data.status === '2fa_required') {
                    showToast('2FA Required - Enter code', false);
                    document.getElementById('loginForm').style.display = 'none';
                    document.getElementById('twofaForm').style.display = 'block';
                    currentSessionId = data.session_id;
                } else {
                    showToast(data.error || 'Login failed', true);
                }
            } catch (e) {
                showToast('Network error', true);
            }
            
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-bolt"></i> EXTRACT TOKEN';
        }
        
        async function submit2FA() {
            const code = document.getElementById('twofaCode').value;
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            
            if (!code || code.length < 6) {
                showToast('Enter valid 2FA code!', true);
                return;
            }
            
            const btn = event.target;
            btn.disabled = true;
            btn.innerHTML = '<span class="loader"></span> VERIFYING...';
            
            try {
                const res = await fetch('/api/extract', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        email, password, 
                        twofa_code: code, 
                        session_id: currentSessionId
                    })
                });
                const data = await res.json();
                
                if (data.success) {
                    showToast('2FA Verified! Token extracted ✓');
                    showResult(data.token, data.user);
                    document.getElementById('twofaForm').style.display = 'none';
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
            const token = document.getElementById('checkToken').value.trim();
            
            if (!token) {
                showToast('Paste a token first!', true);
                return;
            }
            
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
                    showToast(`Valid Token - ${data.user.name}`);
                    
                    const html = `
                        <div class="token-result" style="margin-top: 20px;">
                            <h4 style="color: #00ff88; margin-bottom: 15px;">
                                <i class="fas fa-check-circle"></i> TOKEN VALID!
                            </h4>
                            <div class="user-info">
                                <div class="user-avatar"><i class="fas fa-user"></i></div>
                                <div>
                                    <strong>${data.user.name}</strong><br>
                                    <small style="color: rgba(255,255,255,0.6);">UID: ${data.user.uid}</small>
                                </div>
                            </div>
                            <div class="token-display">${token}</div>
                            <button class="copy-btn" onclick="navigator.clipboard.writeText('${token}');showToast('Token copied!')">
                                <i class="fas fa-copy"></i> COPY TOKEN
                            </button>
                        </div>
                    `;
                    document.getElementById('checkResult').innerHTML = html;
                } else {
                    showToast('Invalid or expired token', true);
                    document.getElementById('checkResult').innerHTML = `
                        <div style="color: #ff4757; margin-top: 20px; text-align: center;">
                            <i class="fas fa-times-circle"></i> Invalid Token
                        </div>
                    `;
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

# ==================== VERCEL HANDLER ====================
def handler(request, context):
    return app(request.environ, lambda status, headers: None)

# ==================== MAIN ====================
if __name__ == '__main__':
    print("\033[92m" + "="*50 + "\033[0m")
    print("\033[93m🔐 AHMAD ALI (RDX) - FB TOKEN EXTRACTOR PRO 🔐\033[0m")
    print("\033[92m" + "="*50 + "\033[0m")
    print("\033[96m✅ 2FA BYPASS SUPPORT ENABLED\033[0m")
    print("\033[96m🌐 Server running at: http://localhost:5000\033[0m")
    print("\033[92m" + "="*50 + "\033[0m")
    app.run(host='0.0.0.0', port=5000, debug=False)
