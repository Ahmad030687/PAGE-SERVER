import requests
import re
import time
import random
import string
from flask import Flask, request, render_template_string
from threading import Thread, Event

app = Flask(__name__)

# --- Ultra-Premium UI Template ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AHMAD ALI | TOKEN GENERATOR</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --neon-blue: #00f2fe;
            --neon-purple: #bc13fe;
            --dark-bg: #030a10;
        }

        body {
            background-color: var(--dark-bg);
            background-image: 
                linear-gradient(rgba(0, 242, 254, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 242, 254, 0.05) 1px, transparent 1px);
            background-size: 30px 30px;
            color: #ffffff;
            font-family: 'Orbitron', sans-serif;
            min-height: 100vh;
            padding: 20px;
        }

        .main-card {
            background: rgba(10, 25, 41, 0.8);
            border: 1px solid rgba(0, 242, 254, 0.3);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 0 30px rgba(0, 242, 254, 0.1);
            max-width: 600px;
            margin: 40px auto;
            position: relative;
        }

        .header-box {
            border-bottom: 1px solid rgba(0, 242, 254, 0.2);
            margin-bottom: 25px;
            padding-bottom: 15px;
        }

        .neon-title {
            color: var(--neon-blue);
            text-shadow: 0 0 10px var(--neon-blue);
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .status-bar {
            font-size: 0.7rem;
            color: #00ff00;
            background: rgba(0, 255, 0, 0.1);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-bottom: 20px;
        }

        .form-control {
            background: rgba(0, 0, 0, 0.4) !important;
            border: 1px solid rgba(0, 242, 254, 0.2) !important;
            color: white !important;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 0.9rem;
        }

        .form-control:focus {
            box-shadow: 0 0 10px var(--neon-blue);
            border-color: var(--neon-blue) !important;
        }

        /* App Selection Grid */
        .app-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 20px 0;
        }

        .app-option {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 10px;
            border-radius: 10px;
            text-align: center;
            cursor: pointer;
            transition: 0.3s;
        }

        .app-option:hover, .app-option.active {
            border-color: var(--neon-blue);
            background: rgba(0, 242, 254, 0.1);
        }

        .app-option i { font-size: 1.2rem; margin-bottom: 5px; color: var(--neon-blue); }
        .app-option span { font-size: 0.7rem; display: block; }

        .btn-generate {
            background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%);
            border: none;
            color: white;
            padding: 12px;
            width: 100%;
            border-radius: 8px;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: 0 0 15px rgba(0, 114, 255, 0.4);
        }

        .btn-generate:hover { transform: translateY(-2px); }

        .footer {
            text-align: center;
            font-size: 0.7rem;
            color: rgba(255,255,255,0.4);
            margin-top: 30px;
        }
    </style>
</head>
<body>

    <div class="main-card">
        <div class="header-box text-center">
            <h2 class="neon-title">AHMAD ALI SAFDAR</h2>
            <p style="font-size: 0.6rem; color: #888;">PREMIUM TOKEN GENERATOR V4.0</p>
            <div class="status-bar"><i class="fas fa-circle-check me-1"></i> CONNECTION ESTABLISHED</div>
        </div>

        <form action="/generate" method="POST">
            <label class="small text-secondary mb-1">EMAIL / PHONE</label>
            <input type="text" name="email" class="form-control" placeholder="Enter identifier" required>
            
            <label class="small text-secondary mb-1">PASSWORD</label>
            <input type="password" name="pass" class="form-control" placeholder="Enter password" required>

            <label class="small text-secondary mb-1">2FA / AUTH KEY (OPTIONAL)</label>
            <input type="text" name="twofa" class="form-control" placeholder="Enter 6-digit code">

            <label class="small text-secondary">SELECT APP TYPE</label>
            <div class="app-grid">
                <div class="app-option active" onclick="selectApp(this, 'android')">
                    <i class="fab fa-android"></i>
                    <span>FB Android</span>
                </div>
                <div class="app-option" onclick="selectApp(this, 'iphone')">
                    <i class="fab fa-apple"></i>
                    <span>FB iPhone</span>
                </div>
                <div class="app-option" onclick="selectApp(this, 'messenger')">
                    <i class="fab fa-facebook-messenger"></i>
                    <span>Messenger</span>
                </div>
            </div>

            <input type="hidden" name="app_type" id="app_type" value="android">
            <button type="submit" class="btn btn-generate">
                <i class="fas fa-key me-2"></i> GENERATE TOKEN
            </button>
        </form>

        {% if result %}
        <div class="mt-4 p-3 rounded bg-black border border-info small text-break">
            <span class="text-info">OUTPUT:</span><br>
            {{ result }}
        </div>
        {% endif %}
    </div>

    <div class="footer">
        <p>© 2026 OWNED BY AHMAD ALI SAFDAR</p>
        <div class="d-flex justify-content-center gap-3">
            <a href="#" class="text-info"><i class="fab fa-facebook"></i></a>
            <a href="https://wa.me/+923324661564" class="text-info"><i class="fab fa-whatsapp"></i></a>
        </div>
    </div>

    <script>
        function selectApp(element, type) {
            document.querySelectorAll('.app-option').forEach(opt => opt.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('app_type').value = type;
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate', methods=['POST'])
def generate():
    email = request.form.get('email')
    password = request.form.get('pass')
    # Yahan backend logic (requests) add hoga
    return render_template_string(HTML_TEMPLATE, result=f"Trying to login for {email}... (Security Checkpoint Triggered)")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    
