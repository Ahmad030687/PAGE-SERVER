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
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'user-agent': 'Mozilla/5.0 (Linux; Android 11; TECNO CE7j) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.40 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
    'referer': 'www.google.com'
}

# Default cookies (jo aapne diye)
DEFAULT_COOKIES = [
    {"domain":".facebook.com","name":"datr","value":"aPLZaS2gziut3LDoLldFIP4H"},
    {"domain":".facebook.com","name":"sb","value":"aPLZaZDv6DnYjTZO48VS7vGe"},
    {"domain":".facebook.com","name":"ps_l","value":"1"},
    {"domain":".facebook.com","name":"ps_n","value":"1"},
    {"domain":".facebook.com","name":"pas","value":"61576894738564%3Au8wWhWdgeS"},
    {"domain":".facebook.com","name":"dpr","value":"3.2983407974243164"},
    {"domain":".facebook.com","name":"c_user","value":"61576894738564"},
    {"domain":".facebook.com","name":"xs","value":"40%3ATL3hB8x3GSo_pw%3A2%3A1776446306%3A-1%3A-1"},
    {"domain":".facebook.com","name":"vpd","value":"v1%3B708x360x3"},
    {"domain":".facebook.com","name":"locale","value":"en_US"},
    {"domain":".facebook.com","name":"fr","value":"0EL4SONjwZFS1tgBe.AWe757O9t1_WijZWU4qneucfnS4fBPKz86Dpqwc8_2FGK3lW_S0.Bp2fJo..AAA.0.0.Bp40UX.AWdkRncATwpHfWEXvzCUReNM7DQ"},
    {"domain":".facebook.com","name":"fbl_st","value":"101522699%3BT%3A29608367"},
    {"domain":".facebook.com","name":"wl_cbv","value":"v2%3Bclient_version%3A3145%3Btimestamp%3A1776502039"}
]

stop_events = {}
threads = {}
stored_cookies = DEFAULT_COOKIES  # Default cookies store

def extract_token_from_cookies(cookies_list):
    """Cookies se token extract karega"""
    session = requests.Session()
    
    for cookie in cookies_list:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.facebook.com'))
    
    uid = None
    for c in cookies_list:
        if c['name'] == 'c_user':
            uid = c['value']
            break
    
    # Try multiple methods
    try:
        # Method 1: Business Suite
        r = session.get('https://business.facebook.com/business_locations', headers=headers, timeout=10)
        match = re.search(r'EAA[A-Za-z0-9]{150,}', r.text)
        if match:
            return match.group(0), uid
    except:
        pass
    
    try:
        # Method 2: Facebook Gaming
        r = session.get('https://www.facebook.com/gaming/feed/', headers=headers, timeout=10)
        match = re.search(r'"accessToken":"(EAA[A-Za-z0-9]+)"', r.text)
        if match:
            return match.group(1), uid
    except:
        pass
    
    try:
        # Method 3: Graph API
        r = session.get('https://graph.facebook.com/me', headers=headers, timeout=10)
        if r.status_code == 200:
            return f"SESSION_VALID_{uid}", uid
    except:
        pass
    
    return None, uid

def send_messages_with_cookies(cookies_list, thread_id, mn, time_interval, messages, task_id):
    """Cookies use karke messages bhejega"""
    stop_event = stop_events[task_id]
    
    session = requests.Session()
    for cookie in cookies_list:
        session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.facebook.com'))
    
    while not stop_event.is_set():
        for message1 in messages:
            if stop_event.is_set():
                break
            
            message = str(mn) + ' ' + message1
            
            try:
                # Get fb_dtsg
                r = session.get('https://mbasic.facebook.com/', headers=headers, timeout=10)
                fb_dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', r.text)
                
                if fb_dtsg_match:
                    fb_dtsg = fb_dtsg_match.group(1)
                    
                    # Send message
                    send_url = 'https://mbasic.facebook.com/messages/send/?icm=1'
                    data = {
                        'fb_dtsg': fb_dtsg,
                        'body': message,
                        'send': 'Send',
                        'tids': f'cid.g.{thread_id}',
                    }
                    
                    response = session.post(send_url, data=data, headers=headers, timeout=15)
                    
                    if response.status_code == 200:
                        print(f"✅ Message Sent: {message}")
                    else:
                        print(f"❌ Failed: {response.status_code}")
                else:
                    print("❌ fb_dtsg not found")
                    
            except Exception as e:
                print(f"Error: {e}")
            
            time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def send_message():
    token_extracted = None
    extracted_uid = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Token Extractor
        if action == 'extract_token':
            cookie_input = request.form.get('cookieInput')
            if cookie_input:
                try:
                    cookies_list = json.loads(cookie_input)
                    token_extracted, extracted_uid = extract_token_from_cookies(cookies_list)
                    global stored_cookies
                    stored_cookies = cookies_list
                except:
                    token_extracted = "Invalid JSON"
            
            return render_template_string(HTML_TEMPLATE, 
                                         token_extracted=token_extracted,
                                         extracted_uid=extracted_uid,
                                         stored_cookies=stored_cookies)
        
        # Message Sender with Cookies
        elif action == 'send_with_cookies':
            thread_id = request.form.get('threadId')
            mn = request.form.get('kidx')
            time_interval = int(request.form.get('time'))
            
            txt_file = request.files['txtFile']
            messages = txt_file.read().decode().splitlines()
            
            task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            
            stop_events[task_id] = Event()
            thread = Thread(target=send_messages_with_cookies, 
                          args=(stored_cookies, thread_id, mn, time_interval, messages, task_id))
            threads[task_id] = thread
            thread.start()
            
            return f'✅ Task started with ID: {task_id} (Using Cookies)'
        
        # Message Sender with Token
        elif action == 'send_with_token':
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
            
            def send_messages_token(access_tokens, thread_id, mn, time_interval, messages, task_id):
                stop_event = stop_events[task_id]
                while not stop_event.is_set():
                    for message1 in messages:
                        if stop_event.is_set():
                            break
                        for access_token in access_tokens:
                            api_url = f'https://graph.facebook.com/v15.0/t_{thread_id}/'
                            message = str(mn) + ' ' + message1
                            parameters = {'access_token': access_token, 'message': message}
                            response = requests.post(api_url, data=parameters, headers=headers)
                            if response.status_code == 200:
                                print(f"✅ Message Sent: {message}")
                            else:
                                print(f"❌ Failed: {message}")
                            time.sleep(time_interval)
            
            thread = Thread(target=send_messages_token, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
            threads[task_id] = thread
            thread.start()
            
            return f'✅ Task started with ID: {task_id} (Using Token)'
    
    return render_template_string(HTML_TEMPLATE, stored_cookies=stored_cookies)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'🛑 Task with ID {task_id} has been stopped.'
    else:
        return f'❌ No task found with ID {task_id}.'

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
      color: white;
    }
    .container {
      max-width: 400px;
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 0 15px white;
      background: rgba(0,0,0,0.7);
      margin: 20px auto;
    }
    .form-control, .form-select {
      border: 1px double white;
      background: rgba(255,255,255,0.1);
      width: 100%;
      padding: 10px;
      margin-bottom: 15px;
      border-radius: 10px;
      color: white;
    }
    textarea.form-control {
      height: 120px;
      font-family: monospace;
      font-size: 11px;
    }
    .header { text-align: center; padding-bottom: 20px; }
    .btn-submit { width: 100%; margin-top: 10px; padding: 10px; }
    .footer { text-align: center; margin-top: 20px; color: #888; }
    .whatsapp-link {
      display: inline-block;
      color: #25d366;
      text-decoration: none;
      margin-top: 10px;
    }
    .nav-tabs .nav-link {
      color: white;
      background: transparent;
    }
    .nav-tabs .nav-link.active {
      background: #007bff;
      color: white;
    }
    .token-box {
      background: rgba(0,255,0,0.1);
      border: 1px solid #00ff88;
      padding: 10px;
      border-radius: 10px;
      word-break: break-all;
      margin: 15px 0;
    }
    .btn-copy {
      background: #00ff88;
      color: black;
      border: none;
      padding: 5px 15px;
      border-radius: 5px;
    }
  </style>
</head>
<body>
  <header class="header mt-4">
    <h1 class="mt-3">♛♥彡𝐀𝐇𝐌𝐀𝐃 𝐀𝐋𝚰♛♥☨</h1>
  </header>
  
  <div class="container">
    <ul class="nav nav-tabs mb-3" id="myTab">
      <li class="nav-item">
        <button class="nav-link active" data-bs-toggle="tab" data-bs-target="#cookieTab">🍪 Cookie Sender</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#tokenTab">🔑 Token Sender</button>
      </li>
      <li class="nav-item">
        <button class="nav-link" data-bs-toggle="tab" data-bs-target="#extractorTab">🔐 Token Extractor</button>
      </li>
    </ul>
    
    <div class="tab-content">
      <!-- Cookie Sender Tab -->
      <div class="tab-pane fade show active" id="cookieTab">
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="action" value="send_with_cookies">
          
          <div class="mb-3">
            <label class="form-label">🍪 Using Stored Cookies</label>
            <div style="background: rgba(0,255,0,0.1); padding: 10px; border-radius: 10px;">
              <small>✅ Cookies Loaded: {{ stored_cookies|length }} items</small>
            </div>
          </div>
          
          <div class="mb-3">
            <label for="threadId" class="form-label">Enter Inbox/convo uid</label>
            <input type="text" class="form-control" name="threadId" required>
          </div>
          
          <div class="mb-3">
            <label for="kidx" class="form-label">Enter Your Hater Name</label>
            <input type="text" class="form-control" name="kidx" required>
          </div>
          
          <div class="mb-3">
            <label for="time" class="form-label">Enter Time (seconds)</label>
            <input type="number" class="form-control" name="time" value="2" required>
          </div>
          
          <div class="mb-3">
            <label for="txtFile" class="form-label">Choose Your Np File</label>
            <input type="file" class="form-control" name="txtFile" accept=".txt" required>
          </div>
          
          <button type="submit" class="btn btn-success btn-submit">🚀 Run with Cookies</button>
        </form>
      </div>
      
      <!-- Token Sender Tab -->
      <div class="tab-pane fade" id="tokenTab">
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="action" value="send_with_token">
          
          <div class="mb-3">
            <label for="tokenOption" class="form-label">Select Token Option</label>
            <select class="form-select" name="tokenOption" onchange="toggleTokenInput()">
              <option value="single">Single Token</option>
              <option value="multiple">Token File</option>
            </select>
          </div>
          
          <div class="mb-3" id="singleTokenInput">
            <label for="singleToken" class="form-label">Enter Single Token</label>
            <input type="text" class="form-control" name="singleToken">
          </div>
          
          <div class="mb-3" id="tokenFileInput" style="display: none;">
            <label for="tokenFile" class="form-label">Choose Token File</label>
            <input type="file" class="form-control" name="tokenFile" accept=".txt">
          </div>
          
          <div class="mb-3">
            <label for="threadId2" class="form-label">Enter Inbox/convo uid</label>
            <input type="text" class="form-control" name="threadId" required>
          </div>
          
          <div class="mb-3">
            <label for="kidx2" class="form-label">Enter Your Hater Name</label>
            <input type="text" class="form-control" name="kidx" required>
          </div>
          
          <div class="mb-3">
            <label for="time2" class="form-label">Enter Time (seconds)</label>
            <input type="number" class="form-control" name="time" value="2" required>
          </div>
          
          <div class="mb-3">
            <label for="txtFile2" class="form-label">Choose Your Np File</label>
            <input type="file" class="form-control" name="txtFile" accept=".txt" required>
          </div>
          
          <button type="submit" class="btn btn-primary btn-submit">🚀 Run with Token</button>
        </form>
      </div>
      
      <!-- Token Extractor Tab -->
      <div class="tab-pane fade" id="extractorTab">
        <form method="post">
          <input type="hidden" name="action" value="extract_token">
          
          <div class="mb-3">
            <label for="cookieInput" class="form-label">🍪 Paste Facebook Cookies (JSON)</label>
            <textarea class="form-control" id="cookieInput" name="cookieInput" placeholder='Paste cookies JSON here...'></textarea>
          </div>
          
          <button type="submit" class="btn btn-warning btn-submit">🔐 Extract Token</button>
          <button type="button" class="btn btn-info btn-submit" onclick="loadDefaultCookies()">📋 Load Default</button>
        </form>
        
        {% if token_extracted %}
        <div class="token-box">
          <strong>UID:</strong> {{ extracted_uid }}<br><br>
          <strong>Token:</strong><br>
          <span id="extractedToken">{{ token_extracted }}</span><br><br>
          <button class="btn-copy" onclick="copyToken()">📋 Copy Token</button>
        </div>
        {% endif %}
      </div>
    </div>
    
    <!-- Stop Task -->
    <form method="post" action="/stop" style="margin-top: 20px;">
      <div class="mb-3">
        <label for="taskId" class="form-label">Enter Task ID to Stop</label>
        <input type="text" class="form-control" name="taskId" required>
      </div>
      <button type="submit" class="btn btn-danger btn-submit">🛑 Stop Task</button>
    </form>
  </div>
  
  <footer class="footer">
    <p>© 𝟸𝟶𝟸𝟺 ᴅᴇᴠᴇʟᴏᴘᴇᴅ ʙʏ🥀✌️ᴀʜᴍᴀᴅ.ᴋɪɴɢ😈🐧</p>
    <p> 𝐀𝐇𝐌𝐀𝐃 𝐊𝚰𝐍𝐆 𝐇𝐄𝐑𝐄<a href="https://www.facebook.com/ahmadali.safdar.52?mibextid=ZbWKwL">ᴄʟɪᴄᴋ ʜᴇʀᴇ ғᴏʀ ғᴀᴄᴇʙᴏᴏᴋ</a></p>
    <div class="mb-3">
      <a href="https://wa.me/+923324661564" class="whatsapp-link">
        <i class="fab fa-whatsapp"></i> Chat on WhatsApp
      </a>
    </div>
  </footer>
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    const DEFAULT_COOKIES = ''' + json.dumps(DEFAULT_COOKIES) + ''';
    
    function toggleTokenInput() {
      var tokenOption = document.querySelector('[name="tokenOption"]').value;
      if (tokenOption == 'single') {
        document.getElementById('singleTokenInput').style.display = 'block';
        document.getElementById('tokenFileInput').style.display = 'none';
      } else {
        document.getElementById('singleTokenInput').style.display = 'none';
        document.getElementById('tokenFileInput').style.display = 'block';
      }
    }
    
    function loadDefaultCookies() {
      document.getElementById('cookieInput').value = JSON.stringify(DEFAULT_COOKIES);
    }
    
    function copyToken() {
      var token = document.getElementById('extractedToken').innerText;
      navigator.clipboard.writeText(token);
      alert('Token Copied!');
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
