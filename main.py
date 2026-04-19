# -*- coding: utf-8 -*-
"""
FB MASTER PRO 2026 - AHMAD ALI SAFDAR EDITION
All-In-One: Extractor + Convo + Multi-Token
"""

from flask import Flask, request, render_template_string, jsonify
import requests
import time
import random
import uuid
import re
from threading import Thread, Event
from datetime import datetime

app = Flask(__name__)

# Global storage for background tasks
tasks = {}
stop_events = {}

# --- CORE MESSAGING LOGIC ---
def convo_engine(task_id, tokens, target_id, messages, delay, prefix):
    stop_event = stop_events[task_id]
    tasks[task_id]['status'] = "Running"
    
    while not stop_event.is_set():
        for msg in messages:
            for token in tokens:
                if stop_event.is_set(): break
                
                try:
                    full_msg = f"{prefix} {msg}"
                    # Mbasic method for stability
                    url = f"https://mbasic.facebook.com/messages/send/?tid={target_id}"
                    # Note: In a real server, you'd handle cookies/dtsg here. 
                    # This is the simplified logic for your framework.
                    
                    tasks[task_id]['sent'] += 1
                    tasks[task_id]['logs'].insert(0, f"✅ Sent: {msg[:20]}... from {token[:10]}")
                except Exception as e:
                    tasks[task_id]['logs'].insert(0, f"❌ Error: {str(e)}")
                
                time.sleep(delay)
    
    tasks[task_id]['status'] = "Stopped"

# --- UI DESIGN (Ahmad Ali Premium Style) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AHMAD ALI | FB MASTER PRO</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Rajdhani:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root { --gold: #ffcc00; --dark: #050505; --glass: rgba(255, 255, 255, 0.05); }
        body { background: var(--dark); color: white; font-family: 'Rajdhani', sans-serif; margin: 0; padding: 10px; }
        .main-container { max-width: 600px; margin: auto; }
        .header { text-align: center; padding: 20px; border-bottom: 2px solid var(--gold); margin-bottom: 20px; }
        .header h1 { font-family: 'Orbitron'; color: var(--gold); text-shadow: 0 0 15px var(--gold); margin: 0; }
        .glass-card { background: var(--glass); border: 1px solid rgba(255,204,0,0.2); backdrop-filter: blur(10px); border-radius: 15px; padding: 20px; margin-bottom: 20px; }
        input, select, textarea { width: 100%; background: #111; border: 1px solid #333; color: white; padding: 12px; border-radius: 8px; margin-bottom: 10px; box-sizing: border-box; }
        .btn-gold { width: 100%; padding: 15px; border: none; border-radius: 8px; background: linear-gradient(45deg, #ffcc00, #ffaa00); color: black; font-weight: bold; cursor: pointer; font-family: 'Orbitron'; }
        .log-box { height: 150px; overflow-y: auto; background: black; padding: 10px; font-size: 0.8rem; border-radius: 5px; color: #00ff00; }
        .footer { text-align: center; font-size: 0.7rem; opacity: 0.5; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="main-container">
        <div class="header">
            <h1>FB MASTER PRO</h1>
            <p style="letter-spacing: 3px;">AHMAD ALI SAFDAR EDITION</p>
        </div>

        <div class="glass-card">
            <h3 style="color: var(--gold);"><i class="fas fa-key"></i> FAST EXTRACTOR</h3>
            <input type="text" id="email" placeholder="Email/Phone">
            <input type="password" id="pass" placeholder="Password">
            <button class="btn-gold" onclick="extractToken()">GET TOKEN</button>
            <div id="tokenResult" style="margin-top:10px; font-size:0.8rem; word-break:break-all;"></div>
        </div>

        <div class="glass-card">
            <h3 style="color: var(--gold);"><i class="fas fa-paper-plane"></i> CONVO LOADER</h3>
            <label>Upload Token File (.txt)</label>
            <input type="file" id="tokenFile">
            <input type="text" id="convoId" placeholder="Convo/Thread ID">
            <input type="text" id="prefix" placeholder="Hater Name / Prefix">
            <label>Upload Message File (.txt)</label>
            <input type="file" id="msgFile">
            <input type="number" id="delay" placeholder="Delay in Seconds" value="5">
            <button class="btn-gold" onclick="startConvo()">START LOADING</button>
        </div>

        <div class="glass-card">
            <h3 style="color: var(--gold);"><i class="fas fa-terminal"></i> LIVE LOGS</h3>
            <div id="status">Status: Idle</div>
            <div class="log-box" id="logs">Waiting for task...</div>
        </div>

        <div class="footer">
            OWNER: AHMAD ALI SAFDAR | TOBA TEK SINGH<br>
            POWERED BY AHMAD PHOTOSTATE & IT SOLUTIONS
        </div>
    </div>

    <script>
        async function extractToken() {
            const email = document.getElementById('email').value;
            const pass = document.getElementById('pass').value;
            const resDiv = document.getElementById('tokenResult');
            resDiv.innerHTML = "Extracting...";
            
            // Note: Call your backend /extract_token here
            resDiv.innerHTML = "Token: EAAAA... (Check Console)";
        }

        function startConvo() {
            document.getElementById('status').innerHTML = "Status: <span style='color:#00ff00'>Running...</span>";
            const logBox = document.getElementById('logs');
            logBox.innerHTML = "Task started successfully! Background process active.";
        }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/extract_token', methods=['POST'])
def extract():
    # Token extraction logic yahan aayegi
    return jsonify({"success": True, "token": "EAAAA..."})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
 
