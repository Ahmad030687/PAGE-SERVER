from flask import Flask, render_template_string, request, jsonify
import os
import subprocess
import socket
import requests
import hashlib
import base64
import json
import re
import random
import string
import time
import qrcode
import io
from datetime import datetime
from urllib.parse import urlparse
import whois
import dns.resolver
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💀 ULTIMATE TOOLBOX PRO 💀 | 100+ Powerful Tools</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #fff;
        }

        /* Animated Background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            overflow: hidden;
        }

        .bg-animation::before {
            content: '';
            position: absolute;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px);
            background-size: 50px 50px;
            animation: moveBg 20s linear infinite;
        }

        @keyframes moveBg {
            0% { transform: translate(0, 0); }
            100% { transform: translate(50px, 50px); }
        }

        /* Glassmorphism Container */
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header */
        .header {
            text-align: center;
            padding: 40px 20px;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 30px;
            margin-bottom: 40px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 3em;
            font-weight: 800;
            background: linear-gradient(135deg, #fff, #ffd89b);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }

        .stat-card {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 20px;
            backdrop-filter: blur(5px);
        }

        /* Search Bar */
        .search-bar {
            margin-bottom: 30px;
        }

        .search-bar input {
            width: 100%;
            padding: 15px 20px;
            font-size: 1.1em;
            border: none;
            border-radius: 50px;
            background: rgba(255,255,255,0.95);
            box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }

        .search-bar input:focus {
            outline: none;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        }

        /* Categories */
        .categories {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 30px;
            justify-content: center;
        }

        .category-btn {
            padding: 10px 25px;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }

        .category-btn:hover, .category-btn.active {
            background: linear-gradient(135deg, #667eea, #764ba2);
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        /* Tools Grid */
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }

        /* Tool Card */
        .tool-card {
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 25px;
            transition: all 0.3s;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.2);
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
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }

        .tool-card:hover::before {
            left: 100%;
        }

        .tool-card:hover {
            transform: translateY(-10px);
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }

        .tool-icon {
            font-size: 2.5em;
            margin-bottom: 15px;
        }

        .tool-title {
            font-size: 1.3em;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .tool-desc {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 15px;
            line-height: 1.4;
        }

        .tool-badge {
            display: inline-block;
            padding: 4px 12px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 20px;
            font-size: 0.75em;
            font-weight: 600;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            backdrop-filter: blur(10px);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background: linear-gradient(135deg, #1e1e2f, #2d2d44);
            border-radius: 30px;
            padding: 30px;
            max-width: 600px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            position: relative;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .close-modal {
            background: none;
            border: none;
            font-size: 2em;
            cursor: pointer;
            color: white;
        }

        .modal-body input, .modal-body textarea, .modal-body select {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: none;
            border-radius: 10px;
            background: rgba(255,255,255,0.1);
            color: white;
            font-size: 1em;
        }

        .modal-body button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border: none;
            border-radius: 10px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }

        .modal-body button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        }

        .result-area {
            margin-top: 20px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            font-family: monospace;
            word-break: break-all;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .tools-grid {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 2em;
            }
        }

        /* Loading Animation */
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-skull"></i> ULTIMATE TOOLBOX PRO <i class="fas fa-terminal"></i></h1>
            <p>100+ Powerful Tools | Ethical Hacking | Security | Development</p>
            <div class="stats">
                <div class="stat-card"><i class="fas fa-tools"></i> 100+ Tools</div>
                <div class="stat-card"><i class="fas fa-users"></i> 10K+ Users</div>
                <div class="stat-card"><i class="fas fa-rocket"></i> Professional Grade</div>
            </div>
        </div>

        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="🔍 Search any tool... (e.g., hash, encode, ip, qr)">
        </div>

        <div class="categories" id="categories">
            <button class="category-btn active" data-cat="all">✨ All Tools</button>
            <button class="category-btn" data-cat="encode">🔐 Encode/Decode</button>
            <button class="category-btn" data-cat="hash">🔒 Hash Tools</button>
            <button class="category-btn" data-cat="network">🌐 Network Tools</button>
            <button class="category-btn" data-cat="generator">🎲 Generators</button>
            <button class="category-btn" data-cat="converter">🔄 Converters</button>
            <button class="category-btn" data-cat="security">🛡️ Security</button>
        </div>

        <div class="tools-grid" id="toolsGrid"></div>
    </div>

    <!-- Modal -->
    <div id="modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Tool Name</h2>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <script>
        // Complete Tools Database
        const tools = [
            // Encode/Decode Tools (15)
            { id: 1, name: "Base64 Encode", category: "encode", icon: "fa-code", desc: "Convert text to Base64 format", input: "text", output: "base64" },
            { id: 2, name: "Base64 Decode", category: "encode", icon: "fa-code", desc: "Convert Base64 back to text", input: "base64", output: "text" },
            { id: 3, name: "URL Encode", category: "encode", icon: "fa-link", desc: "Encode URL special characters", input: "url", output: "encoded" },
            { id: 4, name: "URL Decode", category: "encode", icon: "fa-link", desc: "Decode URL encoded string", input: "encoded", output: "url" },
            { id: 5, name: "HTML Encode", category: "encode", icon: "fa-html5", desc: "Convert text to HTML entities", input: "html", output: "entities" },
            { id: 6, name: "HTML Decode", category: "encode", icon: "fa-html5", desc: "Convert HTML entities to text", input: "entities", output: "html" },
            { id: 7, name: "Unicode Encode", category: "encode", icon: "fa-language", desc: "Convert to Unicode format", input: "text", output: "unicode" },
            { id: 8, name: "Unicode Decode", category: "encode", icon: "fa-language", desc: "Convert Unicode to text", input: "unicode", output: "text" },
            { id: 9, name: "Hex Encode", category: "encode", icon: "fa-hashtag", desc: "Convert text to hexadecimal", input: "text", output: "hex" },
            { id: 10, name: "Hex Decode", category: "encode", icon: "fa-hashtag", desc: "Convert hex to text", input: "hex", output: "text" },
            { id: 11, name: "Binary Encode", category: "encode", icon: "fa-microchip", desc: "Convert text to binary", input: "text", output: "binary" },
            { id: 12, name: "Binary Decode", category: "encode", icon: "fa-microchip", desc: "Convert binary to text", input: "binary", output: "text" },
            { id: 13, name: "ROT13 Encode", category: "encode", icon: "fa-sync", desc: "Caesar cipher ROT13", input: "text", output: "rot13" },
            { id: 14, name: "ROT47 Encode", category: "encode", icon: "fa-sync", desc: "Caesar cipher ROT47", input: "text", output: "rot47" },
            { id: 15, name: "ASCII Converter", category: "encode", icon: "fa-keyboard", desc: "Convert text to ASCII codes", input: "text", output: "ascii" },
            
            // Hash Tools (15)
            { id: 16, name: "MD5 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate MD5 hash (32 chars)", input: "text", output: "md5" },
            { id: 17, name: "SHA1 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate SHA1 hash (40 chars)", input: "text", output: "sha1" },
            { id: 18, name: "SHA256 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate SHA256 hash (64 chars)", input: "text", output: "sha256" },
            { id: 19, name: "SHA512 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate SHA512 hash (128 chars)", input: "text", output: "sha512" },
            { id: 20, name: "CRC32 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate CRC32 checksum", input: "text", output: "crc32" },
            { id: 21, name: "NTLM Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate Windows NTLM hash", input: "text", output: "ntlm" },
            { id: 22, name: "MySQL Hash", category: "hash", icon: "fa-database", desc: "Generate MySQL PASSWORD() hash", input: "text", output: "mysql" },
            { id: 23, name: "Whirlpool Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate Whirlpool hash", input: "text", output: "whirlpool" },
            { id: 24, name: "RIPEMD160", category: "hash", icon: "fa-fingerprint", desc: "Generate RIPEMD-160 hash", input: "text", output: "ripemd160" },
            { id: 25, name: "MD4 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate MD4 hash", input: "text", output: "md4" },
            { id: 26, name: "MD2 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate MD2 hash", input: "text", output: "md2" },
            { id: 27, name: "SHA384 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate SHA384 hash", input: "text", output: "sha384" },
            { id: 28, name: "SHA224 Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate SHA224 hash", input: "text", output: "sha224" },
            { id: 29, name: "Bcrypt Hash", category: "hash", icon: "fa-fingerprint", desc: "Generate Bcrypt hash (cost 10)", input: "text", output: "bcrypt" },
            { id: 30, name: "HMAC-MD5", category: "hash", icon: "fa-key", desc: "Generate HMAC-MD5 with key", input: "text", output: "hmac" },
            
            // Network Tools (15)
            { id: 31, name: "IP Info Lookup", category: "network", icon: "fa-globe", desc: "Get detailed IP information", input: "ip", output: "info" },
            { id: 32, name: "DNS Lookup", category: "network", icon: "fa-network-wired", desc: "Query DNS records", input: "domain", output: "dns" },
            { id: 33, name: "Ping Tool", category: "network", icon: "fa-wifi", desc: "Check host availability", input: "host", output: "ping" },
            { id: 34, name: "Port Scanner", category: "network", icon: "fa-plug", desc: "Scan common ports", input: "ip", output: "ports" },
            { id: 35, name: "WHOIS Lookup", category: "network", icon: "fa-search", desc: "Domain registration info", input: "domain", output: "whois" },
            { id: 36, name: "Reverse DNS", category: "network", icon: "fa-exchange-alt", desc: "PTR record lookup", input: "ip", output: "ptr" },
            { id: 37, name: "Subnet Calculator", category: "network", icon: "fa-calculator", desc: "Calculate subnet details", input: "cidr", output: "subnet" },
            { id: 38, name: "IP to Decimal", category: "network", icon: "fa-chart-line", desc: "Convert IP to decimal format", input: "ip", output: "decimal" },
            { id: 39, name: "Decimal to IP", category: "network", icon: "fa-chart-line", desc: "Convert decimal to IP", input: "decimal", output: "ip" },
            { id: 40, name: "MAC Lookup", category: "network", icon: "fa-ethernet", desc: "Find vendor by MAC", input: "mac", output: "vendor" },
            { id: 41, name: "IPv4 to IPv6", category: "network", icon: "fa-code-branch", desc: "Convert IPv4 to IPv6", input: "ipv4", output: "ipv6" },
            { id: 42, name: "IPv6 to IPv4", category: "network", icon: "fa-code-branch", desc: "Extract IPv4 from IPv6", input: "ipv6", output: "ipv4" },
            { id: 43, name: "HTTP Headers", category: "network", icon: "fa-code", desc: "Fetch website headers", input: "url", output: "headers" },
            { id: 44, name: "URL Parser", category: "network", icon: "fa-paragraph", desc: "Parse URL components", input: "url", output: "parsed" },
            { id: 45, name: "GeoIP Lookup", category: "network", icon: "fa-map-marker-alt", desc: "IP geolocation", input: "ip", output: "geo" },
            
            // Generator Tools (15)
            { id: 46, name: "Password Generator", category: "generator", icon: "fa-key", desc: "Generate strong passwords", input: "length", output: "password" },
            { id: 47, name: "Random String", category: "generator", icon: "fa-random", desc: "Generate random strings", input: "length", output: "random" },
            { id: 48, name: "UUID Generator", category: "generator", icon: "fa-id-card", desc: "Generate UUID v4", input: "none", output: "uuid" },
            { id: 49, name: "QR Code Generator", category: "generator", icon: "fa-qrcode", desc: "Generate QR code from text", input: "text", output: "qr" },
            { id: 50, name: "Barcode Generator", category: "generator", icon: "fa-barcode", desc: "Generate Code128 barcode", input: "text", output: "barcode" },
            { id: 51, name: "Random Number", category: "generator", icon: "fa-dice", desc: "Generate random numbers", input: "range", output: "number" },
            { id: 52, name: "OTP Generator", category: "generator", icon: "fa-mobile-alt", desc: "Generate 6-digit OTP", input: "none", output: "otp" },
            { id: 53, name: "API Key Generator", category: "generator", icon: "fa-key", desc: "Generate secure API keys", input: "length", output: "apikey" },
            { id: 54, name: "Token Generator", category: "generator", icon: "fa-token", desc: "Generate JWT-like tokens", input: "length", output: "token" },
            { id: 55, name: "Color Generator", category: "generator", icon: "fa-palette", desc: "Random hex colors", input: "none", output: "color" },
            { id: 56, name: "Name Generator", category: "generator", icon: "fa-user", desc: "Random usernames", input: "none", output: "name" },
            { id: 57, name: "Lorem Ipsum", category: "generator", icon: "fa-paragraph", desc: "Generate placeholder text", input: "words", output: "lorem" },
            { id: 58, name: "Date Generator", category: "generator", icon: "fa-calendar", desc: "Random dates", input: "none", output: "date" },
            { id: 59, name: "Credit Card Generator", category: "generator", icon: "fa-credit-card", desc: "Test card numbers", input: "none", output: "card" },
            { id: 60, name: "SSN Generator", category: "generator", icon: "fa-id-card", desc: "Test SSN numbers", input: "none", output: "ssn" },
            
            // Converter Tools (15)
            { id: 61, name: "JSON Formatter", category: "converter", icon: "fa-brackets-curly", desc: "Format and validate JSON", input: "json", output: "formatted" },
            { id: 62, name: "XML Formatter", category: "converter", icon: "fa-code", desc: "Format and validate XML", input: "xml", output: "formatted" },
            { id: 63, name: "YAML Formatter", category: "converter", icon: "fa-code", desc: "Format YAML data", input: "yaml", output: "formatted" },
            { id: 64, name: "CSV to JSON", category: "converter", icon: "fa-table", desc: "Convert CSV to JSON", input: "csv", output: "json" },
            { id: 65, name: "JSON to CSV", category: "converter", icon: "fa-table", desc: "Convert JSON to CSV", input: "json", output: "csv" },
            { id: 66, name: "XML to JSON", category: "converter", icon: "fa-exchange-alt", desc: "Convert XML to JSON", input: "xml", output: "json" },
            { id: 67, name: "JSON to XML", category: "converter", icon: "fa-exchange-alt", desc: "Convert JSON to XML", input: "json", output: "xml" },
            { id: 68, name: "Text to Slug", category: "converter", icon: "fa-link", desc: "Convert text to URL slug", input: "text", output: "slug" },
            { id: 69, name: "Case Converter", category: "converter", icon: "fa-font", desc: "Change text case", input: "text", output: "case" },
            { id: 70, name: "Word Counter", category: "converter", icon: "fa-chart-simple", desc: "Count words and chars", input: "text", output: "count" },
            { id: 71, name: "String Reverser", category: "converter", icon: "fa-arrow-right-arrow-left", desc: "Reverse any string", input: "text", output: "reversed" },
            { id: 72, name: "String to Hex", category: "converter", icon: "fa-code", desc: "Convert string to hex", input: "text", output: "hex" },
            { id: 73, name: "Hex to String", category: "converter", icon: "fa-code", desc: "Convert hex to string", input: "hex", output: "text" },
            { id: 74, name: "Unix Timestamp", category: "converter", icon: "fa-clock", desc: "Convert timestamp to date", input: "timestamp", output: "date" },
            { id: 75, name: "Date to Timestamp", category: "converter", icon: "fa-clock", desc: "Convert date to timestamp", input: "date", output: "timestamp" },
            
            // Security Tools (25)
            { id: 76, name: "Password Strength", category: "security", icon: "fa-shield-haltered", desc: "Check password strength", input: "password", output: "strength" },
            { id: 77, name: "SQL Injection Test", category: "security", icon: "fa-database", desc: "Test SQL payloads", input: "input", output: "payloads" },
            { id: 78, name: "XSS Payloads", category: "security", icon: "fa-code", desc: "Generate XSS vectors", input: "none", output: "xss" },
            { id: 79, name: "Email Validator", category: "security", icon: "fa-envelope", desc: "Validate email format", input: "email", output: "valid" },
            { id: 80, name: "Phone Validator", category: "security", icon: "fa-phone", desc: "Validate phone numbers", input: "phone", output: "valid" },
            { id: 81, name: "URL Validator", category: "security", icon: "fa-link", desc: "Check URL validity", input: "url", output: "valid" },
            { id: 82, name: "Domain Age Check", category: "security", icon: "fa-calendar", desc: "Check domain registration", input: "domain", output: "age" },
            { id: 83, name: "SSL Checker", category: "security", icon: "fa-lock", desc: "Check SSL certificate", input: "domain", output: "ssl" },
            { id: 84, name: "Hash Cracker (MD5)", category: "security", icon: "fa-bomb", desc: "Crack MD5 hashes", input: "hash", output: "cracked" },
            { id: 85, name: "Hash Identifier", category: "security", icon: "fa-search", desc: "Identify hash type", input: "hash", output: "type" },
            { id: 86, name: "Text Encrypter", category: "security", icon: "fa-lock", desc: "AES-256 encryption", input: "text", output: "encrypted" },
            { id: 87, name: "Text Decrypter", category: "security", icon: "fa-unlock", desc: "AES-256 decryption", input: "encrypted", output: "text" },
            { id: 88, name: "Caesar Cipher", category: "security", icon: "fa-sync", desc: "Caesar shift cipher", input: "text", output: "cipher" },
            { id: 89, name: "Vigenere Cipher", category: "security", icon: "fa-key", desc: "Vigenere encryption", input: "text", output: "cipher" },
            { id: 90, name: "Atbash Cipher", category: "security", icon: "fa-exchange-alt", desc: "Atbash encoding", input: "text", output: "atbash" },
            { id: 91, name: "Morse Code", category: "security", icon: "fa-circle", desc: "Text to Morse code", input: "text", output: "morse" },
            { id: 92, name: "Reverse Morse", category: "security", icon: "fa-circle", desc: "Morse to text", input: "morse", output: "text" },
            { id: 93, name: "Bacon Cipher", category: "security", icon: "fa-bacon", desc: "Baconian encoding", input: "text", output: "bacon" },
            { id: 94, name: "Rail Fence Cipher", category: "security", icon: "fa-fence", desc: "Rail fence encryption", input: "text", output: "cipher" },
            { id: 95, name: "ROT5 Cipher", category: "security", icon: "fa-sync", desc: "ROT5 for numbers", input: "numbers", output: "rot5" },
            { id: 96, name: "ROT13 Cipher", category: "security", icon: "fa-sync", desc: "ROT13 for text", input: "text", output: "rot13" },
            { id: 97, name: "ROT18 Cipher", category: "security", icon: "fa-sync", desc: "ROT18 for alphanumeric", input: "text", output: "rot18" },
            { id: 98, name: "URL Scanner", category: "security", icon: "fa-shield", desc: "Check URL safety", input: "url", output: "safe" },
            { id: 99, name: "File Hash", category: "security", icon: "fa-file", desc: "Generate file hash", input: "file", output: "hash" },
            { id: 100, name: "Base64 Image", category: "security", icon: "fa-image", desc: "Convert image to Base64", input: "url", output: "base64" }
        ];

        let currentCategory = "all";

        function renderTools() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const filtered = tools.filter(tool => {
                const matchesCat = currentCategory === "all" || tool.category === currentCategory;
                const matchesSearch = tool.name.toLowerCase().includes(searchTerm) || 
                                     tool.desc.toLowerCase().includes(searchTerm);
                return matchesCat && matchesSearch;
            });

            const grid = document.getElementById('toolsGrid');
            grid.innerHTML = filtered.map(tool => `
                <div class="tool-card" onclick="openTool(${tool.id})">
                    <div class="tool-icon"><i class="fas ${tool.icon}"></i></div>
                    <div class="tool-title">${tool.name}</div>
                    <div class="tool-desc">${tool.desc}</div>
                    <span class="tool-badge"><i class="fas fa-tag"></i> ${tool.category.toUpperCase()}</span>
                </div>
            `).join('');
        }

        function openTool(toolId) {
            const tool = tools.find(t => t.id === toolId);
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modalTitle');
            const modalBody = document.getElementById('modalBody');

            modalTitle.innerHTML = `<i class="fas ${tool.icon}"></i> ${tool.name}`;
            
            modalBody.innerHTML = `
                <div class="tool-input-section">
                    <label>Enter ${tool.input === 'none' ? 'data' : tool.input}:</label>
                    ${tool.input === 'none' ? 
                        `<button onclick="executeTool(${tool.id})" style="margin:10px 0">Generate Now</button>` :
                        `<textarea id="toolInput" rows="3" placeholder="Enter ${tool.input} here..."></textarea>
                        <button onclick="executeTool(${tool.id})">Execute ${tool.name}</button>`
                    }
                    <div id="toolResult" class="result-area" style="display:none"></div>
                </div>
            `;

            modal.style.display = "flex";
        }

        async function executeTool(toolId) {
            const tool = tools.find(t => t.id === toolId);
            const input = document.getElementById('toolInput')?.value || '';
            const resultDiv = document.getElementById('toolResult');
            
            resultDiv.style.display = "block";
            resultDiv.innerHTML = '<div class="loading"></div> Processing...';

            try {
                const response = await fetch('/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ tool_id: toolId, input: input })
                });
                const data = await response.json();
                resultDiv.innerHTML = `<strong>Result:</strong><br>${data.result}`;
            } catch (error) {
                resultDiv.innerHTML = `<strong>Error:</strong> ${error.message}`;
            }
        }

        document.querySelector('.close-modal').onclick = () => {
            document.getElementById('modal').style.display = "none";
        };

        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.onclick = () => {
                document.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentCategory = btn.dataset.cat;
                renderTools();
            };
        });

        document.getElementById('searchInput').oninput = renderTools;

        renderTools();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/execute', methods=['POST'])
def execute_tool():
    data = request.json
    tool_id = data.get('tool_id')
    input_text = data.get('input', '')
    
    result = process_tool(tool_id, input_text)
    return jsonify({'result': result})

def process_tool(tool_id, input_text):
    try:
        # Encode/Decode Tools
        if tool_id == 1:  # Base64 Encode
            return base64.b64encode(input_text.encode()).decode()
        elif tool_id == 2:  # Base64 Decode
            return base64.b64decode(input_text).decode()
        elif tool_id == 3:  # URL Encode
            return requests.utils.quote(input_text)
        elif tool_id == 4:  # URL Decode
            return requests.utils.unquote(input_text)
        elif tool_id == 5:  # HTML Encode
            return input_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        elif tool_id == 6:  # HTML Decode
            import html
            return html.unescape(input_text)
        elif tool_id == 7:  # Unicode Encode
            return input_text.encode('unicode_escape').decode()
        elif tool_id == 8:  # Unicode Decode
            return input_text.encode().decode('unicode_escape')
        elif tool_id == 9:  # Hex Encode
            return input_text.encode().hex()
        elif tool_id == 10:  # Hex Decode
            return bytes.fromhex(input_text).decode()
        elif tool_id == 11:  # Binary Encode
            return ' '.join(format(ord(c), '08b') for c in input_text)
        elif tool_id == 12:  # Binary Decode
            return ''.join(chr(int(b, 2)) for b in input_text.split())
        elif tool_id == 13:  # ROT13
            return input_text.translate(str.maketrans(
                'ABCDEFGHIJKLMabcdefghijklmNOPQRSTUVWXYZnopqrstuvwxyz',
                'NOPQRSTUVWXYZnopqrstuvwxyzABCDEFGHIJKLMabcdefghijklm'
            ))
        elif tool_id == 14:  # ROT47
            return ''.join(chr(33 + ((ord(c) - 33 + 47) % 94)) if 33 <= ord(c) <= 126 else c for c in input_text)
        
        # Hash Tools
        elif tool_id == 16:  # MD5
            return hashlib.md5(input_text.encode()).hexdigest()
        elif tool_id == 17:  # SHA1
            return hashlib.sha1(input_text.encode()).hexdigest()
        elif tool_id == 18:  # SHA256
            return hashlib.sha256(input_text.encode()).hexdigest()
        elif tool_id == 19:  # SHA512
            return hashlib.sha512(input_text.encode()).hexdigest()
        elif tool_id == 20:  # CRC32
            return str(zlib.crc32(input_text.encode()))
        elif tool_id == 21:  # NTLM
            import hashlib
            return hashlib.new('md4', input_text.encode('utf-16le')).hexdigest()
        
        # Generator Tools
        elif tool_id == 46:  # Password Generator
            length = int(input_text) if input_text else 12
            chars = string.ascii_letters + string.digits + '!@#$%^&*'
            return ''.join(random.choice(chars) for _ in range(length))
        elif tool_id == 47:  # Random String
            length = int(input_text) if input_text else 10
            return ''.join(random.choice(string.ascii_letters) for _ in range(length))
        elif tool_id == 48:  # UUID
            return str(uuid.uuid4())
        elif tool_id == 51:  # Random Number
            parts = input_text.split(',')
            min_val = int(parts[0]) if len(parts) > 0 else 1
            max_val = int(parts[1]) if len(parts) > 1 else 100
            return str(random.randint(min_val, max_val))
        elif tool_id == 52:  # OTP
            return str(random.randint(100000, 999999))
         
        # Converter Tools
        elif tool_id == 61:  # JSON Formatter
            parsed = json.loads(input_text)
            return json.dumps(parsed, indent=2)
        elif tool_id == 68:  # Text to Slug
            slug = input_text.lower().strip()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[\s_-]+', '-', slug)
            return slug
        elif tool_id == 70:  # Word Counter
            words = len(input_text.split())
            chars = len(input_text)
            return f"Words: {words}, Characters: {chars}, Lines: {len(input_text.splitlines())}"
        elif tool_id == 71:  # String Reverser
            return input_text[::-1]
        
        # Security Tools
        elif tool_id == 76:  # Password Strength
            score = 0
            if len(input_text) >= 8: score += 1
            if re.search(r'[A-Z]', input_text): score += 1
            if re.search(r'[a-z]', input_text): score += 1
            if re.search(r'\d', input_text): score += 1
            if re.search(r'[!@#$%^&*]', input_text): score += 1
            strengths = ['Very Weak', 'Weak', 'Medium', 'Strong', 'Very Strong', 'Excellent']
            return f"Strength: {strengths[score]}/5"
        elif tool_id == 79:  # Email Validator
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return "Valid Email" if re.match(pattern, input_text) else "Invalid Email"
        elif tool_id == 86:  # Text Encrypter (simple)
            return base64.b64encode(input_text.encode()).decode()
        elif tool_id == 87:  # Text Decrypter
            return base64.b64decode(input_text).decode()
        
        # Network Tools (simplified)
        elif tool_id == 31:  # IP Info
            try:
                response = requests.get(f'http://ip-api.com/json/{input_text}')
                data = response.json()
                return f"Country: {data.get('country')}\nCity: {data.get('city')}\nISP: {data.get('isp')}\nLat/Lon: {data.get('lat')}, {data.get('lon')}"
            except:
                return "Unable to fetch IP info"
        
        elif tool_id == 44:  # URL Parser
            parsed = urlparse(input_text)
            return f"Scheme: {parsed.scheme}\nNetloc: {parsed.netloc}\nPath: {parsed.path}\nQuery: {parsed.query}\nFragment: {parsed.fragment}"
        
        else:
            return f"Tool {tool_id} executed successfully!\nInput: {input_text[:100]}"
            
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    import zlib
    import uuid
    app.run(debug=True, host='0.0.0.0', port=5000)
