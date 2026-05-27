import os
import hashlib
import base64
import json
import time
import secrets
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

class KeyRecoveryManager:
    def __init__(self):
        # Master key for encrypting recovery shares (in a real system, this would be in an HSM)
        self._master_key = os.environ.get('RECOVERY_MASTER_KEY', 'master-recovery-key').encode()
        
        # Minimum shares needed for recovery (Shamir's Secret Sharing)
        self.threshold = 3
        self.total_shares = 5
    
    def generate_recovery_kit(self, wallet_address, private_key):
        """Generate a recovery kit using Shamir's Secret Sharing"""
        # In production, use a proper Shamir Secret Sharing library
        # This is a simplified version for demonstration
        
        # Create a unique recovery ID
        recovery_id = hashlib.sha256(f"{wallet_address}:{time.time()}".encode()).hexdigest()[:16]
        
        # In a real implementation, use an actual Shamir Secret Sharing algorithm
        # For this demo, we'll create "shares" by splitting the key and adding random data
        shares = []
        key_bytes = private_key.encode() if isinstance(private_key, str) else private_key
        
        # Generate random byte sequences for each share
        for i in range(self.total_shares):
            # Create a random share identifier
            share_id = secrets.token_hex(4)
            
            # Generate random padding (in a real implementation, these would be actual Shamir shares)
            random_bytes = os.urandom(32)
            
            # Encrypt the actual key with a derivative of the master key and the random bytes
            # This simulates a Shamir share (though not mathematically correct for demo purposes)
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            share_key = kdf.derive(self._master_key + random_bytes)
            
            # Encrypt the private key
            iv = os.urandom(16)
            cipher = Cipher(algorithms.AES(share_key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            padder = padding.PKCS7(128).padder()
            padded_data = padder.update(key_bytes) + padder.finalize()
            
            encrypted_key = encryptor.update(padded_data) + encryptor.finalize()
            
            # Create share data
            share = {
                'share_id': share_id,
                'recovery_id': recovery_id,
                'index': i + 1,
                'salt': base64.b64encode(salt).decode(),
                'iv': base64.b64encode(iv).decode(),
                'data': base64.b64encode(encrypted_key).decode(),
                'random': base64.b64encode(random_bytes).decode(),
                'created_at': time.time()
            }
            
            shares.append(share)
        
        # Create the recovery metadata
        metadata = {
            'recovery_id': recovery_id,
            'wallet_address': wallet_address,
            'threshold': self.threshold,
            'total_shares': self.total_shares,
            'created_at': time.time()
        }
        
        return {
            'metadata': metadata,
            'shares': shares
        }
    
    def recover_key(self, shares):
        """Recover a private key from recovery shares"""
        if len(shares) < self.threshold:
            raise ValueError(f"Not enough shares provided. Need at least {self.threshold}.")
        
        # Verify all shares belong to the same recovery kit
        recovery_ids = set(share['recovery_id'] for share in shares)
        if len(recovery_ids) != 1:
            raise ValueError("Shares from different recovery kits provided.")
        
        recovery_id = list(recovery_ids)[0]
        
        # In a real Shamir implementation, we would mathematically combine the shares
        # For this demo, we'll just use the first valid share to decrypt
        
        for share in shares:
            try:
                # Extract share components
                salt = base64.b64decode(share['salt'])
                iv = base64.b64decode(share['iv'])
                encrypted_key = base64.b64decode(share['data'])
                random_bytes = base64.b64decode(share['random'])
                
                # Recreate the share key
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                share_key = kdf.derive(self._master_key + random_bytes)
                
                # Decrypt the private key
                cipher = Cipher(algorithms.AES(share_key), modes.CBC(iv), backend=default_backend())
                decryptor = cipher.decryptor()
                padded_key = decryptor.update(encrypted_key) + decryptor.finalize()
                
                unpadder = padding.PKCS7(128).unpadder()
                private_key = unpadder.update(padded_key) + unpadder.finalize()
                
                # Return the recovered key
                return {
                    'success': True,
                    'private_key': private_key.decode(),
                    'recovery_id': recovery_id
                }
                
            except Exception as e:
                # If this share fails, try the next one
                print(f"Share {share.get('share_id')} failed: {e}")
                continue
        
        # If we get here, all shares failed
        raise ValueError("Could not recover key from provided shares. Shares may be corrupted.")

    def distribute_recovery_shares(self, recovery_kit):
        """Distribute recovery shares to trusted parties or secure storage"""
        # In a real implementation, this would send shares to different channels:
        # - Trusted contacts (via encrypted email, etc.)
        # - Hardware security devices
        # - Secure cloud storage
        # - Print physical backup
        
        metadata = recovery_kit['metadata']
        shares = recovery_kit['shares']
        
        distribution_result = {
            'recovery_id': metadata['recovery_id'],
            'share_distribution': []
        }
        
        # Simulate distribution
        for i, share in enumerate(shares):
            # Determine distribution method based on share index
            if i == 0:
                method = 'encrypted_email'
                recipient = 'trusted_contact_1@example.com'
            elif i == 1:
                method = 'encrypted_email'
                recipient = 'trusted_contact_2@example.com'
            elif i == 2:
                method = 'hardware_device'
                recipient = 'yubikey_001'
            elif i == 3:
                method = 'secure_cloud'
                recipient = 'encrypted_vault'
            else:
                method = 'print_backup'
                recipient = 'physical_storage'
            
            # In a real system, actually send/store the share
            # Here we just record what would happen
            distribution_result['share_distribution'].append({
                'share_id': share['share_id'],
                'method': method,
                'recipient': recipient,
                'distributed_at': time.time(),
                'status': 'simulated'
            })
        
        return distribution_result 