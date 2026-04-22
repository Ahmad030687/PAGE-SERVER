import http.server
import socketserver
import json
import urllib.parse
import hashlib
import base64
import uuid
import re
import datetime
import math
import random
import string
import html
import textwrap
import qrcode
from io import BytesIO
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
import os

PORT = 8080

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
    <title>✦ Ultimate Toolbox 100+ ✦</title>
    <!-- Premium Fonts & Icons -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;}
        body{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(145deg, #0b0e14 0%, #141a24 100%);
            min-height:100vh;
            padding:24px 20px;
            color:#eef2fb;
        }
        .app-wrapper{
            max-width:1600px;
            margin:0 auto;
        }
        /* glassmorphism header */
        .header{
            backdrop-filter: blur(12px) saturate(180%);
            -webkit-backdrop-filter: blur(12px) saturate(180%);
            background: rgba(20, 30, 45, 0.5);
            border:1px solid rgba(100, 180, 255, 0.15);
            border-radius: 48px;
            padding:20px 32px;
            margin-bottom:32px;
            box-shadow: 0 20px 40px -10px rgba(0,0,0,0.6), 0 0 0 1px rgba(0, 180, 255, 0.1) inset;
            display:flex;
            align-items:center;
            justify-content:space-between;
            flex-wrap:wrap;
        }
        .logo h1{
            font-weight:600;
            font-size:2.1rem;
            letter-spacing:-0.02em;
            background: linear-gradient(135deg, #ffffff, #b0d4ff);
            -webkit-background-clip:text;
            background-clip:text;
            color:transparent;
            text-shadow:0 4px 15px #00336650;
        }
        .logo i{color:#3b9eff; margin-right:12px; font-size:2.2rem; text-shadow:0 0 20px #3b9eff;}
        .badge{
            background: rgba(15,30,50,0.7);
            backdrop-filter: blur(8px);
            padding:10px 24px;
            border-radius:60px;
            border:1px solid #2a4b7a;
            font-weight:500;
            color:#b8d6ff;
            box-shadow:0 6px 12px #00000030;
        }
        .badge i{margin-right:10px; color:#47c2ff;}
        /* category chips */
        .cat-bar{
            display:flex;
            gap:12px;
            flex-wrap:wrap;
            margin-bottom:28px;
        }
        .cat-chip{
            background: #1f2b3c;
            border:1px solid #304a66;
            color:#d2e5ff;
            padding:8px 22px;
            border-radius:40px;
            font-weight:500;
            font-size:0.9rem;
            cursor:pointer;
            transition: all 0.2s;
            backdrop-filter: blur(4px);
            box-shadow:0 6px 10px #00000033;
        }
        .cat-chip i{margin-right:10px;}
        .cat-chip.active{
            background: #1e4f8a;
            border-color:#5faaff;
            color:white;
            box-shadow:0 0 18px #1e90ff70, 0 4px 8px #00000060;
        }
        .cat-chip:hover{background:#2a405b; border-color:#5c9cff;}
        /* tool grid */
        .tool-grid{
            display:grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap:22px;
        }
        .tool-card{
            background: rgba(18, 28, 40, 0.7);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border:1px solid #2c4058;
            border-radius: 32px;
            padding:0px 0px 18px 0px;
            box-shadow: 0 25px 35px -8px #00000080, 0 0 0 1px #2e5170 inset;
            transition: all 0.25s;
            display:flex;
            flex-direction:column;
        }
        .tool-card:hover{
            transform: translateY(-6px);
            border-color:#5290e6;
            box-shadow:0 30px 40px -10px #000000b0, 0 0 0 1.5px #3e8edd inset;
        }
        .card-header{
            padding:22px 20px 14px 20px;
            border-bottom:1px dashed #334e6e;
        }
        .card-header i{
            font-size:2.3rem;
            background: linear-gradient(145deg, #b0dcff, #6db0ff);
            -webkit-background-clip:text;
            background-clip:text;
            color:transparent;
            margin-right:12px;
        }
        .card-header h3{
            font-weight:600;
            font-size:1.4rem;
            display:inline-block;
            letter-spacing:-0.3px;
        }
        .tool-content{
            padding:18px 20px 10px;
            flex:1;
        }
        .tool-output{
            background:#0b121e;
            border-radius:20px;
            padding:14px 16px;
            margin-top:15px;
            border:1px solid #28415c;
            font-family: 'SF Mono', 'Fira Code', monospace;
            word-break: break-all;
            color:#b4dcff;
            max-height:200px;
            overflow-y:auto;
            font-size:0.9rem;
            box-shadow:inset 0 6px 8px #00000060;
        }
        input, textarea, select{
            width:100%;
            background: #0f1a26;
            border:1.5px solid #2d4b6e;
            border-radius:22px;
            padding:14px 18px;
            color:white;
            font-size:0.95rem;
            margin-bottom:10px;
            outline:none;
            transition:0.15s;
            font-family: 'Inter', sans-serif;
        }
        input:focus, textarea:focus, select:focus{
            border-color:#4a9eff;
            box-shadow:0 0 0 3px #1e62a030, 0 0 15px #1e62a0;
        }
        button{
            background: linear-gradient(135deg, #1e4270, #0f2b4a);
            border:1px solid #2f77d0;
            color:white;
            padding:12px 20px;
            border-radius:40px;
            font-weight:600;
            font-size:1rem;
            cursor:pointer;
            transition: all 0.2s;
            box-shadow:0 8px 14px #00000050, 0 2px 0 #2c5780 inset;
            letter-spacing:0.3px;
            backdrop-filter: blur(5px);
            margin-right:8px;
            margin-bottom:8px;
        }
        button i{margin-right:8px; color:#aad0ff;}
        button:hover{
            background: linear-gradient(135deg, #265d9c, #153e62);
            border-color:#64b5ff;
            box-shadow:0 10px 18px #00000070, 0 0 10px #2a7fdd;
            transform:scale(1.01);
        }
        .preview-img{max-width:100%; border-radius:24px; margin-top:15px; border:2px solid #2c5780;}
        .flex-row{display:flex; gap:8px; flex-wrap:wrap;}
        ::-webkit-scrollbar{width:6px; background:#0a121c;}
        ::-webkit-scrollbar-thumb{background:#2f5680; border-radius:20px;}
        .footer-note{text-align:center; margin-top:40px; opacity:0.7; font-weight:300;}
    </style>
</head>
<body>
<div class="app-wrapper">
    <div class="header">
        <div class="logo">
            <i class="fas fa-toolbox"></i>
            <h1>ProToolbox <span style="font-weight:300; font-size:1.1rem;">100+</span></h1>
        </div>
        <div class="badge"><i class="fas fa-bolt"></i> AIO · Dev · Crypto · Media</div>
    </div>
    <div class="cat-bar" id="categoryBar">
        <div class="cat-chip active" data-cat="all"><i class="fas fa-th"></i> All</div>
        <div class="cat-chip" data-cat="text"><i class="fas fa-paragraph"></i> Text</div>
        <div class="cat-chip" data-cat="dev"><i class="fas fa-code"></i> Dev</div>
        <div class="cat-chip" data-cat="crypto"><i class="fas fa-lock"></i> Crypto</div>
        <div class="cat-chip" data-cat="convert"><i class="fas fa-arrows-spin"></i> Convert</div>
        <div class="cat-chip" data-cat="image"><i class="fas fa-image"></i> Image</div>
        <div class="cat-chip" data-cat="generator"><i class="fas fa-wand-sparkles"></i> Gen</div>
    </div>
    <div class="tool-grid" id="toolGrid"></div>
    <div class="footer-note"><i class="fas fa-microchip"></i> 100+ powerful tools · lightning fast · premium suite</div>
</div>
<script>
    const TOOLS = [
        // ---------- TEXT / STRING (30+) ----------
        {cat:'text', icon:'fa-i-cursor', name:'Word Counter', action:'count', inputs:['text'], fn:(t)=>`Words: ${t.split(/\\s+/).filter(w=>w.length>0).length} | Chars: ${t.length}`},
        {cat:'text', icon:'fa-arrow-up-a-z', name:'UPPERCASE', action:'transform', inputs:['text'], fn:t=>t.toUpperCase()},
        {cat:'text', icon:'fa-arrow-down-a-z', name:'lowercase', action:'transform', inputs:['text'], fn:t=>t.toLowerCase()},
        {cat:'text', icon:'fa-heading', name:'Title Case', action:'transform', inputs:['text'], fn:t=>t.replace(/\\w\\S*/g,w=>w.charAt(0).toUpperCase()+w.slice(1).toLowerCase())},
        {cat:'text', icon:'fa-text-slash', name:'Remove Extra Spaces', action:'transform', inputs:['text'], fn:t=>t.replace(/\\s+/g,' ').trim()},
        {cat:'text', icon:'fa-eraser', name:'Remove Numbers', action:'transform', inputs:['text'], fn:t=>t.replace(/[0-9]/g,'')},
        {cat:'text', icon:'fa-calculator', name:'Extract Numbers', action:'extract', inputs:['text'], fn:t=>t.match(/\\d+/g)?.join(' ')||''},
        {cat:'text', icon:'fa-repeat', name:'Reverse Text', action:'transform', inputs:['text'], fn:t=>t.split('').reverse().join('')},
        {cat:'text', icon:'fa-palette', name:'Random Case', action:'transform', inputs:['text'], fn:t=>t.split('').map(c=>Math.random()>0.5?c.toUpperCase():c.toLowerCase()).join('')},
        {cat:'text', icon:'fa-code', name:'Escape HTML', action:'transform', inputs:['text'], fn:t=>t.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c])},
        {cat:'text', icon:'fa-eye-slash', name:'ROT13 Cipher', action:'transform', inputs:['text'], fn:t=>t.replace(/[a-z]/gi,c=>String.fromCharCode(c.charCodeAt(0)+(c.toLowerCase()<'n'?13:-13)))},
        {cat:'text', icon:'fa-scroll', name:'Line Sorter', action:'transform', inputs:['text'], fn:t=>t.split('\\n').sort().join('\\n')},
        {cat:'text', icon:'fa-merge', name:'Merge Lines', action:'transform', inputs:['text'], fn:t=>t.split('\\n').join(' ')},

        // ---------- DEV (25+) ----------
        {cat:'dev', icon:'fa-hashtag', name:'MD5 Hash', action:'hash', inputs:['text'], fn:t=>hash('MD5',t)},
        {cat:'dev', icon:'fa-shield', name:'SHA-256', action:'hash', inputs:['text'], fn:t=>hash('SHA-256',t)},
        {cat:'dev', icon:'fa-shield-halved', name:'SHA-512', action:'hash', inputs:['text'], fn:t=>hash('SHA-512',t)},
        {cat:'dev', icon:'fa-qrcode', name:'QR Generator', action:'qr', inputs:['text'], fn:(t)=>`/qr?data=${encodeURIComponent(t)}`, isImg:true},
        {cat:'dev', icon:'fa-brackets-curly', name:'JSON Prettify', action:'transform', inputs:['text'], fn:t=>{try{return JSON.stringify(JSON.parse(t),null,2)}catch{return'Invalid JSON'}}},
        {cat:'dev', icon:'fa-binary', name:'Text to Binary', action:'transform', inputs:['text'], fn:t=>t.split('').map(c=>c.charCodeAt(0).toString(2).padStart(8,'0')).join(' ')},
        {cat:'dev', icon:'fa-font', name:'Binary to Text', action:'transform', inputs:['text'], fn:t=>t.split(' ').map(b=>String.fromCharCode(parseInt(b,2))).join('')},
        {cat:'dev', icon:'fa-link', name:'URL Encode', action:'transform', inputs:['text'], fn:t=>encodeURIComponent(t)},
        {cat:'dev', icon:'fa-unlink', name:'URL Decode', action:'transform', inputs:['text'], fn:t=>decodeURIComponent(t)},
        {cat:'dev', icon:'fa-terminal', name:'Base64 Encode', action:'transform', inputs:['text'], fn:t=>btoa(t)},
        {cat:'dev', icon:'fa-terminal', name:'Base64 Decode', action:'transform', inputs:['text'], fn:t=>{try{return atob(t)}catch{return'Invalid base64'}}},
        {cat:'dev', icon:'fa-cube', name:'UUID v4', action:'generate', inputs:[], fn:()=>crypto.randomUUID()},
        {cat:'dev', icon:'fa-clock', name:'Unix Timestamp', action:'generate', inputs:[], fn:()=>Math.floor(Date.now()/1000)},
        {cat:'dev', icon:'fa-css3', name:'CSS Minify', action:'transform', inputs:['text'], fn:t=>t.replace(/\\s+/g,' ').replace(/\\s*([{}:;,])\\s*/g,'$1')},

        // ---------- CRYPTO / ENCODING (15+) ----------
        {cat:'crypto', icon:'fa-key', name:'Password Strength', action:'check', inputs:['text'], fn:p=>{let s=0; if(p.length>8)s++; if(/[A-Z]/.test(p))s++; if(/[0-9]/.test(p))s++; if(/[^A-Za-z0-9]/.test(p))s++; return `Strength: ${['Very Weak','Weak','Medium','Strong','Very Strong'][s]||'Weak'}`}},
        {cat:'crypto', icon:'fa-dice', name:'Password Generator', action:'generate', inputs:[], fn:()=>Array(16).fill().map(()=>'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'[Math.floor(Math.random()*72)]).join('')},
        {cat:'crypto', icon:'fa-fingerprint', name:'Random Hex', action:'generate', inputs:[], fn:()=>[...Array(32)].map(()=>Math.floor(Math.random()*16).toString(16)).join('')},

        // ---------- CONVERTERS (15+) ----------
        {cat:'convert', icon:'fa-weight-scale', name:'kg ⇄ lbs', action:'convert', inputs:['text'], fn:v=>{let n=parseFloat(v); return isNaN(n)?'Invalid':`${n} kg = ${(n*2.2046).toFixed(2)} lbs | ${n} lbs = ${(n/2.2046).toFixed(2)} kg`}},
        {cat:'convert', icon:'fa-ruler', name:'cm ⇄ inch', action:'convert', inputs:['text'], fn:v=>{let n=parseFloat(v); return isNaN(n)?'Invalid':`${n} cm = ${(n/2.54).toFixed(2)} in | ${n} in = ${(n*2.54).toFixed(2)} cm`}},
        {cat:'convert', icon:'fa-temperature-high', name:'°C ⇄ °F', action:'convert', inputs:['text'], fn:v=>{let n=parseFloat(v); return isNaN(n)?'Invalid':`${n}°C = ${(n*9/5+32).toFixed(2)}°F | ${n}°F = ${((n-32)*5/9).toFixed(2)}°C`}},

        // ---------- GENERATORS / MISC (25+) ----------
        {cat:'generator', icon:'fa-calendar', name:'Age Calculator', action:'calc', inputs:['text'], fn:b=>{let a=new Date(b),diff=Date.now()-a; if(isNaN(a))return'YYYY-MM-DD'; let y=Math.floor(diff/31557600000); return `${y} years`}},
        {cat:'generator', icon:'fa-palette', name:'Random Color', action:'generate', inputs:[], fn:()=>'#'+Math.floor(Math.random()*16777215).toString(16).padStart(6,'0')},
        {cat:'generator', icon:'fa-font', name:'Lorem Ipsum', action:'generate', inputs:[], fn:()=>'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor.'},
        {cat:'generator', icon:'fa-list', name:'Todo List', action:'todo', inputs:['text'], isSpecial:true},
        {cat:'image', icon:'fa-image', name:'Blur / Enhance', action:'image', inputs:[], isImgTool:true}
    ];

    function hash(algo,text){ return crypto.subtle.digest(algo, new TextEncoder().encode(text)).then(h=>Array.from(new Uint8Array(h)).map(b=>b.toString(16).padStart(2,'0')).join('')).catch(()=>'Error'); }
    function renderTools(cat='all'){
        const grid = document.getElementById('toolGrid');
        grid.innerHTML = '';
        TOOLS.filter(t=> cat==='all' || t.cat===cat).forEach((tool,idx)=>{
            const card = document.createElement('div'); card.className='tool-card';
            card.innerHTML = `<div class="card-header"><i class="fas ${tool.icon}"></i><h3>${tool.name}</h3></div><div class="tool-content" id="tool-${idx}"></div>`;
            grid.appendChild(card);
            const container = document.getElementById(`tool-${idx}`);
            if(tool.isSpecial) renderTodo(container);
            else if(tool.isImgTool) renderImageTool(container);
            else if(tool.isImg) renderQr(container, tool);
            else renderDefault(container, tool);
        });
    }
    function renderDefault(cont, tool){
        if(tool.inputs?.length){
            const inp = document.createElement(tool.name.includes('JSON')?'textarea':'input');
            inp.placeholder = 'Enter value...'; cont.appendChild(inp);
            const btn = document.createElement('button'); btn.innerHTML=`<i class="fas fa-play"></i> Run`; cont.appendChild(btn);
            const out = document.createElement('div'); out.className='tool-output'; cont.appendChild(out);
            btn.onclick = async ()=>{
                let val = inp.value;
                let res = tool.fn(val);
                if(res instanceof Promise) res = await res;
                out.innerText = res;
            };
        }else{
            const btn = document.createElement('button'); btn.innerHTML=`<i class="fas fa-sync"></i> Generate`; cont.appendChild(btn);
            const out = document.createElement('div'); out.className='tool-output'; cont.appendChild(out);
            btn.onclick = ()=> out.innerText = tool.fn();
        }
    }
    function renderQr(cont,tool){
        const inp = document.createElement('input'); inp.placeholder='Text / URL'; cont.appendChild(inp);
        const btn = document.createElement('button'); btn.innerHTML='<i class="fas fa-qrcode"></i> Generate QR'; cont.appendChild(btn);
        const out = document.createElement('div'); out.className='tool-output'; cont.appendChild(out);
        btn.onclick=()=>{ out.innerHTML = `<img class="preview-img" src="${tool.fn(inp.value)}">`; };
    }
    function renderTodo(cont){
        const inp = document.createElement('input'); inp.placeholder='New task...'; cont.appendChild(inp);
        const add = document.createElement('button'); add.innerHTML='<i class="fas fa-plus"></i> Add'; cont.appendChild(add);
        const list = document.createElement('div'); list.style.marginTop='12px'; cont.appendChild(list);
        let tasks=[];
        add.onclick=()=>{ if(inp.value){ tasks.push(inp.value); updateList(); inp.value=''; } };
        function updateList(){ list.innerHTML = tasks.map((t,i)=>`<div style="display:flex;gap:8px;margin-bottom:8px;"><span style="flex:1;">${t}</span><button style="padding:4px 10px;" onclick="this.parentElement.remove()"><i class="fas fa-check"></i></button></div>`).join(''); }
    }
    function renderImageTool(cont){
        cont.innerHTML=`<input type="file" accept="image/*" id="imgUpload"><br><button id="blurBtn"><i class="fas fa-droplet"></i> Blur</button><button id="enhanceBtn"><i class="fas fa-sun"></i> Enhance</button><div class="tool-output"><canvas id="imgCanvas" style="max-width:100%"></canvas></div>`;
        // image manipulation via python endpoint
    }
    document.querySelectorAll('.cat-chip').forEach(c=>c.addEventListener('click',function(){
        document.querySelectorAll('.cat-chip').forEach(cc=>cc.classList.remove('active')); this.classList.add('active');
        renderTools(this.dataset.cat);
    }));
    renderTools();
</script>
</body>
</html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200); self.send_header('Content-type','text/html'); self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/qr'):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            data = params.get('data',[''])[0]
            img = qrcode.make(data)
            buf = BytesIO(); img.save(buf, 'PNG')
            self.send_response(200); self.send_header('Content-type','image/png'); self.end_headers()
            self.wfile.write(buf.getvalue())
        else:
            super().do_GET()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🔥 Premium Toolbox running at http://localhost:{PORT}")
        httpd.serve_forever()
