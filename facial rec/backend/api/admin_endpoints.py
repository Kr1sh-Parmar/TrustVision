from flask import Blueprint, request, jsonify
import os
import time
import datetime
import numpy as np
import pandas as pd
from ..fraud_detection.fraud_detector import FraudDetector
from ..blockchain.multi_chain_manager import MultiChainManager
from ..face_recognition.face_detector import FaceAuthenticator
from ..security.hardware_security import HardwareSecurityManager
from ..security.key_recovery import KeyRecoveryManager

admin_bp = Blueprint('admin', __name__)

# Initialize components
fraud_detector = FraudDetector()
multi_chain_manager = MultiChainManager()
hsm = HardwareSecurityManager()
key_recovery = KeyRecoveryManager()

# Authentication middleware (simplified for demonstration)
def admin_required(f):
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'Unauthorized access'}), 401
            
        token = auth_header.split(' ')[1]
        # In a real implementation, verify the token
        # For this demo, we'll use a simple hardcoded token
        if token != os.environ.get('ADMIN_API_TOKEN', 'admin-secret-token'):
            return jsonify({'success': False, 'error': 'Invalid token'}), 403
            
        return f(*args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard-overview', methods=['GET'])
@admin_required
def dashboard_overview():
    """Get main dashboard metrics"""
    # Get system stats
    
    # Get activity counts from fraud detector
    total_verifications = len([a for a in fraud_detector.recent_activities if a.get('activity_type') == 'verification'])
    total_registrations = len([a for a in fraud_detector.recent_activities if a.get('activity_type') == 'registration'])
    total_transactions = len([a for a in fraud_detector.recent_activities if a.get('activity_type') == 'transaction'])
    
    # Get chain distribution
    chain_distribution = {}
    for chain in multi_chain_manager.get_supported_platforms():
        # In a real implementation, this would query each blockchain
        chain_distribution[chain] = {
            'registrations': np.random.randint(10, 100),  # Simulated data
            'verifications': np.random.randint(50, 500)   # Simulated data
        }
    
    # Get fraud metrics
    fraud_alerts = len([a for a in fraud_detector.recent_activities if a.get('is_fraud', False)])
    success_rate = sum(1 for a in fraud_detector.recent_activities if a.get('success', False)) / max(1, len(fraud_detector.recent_activities))
    
    # Get time-based metrics - simulate with random data for this demo
    now = time.time()
    day_in_secs = 24 * 60 * 60
    
    hourly_activity = []
    for i in range(24):
        hourly_activity.append({
            'hour': i,
            'verifications': np.random.randint(5, 30),
            'registrations': np.random.randint(1, 10)
        })
    
    daily_activity = []
    for i in range(7):
        day = now - (6 - i) * day_in_secs
        day_str = datetime.datetime.fromtimestamp(day).strftime('%Y-%m-%d')
        daily_activity.append({
            'date': day_str,
            'verifications': np.random.randint(20, 200),
            'registrations': np.random.randint(5, 50),
            'transactions': np.random.randint(10, 100)
        })
    
    return jsonify({
        'success': True,
        'overview': {
            'total_users': total_registrations,
            'total_verifications': total_verifications,
            'total_transactions': total_transactions,
            'fraud_alerts': fraud_alerts,
            'success_rate': success_rate
        },
        'chain_distribution': chain_distribution,
        'hourly_activity': hourly_activity,
        'daily_activity': daily_activity,
        'system_health': {
            'api_status': 'healthy',
            'blockchain_connections': len(multi_chain_manager.chain_managers),
            'hsm_status': hsm.enclave_id is not None,
            'last_updated': now
        }
    })

@admin_bp.route('/fraud-alerts', methods=['GET'])
@admin_required
def get_fraud_alerts():
    """Get detailed fraud alerts"""
    # Get all suspicious activities
    alerts = []
    for activity in fraud_detector.recent_activities:
        if activity.get('is_fraud', False) or activity.get('failed', False):
            alerts.append({
                'user_id': activity.get('user_id', 'unknown'),
                'timestamp': activity.get('timestamp', 0),
                'activity_type': activity.get('activity_type', 'unknown'),
                'reason': activity.get('reason', 'Suspicious activity'),
                'confidence': activity.get('confidence', 0.0),
                'ip_address': activity.get('ip_address', 'unknown'),
                'device': activity.get('device', 'unknown'),
                'location': activity.get('location', 'unknown'),
                'status': 'open'  # In a real system, alerts could be marked as resolved
            })
    
    # Sort by newest first
    alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'success': True,
        'alerts': alerts,
        'total_count': len(alerts)
    })

@admin_bp.route('/user-activity/<user_id>', methods=['GET'])
@admin_required
def get_user_activity(user_id):
    """Get activity history for a specific user"""
    # Filter activities for this user
    activities = [a for a in fraud_detector.recent_activities if a.get('user_id') == user_id]
    
    # Get behavior patterns
    behavior = fraud_detector.user_behaviors.get(user_id, {})
    
    # In a real system, you would query blockchain for all user registrations
    blockchain_info = {
        'registered_chains': [],
        'last_verification': None,
        'verification_count': 0
    }
    
    for chain in multi_chain_manager.get_supported_platforms():
        if np.random.random() > 0.5:  # Simulate some chains having registrations
            blockchain_info['registered_chains'].append(chain)
    
    if activities:
        verifications = [a for a in activities if a.get('activity_type') == 'verification']
        if verifications:
            blockchain_info['verification_count'] = len(verifications)
            blockchain_info['last_verification'] = max(v.get('timestamp', 0) for v in verifications)
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'activities': activities,
        'behavior_patterns': {
            'login_times': list(behavior.get('login_times', [])),
            'login_locations': list(behavior.get('login_locations', [])),
            'devices': list(behavior.get('devices', [])),
            'ip_addresses': list(behavior.get('ip_addresses', []))
        },
        'blockchain_info': blockchain_info
    })

@admin_bp.route('/system-metrics', methods=['GET'])
@admin_required
def get_system_metrics():
    """Get detailed system performance metrics"""
    # In a real system, these would be actual metrics from monitoring tools
    return jsonify({
        'success': True,
        'api_performance': {
            'average_response_time': 120,  # ms
            'requests_per_minute': 42,
            'error_rate': 0.01,
            'uptime': 99.98  # percentage
        },
        'face_recognition': {
            'average_detection_time': 85,  # ms
            'average_embedding_time': 150,  # ms
            'accuracy': 0.9945
        },
        'blockchain': {
            'average_transaction_time': 2500,  # ms
            'gas_usage': 45000,
            'confirmation_rate': 0.99
        },
        'resource_usage': {
            'cpu': 38,  # percentage
            'memory': 64,  # percentage
            'disk': 42,  # percentage
            'network': 22  # percentage
        }
    })

# Add an endpoint to trigger model retraining
@admin_bp.route('/retrain-fraud-model', methods=['POST'])
@admin_required
def retrain_fraud_model():
    """Manually trigger retraining of the fraud detection model"""
    success = fraud_detector.train_model()
    
    return jsonify({
        'success': success,
        'message': 'Model retraining successful' if success else 'Not enough data for retraining'
    })

# Add an endpoint to create a recovery kit for a user
@admin_bp.route('/generate-recovery-kit', methods=['POST'])
@admin_required
def generate_recovery_kit():
    """Generate a key recovery kit for a user"""
    data = request.json
    wallet_address = data.get('wallet_address')
    private_key = data.get('private_key')
    
    if not wallet_address or not private_key:
        return jsonify({'success': False, 'error': 'Wallet address and private key required'})
    
    try:
        # Generate the recovery kit
        recovery_kit = key_recovery.generate_recovery_kit(wallet_address, private_key)
        
        # Simulate distribution (in a real system, this would actually distribute the shares)
        distribution = key_recovery.distribute_recovery_shares(recovery_kit)
        
        return jsonify({
            'success': True,
            'recovery_id': recovery_kit['metadata']['recovery_id'],
            'distribution': distribution
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 