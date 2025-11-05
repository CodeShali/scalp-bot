#!/usr/bin/env python3
"""
GitHub Webhook Server for Auto-Deploy
Listens for GitHub push events and automatically pulls + restarts the bot
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import subprocess
import logging
import os
from pathlib import Path

app = Flask(__name__)

# Configuration
REPO_PATH = Path(__file__).parent.absolute()
SECRET_TOKEN = os.environ.get('WEBHOOK_SECRET', 'your-secret-token-here')
SERVICE_NAME = 'scalp-bot'

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(REPO_PATH / 'webhook.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def verify_signature(payload_body, signature_header):
    """Verify that the payload was sent from GitHub by validating SHA256."""
    if not signature_header:
        return False
    
    hash_object = hmac.new(
        SECRET_TOKEN.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    return hmac.compare_digest(expected_signature, signature_header)


def git_pull():
    """Pull latest changes from git."""
    try:
        logger.info("Pulling latest changes from git...")
        result = subprocess.run(
            ['git', 'pull', 'origin', 'main'],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Git pull successful: {result.stdout}")
            return True
        else:
            logger.error(f"Git pull failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error during git pull: {e}")
        return False


def restart_service():
    """Restart the systemd service."""
    try:
        logger.info(f"Restarting {SERVICE_NAME} service...")
        result = subprocess.run(
            ['sudo', 'systemctl', 'restart', SERVICE_NAME],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            logger.info(f"Service {SERVICE_NAME} restarted successfully")
            return True
        else:
            logger.error(f"Service restart failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error restarting service: {e}")
        return False


@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle GitHub webhook POST requests."""
    
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        logger.warning("Invalid signature - webhook rejected")
        return jsonify({'error': 'Invalid signature'}), 403
    
    # Get event type
    event = request.headers.get('X-GitHub-Event', 'ping')
    
    if event == 'ping':
        logger.info("Received ping event from GitHub")
        return jsonify({'message': 'Pong!'}), 200
    
    if event == 'push':
        payload = request.json
        
        # Get commit info
        ref = payload.get('ref', '')
        commits = payload.get('commits', [])
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        
        logger.info(f"Push event received from {pusher}")
        logger.info(f"Ref: {ref}")
        logger.info(f"Commits: {len(commits)}")
        
        # Only deploy on push to main branch
        if ref == 'refs/heads/main':
            logger.info("Push to main branch detected - starting auto-deploy")
            
            # Pull latest changes
            if not git_pull():
                return jsonify({'error': 'Git pull failed'}), 500
            
            # Restart service
            if not restart_service():
                return jsonify({'error': 'Service restart failed'}), 500
            
            logger.info("Auto-deploy completed successfully!")
            return jsonify({
                'message': 'Deploy successful',
                'commits': len(commits),
                'pusher': pusher
            }), 200
        else:
            logger.info(f"Ignoring push to {ref} (not main branch)")
            return jsonify({'message': 'Ignored - not main branch'}), 200
    
    return jsonify({'message': 'Event received'}), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': SERVICE_NAME,
        'repo_path': str(REPO_PATH)
    }), 200


if __name__ == '__main__':
    logger.info("Starting webhook server...")
    logger.info(f"Repo path: {REPO_PATH}")
    logger.info(f"Service name: {SERVICE_NAME}")
    
    # Run on port 5000 (internal, will be proxied by nginx)
    app.run(host='0.0.0.0', port=5000, debug=False)
