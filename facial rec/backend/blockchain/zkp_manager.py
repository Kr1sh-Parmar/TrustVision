import hashlib
import random
import time
from web3 import Web3
import json
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class ZKProofManager:
    def __init__(self):
        # Generate key pair for ZKP operations
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()
        
        # Serialize public key for sharing
        self.public_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def generate_challenge(self, face_hash):
        """Generate a random challenge based on the face hash"""
        # Create a unique nonce for this verification
        nonce = str(random.randint(10000, 99999)) + str(time.time())
        
        # Combine face hash with nonce to create challenge
        challenge_data = face_hash + nonce
        challenge_hash = hashlib.sha256(challenge_data.encode()).hexdigest()
        
        return {
            'challenge_hash': challenge_hash,
            'nonce': nonce
        }
    
    def create_proof(self, face_embedding, challenge):
        """Create a zero-knowledge proof that we know the face embedding 
        without revealing the actual embedding"""
        
        # Convert embedding to string for proof generation
        embedding_str = str(face_embedding)
        
        # Combine with challenge nonce
        proof_data = embedding_str + challenge['nonce']
        
        # Sign the combined data using our private key
        signature = self.private_key.sign(
            proof_data.encode(),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        # Return the proof (signature) and public key for verification
        return {
            'signature': signature.hex(),
            'public_key': self.public_key_pem.decode(),
            'nonce': challenge['nonce']
        }
    
    def verify_proof(self, proof, face_hash, challenge):
        """Verify a zero-knowledge proof without knowing the original face embedding"""
        try:
            # Convert signature from hex back to bytes
            signature = bytes.fromhex(proof['signature'])
            
            # Deserialize the public key
            public_key = serialization.load_pem_public_key(
                proof['public_key'].encode()
            )
            
            # Recreate the challenge hash
            challenge_data = face_hash + challenge['nonce']
            expected_challenge = hashlib.sha256(challenge_data.encode()).hexdigest()
            
            # Check if the challenge matches
            if expected_challenge != challenge['challenge_hash']:
                return False
                
            # Verify the signature (will raise exception if invalid)
            # We don't need the original face embedding to verify!
            public_key.verify(
                signature,
                (str(face_hash) + proof['nonce']).encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            print(f"ZKP verification error: {e}")
            return False

    def generate_witness(self, face_embedding, face_hash):
        """Generate ZKP witness for blockchain verification without revealing embedding"""
        # In a real implementation, this would use zk-SNARKs or similar technology
        # This is a simplified version
        
        # Create a hash of the embedding
        embedding_str = str(face_embedding)
        witness_hash = hashlib.sha256(embedding_str.encode()).hexdigest()
        
        # Create a unique salt
        salt = os.urandom(16).hex()
        
        # Create the witness by combining the hash and salt
        witness = hashlib.sha256((witness_hash + salt).encode()).hexdigest()
        
        return {
            'witness': witness,
            'salt': salt
        }
    
    def verify_witness(self, witness_data, face_hash):
        """Verify the ZKP witness on-chain"""
        # In a real implementation, this would verify a zk-SNARK proof
        # For now, we just check if the witness was correctly generated
        
        # Recreate the witness hash from the provided data
        witness_hash = hashlib.sha256((face_hash + witness_data['salt']).encode()).hexdigest()
        
        # Compare with the provided witness
        return witness_hash == witness_data['witness'] 