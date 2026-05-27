from flask import Blueprint, request, jsonify
import os
import cv2
import numpy as np
import base64
import time
import json
from ..face_recognition.face_detector import FaceAuthenticator
from ..blockchain.eth_manager import EthereumManager
from ..blockchain.zkp_manager import ZKProofManager
from ..fraud_detection.fraud_detector import FraudDetector

security_bp = Blueprint('security', __name__)

# Initialize components
face_auth = FaceAuthenticator()
eth_manager = EthereumManager(
    contract_address=os.environ.get('CONTRACT_ADDRESS'),
    contract_abi_path='../smart_contracts/build/IdentityVerification.json',
    provider_url=os.environ.get('ETHEREUM_PROVIDER_URL')
)
zkp_manager = ZKProofManager()
fraud_detector = FraudDetector()

@security_bp.route('/secure-verify', methods=['POST'])
def secure_verify_identity():
    data = request.json
    
    # Get client info for fraud detection
    client_ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    wallet_address = data['wallet_address']
    
    # Record activity for fraud detection
    fraud_detector.record_activity(wallet_address, {
        'login_time': time.time(),
        'ip_address': client_ip,
        'device': user_agent,
        'activity_type': 'verification'
    })
    
    # Decode base64 image
    image_data = base64.b64decode(data['face_image'])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract face and check liveness
    face = face_auth.detect_face(img)
    if face is None:
        # Record failed attempt
        fraud_detector.record_activity(wallet_address, {
            'failed': True,
            'reason': 'No face detected'
        })
        return jsonify({'success': False, 'error': 'No face detected'})
    
    if not face_auth.check_liveness(face):
        # Record failed attempt - potential spoofing
        fraud_detector.record_activity(wallet_address, {
            'failed': True,
            'reason': 'Liveness check failed'
        })
        return jsonify({'success': False, 'error': 'Liveness check failed'})
    
    # Generate embedding and hash
    embedding = face_auth.generate_face_embedding(face)
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate embedding'})
    
    face_hash = face_auth.face_hash(embedding)
    
    # Verify on blockchain using ZKP
    try:
        # First check if user has a registered identity
        has_identity = eth_manager.has_registered_identity(wallet_address)
        if not has_identity:
            return jsonify({'success': False, 'error': 'No registered identity found'})
        
        # Generate ZKP challenge
        challenge = zkp_manager.generate_challenge(face_hash)
        
        # Generate proof
        proof = zkp_manager.create_proof(embedding, challenge)
        
        # Verify identity using ZKP
        is_verified = eth_manager.verify_identity(wallet_address, face_hash)
        
        # Also verify the ZKP
        zkp_verified = zkp_manager.verify_proof(proof, face_hash, challenge)
        
        # Check for suspicious activity with fraud detector
        if is_verified and zkp_verified:
            fraud_check = fraud_detector.verify_transaction_security(
                wallet_address,
                {
                    'transaction_type': 'authentication',
                    'timestamp': time.time()
                },
                True  # Face verification succeeded
            )
            
            # If fraud detection flags as insecure
            if not fraud_check['is_secure']:
                # Still allow login but with warning
                return jsonify({
                    'success': True,
                    'verified': True,
                    'security_warning': True,
                    'warning_reason': fraud_check['reason'],
                    'warning_confidence': fraud_check['confidence']
                })
        
        # Record verification result
        fraud_detector.record_verification(wallet_address, {
            'success': is_verified and zkp_verified
        })
        
        return jsonify({
            'success': True,
            'verified': is_verified and zkp_verified,
            'zkp_used': True
        })
    except Exception as e:
        # Record failed attempt
        fraud_detector.record_activity(wallet_address, {
            'failed': True,
            'reason': str(e)
        })
        return jsonify({'success': False, 'error': str(e)})

@security_bp.route('/secure-transaction', methods=['POST'])
def secure_transaction():
    data = request.json
    
    wallet_address = data['wallet_address']
    transaction_amount = data.get('transaction_amount', 0)
    transaction_to = data.get('transaction_to', '')
    
    # Record transaction attempt
    fraud_detector.record_activity(wallet_address, {
        'login_time': time.time(),
        'ip_address': request.remote_addr,
        'device': request.headers.get('User-Agent', ''),
        'transaction_amount': transaction_amount,
        'recipient': transaction_to,
        'activity_type': 'transaction'
    })
    
    # First verify identity using secure verification
    # This would typically be done before this endpoint is called
    # but we'll simulate it here
    verification_result = data.get('verification_result', False)
    
    # Check for fraud using AI
    security_check = fraud_detector.verify_transaction_security(
        wallet_address,
        {
            'transaction_amount': transaction_amount,
            'recipient': transaction_to,
            'transaction_id': data.get('transaction_id', ''),
            'transaction_type': data.get('transaction_type', 'payment')
        },
        verification_result
    )
    
    # If suspicious, require additional verification or block
    if not security_check['is_secure']:
        # If high confidence of fraud, block transaction
        if security_check['confidence'] > 0.8:
            return jsonify({
                'success': False,
                'transaction_approved': False,
                'reason': security_check['reason'],
                'requires_additional_verification': True
            })
        # If medium confidence, warn but allow
        else:
            return jsonify({
                'success': True,
                'transaction_approved': True,
                'security_warning': True,
                'warning_reason': security_check['reason'],
                'warning_confidence': security_check['confidence']
            })
    
    # If everything looks good, approve transaction
    return jsonify({
        'success': True,
        'transaction_approved': True
    })

@security_bp.route('/fraud-alerts', methods=['GET'])
def get_fraud_alerts():
    """Get all recent fraud alerts for an organization or user"""
    # This would typically require admin authentication
    
    # Get recent activities
    recent = list(fraud_detector.recent_activities)
    
    # Filter to only failed or suspicious activities
    alerts = []
    for activity in recent:
        if activity.get('failed', False) or activity.get('is_fraud', False):
            alerts.append({
                'user_id': activity.get('user_id', 'unknown'),
                'timestamp': activity.get('timestamp', 0),
                'activity_type': activity.get('activity_type', 'unknown'),
                'reason': activity.get('reason', 'Suspicious activity'),
                'ip_address': activity.get('ip_address', 'unknown'),
                'device': activity.get('device', 'unknown')
            })
    
    return jsonify({
        'success': True,
        'alerts': alerts
    })

@security_bp.route('/train-fraud-model', methods=['POST'])
def train_fraud_model():
    """Trigger training of the fraud detection model"""
    # This would typically require admin authentication
    
    success = fraud_detector.train_model()
    
    return jsonify({
        'success': success,
        'message': 'Model training completed' if success else 'Not enough data for training'
    }) 