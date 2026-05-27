from flask import Flask, request, jsonify
import os
import cv2
import numpy as np
import base64
from ..face_recognition.face_detector import FaceAuthenticator
from ..blockchain.eth_manager import EthereumManager
from ..blockchain.multi_chain_manager import MultiChainManager, BlockchainPlatform
from ..security.hardware_security import HardwareSecurityManager

app = Flask(__name__)

# Initialize components
face_auth = FaceAuthenticator()
eth_manager = EthereumManager(
    contract_address=os.environ.get('CONTRACT_ADDRESS'),
    contract_abi_path='../smart_contracts/build/IdentityVerification.json',
    provider_url=os.environ.get('ETHEREUM_PROVIDER_URL')
)

# Initialize new components
multi_chain_manager = MultiChainManager()
hsm = HardwareSecurityManager()

@app.route('/register', methods=['POST'])
def register_identity():
    data = request.json
    
    # Decode base64 image
    image_data = base64.b64decode(data['face_image'])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract face and check liveness
    face = face_auth.detect_face(img)
    if face is None:
        return jsonify({'success': False, 'error': 'No face detected'})
    
    if not face_auth.check_liveness(face):
        return jsonify({'success': False, 'error': 'Liveness check failed'})
    
    # Generate embedding and hash
    embedding = face_auth.generate_face_embedding(face)
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate embedding'})
    
    face_hash = face_auth.face_hash(embedding)
    
    # Register on blockchain
    try:
        wallet_address = data['wallet_address']
        private_key = data['private_key']  # In production, never send private keys to the server
        
        receipt = eth_manager.register_identity(wallet_address, private_key, face_hash)
        
        return jsonify({
            'success': True, 
            'transaction_hash': receipt.transactionHash.hex(),
            'face_hash': face_hash
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/verify', methods=['POST'])
def verify_identity():
    data = request.json
    
    # Decode base64 image
    image_data = base64.b64decode(data['face_image'])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract face and check liveness
    face = face_auth.detect_face(img)
    if face is None:
        return jsonify({'success': False, 'error': 'No face detected'})
    
    if not face_auth.check_liveness(face):
        return jsonify({'success': False, 'error': 'Liveness check failed'})
    
    # Generate embedding and hash
    embedding = face_auth.generate_face_embedding(face)
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate embedding'})
    
    face_hash = face_auth.face_hash(embedding)
    
    # Verify on blockchain
    try:
        wallet_address = data['wallet_address']
        
        # First check if user has a registered identity
        has_identity = eth_manager.has_registered_identity(wallet_address)
        if not has_identity:
            return jsonify({'success': False, 'error': 'No registered identity found'})
        
        # Verify the identity
        is_verified = eth_manager.verify_identity(wallet_address, face_hash)
        
        return jsonify({
            'success': True,
            'verified': is_verified
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/liveness-challenge', methods=['POST'])
def liveness_challenge():
    data = request.json
    
    # Decode base64 image
    image_data = base64.b64decode(data['face_image'])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract face
    face = face_auth.detect_face(img)
    if face is None:
        return jsonify({'success': False, 'error': 'No face detected'})
    
    # Perform liveness check and get the challenge
    is_live = face_auth.check_liveness(face, perform_challenge=True)
    current_challenge = face_auth.get_liveness_challenge()
    
    return jsonify({
        'success': True,
        'is_live': is_live,
        'challenge': current_challenge
    })

@app.route('/multi-chain-register', methods=['POST'])
def multi_chain_register():
    data = request.json
    
    # Get blockchain platforms to register on
    platform_names = data.get('platforms', ['ethereum'])
    platforms = [BlockchainPlatform(name) for name in platform_names]
    
    # Wallet addresses for each platform
    wallet_addresses = data.get('wallet_addresses', [])
    private_keys = data.get('private_keys', [])
    
    # Validate inputs
    if len(platforms) != len(wallet_addresses) or len(platforms) != len(private_keys):
        return jsonify({'success': False, 'error': 'Must provide wallet address and private key for each platform'})
    
    # Decode base64 image
    image_data = base64.b64decode(data['face_image'])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract face and check liveness
    face = face_auth.detect_face(img)
    if face is None:
        return jsonify({'success': False, 'error': 'No face detected'})
    
    if not face_auth.check_liveness(face):
        return jsonify({'success': False, 'error': 'Liveness check failed'})
    
    # Generate embedding and hash
    embedding = face_auth.generate_face_embedding(face)
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate embedding'})
        
    # Secure the biometric template using HSM
    protected_template = hsm.secure_face_template(embedding)
    
    # Generate blockchain-compatible hash
    face_hash = face_auth.face_hash(embedding)
    
    # Register on multiple blockchains
    try:
        results = multi_chain_manager.register_cross_chain(
            platforms, 
            wallet_addresses, 
            private_keys, 
            face_hash
        )
        
        # Store the protected template (in a real system, this would go to a secure database)
        # Here we just return it as part of the response
        return jsonify({
            'success': True,
            'registration_results': results,
            'face_hash': face_hash,
            'protected_template': protected_template
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/secure-hsm-verify', methods=['POST'])
def hsm_verify_identity():
    data = request.json
    wallet_address = data['wallet_address']
    protected_template = data['protected_template']
    
    # Decode base64 image
    image_data = base64.b64decode(data['face_image'])
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Extract face and check liveness
    face = face_auth.detect_face(img)
    if face is None:
        return jsonify({'success': False, 'error': 'No face detected'})
    
    if not face_auth.check_liveness(face):
        return jsonify({'success': False, 'error': 'Liveness check failed'})
    
    # Generate embedding
    embedding = face_auth.generate_face_embedding(face)
    if embedding is None:
        return jsonify({'success': False, 'error': 'Failed to generate embedding'})
    
    # Verify against the protected template using HSM
    is_match = hsm.verify_against_template(embedding, protected_template)
    
    if not is_match:
        return jsonify({'success': False, 'error': 'Face does not match protected template'})
    
    # Also verify on blockchain for completeness
    face_hash = face_auth.face_hash(embedding)
    
    try:
        # Verify on blockchain
        blockchain_verified = eth_manager.verify_identity(wallet_address, face_hash)
        
        return jsonify({
            'success': True,
            'verified': is_match and blockchain_verified,
            'hsm_verified': is_match,
            'blockchain_verified': blockchain_verified
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True) 