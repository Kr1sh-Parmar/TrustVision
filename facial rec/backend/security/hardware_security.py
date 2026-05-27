import os
import base64
import hashlib
import hmac
import time
import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class HardwareSecurityManager:
    def __init__(self):
        # In a real implementation, this would connect to a physical HSM
        # Here we simulate HSM functionality
        self.hsm_api_endpoint = os.environ.get('HSM_API_ENDPOINT', 'https://hsm-simulator.example.com')
        self.hsm_api_key = os.environ.get('HSM_API_KEY', 'demo-key')
        
        # Secure key used for protecting biometric templates
        # In a real HSM, this would never leave the hardware
        self._secure_key = os.environ.get('BIOMETRIC_PROTECTION_KEY', 'this-would-be-in-hsm').encode()
        
        # Initialize the secure enclave parameters
        self.enclave_id = None
        self.init_secure_enclave()
        
    def init_secure_enclave(self):
        """Initialize a secure enclave for biometric operations"""
        # In a real implementation, this would create a secure session with the HSM
        # or initialize a Trusted Execution Environment (TEE)
        try:
            # Simulated call to HSM
            response = {
                'enclave_id': 'hsm-enclave-' + hashlib.sha256(str(time.time()).encode()).hexdigest()[:8],
                'status': 'initialized'
            }
            self.enclave_id = response['enclave_id']
            print(f"Secure enclave initialized: {self.enclave_id}")
            return True
        except Exception as e:
            print(f"Failed to initialize secure enclave: {e}")
            return False
    
    def secure_face_template(self, face_embedding):
        """Protect the face template using hardware security"""
        if not self.enclave_id:
            raise ValueError("Secure enclave not initialized")
            
        # Convert embedding to bytes
        embedding_bytes = str(face_embedding).encode()
        
        # Generate a unique IV
        iv = os.urandom(16)
        
        # In a real HSM, this encryption would happen within the hardware
        # The raw biometric data would never be exposed to the software
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(embedding_bytes) + padder.finalize()
        
        cipher = Cipher(algorithms.AES(self._secure_key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # Combine IV and encrypted data
        protected_template = base64.b64encode(iv + encrypted_data).decode()
        
        # Generate a verification token that proves this template was protected by the HSM
        token = hmac.new(self._secure_key, protected_template.encode(), hashlib.sha256).hexdigest()
        
        return {
            'protected_template': protected_template,
            'token': token,
            'enclave_id': self.enclave_id
        }
    
    def verify_against_template(self, new_embedding, protected_template_data):
        """Verify a face embedding against a protected template using the HSM"""
        if not self.enclave_id:
            raise ValueError("Secure enclave not initialized")
            
        try:
            protected_template = protected_template_data['protected_template']
            token = protected_template_data['token']
            
            # Verify the template hasn't been tampered with
            expected_token = hmac.new(self._secure_key, protected_template.encode(), hashlib.sha256).hexdigest()
            if token != expected_token:
                return False
            
            # Decode and decrypt the protected template
            encrypted_data = base64.b64decode(protected_template)
            iv = encrypted_data[:16]
            encrypted_template = encrypted_data[16:]
            
            # Decrypt using the secure key
            cipher = Cipher(algorithms.AES(self._secure_key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(encrypted_template) + decryptor.finalize()
            
            unpadder = padding.PKCS7(128).unpadder()
            template_bytes = unpadder.update(padded_data) + unpadder.finalize()
            
            # In a real HSM, the comparison would happen within the hardware
            # This is a simplified simulation for demonstration
            similarity = self._compute_similarity(eval(template_bytes.decode()), new_embedding)
            
            # Use a threshold to determine verification
            return similarity > 0.85
            
        except Exception as e:
            print(f"Template verification error: {e}")
            return False
    
    def _compute_similarity(self, template1, template2):
        """Compute cosine similarity between two face embeddings"""
        # In a real HSM, this would be a secure comparison inside the hardware
        import numpy as np
        
        v1 = np.array(template1)
        v2 = np.array(template2)
        
        # Compute cosine similarity
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        similarity = dot_product / (norm_v1 * norm_v2)
        return float(similarity)
    
    def secure_key_generation(self, seed_phrase=None):
        """Generate or recover a secure key inside the HSM"""
        # In a real HSM, the private key would never leave the hardware
        if seed_phrase:
            # Generate key deterministically from seed phrase
            key_material = hashlib.pbkdf2_hmac(
                'sha256', 
                seed_phrase.encode(), 
                self._secure_key, 
                iterations=100000
            )
        else:
            # Generate a random key
            key_material = os.urandom(32)
        
        # Store the key identifier, not the key itself
        key_id = hashlib.sha256(key_material).hexdigest()
        
        return {
            'key_id': key_id,
            'created_at': time.time()
        }
    
    def sign_transaction(self, key_id, transaction_data):
        """Sign a transaction using a key stored in the HSM"""
        # In a real HSM, this would use the secure key to sign without exposing it
        # Here we simulate the signing process
        
        # For demo purposes only - in a real HSM the key would never be exposed
        # and the signing would happen inside the secure hardware
        key_bytes = hashlib.sha256((key_id + self.enclave_id).encode()).digest()
        
        # Create a signature using HMAC
        signature = hmac.new(key_bytes, transaction_data.encode(), hashlib.sha256).hexdigest()
        
        return {
            'signature': signature,
            'key_id': key_id,
            'timestamp': time.time()
        } 