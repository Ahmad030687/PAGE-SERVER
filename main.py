#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AHMAD ALI (RDX) - 100% WORKING TOKEN EXTRACTOR + CHECKER

import uuid, json, requests
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)
sessions = {}

# ==================== 100% WORKING TOKEN EXTRACTOR ====================
def extract_fb_token(email, password, twofa_code=None, session_id=None):
    try:
        # Create or reuse session
        if session_id and session_id in sessions:
            sess = sessions[session_id]
        else:
            sess = requests.Session()
            session_id = str(uuid.uuid4())
            sessions[session_id] = sess
        
        device_id = str(uuid.uuid4()).replace('-', '')[:16]
        adid = str(uuid.uuid4()).upper()
        
        # Headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.135 Mobile Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-FB-Connection-Type": "WIFI",
        }
        
        # If 2FA code provided
        if twofa_code:
            return verify_2fa_code(sess, session_id, twofa_code, email, headers)
        
        # Login data
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
            "api_key": "882a8490361da98702bf97a021ddc14d",
        }
        
        # Try main endpoint
        resp = sess.post("https://b-api.facebook.com/method/auth.login", 
                        data=data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            
            # Success - Got token
            if "access_token" in result:
                token = result["access_token"]
                del sessions[session_id]
                return True, token, "success", None
            
            # 2FA Required
            elif "error" in result:
                err = result["error"]
                err_msg = str(err.get("message", "")).lower()
                err_code = err.get("code", 0)
                
                if err_code == 403 or "two-factor" in err_msg or "login_approval" in err_msg:
                    sessions[session_id] = sess
                    return False, "2FA Required", "2fa", session_id
                
                elif "incorrect" in err_msg or err_code == 401:
                    return False, "Incorrect email or password", "error", None
                
                elif "checkpoint" in err_msg:
                    return False, "Account locked - Verify on browser", "error", None
                
                else:
                    return False, err.get("message", "Login failed"), "error", None
        
        # Try alternative endpoint
        headers2 = headers.copy()
        headers2["Authorization"] = "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32"
        headers2["Host"] = "graph.facebook.com"
        
        data2 = {
            "adid": adid,
            "email": email,
            "password": password,
            "format": "json",
            "device_id": device_id,
            "cpl": "true",
            "credentials_type": "device_based_login_password",
            "generate_session_cookies": "1",
            "source": "login",
            "method": "auth.login",
        }
        
        resp2 = sess.post("https://graph.facebook.com/auth/login", 
                         data=data2, headers=headers2, timeout=30)
        
        if resp2.status_code == 200:
            result2 = resp2.json()
            if "access_token" in result2:
                token = result2["access_token"]
                del sessions[session_id]
                return True, token, "success", None
        
        return False, "Network error - Try again", "error", None
        
    except requests.exceptions.ConnectionError:
        return False, "No internet connection", "error", None
    except Exception as e:
        return False, f"Error: {str(e)}", "error", None

def verify_2fa_code(sess, session_id, code, email, headers):
    try:
        data = {
            "code": code,
            "email": email,
            "method": "authenticator",
            "fb_api_req_friendly_name": "two_factor_verification",
            "api_key": "882a8490361da98702bf97a021ddc14d",
        }
        
        resp = sess.post("https://graph.facebook.com/auth/login/twofactor", 
                        data=data, headers=headers, timeout=30)
        
        if resp.status_code == 200:
            result = resp.json()
            if "access_token" in result:
                token = result["access_token"]
                del sessions[session_id]
                return True, token, "success", None
        
        return False, "Invalid 2FA code", "error", session_id
        
    except Exception as e:
        return False, f"2FA error: {str(e)}", "error", session_id

def check_token_validity(token):
    try:
        headers = {"Authorization": f"Bearer {token}"}
        resp = requests.get("https://graph.facebook.com/me?fields=name,id", 
                           headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {"valid": True, "name": data.get("name", "Unknown"), 
                   "uid": data.get("id", "Unknown")}
    except:
        pass
    return {"valid": False, "name": None, "uid": None}

# ==================== FLASK ROUTES ====================
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/extract', methods=['POST'])
def extract():
    d = request.json
    email = d.get('email', '').strip()
    pwd = d.get('password', '')
    code = d.get('code', '').strip()
    sid = d.get('sid', '').strip()
    
    if not email or not pwd:
        return jsonify({'ok': False, 'err': 'Email and password required'})
    
    ok, msg, status, new_sid = extract_fb_token(email, pwd, code if code else None, sid if sid else None)
    
    if ok:
        token = msg
        user = check_token_validity(token)
        return jsonify({'ok': True, 'token': token, 'user': user})
    elif status == "2fa":
        return jsonify({'ok': False, 'status': '2fa', 'sid': new_sid, 'msg': msg})
    else:
        return jsonify({'ok': False, 'err': msg})

@app.route('/api/check', methods=['POST'])
def check():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'ok': False, 'err': 'No token'})
    
    user = check_token_validity(token)
    if user['valid']:
        return jsonify({'ok': True, 'user': user})
    return jsonify({'ok': False, 'err': 'Invalid token'})

# ==================== PREMIUM UI (COMPACT) ====================
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔐 AHMAD ALI - TOKEN EXTRACTOR</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Plus Jakarta Sans',sans-serif;background:linear-gradient(135deg,#0a0f1e,#0f1629);min-height:100vh;color:#fff;padding:20px}
        .container{max-width:500px;margin:0 auto}
        .header{text-align:center;padding:20px 0}
        .glow{font-size:12px;letter-spacing:4px;background:linear-gradient(135deg,#00ff88,#00ccff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-weight:700}
        .title{font-size:34px;font-weight:800;background:linear-gradient(135deg,#fff,#00ff88,#00ccff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
        .card{background:rgba(15,25,45,0.7);backdrop-filter:blur(20px);border:1px solid #00ff8833;border-radius:24px;padding:24px;margin-bottom:16px}
        .card-title{font-size:18px;margin-bottom:20px;display:flex;align-items:center;gap:10px}
        .card-title i{color:#00ff88}
        input,textarea{width:100%;background:#0000004d;border:1px solid #ffffff22;border-radius:16px;padding:14px 16px;color:#fff;font-family:inherit;margin-bottom:16px;outline:none;resize:vertical}
        input:focus,textarea:focus{border-color:#00ff88;box-shadow:0 0 20px #00ff8844}
        .btn{width:100%;padding:15px;border:none;border-radius:40px;font-weight:700;font-size:15px;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;transition:0.3s}
        .btn-green{background:linear-gradient(135deg,#00ff88,#00cc6a);color:#000}
        .btn-green:hover{transform:translateY(-3px);box-shadow:0 15px 30px #00ff8866}
        .btn-blue{background:linear-gradient(135deg,#2d3a5e,#1a2744);color:#fff;margin-top:12px}
        .btn:disabled{opacity:0.5;cursor:not-allowed}
        .twofa-box{background:#ffd70015;border:1px solid #ffd70033;border-radius:16px;padding:20px;margin-top:16px}
        .result-box{background:#00ff8810;border:1px solid #00ff8833;border-radius:16px;padding:20px;margin-top:16px}
        .token{background:#00000080;border-radius:12px;padding:14px;font-family:monospace;font-size:12px;color:#00ff88;word-break:break-all;margin:12px 0}
        .user{display:flex;align-items:center;gap:12px;margin:12px 0}
        .avatar{width:45px;height:45px;background:linear-gradient(135deg,#00ff88,#00ccff);border-radius:50%;display:flex;align-items:center;justify-content:center;color:#000;font-size:20px}
        .copy-btn{background:#00ff8833;border:1px solid #00ff88;color:#00ff88;padding:10px 16px;border-radius:30px;cursor:pointer;font-weight:600;font-size:13px}
        .loader{width:20px;height:20px;border:2px solid #ffffff33;border-radius:50%;border-top-color:#00ff88;animation:spin 0.8s infinite}
        @keyframes spin{to{transform:rotate(360deg)}}
        .toast{position:fixed;top:20px;right:20px;background:#00ff88;color:#000;padding:12px 20px;border-radius:40px;font-weight:700;transform:translateX(400px);transition:0.4s;z-index:1000}
        .toast.show{transform:translateX(0)}
        .toast.error{background:#ff4757;color:#fff}
        .tab-bar{display:flex;gap:8px;background:#00000033;padding:6px;border-radius:40px;margin-bottom:20px}
        .tab{flex:1;padding:12px;text-align:center;border-radius:40px;cursor:pointer;font-weight:600;color:#ffffff99;transition:0.3s}
        .tab.active{background:#00ff8822;border:1px solid #00ff88;color:#fff}
        .section{display:none}
        .section.active{display:block}
        .footer{text-align:center;padding:20px;color:#888;font-size:12px}
        .footer a{color:#00ccff}
    </style>
</head>
<body>
    <div class="toast" id="toast"><i class="fas fa-check-circle"></i> <span id="toastMsg"></span></div>
    
    <div class="container">
        <div class="header">
            <div class="glow">⚡ PREMIUM VIP ⚡</div>
            <div class="title">AHMAD ALI</div>
            <div style="margin-top:8px"><span style="background:#ffd700;color:#000;padding:4px 16px;border-radius:30px;font-size:11px;font-weight:700"><i class="fas fa-crown"></i> TOKEN MASTER</span></div>
        </div>
        
        <div class="tab-bar">
            <div class="tab active" onclick="switchTab('extract')"><i class="fas fa-key"></i> Extract</div>
            <div class="tab" onclick="switchTab('check')"><i class="fas fa-search"></i> Check</div>
        </div>
        
        <!-- EXTRACT SECTION -->
        <div id="extractSection" class="section active">
            <div class="card">
                <div class="card-title"><i class="fas fa-unlock-alt"></i> TOKEN EXTRACTOR</div>
                
                <div id="loginForm">
                    <input type="text" id="email" placeholder="Email / Phone">
                    <input type="password" id="password" placeholder="Password">
                    <button class="btn btn-green" onclick="extractToken()"><i class="fas fa-bolt"></i> EXTRACT TOKEN</button>
                </div>
                
                <div id="twofaForm" style="display:none">
                    <div class="twofa-box">
                        <div style="color:#ffd700;font-weight:600;margin-bottom:12px"><i class="fas fa-shield-alt"></i> 2FA VERIFICATION</div>
                        <p style="font-size:13px;margin-bottom:16px">Enter 6-digit code from Google Authenticator or SMS</p>
                        <input type="text" id="twofaCode" placeholder="000000" maxlength="6">
                        <button class="btn btn-green" onclick="submit2FA()"><i class="fas fa-check"></i> VERIFY 2FA</button>
                        <button class="btn btn-blue" onclick="resetForm()"><i class="fas fa-arrow-left"></i> BACK</button>
                    </div>
                </div>
                
                <div id="resultSection"></div>
            </div>
        </div>
        
        <!-- CHECK SECTION -->
        <div id="checkSection" class="section">
            <div class="card">
                <div class="card-title"><i class="fas fa-search"></i> CHECK TOKEN</div>
                <textarea id="checkToken" placeholder="Paste Facebook token here..." rows="4"></textarea>
                <button class="btn btn-green" onclick="checkToken()"><i class="fas fa-check-circle"></i> VERIFY TOKEN</button>
                <div id="checkResult"></div>
            </div>
        </div>
        
        <div class="footer">
            <i class="fas fa-heart" style="color:#ff4757"></i> 
            <a href="https://wa.me/+923277348009">AHMAD ALI (RDX)</a> | 100% WORKING
        </div>
    </div>
    
    <script>
        let currentSid = null;
        let currentToken = '';
        
        function showToast(m,e=!1){let t=document.getElementById('toast');document.getElementById('toastMsg').textContent=m;t.className='toast'+(e?' error':'');t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000)}
        function switchTab(t){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));event.target.classList.add('active');document.getElementById('extractSection').classList.toggle('active',t==='extract');document.getElementById('checkSection').classList.toggle('active',t==='check')}
        function resetForm(){document.getElementById('loginForm').style.display='block';document.getElementById('twofaForm').style.display='none';currentSid=null}
        
        function showResult(token,user){
            document.getElementById('resultSection').innerHTML=`
                <div class="result-box">
                    <h4 style="color:#00ff88;margin-bottom:15px"><i class="fas fa-check-circle"></i> TOKEN EXTRACTED!</h4>
                    <div class="user">
                        <div class="avatar"><i class="fas fa-user"></i></div>
                        <div><strong>${user.name}</strong><br><small>UID: ${user.uid}</small></div>
                    </div>
                    <div class="token">${token}</div>
                    <button class="copy-btn" onclick="copyToken()"><i class="fas fa-copy"></i> COPY TOKEN</button>
                </div>
            `;
            currentToken=token;
            document.getElementById('loginForm').style.display='none';
            document.getElementById('twofaForm').style.display='none';
        }
        
        function copyToken(){navigator.clipboard.writeText(currentToken);showToast('Token copied! ✓')}
        
        async function extractToken(){
            let e=document.getElementById('email').value,p=document.getElementById('password').value;
            if(!e||!p){showToast('Enter email and password!',!0);return}
            let b=event.target;b.disabled=!0;b.innerHTML='<span class="loader"></span> EXTRACTING...';
            try{
                let r=await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p,sid:currentSid})});
                let d=await r.json();
                if(d.ok){showToast('Token extracted! ✓');showResult(d.token,d.user)}
                else if(d.status==='2fa'){showToast('2FA Required - Enter code');document.getElementById('loginForm').style.display='none';document.getElementById('twofaForm').style.display='block';currentSid=d.sid}
                else{showToast(d.err||'Failed',!0)}
            }catch(x){showToast('Network error',!0)}
            b.disabled=!1;b.innerHTML='<i class="fas fa-bolt"></i> EXTRACT TOKEN';
        }
        
        async function submit2FA(){
            let c=document.getElementById('twofaCode').value,e=document.getElementById('email').value,p=document.getElementById('password').value;
            if(!c||c.length<6){showToast('Enter valid 2FA code!',!0);return}
            let b=event.target;b.disabled=!0;b.innerHTML='<span class="loader"></span> VERIFYING...';
            try{
                let r=await fetch('/api/extract',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:e,password:p,code:c,sid:currentSid})});
                let d=await r.json();
                if(d.ok){showToast('2FA Verified! ✓');showResult(d.token,d.user)}
                else{showToast(d.err||'Invalid code',!0)}
            }catch(x){showToast('Error',!0)}
            b.disabled=!1;b.innerHTML='<i class="fas fa-check"></i> VERIFY 2FA';
        }
        
        async function checkToken(){
            let t=document.getElementById('checkToken').value.trim();
            if(!t){showToast('Paste a token!',!0);return}
            let b=event.target;b.disabled=!0;b.innerHTML='<span class="loader"></span> CHECKING...';
            try{
                let r=await fetch('/api/check',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:t})});
                let d=await r.json();
                if(d.ok){
                    showToast(`Valid - ${d.user.name}`);
                    document.getElementById('checkResult').innerHTML=`
                        <div class="result-box">
                            <h4 style="color:#00ff88"><i class="fas fa-check-circle"></i> TOKEN VALID</h4>
                            <div class="user">
                                <div class="avatar"><i class="fas fa-user"></i></div>
                                <div><strong>${d.user.name}</strong><br><small>UID: ${d.user.uid}</small></div>
                            </div>
                        </div>
                    `;
                }else{
                    showToast('Invalid token',!0);
                    document.getElementById('checkResult').innerHTML='<div style="color:#ff4757;margin-top:16px"><i class="fas fa-times-circle"></i> Invalid Token</div>';
                }
            }catch(x){showToast('Error',!0)}
            b.disabled=!1;b.innerHTML='<i class="fas fa-check-circle"></i> VERIFY TOKEN';
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("\033[92m" + "="*50 + "\033[0m")
    print("\033[93m🔐 AHMAD ALI - 100% WORKING TOKEN EXTRACTOR 🔐\033[0m")
    print("\033[92m" + "="*50 + "\033[0m")
    print("\033[96m✅ http://localhost:5000\033[0m")
    print("\033[92m" + "="*50 + "\033[0m")
    app.run(host='0.0.0.0', port=5000, debug=False)
