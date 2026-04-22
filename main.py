import dns.resolver
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, hashlib, base64, uuid, re, datetime, math, random, string, html, urllib.parse, os
from io import BytesIO
try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps
    import qrcode
    PIL_AVAILABLE = True
except:
    PIL_AVAILABLE = False

PORT = int(os.environ.get('PORT', 8080))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✨ ProToolbox 100+ | Premium Suite</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;background:linear-gradient(135deg,#0a0f1e 0%,#0d1425 50%,#0a0f1e 100%);min-height:100vh;padding:20px;color:#fff}
        body::before{content:'';position:fixed;top:0;left:0;right:0;bottom:0;background:radial-gradient(circle at 20% 80%,#3b82f620 0%,transparent 50%),radial-gradient(circle at 80% 20%,#8b5cf620 0%,transparent 50%),radial-gradient(circle at 40% 40%,#06b6d420 0%,transparent 50%);pointer-events:none;z-index:-1}
        .wrapper{max-width:1600px;margin:0 auto}
        .header{backdrop-filter:blur(20px);background:linear-gradient(135deg,#1e293b80,#0f172a80);border:1px solid #3b82f640;border-radius:60px;padding:20px 32px;margin-bottom:24px;box-shadow:0 20px 40px #00000080,0 0 0 1px #3b82f620 inset,0 0 40px #3b82f620;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap}
        .logo h1{font-weight:700;font-size:2.2rem;background:linear-gradient(135deg,#fff,#93c5fd,#60a5fa);-webkit-background-clip:text;background-clip:text;color:transparent}
        .logo i{color:#3b82f6;margin-right:15px;font-size:2.2rem;filter:drop-shadow(0 0 15px #3b82f6)}
        .badge{background:linear-gradient(135deg,#1e293b,#0f172a);padding:12px 28px;border-radius:50px;border:1px solid #3b82f680;font-weight:600;color:#bfdbfe;box-shadow:0 8px 20px #000,0 0 20px #3b82f630}
        .badge i{margin-right:10px;color:#60a5fa}
        .search-box{margin-bottom:20px;position:relative}
        .search-box input{width:100%;padding:18px 24px 18px 60px;border-radius:60px;font-size:1.1rem;background:#0f172a;border:1.5px solid #1e3a5f;color:#fff;outline:none}
        .search-box input:focus{border-color:#3b82f6;box-shadow:0 0 20px #3b82f680}
        .search-box i{position:absolute;left:24px;top:50%;transform:translateY(-50%);color:#3b82f6;font-size:1.3rem}
        .cat-bar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:24px}
        .cat-chip{background:linear-gradient(145deg,#1e293b,#0f172a);border:1.5px solid #334155;color:#cbd5e1;padding:10px 22px;border-radius:50px;font-weight:600;font-size:0.9rem;cursor:pointer;transition:all .2s;backdrop-filter:blur(12px);box-shadow:0 8px 16px #00000040}
        .cat-chip i{margin-right:10px}
        .cat-chip.active{background:linear-gradient(145deg,#2563eb,#1d4ed8);border-color:#60a5fa;color:#fff;box-shadow:0 8px 20px #000,0 0 30px #3b82f6}
        .cat-chip:hover{background:linear-gradient(145deg,#1e293b,#1e3a5f);border-color:#3b82f6;transform:translateY(-2px)}
        .tool-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}
        .tool-card{background:linear-gradient(145deg,#1e293bb0,#0f172ad0);backdrop-filter:blur(20px);border:1.5px solid #3b82f620;border-radius:36px;padding:0;box-shadow:0 25px 35px #000000b0,0 0 0 1px #3b82f620 inset;transition:all .3s;overflow:hidden}
        .tool-card:hover{transform:translateY(-6px);border-color:#3b82f6;box-shadow:0 35px 45px #000000e0,0 0 0 2px #3b82f640 inset,0 0 40px #3b82f630}
        .card-header{padding:22px 20px 14px;border-bottom:1.5px dashed #1e3a5f;background:linear-gradient(135deg,#0f172a40,transparent)}
        .card-header i{font-size:2.2rem;background:linear-gradient(145deg,#93c5fd,#3b82f6);-webkit-background-clip:text;background-clip:text;color:transparent;margin-right:12px;filter:drop-shadow(0 0 12px #3b82f6)}
        .card-header h3{font-weight:700;font-size:1.3rem;display:inline-block;background:linear-gradient(135deg,#f8fafc,#bfdbfe);-webkit-background-clip:text;background-clip:text;color:transparent}
        .tool-content{padding:18px 20px 20px}
        .tool-output{background:#020617;border-radius:20px;padding:16px;margin-top:14px;border:1.5px solid #1e3a5f;font-family:'Monaco','Menlo',monospace;word-break:break-all;color:#bae6fd;max-height:200px;overflow-y:auto;font-size:0.9rem;box-shadow:inset 0 6px 10px #000}
        input,textarea,select{width:100%;background:#0f172a;border:1.5px solid #1e3a5f;border-radius:24px;padding:12px 18px;color:#fff;font-size:0.95rem;margin-bottom:10px;outline:none}
        input:focus,textarea:focus,select:focus{border-color:#3b82f6;box-shadow:0 0 0 3px #3b82f620,0 0 15px #3b82f6}
        button{background:linear-gradient(145deg,#2563eb,#1d4ed8);border:1.5px solid #60a5fa;color:#fff;padding:12px 20px;border-radius:40px;font-weight:600;font-size:0.9rem;cursor:pointer;transition:all .2s;box-shadow:0 8px 16px #000,0 2px 0 #60a5fa inset;margin-right:8px;margin-bottom:8px}
        button:hover{background:linear-gradient(145deg,#3b82f6,#2563eb);border-color:#93c5fd;box-shadow:0 12px 20px #000,0 0 20px #3b82f6;transform:scale(1.02)}
        .preview-img{max-width:100%;border-radius:20px;margin-top:12px;border:2px solid #1e3a5f}
        .footer{text-align:center;margin-top:40px;padding:20px;opacity:0.7;color:#94a3b8;border-top:1px solid #1e3a5f40}
        ::-webkit-scrollbar{width:6px;background:#020617}
        ::-webkit-scrollbar-thumb{background:linear-gradient(#2563eb,#1d4ed8);border-radius:20px}
    </style>
</head>
<body>
<div class="wrapper">
    <div class="header">
        <div class="logo"><i class="fas fa-crown"></i><h1>ProToolbox <span style="font-weight:300;font-size:1.2rem;background:none;color:#93c5fd;">100+</span></h1></div>
        <div class="badge"><i class="fas fa-bolt"></i> PREMIUM · ALL-IN-ONE · VERCEL READY</div>
    </div>
    <div class="search-box"><i class="fas fa-search"></i><input type="text" id="searchInput" placeholder="Search 100+ tools... (hash, qr, crypto, convert, image)"></div>
    <div class="cat-bar" id="categoryBar">
        <div class="cat-chip active" data-cat="all"><i class="fas fa-grid-2"></i>All</div><div class="cat-chip" data-cat="text"><i class="fas fa-align-left"></i>Text</div><div class="cat-chip" data-cat="dev"><i class="fas fa-code"></i>Dev</div><div class="cat-chip" data-cat="crypto"><i class="fas fa-shield"></i>Crypto</div><div class="cat-chip" data-cat="convert"><i class="fas fa-arrows-rotate"></i>Convert</div><div class="cat-chip" data-cat="generator"><i class="fas fa-wand-sparkles"></i>Gen</div><div class="cat-chip" data-cat="math"><i class="fas fa-calculator"></i>Math</div>
    </div>
    <div class="tool-grid" id="toolGrid"></div>
    <div class="footer"><i class="fas fa-circle"></i> 100+ PROFESSIONAL TOOLS · LIGHTNING FAST · VERCEL DEPLOYED <i class="fas fa-circle"></i></div>
</div>
<script>
    const TOOLS = [
        {cat:'text',icon:'fa-i-cursor',name:'Word Counter',fn:t=>`Words: ${t.split(/\\s+/).filter(w=>w).length} | Chars: ${t.length} | Lines: ${t.split('\\n').length}`},
        {cat:'text',icon:'fa-arrow-up-a-z',name:'UPPERCASE',fn:t=>t.toUpperCase()},
        {cat:'text',icon:'fa-arrow-down-a-z',name:'lowercase',fn:t=>t.toLowerCase()},
        {cat:'text',icon:'fa-heading',name:'Title Case',fn:t=>t.replace(/\\w\\S*/g,w=>w.charAt(0).toUpperCase()+w.slice(1).toLowerCase())},
        {cat:'text',icon:'fa-text-slash',name:'Remove Spaces',fn:t=>t.replace(/\\s+/g,' ').trim()},
        {cat:'text',icon:'fa-eraser',name:'Remove Numbers',fn:t=>t.replace(/[0-9]/g,'')},
        {cat:'text',icon:'fa-filter',name:'Extract Numbers',fn:t=>t.match(/\\d+/g)?.join(' ')||''},
        {cat:'text',icon:'fa-filter',name:'Extract Emails',fn:t=>t.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}/g)?.join('\\n')||'No emails'},
        {cat:'text',icon:'fa-filter',name:'Extract URLs',fn:t=>t.match(/https?:\\/\\/[^\\s]+/g)?.join('\\n')||'No URLs'},
        {cat:'text',icon:'fa-repeat',name:'Reverse Text',fn:t=>t.split('').reverse().join('')},
        {cat:'text',icon:'fa-shuffle',name:'Random Case',fn:t=>t.split('').map(c=>Math.random()>0.5?c.toUpperCase():c.toLowerCase()).join('')},
        {cat:'text',icon:'fa-code',name:'Escape HTML',fn:t=>t.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'})[c])},
        {cat:'text',icon:'fa-eye-slash',name:'ROT13',fn:t=>t.replace(/[a-z]/gi,c=>String.fromCharCode(c.charCodeAt(0)+(c.toLowerCase()<'n'?13:-13)))},
        {cat:'text',icon:'fa-arrow-up-wide-short',name:'Sort Lines',fn:t=>t.split('\\n').sort().join('\\n')},
        {cat:'text',icon:'fa-merge',name:'Merge Lines',fn:t=>t.split('\\n').join(' ')},
        {cat:'text',icon:'fa-border-all',name:'Add Line Numbers',fn:t=>t.split('\\n').map((l,i)=>`${i+1}: ${l}`).join('\\n')},
        {cat:'text',icon:'fa-scissors',name:'Remove Duplicates',fn:t=>[...new Set(t.split('\\n'))].join('\\n')},
        {cat:'text',icon:'fa-ruler',name:'Char Frequency',fn:t=>{let f={};t.split('').forEach(c=>f[c]=(f[c]||0)+1);return Object.entries(f).map(([c,n])=>`'${c}': ${n}`).join('\\n')}},
        {cat:'dev',icon:'fa-hashtag',name:'MD5',fn:async t=>await hash('MD5',t)},
        {cat:'dev',icon:'fa-shield',name:'SHA-1',fn:async t=>await hash('SHA-1',t)},
        {cat:'dev',icon:'fa-shield-halved',name:'SHA-256',fn:async t=>await hash('SHA-256',t)},
        {cat:'dev',icon:'fa-shield',name:'SHA-512',fn:async t=>await hash('SHA-512',t)},
        {cat:'dev',icon:'fa-qrcode',name:'QR Code',isImg:true,fn:t=>`/qr?data=${encodeURIComponent(t)}`},
        {cat:'dev',icon:'fa-brackets-curly',name:'JSON Prettify',fn:t=>{try{return JSON.stringify(JSON.parse(t),null,2)}catch{return'Invalid JSON'}}},
        {cat:'dev',icon:'fa-binary',name:'Text → Binary',fn:t=>t.split('').map(c=>c.charCodeAt(0).toString(2).padStart(8,'0')).join(' ')},
        {cat:'dev',icon:'fa-font',name:'Binary → Text',fn:t=>t.split(' ').map(b=>String.fromCharCode(parseInt(b,2))).join('')},
        {cat:'dev',icon:'fa-link',name:'URL Encode',fn:t=>encodeURIComponent(t)},
        {cat:'dev',icon:'fa-unlink',name:'URL Decode',fn:t=>{try{return decodeURIComponent(t)}catch{return'Invalid'}}},
        {cat:'dev',icon:'fa-terminal',name:'Base64 Encode',fn:t=>btoa(unescape(encodeURIComponent(t)))},
        {cat:'dev',icon:'fa-terminal',name:'Base64 Decode',fn:t=>{try{return decodeURIComponent(escape(atob(t)))}catch{return'Invalid'}}},
        {cat:'dev',icon:'fa-cube',name:'UUID v4',fn:()=>crypto.randomUUID()},
        {cat:'dev',icon:'fa-clock',name:'Unix Timestamp',fn:()=>Math.floor(Date.now()/1000).toString()},
        {cat:'dev',icon:'fa-calendar',name:'Timestamp→Date',fn:t=>new Date(parseInt(t)*1000).toString()},
        {cat:'dev',icon:'fa-css3',name:'CSS Minify',fn:t=>t.replace(/\\/\\*[\\s\\S]*?\\*\\//g,'').replace(/\\s+/g,' ').replace(/\\s*([{}:;,])\\s*/g,'$1')},
        {cat:'dev',icon:'fa-html5',name:'HTML Minify',fn:t=>t.replace(/<!--[\\s\\S]*?-->/g,'').replace(/>\\s+</g,'><').trim()},
        {cat:'dev',icon:'fa-keyboard',name:'JWT Decoder',fn:t=>{try{let p=t.split('.')[1];return JSON.stringify(JSON.parse(atob(p)),null,2)}catch{return'Invalid JWT'}}},
        {cat:'crypto',icon:'fa-key',name:'Password Strength',fn:p=>{let s=0;if(p.length>7)s++;if(p.length>11)s++;if(/[A-Z]/.test(p))s++;if(/[0-9]/.test(p))s++;if(/[^A-Za-z0-9]/.test(p))s++;return`${['Very Weak','Weak','Fair','Good','Strong'][s]||'Weak'} (${s}/5)`}},
        {cat:'crypto',icon:'fa-dice',name:'Password Gen',fn:()=>Array(16).fill().map(()=>'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'[Math.floor(Math.random()*72)]).join('')},
        {cat:'crypto',icon:'fa-fingerprint',name:'Random Hex',fn:()=>[...Array(32)].map(()=>Math.floor(Math.random()*16).toString(16)).join('')},
        {cat:'crypto',icon:'fa-envelope',name:'Email Validator',fn:t=>/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(t)?'✅ Valid':'❌ Invalid'},
        {cat:'crypto',icon:'fa-globe',name:'URL Validator',fn:t=>{try{new URL(t);return'✅ Valid'}catch{return'❌ Invalid'}}},
        {cat:'crypto',icon:'fa-credit-card',name:'Card Validator',fn:t=>{let s=0,d=false;for(let i=t.length-1;i>=0;i--){let n=parseInt(t[i]);if(d&&(n*=2)>9)n-=9;s+=n;d=!d}return s%10===0?'✅ Valid':'❌ Invalid'}},
        {cat:'convert',icon:'fa-weight-scale',name:'kg ⇄ lbs',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter number':`${n}kg = ${(n*2.2046).toFixed(2)}lbs | ${n}lbs = ${(n/2.2046).toFixed(2)}kg`}},
        {cat:'convert',icon:'fa-ruler',name:'cm ⇄ inch',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter number':`${n}cm = ${(n/2.54).toFixed(2)}in | ${n}in = ${(n*2.54).toFixed(2)}cm`}},
        {cat:'convert',icon:'fa-temperature-high',name:'°C ⇄ °F',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter number':`${n}°C = ${(n*9/5+32).toFixed(2)}°F | ${n}°F = ${((n-32)*5/9).toFixed(2)}°C`}},
        {cat:'convert',icon:'fa-temperature-low',name:'°C ⇄ K',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter number':`${n}°C = ${(n+273.15).toFixed(2)}K | ${n}K = ${(n-273.15).toFixed(2)}°C`}},
        {cat:'convert',icon:'fa-gauge-high',name:'km/h ⇄ mph',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter number':`${n}km/h = ${(n/1.609).toFixed(2)}mph | ${n}mph = ${(n*1.609).toFixed(2)}km/h`}},
        {cat:'convert',icon:'fa-clock',name:'Seconds→Time',fn:v=>{let s=parseInt(v);if(isNaN(s))return'Enter seconds';let h=Math.floor(s/3600),m=Math.floor((s%3600)/60);return`${h}h ${m}m ${s%60}s`}},
        {cat:'convert',icon:'fa-coins',name:'USD ⇄ EUR',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter amount':`$${n} = €${(n*0.92).toFixed(2)} | €${n} = $${(n/0.92).toFixed(2)}`}},
        {cat:'convert',icon:'fa-coins',name:'USD ⇄ INR',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter amount':`$${n} = ₹${(n*83).toFixed(2)} | ₹${n} = $${(n/83).toFixed(2)}`}},
        {cat:'convert',icon:'fa-coins',name:'USD ⇄ PKR',fn:v=>{let n=parseFloat(v);return isNaN(n)?'Enter amount':`$${n} = Rs ${(n*278).toFixed(2)} | Rs ${n} = $${(n/278).toFixed(2)}`}},
        {cat:'generator',icon:'fa-calendar',name:'Age Calculator',fn:b=>{let a=new Date(b),diff=Date.now()-a;if(isNaN(a))return'YYYY-MM-DD';let y=Math.floor(diff/31557600000);return`${y} years`}},
        {cat:'generator',icon:'fa-palette',name:'Random Color',fn:()=>'#'+Math.floor(Math.random()*16777215).toString(16).padStart(6,'0')},
        {cat:'generator',icon:'fa-dice',name:'Random Number',fn:()=>Math.floor(Math.random()*1000000).toString()},
        {cat:'generator',icon:'fa-font',name:'Lorem Ipsum',fn:()=>'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor.'},
        {cat:'generator',icon:'fa-user',name:'Random Name',fn:()=>{let f=['James','Mary','John','Patricia','Robert','Linda'];let l=['Smith','Johnson','Brown','Jones','Garcia'];return f[Math.floor(Math.random()*f.length)]+' '+l[Math.floor(Math.random()*l.length)]}},
        {cat:'generator',icon:'fa-phone',name:'Fake Phone',fn:()=>`(${Math.floor(Math.random()*900)+100}) ${Math.floor(Math.random()*900)+100}-${Math.floor(Math.random()*9000)+1000}`},
        {cat:'math',icon:'fa-calculator',name:'Basic Calculator',fn:e=>{try{return eval(e)}catch{return'Error'}}},
        {cat:'math',icon:'fa-square-root-variable',name:'Square Root',fn:n=>{let v=parseFloat(n);return isNaN(v)?'Enter number':Math.sqrt(v).toString()}},
        {cat:'math',icon:'fa-percent',name:'Percentage',fn:v=>{let[n,p]=v.split(',');n=parseFloat(n);p=parseFloat(p);return isNaN(n)||isNaN(p)?'Enter: number,percent':`${p}% of ${n} = ${(n*p/100).toFixed(2)}`}},
        {cat:'math',icon:'fa-chart-pie',name:'Circle Area',fn:r=>{let v=parseFloat(r);return isNaN(v)?'Enter radius':(Math.PI*v*v).toFixed(4)}},
        {cat:'math',icon:'fa-cube',name:'Cube Volume',fn:s=>{let v=parseFloat(s);return isNaN(v)?'Enter side':(v*v*v).toFixed(4)}},
        {cat:'math',icon:'fa-arrow-trend-up',name:'Compound Interest',fn:v=>{let[p,r,t]=v.split(',').map(parseFloat);return isNaN(p)?'Principal,Rate,Time':(p*Math.pow(1+r/100,t)).toFixed(2)}}
    ];
    
    async function hash(algo,text){const e=new TextEncoder().encode(text);const h=await crypto.subtle.digest(algo,e);return Array.from(new Uint8Array(h)).map(b=>b.toString(16).padStart(2,'0')).join('')}
    
    let currentCat='all',searchTerm='';
    function renderTools(){
        const grid=document.getElementById('toolGrid');
        let filtered=TOOLS.filter(t=>(currentCat==='all'||t.cat===currentCat)&&(searchTerm===''||t.name.toLowerCase().includes(searchTerm)||t.cat.toLowerCase().includes(searchTerm)));
        grid.innerHTML=filtered.map((t,i)=>{let id='tool_'+i;setTimeout(()=>renderToolCard(id,t),10);return `<div class="tool-card" id="${id}"><div class="card-header"><i class="fas ${t.icon}"></i><h3>${t.name}</h3></div><div class="tool-content" id="content_${id}"></div></div>`}).join('');
        filtered.forEach((t,i)=>renderToolCard('tool_'+i,t));
    }
    
    function renderToolCard(id,tool){
        const cont=document.getElementById('content_'+id);if(!cont)return;
        cont.innerHTML='';
        if(tool.isImg){
            const inp=document.createElement('input');inp.placeholder='Text/URL for QR';cont.appendChild(inp);
            const btn=document.createElement('button');btn.innerHTML='<i class="fas fa-qrcode"></i> Generate';cont.appendChild(btn);
            const out=document.createElement('div');out.className='tool-output';cont.appendChild(out);
            btn.onclick=()=>{out.innerHTML=`<img class="preview-img" src="${tool.fn(inp.value)}">`};
        }else if(tool.fn.length===0){
            const btn=document.createElement('button');btn.innerHTML='<i class="fas fa-sync"></i> Generate';cont.appendChild(btn);
            const out=document.createElement('div');out.className='tool-output';cont.appendChild(out);
            btn.onclick=async()=>{let res=tool.fn();if(res instanceof Promise)res=await res;out.innerText=res};
        }else{
            const inp=document.createElement(tool.name.includes('JSON')?'textarea':'input');inp.placeholder='Enter value...';cont.appendChild(inp);
            if(tool.name==='Percentage')inp.placeholder='number,percent';
            if(tool.name==='Compound Interest')inp.placeholder='principal,rate,time';
            const btn=document.createElement('button');btn.innerHTML='<i class="fas fa-play"></i> Run';cont.appendChild(btn);
            const out=document.createElement('div');out.className='tool-output';cont.appendChild(out);
            btn.onclick=async()=>{let res=tool.fn(inp.value);if(res instanceof Promise)res=await res;out.innerText=res};
        }
    }
    
    document.querySelectorAll('.cat-chip').forEach(c=>c.addEventListener('click',function(){
        document.querySelectorAll('.cat-chip').forEach(cc=>cc.classList.remove('active'));
        this.classList.add('active');currentCat=this.dataset.cat;renderTools();
    }));
    document.getElementById('searchInput').addEventListener('input',e=>{searchTerm=e.target.value.toLowerCase();renderTools()});
    renderTools();
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        elif self.path.startswith('/qr'):
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            data = params.get('data', [''])[0]
            self.send_response(200)
            self.send_header('Content-type', 'image/png')
            self.end_headers()
            if PIL_AVAILABLE:
                img = qrcode.make(data)
                buf = BytesIO()
                img.save(buf, 'PNG')
                self.wfile.write(buf.getvalue())
            else:
                self.wfile.write(b'')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    print(f'🔥 ProToolbox 100+ running on port {PORT}')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
