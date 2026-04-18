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

def extract_token_from_cookie(cookie_string):
    """Extract Facebook access token from cookie string"""
    try:
        # Try to get token from Facebook API
        session = requests.Session()
        
        # Set cookies from cookie string
        cookies = {}
        for cookie in cookie_string.split(';'):
            if '=' in cookie:
                name, value = cookie.strip().split('=', 1)
                cookies[name.strip()] = value.strip()
        
        session.cookies.update(cookies)
        
        # First try to get EAA token
        headers_fb = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # Method 1: Get from business.facebook.com
        response = session.get('https://business.facebook.com/business_locations', headers=headers_fb)
        match = re.search(r'accessToken\\":\\"([^\\]+)\\"', response.text)
        if match:
            return match.group(1)
        
        # Method 2: Get from m.facebook.com
        response = session.get('https://m.facebook.com/composer/ocelot/async_loader/?publisher=feed', headers=headers_fb)
        match = re.search(r'accessToken\\":\\"([^\\]+)\\"', response.text)
        if match:
            return match.group(1)
        
        # Method 3: Get from developer.facebook.com
        response = session.get('https://developers.facebook.com/tools/explorer/', headers=headers_fb)
        match = re.search(r'\"accessToken\":\"([^\"]+)\"', response.text)
        if match:
            return match.group(1)
        
        # Method 4: Try to get EAAAA token
        response = session.get('https://www.facebook.com/adsmanager/account_settings/information', headers=headers_fb)
        patterns = [
            r'EAA[A-Za-z0-9]{200,}',
            r'EAAB[A-Za-z0-9]{200,}',
            r'EAAC[A-Za-z0-9]{200,}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response.text)
            if match:
                return match.group(0)
        
        return None
        
    except Exception as e:
        print(f"Error extracting token: {e}")
        return None

def extract_token_from_facebook(c_user):
    """Alternative method to get token using c_user"""
    try:
        # Try to generate token using c_user
        session = requests.Session()
        session.cookies.set('c_user', c_user)
        
        response = session.get('https://graph.facebook.com/me?fields=id,name', 
                              headers={'User-Agent': headers['User-Agent']})
        
        if response.status_code == 200:
            # If successful, the session cookie works
            return "Session Valid - Use Full Cookie"
        
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

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
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'extract_token':
            cookie_string = request.form.get('cookieString')
            if cookie_string:
                token = extract_token_from_cookie(cookie_string)
                if token:
                    return render_template_string(HTML_TEMPLATE, 
                        extracted_token=token,
                        extraction_success=True)
                else:
                    return render_template_string(HTML_TEMPLATE,
                        extraction_error="Failed to extract token. Make sure cookie is valid.",
                        extraction_success=False)
        
        elif action == 'send_messages':
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
            thread = Thread(target=send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
            threads[task_id] = thread
            thread.start()
            
            return render_template_string(HTML_TEMPLATE, task_started=True, task_id=task_id)
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return render_template_string(HTML_TEMPLATE, stop_success=True, stopped_task_id=task_id)
    else:
        return render_template_string(HTML_TEMPLATE, stop_error=True, error_task_id=task_id)

# HTML Template
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
      max-width: 450px;
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
      min-height: 100px;
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
            <label for="cookieString" class="form-label">Paste Facebook Cookie</label>
            <textarea class="form-control" id="cookieString" name="cookieString" rows="5" placeholder="Paste your Facebook cookie here..."></textarea>
            <small class="text-muted">Get cookie from facebook.com after login</small>
          </div>
          
          <button type="submit" class="btn btn-success btn-submit">
            <i class="fas fa-key"></i> Extract Token
          </button>
        </form>
        
        {% if extraction_success %}
        <div class="alert alert-success mt-3">
          <strong>Token Extracted Successfully!</strong><br>
          <div style="word-break: break-all; margin-top: 10px;">
            <code>{{ extracted_token }}</code>
          </div>
          <button class="btn btn-sm btn-info mt-2" onclick="copyToken('{{ extracted_token }}')">
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
          <strong>How to get Facebook Cookie:</strong><br>
          1. Login to Facebook<br>
          2. Press F12 (Developer Tools)<br>
          3. Go to Application/Storage tab<br>
          4. Click on Cookies > https://www.facebook.com<br>
          5. Copy all cookie values or use EditThisCookie extension
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
    
    function copyToken(token) {
      navigator.clipboard.writeText(token).then(function() {
        alert('Token copied to clipboard!');
      });
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
