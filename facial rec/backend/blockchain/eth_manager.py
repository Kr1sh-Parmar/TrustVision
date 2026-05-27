from web3 import Web3
import json
import os

class EthereumManager:
    def __init__(self, contract_address, contract_abi_path, provider_url):
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        
        # Load contract ABI
        with open(contract_abi_path, 'r') as f:
            contract_abi = json.load(f)
        
        # Initialize contract
        self.contract = self.w3.eth.contract(address=contract_address, abi=contract_abi)
        
    def register_identity(self, wallet_address, private_key, face_hash):
        """Register a face hash on the blockchain"""
        # Convert face hash to bytes32
        face_hash_bytes = Web3.toBytes(hexstr=face_hash)
        
        # Build transaction
        nonce = self.w3.eth.get_transaction_count(wallet_address)
        tx = self.contract.functions.registerIdentity(face_hash_bytes).build_transaction({
            'from': wallet_address,
            'gas': 2000000,
            'gasPrice': self.w3.to_wei('50', 'gwei'),
            'nonce': nonce,
        })
        
        # Sign and send transaction
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # Wait for transaction to be mined
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_receipt
        
    def verify_identity(self, user_address, face_hash):
        """Verify if a face hash matches the registered identity"""
        face_hash_bytes = Web3.toBytes(hexstr=face_hash)
        
        # Call view function (no transaction needed)
        result = self.contract.functions.verifyIdentity(user_address, face_hash_bytes).call()
        
        return result
        
    def has_registered_identity(self, user_address):
        """Check if a user has a registered identity"""
        return self.contract.functions.hasIdentity(user_address).call() 