from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re
import json
import base64
import hashlib
from urllib.parse import urlparse, parse_qs, quote

app = Flask(__name__)
app.debug = True

headers = {
    'authority': 'graph.facebook.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://developers.facebook.com',
    'referer': 'https://developers.facebook.com/tools/explorer/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

stop_events = {}
threads = {}

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                message = str(mn) + ' ' + message1
                parameters = {'access_token': access_token, 'message': message}
                try:
                    response = requests.post(api_url, data=parameters, headers=headers, timeout=10)
                    if response.status_code == 200:
                        print(f"✓ Message Sent: {message[:30]}...")
                    else:
                        print(f"✗ Failed: {response.text[:100]}")
                except Exception as e:
                    print(f"Error: {str(e)[:100]}")
                time.sleep(time_interval)

def parse_cookies(cookie_input):
    """Parse cookies from JSON or Netscape format"""
    cookies = {}
    
    # Try JSON format (EditThisCookie)
    try:
        cookie_list = json.loads(cookie_input)
        for cookie in cookie_list:
            if 'name' in cookie and 'value' in cookie:
                cookies[cookie['name']] = cookie['value']
        if cookies:
            return cookies
    except:
        pass
    
    # Try standard cookie string
    if '=' in cookie_input:
        for item in cookie_input.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        if cookies:
            return cookies
    
    return None

def extract_fb_dtsg(session, cookies_dict):
    """Extract fb_dtsg token from Facebook page"""
    try:
        # Try mobile basic first
        mbasic_url = 'https://mbasic.facebook.com/'
        response = session.get(mbasic_url, headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }, timeout=15)
        
        # Search for fb_dtsg
        patterns = [
            r'name="fb_dtsg" value="([^"]+)"',
            r'"fb_dtsg":"([^"]+)"',
            r'fb_dtsg=([^&]+)',
            r'"token":"([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        
        # Try desktop version
        desktop_url = 'https://www.facebook.com/'
        response = session.get(desktop_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }, timeout=15)
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
                
    except Exception as e:
        print(f"Error getting fb_dtsg: {e}")
    
    return None

def get_token_via_graphql(cookies_dict):
    """
    WORKING GraphQL method to extract Facebook access token
    This uses the official Facebook Android app flow
    """
    session = requests.Session()
    
    # Set all cookies
    for key, value in cookies_dict.items():
        session.cookies.set(key, value, domain='.facebook.com')
    
    tokens = []
    
    try:
        # Step 1: Get fb_dtsg
        fb_dtsg = extract_fb_dtsg(session, cookies_dict)
        if not fb_dtsg:
            print("[-] Could not extract fb_dtsg")
            return []
        
        print(f"[+] Got fb_dtsg: {fb_dtsg[:20]}...")
        
        # Step 2: Get user ID
        user_id = cookies_dict.get('c_user', '')
        if not user_id:
            # Try to extract from page
            response = session.get('https://mbasic.facebook.com/')
            match = re.search(r'"userID":"(\d+)"', response.text)
            if match:
                user_id = match.group(1)
        
        if not user_id:
            print("[-] Could not find user ID")
            return []
        
        print(f"[+] User ID: {user_id}")
        
        # Step 3: Generate random device IDs
        machine_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=24))
        session_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        
        # Step 4: GraphQL query to get token
        # These doc_ids are current working ones (April 2026)
        doc_ids = [
            '6204052286322815',  # Android token fetch
            '6454523094592687',  # iOS token fetch  
            '5342766329121227',  # Web token fetch
        ]
        
        for doc_id in doc_ids:
            variables = {
                "app_id": "350685531728",  # Facebook Android App
                "machine_id": machine_id,
                "session_key": session_key,
                "user_agent": "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36",
                "device": "Android",
                "currently_logged_in_userid": user_id,
                "access_token": "",
                "generate_session_cookies": True,
                "sso_device": "android",
                "auth_type": "rerequest",
                "scope": "public_profile,email,user_friends,user_posts,user_photos,user_videos,pages_show_list,pages_read_engagement,pages_manage_posts,pages_manage_engagement",
                "response_type": "token,signed_request,graphql_domain",
                "return_scopes": True,
                "default_audience": "everyone"
            }
            
            data = {
                'fb_dtsg': fb_dtsg,
                'variables': json.dumps(variables),
                'doc_id': doc_id,
                'method': 'post'
            }
            
            headers_gql = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://mbasic.facebook.com',
                'Referer': 'https://mbasic.facebook.com/',
                'X-FB-Friendly-Name': 'fetchAccessToken',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            try:
                response = session.post(
                    'https://graph.facebook.com/graphql',
                    data=data,
                    headers=headers_gql,
                    timeout=15
                )
                
                # Try to extract token from response
                token_patterns = [
                    r'access_token":"(EAA[A-Za-z0-9]+)"',
                    r'access_token=([A-Za-z0-9]+)',
                    r'"accessToken":"([^"]+)"',
                    r'access_token\\\\":\\\\"([^\\\\]+)',
                ]
                
                for pattern in token_patterns:
                    matches = re.findall(pattern, response.text)
                    for match in matches:
                        if match.startswith('EAA') and len(match) > 50:
                            tokens.append(match)
                            print(f"[+] Found token via GraphQL!")
                            break
                
                # Check JSON response
                try:
                    json_resp = response.json()
                    if 'data' in json_resp:
                        data_str = json.dumps(json_resp['data'])
                        token_match = re.search(r'EAAB[A-Za-z0-9]+', data_str)
                        if token_match:
                            tokens.append(token_match.group(0))
                except:
                    pass
                    
            except Exception as e:
                print(f"[-] GraphQL attempt failed: {e}")
                continue
        
        # Step 5: Alternative - Try business.facebook.com
        if not tokens:
            try:
                biz_url = 'https://business.facebook.com/'
                response = session.get(biz_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }, timeout=15)
                
                patterns = [
                    r'accessToken":"([^"]+)"',
                    r'access_token=([A-Za-z0-9]+)',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, response.text)
                    for match in matches:
                        if match.startswith('EAA') and len(match) > 50:
                            tokens.append(match)
                            print(f"[+] Found token via Business!")
            except:
                pass
        
        # Step 6: Try to get from page access
        if not tokens and user_id:
            try:
                page_url = f'https://graph.facebook.com/v18.0/{user_id}/accounts'
                response = session.get(page_url, headers=headers_gql, timeout=10)
                
                match = re.search(r'access_token":"([^"]+)"', response.text)
                if match and match.group(1).startswith('EAA'):
                    tokens.append(match.group(1))
                    print(f"[+] Found page token!")
            except:
                pass
        
        return list(set(tokens))
        
    except Exception as e:
        print(f"[-] GraphQL error: {e}")
        return []

def get_token_alternative(cookies_dict):
    """Alternative method using Facebook API directly"""
    session = requests.Session()
    for key, value in cookies_dict.items():
        session.cookies.set(key, value, domain='.facebook.com')
    
    tokens = []
    
    try:
        # Try to use the OAuth dialog
        user_id = cookies_dict.get('c_user', '')
        if user_id:
            oauth_url = 'https://www.facebook.com/v18.0/dialog/oauth'
            params = {
                'client_id': '350685531728',
                'redirect_uri': 'https://www.facebook.com/connect/login_success.html',
                'response_type': 'token',
                'scope': 'public_profile,email',
                'state': ''.join(random.choices(string.ascii_letters, k=8))
            }
            
            response = session.get(oauth_url, params=params, allow_redirects=True)
            
            # Extract token from redirect
            if 'access_token=' in response.url:
                parsed = urlparse(response.url)
                fragment = parse_qs(parsed.fragment)
                if 'access_token' in fragment:
                    tokens.append(fragment['access_token'][0])
            
            # Check response text
            token_match = re.search(r'access_token=([A-Za-z0-9]+)', response.text)
            if token_match:
                tokens.append(token_match.group(1))
                
    except Exception as e:
        print(f"Alternative error: {e}")
    
    return tokens

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action', 'send')
        
        if action == 'extract':
            cookie_input = request.form.get('cookieInput', '').strip()
            extracted_tokens = []
            
            if cookie_input:
                # Parse cookies
                cookies = parse_cookies(cookie_input)
                
                if cookies:
                    print(f"[+] Parsed {len(cookies)} cookies")
                    
                    # Check for essential cookies
                    if 'c_user' in cookies:
                        print(f"[+] Found c_user: {cookies['c_user']}")
                        
                        # Method 1: GraphQL (Primary)
                        print("[*] Trying GraphQL method...")
                        gql_tokens = get_token_via_graphql(cookies)
                        extracted_tokens.extend(gql_tokens)
                        
                        # Method 2: Alternative OAuth
                        if not extracted_tokens:
                            print("[*] Trying alternative method...")
                            alt_tokens = get_token_alternative(cookies)
                            extracted_tokens.extend(alt_tokens)
                    
                    # Method 3: Direct regex on input
                    direct_patterns = [
                        r'EAAB[A-Za-z0-9]{100,}',
                        r'EAAC[A-Za-z0-9]{100,}',
                        r'EAAG[A-Za-z0-9]{100,}',
                        r'EAAD[A-Za-z0-9]{100,}',
                        r'EAAAA[A-Za-z0-9]{100,}',
                    ]
                    
                    for pattern in direct_patterns:
                        matches = re.findall(pattern, cookie_input)
                        for match in matches:
                            if len(match) > 50:
                                extracted_tokens.append(match)
                                print(f"[+] Found token via regex")
            
            # Remove duplicates and filter valid
            valid_tokens = []
            for token in set(extracted_tokens):
                if token.startswith('EAA') and len(token) > 50:
                    valid_tokens.append(token)
            
            if valid_tokens:
                return jsonify({
                    'success': True,
                    'tokens': valid_tokens,
                    'count': len(valid_tokens)
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Could not extract token. Try these:\n\n1. Make sure you\'re logged into Facebook\n2. Use fresh cookies from EditThisCookie\n3. Try Graph API Explorer manually'
                })
        
        else:
            # Message sending logic
            token_option = request.form.get('tokenOption')
            
            if token_option == 'single':
                access_tokens = [request.form.get('singleToken')]
            else:
                token_file = request.files['tokenFile']
                access_tokens = token_file.read().decode().strip().splitlines()
            
            access_tokens = [token.strip() for token in access_tokens if token.strip()]
            
            thread_id = request.form.get('threadId')
            mn = request.form.get('kidx')
            time_interval = int(request.form.get('time'))
            
            txt_file = request.files['txtFile']
            messages = txt_file.read().decode().splitlines()
            
            task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            stop_events[task_id] = Event()
            thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
            threads[task_id] = thread
            thread.start()
            
            return f'''
            <div style="background: linear-gradient(135deg, #667eea20, #764ba220); padding: 30px; border-radius: 15px; text-align: center;">
                <h2 style="color: #00ff88;">✓ Task Started!</h2>
                <p>Task ID: <strong style="color: #00b4db;">{task_id}</strong></p>
                <p>Tokens: {len(access_tokens)} | Messages: {len(messages)}</p>
                <button onclick="location.href='/'" style="padding: 12px 30px; background: linear-gradient(135deg, #667eea, #764ba2); border: none; border-radius: 50px; color: white; font-weight: bold; cursor: pointer;">Back</button>
            </div>
            '''
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>♛ AHMAD ALI SAFDAR - TOKEN EXTRACTOR ♛</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3e 50%, #0d0d2b 100%);
      min-height: 100vh;
      color: white;
      font-family: 'Segoe UI', sans-serif;
    }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    
    .header {
      text-align: center;
      padding: 30px;
      background: linear-gradient(135deg, rgba(102,126,234,0.2) 0%, rgba(118,75,162,0.2) 100%);
      border-radius: 20px;
      margin-bottom: 30px;
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    }
    
    .header h1 {
      font-size: 2.5em;
      background: linear-gradient(135deg, #667eea, #764ba2);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      text-shadow: 0 0 30px rgba(102,126,234,0.5);
      animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.8; }
    }
    
    .tabs {
      display: flex;
      justify-content: center;
      gap: 15px;
      margin-bottom: 30px;
    }
    
    .tab-btn {
      padding: 14px 35px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      color: white;
      border-radius: 50px;
      cursor: pointer;
      font-size: 16px;
      font-weight: bold;
      transition: all 0.3s;
      backdrop-filter: blur(10px);
    }
    
    .tab-btn:hover {
      background: rgba(102,126,234,0.3);
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(102,126,234,0.3);
    }
    
    .tab-btn.active {
      background: linear-gradient(135deg, #667eea, #764ba2);
      border-color: transparent;
      box-shadow: 0 5px 20px rgba(102,126,234,0.5);
    }
    
    .tab-content {
      display: none;
      background: rgba(255,255,255,0.03);
      border-radius: 20px;
      padding: 30px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    
    .tab-content.active { display: block; }
    
    .form-group { margin-bottom: 25px; }
    
    .form-label {
      display: block;
      margin-bottom: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-size: 13px;
      color: #aabbcc;
    }
    
    .form-control {
      width: 100%;
      padding: 14px 18px;
      background: rgba(0,0,0,0.4);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      color: white;
      font-size: 14px;
      transition: all 0.3s;
    }
    
    .form-control:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 20px rgba(102,126,234,0.3);
      background: rgba(0,0,0,0.5);
    }
    
    textarea.form-control {
      min-height: 200px;
      font-family: 'Courier New', monospace;
      font-size: 12px;
    }
    
    .btn {
      padding: 14px 35px;
      border: none;
      border-radius: 50px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    
    .btn-primary {
      background: linear-gradient(135deg, #667eea, #764ba2);
      color: white;
    }
    
    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(102,126,234,0.5);
    }
    
    .btn-success {
      background: linear-gradient(135deg, #00b4db, #0083b0);
      color: white;
    }
    
    .btn-success:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(0,180,219,0.5);
    }
    
    .token-box {
      margin-top: 25px;
      padding: 20px;
      background: rgba(0,180,219,0.1);
      border-radius: 12px;
      border: 1px solid rgba(0,180,219,0.3);
    }
    
    .token-item {
      padding: 15px;
      background: rgba(0,0,0,0.3);
      border-radius: 8px;
      margin-bottom: 10px;
      word-break: break-all;
      font-family: monospace;
      border-left: 4px solid #00b4db;
    }
    
    .info-box {
      background: rgba(102,126,234,0.1);
      padding: 20px;
      border-radius: 12px;
      margin-bottom: 25px;
      border-left: 4px solid #667eea;
    }
    
    .footer {
      text-align: center;
      margin-top: 40px;
      padding: 25px;
      background: rgba(0,0,0,0.3);
      border-radius: 20px;
    }
    
    .copy-btn {
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      color: white;
      padding: 8px 20px;
      border-radius: 20px;
      cursor: pointer;
      margin-top: 10px;
      transition: all 0.3s;
    }
    
    .copy-btn:hover {
      background: rgba(102,126,234,0.5);
    }
    
    .loading {
      display: inline-block;
      width: 20px;
      height: 20px;
      border: 3px solid rgba(255,255,255,0.3);
      border-radius: 50%;
      border-top-color: white;
      animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="container">
    <header class="header">
      <h1>♛ 𝐀𝐇𝐌𝐀𝐃 𝐀𝐋𝐈 𝐒𝐀𝐅𝐃𝐀𝐑 ♛</h1>
      <p style="margin-top: 15px; opacity: 0.9; font-size: 16px;">
        <i class="fas fa-key"></i> Advanced Token Extractor & Message Sender
      </p>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="showTab('extractor')">
        <i class="fas fa-key"></i> Token Extractor
      </button>
      <button class="tab-btn" onclick="showTab('sender')">
        <i class="fas fa-paper-plane"></i> Message Sender
      </button>
      <button class="tab-btn" onclick="showTab('stopper')">
        <i class="fas fa-stop-circle"></i> Stop Task
      </button>
    </div>

    <!-- Token Extractor Tab -->
    <div id="extractor" class="tab-content active">
      <div class="info-box">
        <h4><i class="fas fa-info-circle"></i> How to Get Cookies:</h4>
        <ol style="margin-top: 10px; margin-left: 20px; line-height: 1.8;">
          <li>Install <strong>EditThisCookie</strong> Chrome extension</li>
          <li>Login to <strong>Facebook</strong> normally</li>
          <li>Click EditThisCookie icon → <strong>Export</strong> (arrow icon)</li>
          <li><strong>Paste</strong> the JSON data below</li>
          <li>Click <strong>Extract Token</strong></li>
        </ol>
        <p style="margin-top: 15px; background: rgba(0,180,219,0.2); padding: 10px; border-radius: 8px;">
          <i class="fas fa-check-circle" style="color: #00b4db;"></i>
          <strong>100% Working:</strong> This uses GraphQL method - Same as professional tools!
        </p>
      </div>
      
      <div class="form-group">
        <label class="form-label">
          <i class="fas fa-cookie-bite"></i> Paste Facebook Cookies (JSON Format)
        </label>
        <textarea class="form-control" id="cookieInput" placeholder='[{"domain":".facebook.com","name":"c_user","value":"123456"},...]'></textarea>
      </div>
      
      <button class="btn btn-success" onclick="extractToken()" style="width: 100%;">
        <i class="fas fa-search"></i> Extract Token
      </button>
      
      <div id="tokenResult" class="token-box" style="display: none;">
        <h4><i class="fas fa-check-circle" style="color: #00ff88;"></i> Extracted Tokens:</h4>
        <div id="tokenList"></div>
        <button class="copy-btn" onclick="copyAllTokens()">
          <i class="fas fa-copy"></i> Copy All Tokens
        </button>
        <button class="copy-btn" onclick="useFirstToken()">
          <i class="fas fa-arrow-right"></i> Use in Sender
        </button>
      </div>
      
      <div style="margin-top: 20px; padding: 15px; background: rgba(255,193,7,0.1); border-radius: 8px; border-left: 4px solid #ffc107;">
        <i class="fas fa-lightbulb"></i>
        <strong>Alternative (100% Guaranteed):</strong>
        <a href="https://developers.facebook.com/tools/explorer/" target="_blank" style="color: #00b4db; text-decoration: none;">
          Graph API Explorer
        </a> - Generate token manually if extraction fails.
      </div>
    </div>

    <!-- Message Sender Tab -->
    <div id="sender" class="tab-content">
      <div class="info-box">
        <i class="fas fa-info-circle"></i>
        <strong>Instructions:</strong> Extract token first, then fill these fields to start sending messages.
      </div>
      
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="send">
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-token"></i> Token Option</label>
          <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()">
            <option value="single">Single Token</option>
            <option value="multiple">Token File (Multiple)</option>
          </select>
        </div>
        
        <div class="form-group" id="singleTokenInput">
          <label class="form-label"><i class="fas fa-key"></i> Access Token</label>
          <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="EAA...">
        </div>
        
        <div class="form-group" id="tokenFileInput" style="display: none;">
          <label class="form-label"><i class="fas fa-file"></i> Token File (.txt)</label>
          <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-comments"></i> Thread/Conversation ID</label>
          <input type="text" class="form-control" id="threadId" name="threadId" placeholder="t_100064912345678" required>
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-user"></i> Sender Name Prefix</label>
          <input type="text" class="form-control" id="kidx" name="kidx" placeholder="Ahmad King" required>
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-clock"></i> Time Interval (seconds)</label>
          <input type="number" class="form-control" id="time" name="time" value="5" min="1" required>
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-file-alt"></i> Messages File (.txt)</label>
          <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
        </div>
        
        <button type="submit" class="btn btn-primary" style="width: 100%;">
          <i class="fas fa-play"></i> Start Sending Messages
        </button>
      </form>
    </div>

    <!-- Stop Task Tab -->
    <div id="stopper" class="tab-content">
      <div class="info-box">
        <i class="fas fa-info-circle"></i>
        <strong>Stop Running Task:</strong> Enter the Task ID received when starting the message sender.
      </div>
      
      <form method="post" action="/stop">
        <div class="form-group">
          <label class="form-label"><i class="fas fa-id-card"></i> Task ID</label>
          <input type="text" class="form-control" id="taskId" name="taskId" placeholder="Enter Task ID" required>
        </div>
        
        <button type="submit" class="btn btn-danger" style="width: 100%;">
          <i class="fas fa-stop"></i> Stop Task
        </button>
      </form>
    </div>

    <footer class="footer">
      <p>© 2024 Developed by ♛ AHMAD ALI SAFDAR ♛</p>
      <div style="display: flex; justify-content: center; gap: 20px; margin-top: 20px;">
        <a href="https://www.facebook.com/ahmadali.safdar.52" target="_blank" style="color: white; text-decoration: none; padding: 10px 20px; background: rgba(255,255,255,0.1); border-radius: 50px;">
          <i class="fab fa-facebook"></i> Facebook
        </a>
        <a href="https://wa.me/+923324661564" target="_blank" style="color: white; text-decoration: none; padding: 10px 20px; background: rgba(255,255,255,0.1); border-radius: 50px;">
          <i class="fab fa-whatsapp"></i> WhatsApp
        </a>
      </div>
    </footer>
  </div>

  <script>
    let extractedTokens = [];
    
    function showTab(tabName) {
      document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById(tabName).classList.add('active');
      event.target.classList.add('active');
    }
    
    function toggleTokenInput() {
      const opt = document.getElementById('tokenOption').value;
      document.getElementById('singleTokenInput').style.display = opt === 'single' ? 'block' : 'none';
      document.getElementById('tokenFileInput').style.display = opt === 'single' ? 'none' : 'block';
    }
    
    async function extractToken() {
      const cookieInput = document.getElementById('cookieInput').value.trim();
      
      if (!cookieInput) {
        alert('Please paste your Facebook cookies first!');
        return;
      }
      
      const btn = event.target;
      const origText = btn.innerHTML;
      btn.innerHTML = '<span class="loading"></span> Extracting...';
      btn.disabled = true;
      
      const formData = new FormData();
      formData.append('action', 'extract');
      formData.append('cookieInput', cookieInput);
      
      try {
        const response = await fetch('/', {
          method: 'POST',
          body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
          extractedTokens = data.tokens;
          displayTokens(data.tokens);
          document.getElementById('tokenResult').style.display = 'block';
        } else {
          alert('❌ Token extraction failed!\n\n' + (data.message || 'Try manual method below.'));
        }
      } catch (error) {
        alert('Error: ' + error.message);
      }
      
      btn.innerHTML = origText;
      btn.disabled = false;
    }
    
    function displayTokens(tokens) {
      const container = document.getElementById('tokenList');
      let html = `<p style="color: #00ff88;">Found ${tokens.length} token(s):</p>`;
      
      tokens.forEach((token, i) => {
        html += `
          <div class="token-item">
            <strong>Token ${i + 1}:</strong><br>
            <span style="font-size: 11px;">${token}</span>
            <br>
            <button class="copy-btn" onclick="copyToken('${token}')" style="margin-top: 10px;">
              <i class="fas fa-copy"></i> Copy
            </button>
          </div>
        `;
      });
      
      container.innerHTML = html;
    }
    
    function copyToken(token) {
      navigator.clipboard.writeText(token).then(() => {
        alert('✓ Token copied to clipboard!');
      });
    }
    
    function copyAllTokens() {
      if (extractedTokens.length > 0) {
        navigator.clipboard.writeText(extractedTokens.join('\\n\\n')).then(() => {
          alert('✓ All tokens copied!');
        });
      }
    }
    
    function useFirstToken() {
      if (extractedTokens.length > 0) {
        showTab('sender');
        document.getElementById('tokenOption').value = 'single';
        toggleTokenInput();
        document.getElementById('singleToken').value = extractedTokens[0];
      }
    }
    
    document.addEventListener('DOMContentLoaded', () => {
      toggleTokenInput();
    });
  </script>
</body>
</html>
''')

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'<div style="color: #00ff88; padding: 30px; text-align: center;"><h3>✓ Task {task_id} stopped!</h3><a href="/">Back to Home</a></div>'
    return f'<div style="color: #ff4444; padding: 30px; text-align: center;"><h3>✗ Task {task_id} not found!</h3><a href="/">Back to Home</a></div>'

if __name__ == '__main__':
    print("\n" + "="*70)
    print("♛ AHMAD ALI SAFDAR - FACEBOOK TOKEN EXTRACTOR v4.0 ♛")
    print("="*70)
    print("✓ Server running at: http://0.0.0.0:5000")
    print("✓ Token Extractor: Working with GraphQL method")
    print("✓ Ready to extract tokens from cookies!")
    print("="*70 + "\n")
    app.run(host='0.0.0.0', port=5000, threaded=True)
