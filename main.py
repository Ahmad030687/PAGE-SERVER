# -*- coding: utf-8 -*-
import re, requests, json, base64, time
from flask import Flask, render_template_string, request, jsonify
from urllib.parse import quote, unquote

app = Flask(__name__)

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✨ FB Premium Toolkit</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{
            font-family:'Inter',sans-serif;
            background:linear-gradient(135deg,#0a0a0a 0%,#1a1a2e 50%,#16213e 100%);
            min-height:100vh;
            padding:20px;
        }
        .container{max-width:1300px;margin:0 auto}
        .header{
            text-align:center;
            padding:30px;
            background:rgba(255,255,255,0.03);
            backdrop-filter:blur(20px);
            border-radius:40px;
            border:1px solid rgba(255,255,255,0.1);
            margin-bottom:30px;
            box-shadow:0 20px 60px rgba(0,0,0,0.3),0 0 80px rgba(0,255,255,0.1);
        }
        .header h1{
            font-size:2.8rem;
            font-weight:800;
            background:linear-gradient(135deg,#00d2ff,#3a7bd5,#ff6b6b,#00d2ff);
            background-size:200% 200%;
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            animation:gradient 5s ease infinite;
        }
        @keyframes gradient{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
        .header i{color:#00d2ff;margin-right:10px}
        .grid{
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(350px,1fr));
            gap:20px;
            margin-bottom:20px;
        }
        .card{
            background:rgba(20,20,40,0.6);
            backdrop-filter:blur(20px);
            border:1px solid rgba(255,255,255,0.1);
            border-radius:25px;
            padding:25px;
            transition:all 0.3s;
            box-shadow:0 10px 40px rgba(0,0,0,0.3);
        }
        .card:hover{
            transform:translateY(-5px);
            border-color:rgba(0,210,255,0.5);
            box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 40px rgba(0,210,255,0.2);
        }
        .card-icon{
            width:55px;
            height:55px;
            background:linear-gradient(135deg,#00d2ff,#3a7bd5);
            border-radius:18px;
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:1.8rem;
            color:white;
            margin-bottom:18px;
            box-shadow:0 8px 25px rgba(0,210,255,0.3);
        }
        .card h3{
            color:white;
            font-size:1.4rem;
            margin-bottom:10px;
            font-weight:600;
        }
        .card p{
            color:rgba(255,255,255,0.6);
            font-size:0.9rem;
            margin-bottom:18px;
        }
        .input-group{
            display:flex;
            gap:8px;
            margin-bottom:12px;
        }
        input,textarea{
            flex:1;
            padding:12px 16px;
            background:rgba(0,0,0,0.3);
            border:1.5px solid rgba(255,255,255,0.1);
            border-radius:15px;
            color:white;
            font-size:0.9rem;
            outline:none;
            transition:all 0.3s;
            font-family:'Inter',sans-serif;
        }
        input:focus,textarea:focus{
            border-color:#00d2ff;
            box-shadow:0 0 20px rgba(0,210,255,0.2);
        }
        input::placeholder{color:rgba(255,255,255,0.3)}
        .btn{
            padding:12px 20px;
            background:linear-gradient(135deg,#00d2ff,#3a7bd5);
            border:none;
            border-radius:15px;
            color:white;
            font-weight:600;
            cursor:pointer;
            transition:all 0.3s;
            box-shadow:0 5px 20px rgba(0,210,255,0.3);
            font-size:0.9rem;
            white-space:nowrap;
        }
        .btn:hover{
            transform:translateY(-2px);
            box-shadow:0 8px 30px rgba(58,123,213,0.4);
            background:linear-gradient(135deg,#3a7bd5,#00d2ff);
        }
        .result{
            margin-top:15px;
            padding:15px;
            background:rgba(0,0,0,0.3);
            border-radius:15px;
            border:1px solid rgba(255,255,255,0.1);
            color:white;
            display:none;
            word-break:break-all;
            max-height:250px;
            overflow-y:auto;
        }
        .result.show{display:block}
        .uid-badge{
            font-size:1.8rem;
            font-weight:700;
            color:#00d2ff;
            text-shadow:0 0 20px rgba(0,210,255,0.5);
        }
        .copy-btn{
            margin-top:10px;
            padding:8px 15px;
            background:rgba(0,210,255,0.15);
            border:1px solid #00d2ff;
            border-radius:12px;
            color:#00d2ff;
            cursor:pointer;
            display:inline-block;
            transition:all 0.3s;
            font-size:0.85rem;
        }
        .copy-btn:hover{background:#00d2ff;color:#0a0a0a}
        .status{
            display:inline-block;
            padding:6px 16px;
            border-radius:30px;
            font-weight:600;
            margin:10px 0;
        }
        .valid{background:linear-gradient(135deg,#00b894,#00cec9);color:white}
        .invalid{background:linear-gradient(135deg,#d63031,#e17055);color:white}
        img.preview{
            max-width:150px;
            max-height:150px;
            border-radius:15px;
            border:3px solid rgba(0,210,255,0.3);
            box-shadow:0 0 30px rgba(0,210,255,0.2);
        }
        .tabs{
            display:flex;
            gap:5px;
            margin-bottom:15px;
        }
        .tab{
            padding:8px 15px;
            background:rgba(255,255,255,0.05);
            border:1px solid rgba(255,255,255,0.1);
            border-radius:12px;
            color:rgba(255,255,255,0.6);
            cursor:pointer;
            font-size:0.85rem;
            transition:all 0.3s;
        }
        .tab.active{
            background:linear-gradient(135deg,#00d2ff,#3a7bd5);
            color:white;
            border-color:transparent;
        }
        .quick-tools{
            display:grid;
            grid-template-columns:repeat(3,1fr);
            gap:8px;
            margin-top:10px;
        }
        .qt-btn{
            padding:10px;
            background:rgba(0,0,0,0.2);
            border-radius:12px;
            text-align:center;
            color:white;
            cursor:pointer;
            transition:all 0.3s;
            border:1px solid rgba(255,255,255,0.05);
            font-size:0.8rem;
        }
        .qt-btn:hover{
            background:rgba(0,210,255,0.1);
            border-color:#00d2ff;
        }
        .qt-btn i{color:#00d2ff;margin-right:5px}
        .footer{
            text-align:center;
            padding:25px;
            color:rgba(255,255,255,0.4);
            margin-top:30px;
        }
        ::-webkit-scrollbar{width:5px}
        ::-webkit-scrollbar-thumb{background:linear-gradient(135deg,#00d2ff,#3a7bd5);border-radius:10px}
        @media(max-width:768px){.grid{grid-template-columns:1fr}.header h1{font-size:2rem}}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1><i class="fab fa-facebook"></i> Facebook Premium Toolkit</h1>
        <p style="color:rgba(255,255,255,0.6);margin-top:10px">Link→UID • Token Checker • DP Downloader • Graph Explorer</p>
    </div>
    
    <div class="grid">
        <!-- Card 1: Link to UID -->
        <div class="card">
            <div class="card-icon"><i class="fas fa-link"></i></div>
            <h3><i class="fas fa-id-card"></i> Link → UID</h3>
            <p>Convert Facebook profile URL to numeric User ID</p>
            <div class="input-group">
                <input type="text" id="urlInput" placeholder="https://facebook.com/zuck">
            </div>
            <button class="btn" onclick="convertUID()"><i class="fas fa-magic"></i> Convert</button>
            <div class="result" id="uidResult"></div>
        </div>
        
        <!-- Card 2: Token Checker -->
        <div class="card">
            <div class="card-icon"><i class="fas fa-key"></i></div>
            <h3><i class="fas fa-shield"></i> Token Checker</h3>
            <p>Validate Facebook Access Token & get account info</p>
            <div class="input-group">
                <input type="text" id="tokenInput" placeholder="EAA...">
            </div>
            <button class="btn" onclick="checkToken()"><i class="fas fa-check"></i> Check</button>
            <div class="result" id="tokenResult"></div>
        </div>
        
        <!-- Card 3: DP Downloader -->
        <div class="card">
            <div class="card-icon"><i class="fas fa-camera"></i></div>
            <h3><i class="fas fa-download"></i> DP Downloader</h3>
            <p>Download high-quality profile picture</p>
            <div class="tabs">
                <div class="tab active" onclick="setMode('uid')">By UID</div>
                <div class="tab" onclick="setMode('url')">By URL</div>
            </div>
            <div class="input-group" id="dpUidGroup">
                <input type="text" id="dpInput" placeholder="Enter Facebook UID (e.g., 4)">
            </div>
            <button class="btn" onclick="getDP()"><i class="fas fa-image"></i> Get Picture</button>
            <div class="result" id="dpResult"></div>
        </div>
    </div>
    
    <div class="grid">
        <!-- Card 4: Profile Info -->
        <div class="card">
            <div class="card-icon"><i class="fas fa-user"></i></div>
            <h3><i class="fas fa-info-circle"></i> Profile Info</h3>
            <p>Get basic info from UID or URL</p>
            <div class="input-group">
                <input type="text" id="infoInput" placeholder="UID or Profile URL">
            </div>
            <button class="btn" onclick="getInfo()"><i class="fas fa-search"></i> Get Info</button>
            <div class="result" id="infoResult"></div>
        </div>
        
        <!-- Card 5: Graph Explorer -->
        <div class="card">
            <div class="card-icon"><i class="fas fa-chart-line"></i></div>
            <h3><i class="fas fa-code"></i> Graph Explorer</h3>
            <p>Test Facebook Graph API endpoints</p>
            <div class="input-group">
                <input type="text" id="endpointInput" placeholder="me?fields=id,name" value="me?fields=id,name">
            </div>
            <button class="btn" onclick="exploreGraph()"><i class="fas fa-rocket"></i> Execute</button>
            <div class="result" id="graphResult"></div>
        </div>
        
        <!-- Card 6: Quick Tools -->
        <div class="card">
            <div class="card-icon"><i class="fas fa-toolbox"></i></div>
            <h3><i class="fas fa-bolt"></i> Quick Tools</h3>
            <p>Useful utilities for developers</p>
            <div class="quick-tools">
                <div class="qt-btn" onclick="genTimestamp()"><i class="far fa-clock"></i> Timestamp</div>
                <div class="qt-btn" onclick="genRandomUID()"><i class="fas fa-random"></i> Random UID</div>
                <div class="qt-btn" onclick="encodeURL()"><i class="fas fa-code"></i> URL Encode</div>
                <div class="qt-btn" onclick="decodeURL()"><i class="fas fa-unlock"></i> URL Decode</div>
                <div class="qt-btn" onclick="encodeBase64()"><i class="fas fa-lock"></i> Base64 Encode</div>
                <div class="qt-btn" onclick="decodeBase64()"><i class="fas fa-lock-open"></i> Base64 Decode</div>
            </div>
            <div class="result" id="quickResult"></div>
        </div>
    </div>
    
    <div class="footer">
        <p>⚡ Facebook Premium Toolkit v3.0 • Made with <i class="fas fa-heart" style="color:#ff6b6b"></i> for Power Users</p>
    </div>
</div>

<script>
let dpMode = 'uid';

function setMode(mode){
    dpMode = mode;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('dpUidGroup').innerHTML = `<input type="text" id="dpInput" placeholder="${mode==='uid'?'Enter UID (e.g., 4)':'Enter Profile URL'}">`;
}

async function api(url, data){
    const res = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    return res.json();
}

async function convertUID(){
    const url = document.getElementById('urlInput').value;
    const res = document.getElementById('uidResult');
    if(!url){alert('Enter URL');return;}
    res.classList.add('show');
    res.innerHTML = '<span style="color:#00d2ff">Converting...</span>';
    const data = await api('/api/uid', {url});
    if(data.success){
        res.innerHTML = `<div class="uid-badge">${data.uid}</div><span class="copy-btn" onclick="copyText('${data.uid}')"><i class="far fa-copy"></i> Copy UID</span>`;
    }else{
        res.innerHTML = `<span style="color:#d63031">${data.error}</span>`;
    }
}

async function checkToken(){
    const token = document.getElementById('tokenInput').value;
    const res = document.getElementById('tokenResult');
    if(!token){alert('Enter token');return;}
    res.classList.add('show');
    res.innerHTML = '<span style="color:#00d2ff">Checking...</span>';
    const data = await api('/api/token', {token});
    if(data.valid){
        res.innerHTML = `<span class="status valid"><i class="fas fa-check-circle"></i> Valid Token</span><br><strong>User ID:</strong> ${data.user_id}<br><strong>Name:</strong> ${data.name}`;
    }else{
        res.innerHTML = `<span class="status invalid"><i class="fas fa-times-circle"></i> Invalid Token</span><br>${data.error||''}`;
    }
}

async function getDP(){
    const input = document.getElementById('dpInput').value;
    const res = document.getElementById('dpResult');
    if(!input){alert('Enter UID or URL');return;}
    res.classList.add('show');
    res.innerHTML = '<span style="color:#00d2ff">Fetching...</span>';
    const data = await api('/api/dp', {input, mode: dpMode});
    if(data.success){
        res.innerHTML = `<img src="${data.url}" class="preview" onerror="this.src='https://via.placeholder.com/150?text=No+Image'"><br><a href="${data.url}" target="_blank" class="copy-btn"><i class="fas fa-download"></i> Download</a>`;
    }else{
        res.innerHTML = `<span style="color:#d63031">${data.error}</span>`;
    }
}

async function getInfo(){
    const input = document.getElementById('infoInput').value;
    const res = document.getElementById('infoResult');
    if(!input){alert('Enter UID or URL');return;}
    res.classList.add('show');
    res.innerHTML = '<span style="color:#00d2ff">Loading...</span>';
    const data = await api('/api/info', {input});
    if(data.success){
        res.innerHTML = `<strong>UID:</strong> ${data.uid}<br><strong>Profile:</strong> <a href="${data.url}" target="_blank" style="color:#00d2ff">${data.url}</a><br><strong>Picture:</strong> <a href="${data.pic}" target="_blank" style="color:#00d2ff">View</a>`;
    }else{
        res.innerHTML = `<span style="color:#d63031">${data.error}</span>`;
    }
}

async function exploreGraph(){
    const endpoint = document.getElementById('endpointInput').value;
    const token = document.getElementById('tokenInput').value;
    const res = document.getElementById('graphResult');
    if(!token){alert('Enter token in Token Checker first');return;}
    res.classList.add('show');
    res.innerHTML = '<span style="color:#00d2ff">Fetching...</span>';
    const data = await api('/api/graph', {endpoint, token});
    if(data.success){
        res.innerHTML = `<pre style="color:#00d2ff;white-space:pre-wrap">${JSON.stringify(data.data, null, 2)}</pre>`;
    }else{
        res.innerHTML = `<span style="color:#d63031">${data.error}</span>`;
    }
}

function copyText(t){navigator.clipboard.writeText(t);alert('Copied!')}

function genTimestamp(){
    const ts = Math.floor(Date.now()/1000);
    document.getElementById('quickResult').classList.add('show');
    document.getElementById('quickResult').innerHTML = `<strong>Timestamp:</strong> ${ts}<br><span class="copy-btn" onclick="copyText('${ts}')">Copy</span>`;
}

function genRandomUID(){
    const uid = '1000'+Math.floor(Math.random()*9000000000000000);
    document.getElementById('quickResult').classList.add('show');
    document.getElementById('quickResult').innerHTML = `<strong>Random UID:</strong> ${uid}<br><span class="copy-btn" onclick="copyText('${uid}')">Copy</span>`;
}

function encodeURL(){
    const t = prompt('Enter text to URL encode:');
    if(t){
        const e = encodeURIComponent(t);
        document.getElementById('quickResult').classList.add('show');
        document.getElementById('quickResult').innerHTML = `<strong>Encoded:</strong> ${e}<br><span class="copy-btn" onclick="copyText('${e}')">Copy</span>`;
    }
}

function decodeURL(){
    const t = prompt('Enter URL encoded text:');
    if(t){
        try{
            const d = decodeURIComponent(t);
            document.getElementById('quickResult').classList.add('show');
            document.getElementById('quickResult').innerHTML = `<strong>Decoded:</strong> ${d}<br><span class="copy-btn" onclick="copyText('${d}')">Copy</span>`;
        }catch(e){alert('Invalid URL encoded text')}
    }
}

function encodeBase64(){
    const t = prompt('Enter text to Base64 encode:');
    if(t){
        const e = btoa(t);
        document.getElementById('quickResult').classList.add('show');
        document.getElementById('quickResult').innerHTML = `<strong>Base64:</strong> ${e}<br><span class="copy-btn" onclick="copyText('${e}')">Copy</span>`;
    }
}

function decodeBase64(){
    const t = prompt('Enter Base64 text:');
    if(t){
        try{
            const d = atob(t);
            document.getElementById('quickResult').classList.add('show');
            document.getElementById('quickResult').innerHTML = `<strong>Decoded:</strong> ${d}<br><span class="copy-btn" onclick="copyText('${d}')">Copy</span>`;
        }catch(e){alert('Invalid Base64')}
    }
}
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/uid', methods=['POST'])
def api_uid():
    url = request.json.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'URL required'})
    
    patterns = [r'facebook\.com\/([^\/\?\&]+)', r'fb\.com\/([^\/\?\&]+)', r'id=(\d+)']
    for p in patterns:
        m = re.search(p, url)
        if m:
            val = m.group(1)
            if val.isdigit():
                return jsonify({'success': True, 'uid': val})
            try:
                r = requests.get(f'https://graph.facebook.com/v19.0/{val}', timeout=5)
                if r.status_code == 200:
                    return jsonify({'success': True, 'uid': r.json().get('id', val)})
            except: pass
    return jsonify({'success': False, 'error': 'Cannot extract UID'})

@app.route('/api/token', methods=['POST'])
def api_token():
    token = request.json.get('token', '').strip()
    if not token:
        return jsonify({'valid': False, 'error': 'Token required'})
    try:
        r = requests.get('https://graph.facebook.com/v19.0/me', params={'access_token': token, 'fields': 'id,name'}, timeout=5)
        if r.status_code == 200:
            d = r.json()
            return jsonify({'valid': True, 'user_id': d.get('id'), 'name': d.get('name')})
        return jsonify({'valid': False, 'error': r.json().get('error', {}).get('message', 'Invalid')})
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)})

@app.route('/api/dp', methods=['POST'])
def api_dp():
    inp = request.json.get('input', '').strip()
    mode = request.json.get('mode', 'uid')
    
    uid = inp
    if mode == 'url':
        m = re.search(r'(?:facebook\.com\/|fb\.com\/|id=)([^\/\?\&]+)', inp)
        if m:
            uid = m.group(1)
            if not uid.isdigit():
                try:
                    r = requests.get(f'https://graph.facebook.com/v19.0/{uid}', timeout=3)
                    if r.status_code == 200:
                        uid = r.json().get('id', uid)
                except: pass
    
    return jsonify({'success': True, 'url': f'https://graph.facebook.com/v19.0/{uid}/picture?width=720'})

@app.route('/api/info', methods=['POST'])
def api_info():
    inp = request.json.get('input', '').strip()
    uid = inp
    if not uid.isdigit():
        m = re.search(r'(?:facebook\.com\/|fb\.com\/|id=)([^\/\?\&]+)', inp)
        if m:
            uid = m.group(1)
            if not uid.isdigit():
                try:
                    r = requests.get(f'https://graph.facebook.com/v19.0/{uid}', timeout=3)
                    if r.status_code == 200:
                        uid = r.json().get('id', uid)
                except: pass
    
    return jsonify({'success': True, 'uid': uid, 'url': f'https://facebook.com/{uid}', 'pic': f'https://graph.facebook.com/v19.0/{uid}/picture?width=720'})

@app.route('/api/graph', methods=['POST'])
def api_graph():
    endpoint = request.json.get('endpoint', 'me').lstrip('/')
    token = request.json.get('token', '')
    if not token:
        return jsonify({'success': False, 'error': 'Token required'})
    try:
        url = f'https://graph.facebook.com/v19.0/{endpoint}'
        url += '&' if '?' in url else '?'
        url += f'access_token={token}'
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return jsonify({'success': True, 'data': r.json()})
        return jsonify({'success': False, 'error': r.json().get('error', {}).get('message', 'Failed')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n✨ FB Premium Toolkit - http://127.0.0.1:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
