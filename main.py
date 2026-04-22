# -*- coding: utf-8 -*-
"""
Facebook Premium Toolkit - All-in-One Facebook Tools
Run: python main.py
"""

from flask import Flask, render_template_string, request, jsonify
import re
import requests
from urllib.parse import urlparse, parse_qs
import json

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✨ Facebook Premium Toolkit ✨</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            position: relative;
            overflow-x: hidden;
        }

        /* Animated Background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 30%, rgba(255, 20, 147, 0.15) 0%, transparent 30%),
                radial-gradient(circle at 80% 70%, rgba(0, 255, 255, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 40% 80%, rgba(147, 51, 234, 0.15) 0%, transparent 30%),
                radial-gradient(circle at 90% 10%, rgba(255, 215, 0, 0.12) 0%, transparent 35%);
            pointer-events: none;
            z-index: 0;
            animation: bgPulse 8s ease-in-out infinite alternate;
        }

        @keyframes bgPulse {
            0% { opacity: 0.7; transform: scale(1); }
            100% { opacity: 1; transform: scale(1.05); }
        }

        /* Floating Particles */
        .particle {
            position: fixed;
            width: 4px;
            height: 4px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            pointer-events: none;
            z-index: 0;
            animation: float 20s linear infinite;
        }

        @keyframes float {
            0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
            10% { opacity: 1; }
            90% { opacity: 1; }
            100% { transform: translateY(-100vh) rotate(720deg); opacity: 0; }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 20px;
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 60px;
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.3),
                0 0 80px rgba(0, 255, 255, 0.1),
                inset 0 0 30px rgba(255, 255, 255, 0.05);
            animation: headerGlow 3s ease-in-out infinite alternate;
        }

        @keyframes headerGlow {
            0% { box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 80px rgba(0, 255, 255, 0.1); }
            100% { box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 120px rgba(255, 20, 147, 0.2); }
        }

        .header h1 {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00ffff 0%, #ff69b4 25%, #a855f7 50%, #00ffff 75%, #ff69b4 100%);
            background-size: 200% 200%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 5s ease infinite;
            letter-spacing: 2px;
            text-shadow: 0 0 40px rgba(0, 255, 255, 0.5);
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .header p {
            color: rgba(255, 255, 255, 0.8);
            font-size: 1.2rem;
            margin-top: 10px;
            font-weight: 400;
            letter-spacing: 1px;
        }

        .fb-icon {
            font-size: 3rem;
            color: #1877f2;
            filter: drop-shadow(0 0 20px #1877f2);
            margin-bottom: 10px;
        }

        /* Tools Grid */
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }

        .tool-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 30px;
            padding: 30px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
        }

        .tool-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s ease;
        }

        .tool-card:hover::before {
            left: 100%;
        }

        .tool-card:hover {
            transform: translateY(-10px) scale(1.02);
            border-color: rgba(0, 255, 255, 0.5);
            box-shadow: 
                0 20px 60px rgba(0, 0, 0, 0.4),
                0 0 40px rgba(0, 255, 255, 0.3),
                inset 0 0 20px rgba(0, 255, 255, 0.1);
        }

        .tool-icon {
            width: 70px;
            height: 70px;
            background: linear-gradient(135deg, #00ffff 0%, #ff69b4 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 20px;
            font-size: 2rem;
            color: white;
            box-shadow: 0 10px 30px rgba(0, 255, 255, 0.4);
            transition: all 0.3s ease;
        }

        .tool-card:hover .tool-icon {
            transform: rotate(5deg) scale(1.1);
            box-shadow: 0 15px 40px rgba(255, 105, 180, 0.5);
        }

        .tool-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: white;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .tool-title i {
            color: #00ffff;
            font-size: 1.2rem;
        }

        .tool-description {
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 20px;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }

        .tool-input {
            flex: 1;
            padding: 15px 20px;
            background: rgba(0, 0, 0, 0.3);
            border: 1.5px solid rgba(255, 255, 255, 0.15);
            border-radius: 20px;
            color: white;
            font-size: 0.95rem;
            outline: none;
            transition: all 0.3s ease;
            font-family: 'Plus Jakarta Sans', sans-serif;
        }

        .tool-input:focus {
            border-color: #00ffff;
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
            background: rgba(0, 0, 0, 0.5);
        }

        .tool-input::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .btn {
            padding: 15px 25px;
            background: linear-gradient(135deg, #00ffff 0%, #ff69b4 100%);
            border: none;
            border-radius: 20px;
            color: white;
            font-weight: 600;
            font-size: 0.95rem;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 5px 20px rgba(0, 255, 255, 0.3);
            font-family: 'Plus Jakarta Sans', sans-serif;
            letter-spacing: 0.5px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(255, 105, 180, 0.4);
            background: linear-gradient(135deg, #ff69b4 0%, #00ffff 100%);
        }

        .btn:active {
            transform: translateY(0);
        }

        .result-box {
            margin-top: 20px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            min-height: 60px;
            color: white;
            word-break: break-all;
            display: none;
            animation: fadeIn 0.5s ease;
            backdrop-filter: blur(10px);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .result-box.show {
            display: block;
        }

        .uid-display {
            font-size: 2rem;
            font-weight: 700;
            color: #00ffff;
            text-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
            letter-spacing: 1px;
        }

        .copy-btn {
            margin-top: 10px;
            padding: 10px 20px;
            background: rgba(0, 255, 255, 0.2);
            border: 1px solid #00ffff;
            border-radius: 15px;
            color: #00ffff;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .copy-btn:hover {
            background: #00ffff;
            color: #0f0c29;
        }

        .dp-preview {
            margin-top: 20px;
            text-align: center;
        }

        .dp-preview img {
            max-width: 200px;
            max-height: 200px;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 255, 255, 0.3);
            border: 3px solid rgba(255, 255, 255, 0.2);
            animation: imgGlow 2s ease-in-out infinite alternate;
        }

        @keyframes imgGlow {
            0% { box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(0, 255, 255, 0.3); }
            100% { box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 50px rgba(255, 105, 180, 0.4); }
        }

        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: 600;
            margin-top: 10px;
        }

        .status-valid {
            background: linear-gradient(135deg, #00ff88, #00b4d8);
            color: white;
            box-shadow: 0 0 20px rgba(0, 255, 136, 0.5);
        }

        .status-invalid {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
            box-shadow: 0 0 20px rgba(255, 65, 108, 0.5);
        }

        .status-unknown {
            background: linear-gradient(135deg, #f39c12, #e67e22);
            color: white;
        }

        .tool-tabs {
            display: flex;
            gap: 5px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .tab-btn {
            padding: 10px 18px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            color: rgba(255, 255, 255, 0.7);
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.85rem;
        }

        .tab-btn.active {
            background: linear-gradient(135deg, #00ffff, #ff69b4);
            color: white;
            border-color: transparent;
            box-shadow: 0 5px 20px rgba(0, 255, 255, 0.3);
        }

        .footer {
            text-align: center;
            padding: 30px;
            color: rgba(255, 255, 255, 0.5);
            margin-top: 40px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #00ffff;
            animation: spin 1s ease-in-out infinite;
            margin-left: 10px;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2.5rem;
            }
            
            .tools-grid {
                grid-template-columns: 1fr;
            }
            
            .tool-card {
                padding: 20px;
            }
            
            .input-group {
                flex-direction: column;
            }
        }

        /* Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #00ffff, #ff69b4);
            border-radius: 10px;
        }

        .quick-tools {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-top: 15px;
        }

        .quick-tool {
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 15px;
            text-align: center;
            color: white;
            cursor: pointer;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .quick-tool:hover {
            background: rgba(0, 255, 255, 0.1);
            border-color: #00ffff;
            transform: scale(1.05);
        }

        .quick-tool i {
            font-size: 1.5rem;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #00ffff, #ff69b4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
    </style>
</head>
<body>
    <!-- Animated Particles -->
    <script>
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.left = Math.random() * 100 + '%';
            particle.style.animationDelay = Math.random() * 20 + 's';
            particle.style.animationDuration = (15 + Math.random() * 10) + 's';
            particle.style.width = (2 + Math.random() * 4) + 'px';
            particle.style.height = particle.style.width;
            document.body.appendChild(particle);
        }
    </script>

    <div class="container">
        <!-- Header -->
        <div class="header">
            <div class="fb-icon">
                <i class="fab fa-facebook"></i>
            </div>
            <h1>✨ Facebook Premium Toolkit ✨</h1>
            <p>Professional Facebook Tools • Profile Analyzer • DP Downloader • Token Checker</p>
        </div>

        <!-- Tools Grid -->
        <div class="tools-grid">
            <!-- Tool 1: Profile Link to UID Converter -->
            <div class="tool-card">
                <div class="tool-icon">
                    <i class="fas fa-link"></i>
                </div>
                <div class="tool-title">
                    <i class="fas fa-id-card"></i> Link → UID
                </div>
                <div class="tool-description">
                    Convert any Facebook profile URL to numeric User ID instantly.
                </div>
                <div class="input-group">
                    <input type="text" class="tool-input" id="profileUrl" placeholder="https://facebook.com/username" value="">
                </div>
                <button class="btn" onclick="convertToUid()">
                    <i class="fas fa-magic"></i> Convert to UID
                </button>
                <div class="result-box" id="uidResult">
                    <div class="uid-display" id="uidValue">—</div>
                    <button class="copy-btn" onclick="copyText('uidValue')">
                        <i class="far fa-copy"></i> Copy UID
                    </button>
                </div>
            </div>

            <!-- Tool 2: Facebook Token Checker -->
            <div class="tool-card">
                <div class="tool-icon">
                    <i class="fas fa-key"></i>
                </div>
                <div class="tool-title">
                    <i class="fas fa-shield-alt"></i> Token Checker
                </div>
                <div class="tool-description">
                    Validate Facebook Access Token and get account info.
                </div>
                <div class="input-group">
                    <input type="text" class="tool-input" id="accessToken" placeholder="EAA..." value="">
                </div>
                <button class="btn" onclick="checkToken()">
                    <i class="fas fa-check-circle"></i> Check Token
                </button>
                <div class="result-box" id="tokenResult">
                    <div id="tokenInfo"></div>
                </div>
            </div>

            <!-- Tool 3: Facebook DP Downloader -->
            <div class="tool-card">
                <div class="tool-icon">
                    <i class="fas fa-camera"></i>
                </div>
                <div class="tool-title">
                    <i class="fas fa-download"></i> DP Downloader
                </div>
                <div class="tool-description">
                    Download high-quality Facebook profile picture.
                </div>
                <div class="tool-tabs">
                    <button class="tab-btn active" onclick="switchDpMode('uid')">By UID</button>
                    <button class="tab-btn" onclick="switchDpMode('url')">By Profile URL</button>
                </div>
                <div class="input-group" id="dpUidInput">
                    <input type="text" class="tool-input" id="dpUid" placeholder="Enter Facebook UID" value="">
                </div>
                <div class="input-group" id="dpUrlInput" style="display: none;">
                    <input type="text" class="tool-input" id="dpUrl" placeholder="https://facebook.com/username" value="">
                </div>
                <button class="btn" onclick="downloadDp()">
                    <i class="fas fa-image"></i> Get Profile Picture
                </button>
                <div class="result-box" id="dpResult">
                    <div class="dp-preview" id="dpPreview"></div>
                </div>
            </div>
        </div>

        <!-- Second Row - Additional Tools -->
        <div class="tools-grid">
            <!-- Tool 4: Profile Info -->
            <div class="tool-card">
                <div class="tool-icon">
                    <i class="fas fa-user-circle"></i>
                </div>
                <div class="tool-title">
                    <i class="fas fa-info-circle"></i> Profile Info
                </div>
                <div class="tool-description">
                    Get basic profile information using UID or profile URL.
                </div>
                <div class="input-group">
                    <input type="text" class="tool-input" id="profileInfoInput" placeholder="Enter UID or Profile URL">
                </div>
                <button class="btn" onclick="getProfileInfo()">
                    <i class="fas fa-search"></i> Get Info
                </button>
                <div class="result-box" id="profileInfoResult">
                    <div id="profileInfoContent"></div>
                </div>
            </div>

            <!-- Tool 5: Quick Tools & Utilities -->
            <div class="tool-card">
                <div class="tool-icon">
                    <i class="fas fa-toolbox"></i>
                </div>
                <div class="tool-title">
                    <i class="fas fa-bolt"></i> Quick Tools
                </div>
                <div class="tool-description">
                    Useful utilities for Facebook developers and users.
                </div>
                <div class="quick-tools">
                    <div class="quick-tool" onclick="generateTimestamp()">
                        <i class="far fa-clock"></i>
                        <div>Timestamp</div>
                    </div>
                    <div class="quick-tool" onclick="generateRandomUid()">
                        <i class="fas fa-random"></i>
                        <div>Random UID</div>
                    </div>
                    <div class="quick-tool" onclick="urlEncoder()">
                        <i class="fas fa-code"></i>
                        <div>URL Encode</div>
                    </div>
                    <div class="quick-tool" onclick="urlDecoder()">
                        <i class="fas fa-unlock"></i>
                        <div>URL Decode</div>
                    </div>
                    <div class="quick-tool" onclick="base64Encode()">
                        <i class="fas fa-lock"></i>
                        <div>Base64 Encode</div>
                    </div>
                    <div class="quick-tool" onclick="base64Decode()">
                        <i class="fas fa-lock-open"></i>
                        <div>Base64 Decode</div>
                    </div>
                </div>
                <div class="result-box" id="quickToolResult">
                    <div id="quickToolContent"></div>
                </div>
            </div>

            <!-- Tool 6: Graph API Explorer -->
            <div class="tool-card">
                <div class="tool-icon">
                    <i class="fas fa-chart-line"></i>
                </div>
                <div class="tool-title">
                    <i class="fab fa-facebook-messenger"></i> Graph Explorer
                </div>
                <div class="tool-description">
                    Quick access to Facebook Graph API endpoints.
                </div>
                <div class="tool-tabs">
                    <button class="tab-btn active" onclick="setGraphEndpoint('me')">/me</button>
                    <button class="tab-btn" onclick="setGraphEndpoint('friends')">/friends</button>
                    <button class="tab-btn" onclick="setGraphEndpoint('photos')">/photos</button>
                </div>
                <div class="input-group">
                    <input type="text" class="tool-input" id="graphEndpoint" placeholder="me?fields=id,name,email" value="me?fields=id,name">
                </div>
                <button class="btn" onclick="exploreGraph()">
                    <i class="fas fa-rocket"></i> Explore
                </button>
                <div class="result-box" id="graphResult">
                    <div id="graphContent"></div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>⚡ Facebook Premium Toolkit v2.0 • Made with <i class="fas fa-heart" style="color: #ff69b4;"></i> for Facebook Power Users</p>
            <p style="margin-top: 10px; font-size: 0.85rem;">
                <i class="fas fa-shield"></i> Secure • <i class="fas fa-bolt"></i> Fast • <i class="fas fa-star" style="color: gold;"></i> Premium
            </p>
        </div>
    </div>

    <script>
        let currentDpMode = 'uid';
        let currentInput = '';

        function switchDpMode(mode) {
            currentDpMode = mode;
            document.getElementById('dpUidInput').style.display = mode === 'uid' ? 'block' : 'none';
            document.getElementById('dpUrlInput').style.display = mode === 'url' ? 'block' : 'none';
            
            // Update active tab
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }

        function setGraphEndpoint(endpoint) {
            const endpoints = {
                'me': 'me?fields=id,name,email,picture',
                'friends': 'me/friends?fields=id,name',
                'photos': 'me/photos?fields=id,name,images,created_time&limit=10'
            };
            document.getElementById('graphEndpoint').value = endpoints[endpoint] || endpoint;
            
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }

        async function convertToUid() {
            const url = document.getElementById('profileUrl').value;
            const resultBox = document.getElementById('uidResult');
            const uidValue = document.getElementById('uidValue');
            
            if (!url) {
                alert('Please enter a Facebook profile URL');
                return;
            }
            
            resultBox.classList.add('show');
            uidValue.innerHTML = '<span class="loading-spinner"></span>';
            
            try {
                const response = await fetch('/api/convert_uid', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    uidValue.textContent = data.uid;
                    uidValue.style.color = '#00ffff';
                } else {
                    uidValue.textContent = data.error || 'Conversion failed';
                    uidValue.style.color = '#ff416c';
                }
            } catch (error) {
                uidValue.textContent = 'Error: ' + error.message;
                uidValue.style.color = '#ff416c';
            }
        }

        async function checkToken() {
            const token = document.getElementById('accessToken').value;
            const resultBox = document.getElementById('tokenResult');
            const tokenInfo = document.getElementById('tokenInfo');
            
            if (!token) {
                alert('Please enter an access token');
                return;
            }
            
            resultBox.classList.add('show');
            tokenInfo.innerHTML = '<span class="loading-spinner"></span> Checking token...';
            
            try {
                const response = await fetch('/api/check_token', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token: token})
                });
                
                const data = await response.json();
                
                if (data.valid) {
                    let html = `<span class="status-badge status-valid"><i class="fas fa-check-circle"></i> Token Valid</span>`;
                    html += `<div style="margin-top: 15px;">`;
                    html += `<p><strong>User ID:</strong> ${data.user_id}</p>`;
                    html += `<p><strong>Name:</strong> ${data.name}</p>`;
                    if (data.expires_in) html += `<p><strong>Expires:</strong> ${data.expires_in} seconds</p>`;
                    html += `</div>`;
                    tokenInfo.innerHTML = html;
                } else {
                    tokenInfo.innerHTML = `<span class="status-badge status-invalid"><i class="fas fa-times-circle"></i> Token Invalid</span>`;
                }
            } catch (error) {
                tokenInfo.innerHTML = `<span class="status-badge status-unknown">Error checking token</span>`;
            }
        }

        async function downloadDp() {
            let input = '';
            if (currentDpMode === 'uid') {
                input = document.getElementById('dpUid').value;
            } else {
                input = document.getElementById('dpUrl').value;
            }
            
            const resultBox = document.getElementById('dpResult');
            const dpPreview = document.getElementById('dpPreview');
            
            if (!input) {
                alert('Please enter a UID or profile URL');
                return;
            }
            
            resultBox.classList.add('show');
            dpPreview.innerHTML = '<span class="loading-spinner"></span> Fetching profile picture...';
            
            try {
                const response = await fetch('/api/get_dp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input: input, mode: currentDpMode})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    dpPreview.innerHTML = `
                        <img src="${data.image_url}" alt="Profile Picture" onerror="this.onerror=null; this.src='https://via.placeholder.com/200?text=No+Image';">
                        <br><br>
                        <a href="${data.image_url}" target="_blank" class="copy-btn" style="text-decoration: none;">
                            <i class="fas fa-download"></i> Open & Download
                        </a>
                    `;
                } else {
                    dpPreview.innerHTML = `<p style="color: #ff416c;">${data.error || 'Failed to fetch image'}</p>`;
                }
            } catch (error) {
                dpPreview.innerHTML = `<p style="color: #ff416c;">Error: ${error.message}</p>`;
            }
        }

        async function getProfileInfo() {
            const input = document.getElementById('profileInfoInput').value;
            const resultBox = document.getElementById('profileInfoResult');
            const content = document.getElementById('profileInfoContent');
            
            if (!input) {
                alert('Please enter a UID or profile URL');
                return;
            }
            
            resultBox.classList.add('show');
            content.innerHTML = '<span class="loading-spinner"></span> Fetching info...';
            
            try {
                const response = await fetch('/api/profile_info', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({input: input})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    content.innerHTML = `
                        <p><i class="fas fa-id-badge" style="color: #00ffff;"></i> <strong>UID:</strong> ${data.uid}</p>
                        <p><i class="fas fa-link" style="color: #ff69b4;"></i> <strong>Profile:</strong> <a href="${data.profile_url}" target="_blank" style="color: #00ffff;">${data.profile_url}</a></p>
                        <p><i class="fas fa-image" style="color: #a855f7;"></i> <strong>Picture:</strong> <a href="${data.picture_url}" target="_blank" style="color: #00ffff;">View</a></p>
                    `;
                } else {
                    content.innerHTML = `<p style="color: #ff416c;">${data.error}</p>`;
                }
            } catch (error) {
                content.innerHTML = `<p style="color: #ff416c;">Error: ${error.message}</p>`;
            }
        }

        async function exploreGraph() {
            const endpoint = document.getElementById('graphEndpoint').value;
            const token = document.getElementById('accessToken').value;
            const resultBox = document.getElementById('graphResult');
            const content = document.getElementById('graphContent');
            
            if (!token) {
                alert('Please enter an access token in the Token Checker first');
                return;
            }
            
            resultBox.classList.add('show');
            content.innerHTML = '<span class="loading-spinner"></span> Fetching data...';
            
            try {
                const response = await fetch('/api/graph_explore', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({endpoint: endpoint, token: token})
                });
                
                const data = await response.json();
                
                if (data.success) {
                    content.innerHTML = `<pre style="color: #00ffff; overflow-x: auto; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 10px;">${JSON.stringify(data.data, null, 2)}</pre>`;
                } else {
                    content.innerHTML = `<p style="color: #ff416c;">${data.error}</p>`;
                }
            } catch (error) {
                content.innerHTML = `<p style="color: #ff416c;">Error: ${error.message}</p>`;
            }
        }

        function copyText(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;
            
            navigator.clipboard.writeText(text).then(() => {
                const btn = event.target.closest('.copy-btn');
                const originalHtml = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                setTimeout(() => {
                    btn.innerHTML = originalHtml;
                }, 2000);
            });
        }
        
        // Quick Tools Functions
        function generateTimestamp() {
            const resultBox = document.getElementById('quickToolResult');
            const content = document.getElementById('quickToolContent');
            const timestamp = Math.floor(Date.now() / 1000);
            
            resultBox.classList.add('show');
            content.innerHTML = `
                <p><strong>Unix Timestamp:</strong> ${timestamp}</p>
                <p><strong>Date:</strong> ${new Date().toLocaleString()}</p>
                <button class="copy-btn" onclick="navigator.clipboard.writeText('${timestamp}')"><i class="far fa-copy"></i> Copy</button>
            `;
        }

        function generateRandomUid() {
            const resultBox = document.getElementById('quickToolResult');
            const content = document.getElementById('quickToolContent');
            const uid = '1000' + Math.floor(Math.random() * 9000000000000000);
            
            resultBox.classList.add('show');
            content.innerHTML = `
                <p><strong>Random UID:</strong> ${uid}</p>
                <button class="copy-btn" onclick="navigator.clipboard.writeText('${uid}')"><i class="far fa-copy"></i> Copy</button>
            `;
        }

        function urlEncoder() {
            const text = prompt('Enter text to URL encode:');
            if (text) {
                const resultBox = document.getElementById('quickToolResult');
                const content = document.getElementById('quickToolContent');
                const encoded = encodeURIComponent(text);
                
                resultBox.classList.add('show');
                content.innerHTML = `
                    <p><strong>Original:</strong> ${text}</p>
                    <p><strong>Encoded:</strong> ${encoded}</p>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText('${encoded}')"><i class="far fa-copy"></i> Copy</button>
                `;
            }
        }

        function urlDecoder() {
            const text = prompt('Enter URL encoded text to decode:');
            if (text) {
                try {
                    const resultBox = document.getElementById('quickToolResult');
                    const content = document.getElementById('quickToolContent');
                    const decoded = decodeURIComponent(text);
                    
                    resultBox.classList.add('show');
                    content.innerHTML = `
                        <p><strong>Encoded:</strong> ${text}</p>
                        <p><strong>Decoded:</strong> ${decoded}</p>
                        <button class="copy-btn" onclick="navigator.clipboard.writeText('${decoded}')"><i class="far fa-copy"></i> Copy</button>
                    `;
                } catch (e) {
                    alert('Invalid URL encoded text');
                }
            }
        }

        function base64Encode() {
            const text = prompt('Enter text to Base64 encode:');
            if (text) {
                const resultBox = document.getElementById('quickToolResult');
                const content = document.getElementById('quickToolContent');
                const encoded = btoa(text);
                
                resultBox.classList.add('show');
                content.innerHTML = `
                    <p><strong>Original:</strong> ${text}</p>
                    <p><strong>Base64:</strong> ${encoded}</p>
                    <button class="copy-btn" onclick="navigator.clipboard.writeText('${encoded}')"><i class="far fa-copy"></i> Copy</button>
                `;
            }
        }

        function base64Decode() {
            const text = prompt('Enter Base64 text to decode:');
            if (text) {
                try {
                    const resultBox = document.getElementById('quickToolResult');
                    const content = document.getElementById('quickToolContent');
                    const decoded = atob(text);
                    
                    resultBox.classList.add('show');
                    content.innerHTML = `
                        <p><strong>Base64:</strong> ${text}</p>
                        <p><strong>Decoded:</strong> ${decoded}</p>
                        <button class="copy-btn" onclick="navigator.clipboard.writeText('${decoded}')"><i class="far fa-copy"></i> Copy</button>
                    `;
                } catch (e) {
                    alert('Invalid Base64 text');
                }
            }
        }

        // Initialize default values
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('profileUrl').placeholder = 'https://facebook.com/zuck';
            document.getElementById('accessToken').placeholder = 'EAA... (paste your token here)';
            document.getElementById('dpUid').placeholder = '4 (Mark Zuckerberg)';
        });
    </script>
</body>
</html>
'''

# ==================== API Routes ====================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/convert_uid', methods=['POST'])
def convert_uid():
    data = request.json
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # Extract username from URL
    patterns = [
        r'facebook\.com\/([^\/\?\&]+)',
        r'fb\.com\/([^\/\?\&]+)',
        r'facebook\.com\/profile\.php\?id=(\d+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            username_or_id = match.group(1)
            
            # If it's already a numeric ID
            if username_or_id.isdigit():
                return jsonify({'success': True, 'uid': username_or_id})
            
            # Try to resolve username to UID using Facebook's public endpoint
            try:
                # Use Facebook's graph API public endpoint
                response = requests.get(
                    f'https://graph.facebook.com/v19.0/{username_or_id}',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'id' in data:
                        return jsonify({'success': True, 'uid': data['id']})
            except:
                pass
            
            # Alternative method - try to scrape the profile page
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(f'https://facebook.com/{username_or_id}', headers=headers, timeout=10)
                # Look for user ID in the page source
                id_match = re.search(r'"userID":"(\d+)"', response.text)
                if id_match:
                    return jsonify({'success': True, 'uid': id_match.group(1)})
                
                id_match2 = re.search(r'"owner":\s*{\s*"__typename":\s*"User",\s*"id":\s*"(\d+)"', response.text)
                if id_match2:
                    return jsonify({'success': True, 'uid': id_match2.group(1)})
            except:
                pass
    
    return jsonify({'success': False, 'error': 'Could not extract UID. Make sure the profile exists and is public.'})

@app.route('/api/check_token', methods=['POST'])
def check_token():
    data = request.json
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'valid': False, 'error': 'Token is required'})
    
    try:
        # Check token with Facebook Graph API
        response = requests.get(
            'https://graph.facebook.com/v19.0/me',
            params={
                'access_token': token,
                'fields': 'id,name'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            user_data = response.json()
            return jsonify({
                'valid': True,
                'user_id': user_data.get('id'),
                'name': user_data.get('name')
            })
        else:
            error_data = response.json()
            return jsonify({
                'valid': False,
                'error': error_data.get('error', {}).get('message', 'Invalid token')
            })
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)})

@app.route('/api/get_dp', methods=['POST'])
def get_dp():
    data = request.json
    input_value = data.get('input', '').strip()
    mode = data.get('mode', 'uid')
    
    if not input_value:
        return jsonify({'success': False, 'error': 'Input is required'})
    
    uid = input_value
    
    # If mode is URL, extract UID first
    if mode == 'url':
        patterns = [
            r'facebook\.com\/([^\/\?\&]+)',
            r'fb\.com\/([^\/\?\&]+)',
            r'facebook\.com\/profile\.php\?id=(\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, input_value)
            if match:
                uid = match.group(1)
                if not uid.isdigit():
                    try:
                        response = requests.get(f'https://graph.facebook.com/v19.0/{uid}', timeout=5)
                        if response.status_code == 200:
                            uid = response.json().get('id', uid)
                    except:
                        pass
                break
    
    # Generate profile picture URL
    image_url = f'https://graph.facebook.com/v19.0/{uid}/picture?width=720&height=720'
    
    return jsonify({
        'success': True,
        'uid': uid,
        'image_url': image_url
    })

@app.route('/api/profile_info', methods=['POST'])
def profile_info():
    data = request.json
    input_value = data.get('input', '').strip()
    
    if not input_value:
        return jsonify({'success': False, 'error': 'Input is required'})
    
    uid = input_value
    
    # If not numeric, try to extract UID
    if not uid.isdigit():
        patterns = [
            r'facebook\.com\/([^\/\?\&]+)',
            r'fb\.com\/([^\/\?\&]+)',
            r'facebook\.com\/profile\.php\?id=(\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, input_value)
            if match:
                username = match.group(1)
                if not username.isdigit():
                    try:
                        response = requests.get(f'https://graph.facebook.com/v19.0/{username}', timeout=5)
                        if response.status_code == 200:
                            uid = response.json().get('id', username)
                    except:
                        pass
                else:
                    uid = username
                break
    
    return jsonify({
        'success': True,
        'uid': uid,
        'profile_url': f'https://facebook.com/{uid}',
        'picture_url': f'https://graph.facebook.com/v19.0/{uid}/picture?width=720'
    })

@app.route('/api/graph_explore', methods=['POST'])
def graph_explore():
    data = request.json
    endpoint = data.get('endpoint', 'me')
    token = data.get('token', '')
    
    if not token:
        return jsonify({'success': False, 'error': 'Access token is required'})
    
    try:
        # Clean endpoint
        endpoint = endpoint.lstrip('/')
        url = f'https://graph.facebook.com/v19.0/{endpoint}'
        
        # Check if endpoint already has query parameters
        if '?' in url:
            url += f'&access_token={token}'
        else:
            url += f'?access_token={token}'
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'data': response.json()
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('error', {}).get('message', 'Request failed')
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     ✨ Facebook Premium Toolkit - Starting Server ✨      ║
    ║                                                          ║
    ║     🌐 Open your browser and go to:                      ║
    ║        http://127.0.0.1:5000                            ║
    ║        http://localhost:5000                            ║
    ║                                                          ║
    ║     📱 Features:                                         ║
    ║        • Profile Link → UID Converter                    ║
    ║        • Token Checker                                   ║
    ║        • DP Downloader                                   ║
    ║        • Profile Info                                    ║
    ║        • Graph API Explorer                              ║
    ║        • Quick Developer Tools                           ║
    ║                                                          ║
    ║     Press Ctrl+C to stop the server                      ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)
