import requests
import re
from urllib.parse import parse_qs, urlparse

def parse_cookie_string(cookie_str):
    """Converts a cookie string into a dictionary."""
    cookies = {}
    for item in cookie_str.split(';'):
        item = item.strip()
        if not item:
            continue
        if '=' in item:
            name, value = item.split('=', 1)
            cookies[name.strip()] = value.strip()
    return cookies

def get_fb_dtsg(session):
    """Fetches the fb_dtsg token required for GraphQL requests."""
    # Load Facebook homepage to extract fb_dtsg
    response = session.get('https://mbasic.facebook.com/')
    
    # Method 1: Look for fb_dtsg in the page source
    match = re.search(r'name="fb_dtsg" value="([^"]+)"', response.text)
    if match:
        return match.group(1)
    
    # Method 2: Try the main domain if mbasic fails
    response = session.get('https://www.facebook.com/')
    match = re.search(r'"token":"([^"]+)","async_get_token"', response.text)
    if match:
        return match.group(1)
        
    # Fallback: Look for __dyn and other required tokens
    match = re.search(r'\["DTSGInitData",\[\],{"token":"([^"]+)"', response.text)
    if match:
        return match.group(1)
        
    return None

def extract_token_via_graphql(session, fb_dtsg, app_id="350685531728"):
    """Uses GraphQL to get an access token for a specific app."""
    
    # GraphQL endpoint for OAuth
    oauth_url = "https://www.facebook.com/v11.0/dialog/oauth/read/"
    
    params = {
        "auth_type": "rerequest",
        "scope": "public_profile,email",
        "default_audience": "",
        "access_type": "offline",
        "app_id": app_id,
        "response_type": "token",
        "redirect_uri": "fbconnect://success",
        "display": "touch",
        "e2e": "{}",
        "fb_dtsg": fb_dtsg,
        "from_post": "1",
        "sso": "true"
    }
    
    # Step 1: Initiate OAuth flow
    response = session.get(oauth_url, params=params, allow_redirects=False)
    
    # Step 2: Handle redirect and confirm permissions
    if 'Location' in response.headers:
        redirect_url = response.headers['Location']
        # Extract next parameter
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        
        if 'next' in query_params:
            confirm_url = query_params['next'][0]
            # Make the confirmation request
            response = session.get(confirm_url, allow_redirects=False)
            
            # Step 3: Extract token from redirect
            if 'Location' in response.headers:
                final_url = response.headers['Location']
                # Parse fragment or query for access_token
                fragment = urlparse(final_url).fragment
                if fragment:
                    token_match = re.search(r'access_token=([^&]+)', fragment)
                    if token_match:
                        return token_match.group(1)
    
    return None

def change_token_app(session, old_token, target_app_id):
    """Exchanges a token from one app to another."""
    url = f"https://graph.facebook.com/v11.0/{target_app_id}/activities"
    params = {
        "access_token": old_token,
        "method": "GET",
        "format": "json"
    }
    response = session.get(url, params=params)
    if "error" not in response.text:
        # This call doesn't directly return a token, but validates the session
        # The actual token exchange uses internal flows
        return old_token
    return None

def get_token_from_cookie(cookie_string, target_app_id="350685531728"):
    """Main function to get Facebook token from cookies."""
    session = requests.Session()
    
    # Set cookies
    cookies = parse_cookie_string(cookie_string)
    for name, value in cookies.items():
        session.cookies.set(name, value, domain='.facebook.com')
    
    # Set headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    
    # Step 1: Get fb_dtsg
    fb_dtsg = get_fb_dtsg(session)
    if not fb_dtsg:
        return {"error": "Could not extract fb_dtsg. Cookies may be invalid."}
    
    # Step 2: Extract token using GraphQL
    token = extract_token_via_graphql(session, fb_dtsg, app_id=target_app_id)
    if token:
        return {"access_token": token, "app_id": target_app_id}
    
    # Fallback: Try with different app IDs
    fallback_apps = ["350685531728", "6628568379", "275254692598279"]
    for app_id in fallback_apps:
        if app_id != target_app_id:
            token = extract_token_via_graphql(session, fb_dtsg, app_id=app_id)
            if token:
                return {"access_token": token, "app_id": app_id}
    
    return {"error": "Token extraction failed. Checkpoint or CAPTCHA may be required."}
