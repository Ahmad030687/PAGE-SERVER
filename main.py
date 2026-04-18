from flask import Flask, request, jsonify, render_template_string
import requests
import json
import time
from threading import Thread
import re

app = Flask(__name__)

# Cookie storage
stored_cookies = {}
cookie_servers = {}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>FB Cookie Server</title>
    <style>
        body { background: #0a0a0a; color: #fff; font-family: monospace; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .box { background: #1a1a1a; padding: 20px; border-radius: 10px; margin: 20px 0; border: 1px solid #00ff88; }
        textarea { width: 100%; height: 150px; background: #000; color: #0f0; border: 1px solid #00ff88; padding: 10px; border-radius: 5px; }
        button { background: #00ff88; color: #000; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin: 5px; }
        .danger { background: #ff4444; }
        .warning { background: #ffaa00; }
        .success { color: #00ff88; }
        .error { color: #ff4444; }
        input { width: 100%; padding: 10px; background: #000; color: #fff; border: 1px solid #00ff88; border-radius: 5px; margin: 10px 0; }
        .endpoint { background: #000; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .cookie-list { max-height: 300px; overflow-y: auto; }
        .cookie-item { background: #000; padding: 5px; margin: 5px 0; border-left: 3px solid #00ff88; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍪 FB Cookie Server</h1>
        
        <div class="box">
            <h3>Add Cookie Server</h3>
            <textarea id="cookieInput" placeholder="Paste Facebook cookies (JSON format)"></textarea>
            <button onclick="addCookieServer()">➕ Add Server</button>
            <button onclick="loadDefault()">📋 Load Default</button>
        </div>
        
        <div class="box">
            <h3>Active Cookie Servers</h3>
            <div id="serverList" class="cookie-list"></div>
        </div>
        
        <div class="box">
            <h3>API Endpoints</h3>
            <div class="endpoint">
                <code>GET /api/me?server_id={id}</code> - Get user info<br>
                <code>POST /api/send_message</code> - Send message<br>
                <code>GET /api/servers</code> - List all servers<br>
                <code>DELETE /api/server/{id}</code> - Remove server
            </div>
        </div>
        
        <div class="box">
            <h3>Send Message</h3>
            <input type="text" id="serverId" placeholder="Server ID">
            <input type="text" id="threadId" placeholder="Thread/Conversation ID">
            <input type="text" id="message" placeholder="Message">
            <button onclick="sendMessage()">📨 Send Message</button>
            <div id="sendResult"></div>
        </div>
    </div>
    
    <script>
        const DEFAULT_COOKIES = ''' + json.dumps([
            {"domain":".facebook.com","name":"c_user","value":"61576894738564"},
            {"domain":".facebook.com","name":"xs","value":"40%3ATL3hB8x3GSo_pw%3A2%3A1776446306%3A-1%3A-1"},
            {"domain":".facebook.com","name":"fr","value":"0EL4SONjwZFS1tgBe.AWe757O9t1_WijZWU4qneucfnS4fBPKz86Dpqwc8_2FGK3lW_S0.Bp2fJo..AAA.0.0.Bp40UX.AWdkRncATwpHfWEXvzCUReNM7DQ"},
            {"domain":".facebook.com","name":"datr","value":"aPLZaS2gziut3LDoLldFIP4H"},
            {"domain":".facebook.com","name":"sb","value":"aPLZaZDv6DnYjTZO48VS7vGe"},
            {"domain":".facebook.com","name":"ps_l","value":"1"},
            {"domain":".facebook.com","name":"ps_n","value":"1"},
            {"domain":".facebook.com","name":"pas","value":"61576894738564%3Au8wWhWdgeS"},
            {"domain":".facebook.com","name":"dpr","value":"3.2983407974243164"},
            {"domain":".facebook.com","name":"vpd","value":"v1%3B708x360x3"},
            {"domain":".facebook.com","name":"locale","value":"en_US"},
            {"domain":".facebook.com","name":"fbl_st","value":"101522699%3BT%3A29608367"},
            {"domain":".facebook.com","name":"wl_cbv","value":"v2%3Bclient_version%3A3145%3Btimestamp%3A1776502039"}
        ]) + ''';
        
        function loadDefault() {
            document.getElementById('cookieInput').value = JSON.stringify(DEFAULT_COOKIES);
        }
        
        async function addCookieServer() {
            const cookies = document.getElementById('cookieInput').value;
            try {
                const response = await fetch('/api/add_server', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: cookies
                });
                const data = await response.json();
                if (data.success) {
                    alert('Server added! ID: ' + data.server_id);
                    loadServers();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (e) {
                alert('Error: ' + e);
            }
        }
        
        async function loadServers() {
            const response = await fetch('/api/servers');
            const data = await response.json();
            const list = document.getElementById('serverList');
            list.innerHTML = '';
            for (const [id, info] of Object.entries(data.servers)) {
                list.innerHTML += `<div class="cookie-item">
                    <strong>${id}</strong> - UID: ${info.uid} 
                    <button onclick="deleteServer('${id}')">❌</button>
                    <button onclick="testServer('${id}')">🔍 Test</button>
                </div>`;
            }
        }
        
        async function deleteServer(id) {
            await fetch('/api/server/' + id, {method: 'DELETE'});
            loadServers();
        }
        
        async function testServer(id) {
            const response = await fetch('/api/me?server_id=' + id);
            const data = await response.json();
            alert(JSON.stringify(data, null, 2));
        }
        
        async function sendMessage() {
            const serverId = document.getElementById('serverId').value;
            const threadId = document.getElementById('threadId').value;
            const message = document.getElementById('message').value;
            
            const response = await fetch('/api/send_message', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    server_id: serverId,
                    thread_id: threadId,
                    message: message
                })
            });
            const data = await response.json();
            document.getElementById('sendResult').innerHTML = 
                data.success ? '✅ Sent!' : '❌ Failed: ' + JSON.stringify(data);
        }
        
        loadServers();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/add_server', methods=['POST'])
def add_server():
    try:
        cookie_data = request.get_json()
        
        # Parse cookies
        cookies = {}
        for item in cookie_data:
            if 'name' in item and 'value' in item:
                cookies[item['name']] = item['value']
        
        # Create session
        session = requests.Session()
        for name, value in cookies.items():
            session.cookies.set(name, value, domain='.facebook.com')
        
        # Verify session
        uid = cookies.get('c_user', 'Unknown')
        
        # Generate server ID
        import hashlib
        server_id = hashlib.md5(str(cookies).encode()).hexdigest()[:8]
        
        cookie_servers[server_id] = {
            'cookies': cookies,
            'session': session,
            'uid': uid,
            'created': time.time()
        }
        
        return jsonify({'success': True, 'server_id': server_id, 'uid': uid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/servers')
def list_servers():
    servers = {}
    for sid, data in cookie_servers.items():
        servers[sid] = {
            'uid': data['uid'],
            'created': data['created']
        }
    return jsonify({'servers': servers})

@app.route('/api/server/<server_id>', methods=['DELETE'])
def delete_server(server_id):
    if server_id in cookie_servers:
        del cookie_servers[server_id]
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Server not found'})

@app.route('/api/me')
def get_me():
    server_id = request.args.get('server_id')
    
    if server_id not in cookie_servers:
        return jsonify({'error': 'Invalid server ID'})
    
    server = cookie_servers[server_id]
    session = server['session']
    
    try:
        # Get user info
        r = session.get('https://graph.facebook.com/me?fields=id,name,email', timeout=10)
        if r.status_code == 200:
            return jsonify({'success': True, 'data': r.json()})
        
        # Fallback to mbasic
        r = session.get('https://mbasic.facebook.com/me', timeout=10)
        name_match = re.search(r'<title>(.*?)</title>', r.text)
        name = name_match.group(1) if name_match else 'Unknown'
        
        return jsonify({
            'success': True,
            'data': {
                'id': server['uid'],
                'name': name
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    server_id = data.get('server_id')
    thread_id = data.get('thread_id')
    message = data.get('message')
    
    if server_id not in cookie_servers:
        return jsonify({'success': False, 'error': 'Invalid server ID'})
    
    server = cookie_servers[server_id]
    session = server['session']
    
    try:
        # Get fb_dtsg
        r = session.get('https://mbasic.facebook.com/', timeout=10)
        fb_dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', r.text)
        
        if not fb_dtsg_match:
            return jsonify({'success': False, 'error': 'Could not get fb_dtsg'})
        
        fb_dtsg = fb_dtsg_match.group(1)
        
        # Send message
        send_data = {
            'fb_dtsg': fb_dtsg,
            'body': message,
            'send': 'Send',
            'tids': f'cid.g.{thread_id}',
        }
        
        r = session.post('https://mbasic.facebook.com/messages/send/?icm=1', 
                        data=send_data, timeout=15)
        
        if r.status_code == 200:
            return jsonify({'success': True, 'message': 'Message sent'})
        else:
            return jsonify({'success': False, 'error': f'Status {r.status_code}'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/batch_send', methods=['POST'])
def batch_send():
    """Send messages continuously"""
    data = request.get_json()
    server_id = data.get('server_id')
    thread_id = data.get('thread_id')
    messages = data.get('messages', [])
    delay = data.get('delay', 2)
    
    if server_id not in cookie_servers:
        return jsonify({'success': False, 'error': 'Invalid server ID'})
    
    def send_batch():
        server = cookie_servers[server_id]
        session = server['session']
        
        for msg in messages:
            try:
                r = session.get('https://mbasic.facebook.com/', timeout=10)
                fb_dtsg_match = re.search(r'name="fb_dtsg" value="([^"]+)"', r.text)
                
                if fb_dtsg_match:
                    fb_dtsg = fb_dtsg_match.group(1)
                    send_data = {
                        'fb_dtsg': fb_dtsg,
                        'body': msg,
                        'send': 'Send',
                        'tids': f'cid.g.{thread_id}',
                    }
                    session.post('https://mbasic.facebook.com/messages/send/?icm=1', 
                               data=send_data, timeout=15)
                    print(f"Sent: {msg[:30]}...")
                
                time.sleep(delay)
            except Exception as e:
                print(f"Error: {e}")
    
    Thread(target=send_batch).start()
    return jsonify({'success': True, 'message': 'Batch sending started'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
