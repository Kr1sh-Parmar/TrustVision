import os
from web3 import Web3
import json
from enum import Enum
import requests
from .eth_manager import EthereumManager

class BlockchainPlatform(Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BINANCE = "binance"
    SOLANA = "solana"
    HYPERLEDGER = "hyperledger"

class MultiChainManager:
    def __init__(self):
        # Initialize connections to different blockchains
        self.chain_providers = {
            BlockchainPlatform.ETHEREUM: {
                'provider_url': os.environ.get('ETHEREUM_PROVIDER_URL', 'https://mainnet.infura.io/v3/your-key'),
                'contract_address': os.environ.get('ETH_CONTRACT_ADDRESS'),
                'contract_abi_path': '../smart_contracts/build/IdentityVerification.json'
            },
            BlockchainPlatform.POLYGON: {
                'provider_url': os.environ.get('POLYGON_PROVIDER_URL', 'https://polygon-rpc.com'),
                'contract_address': os.environ.get('POLYGON_CONTRACT_ADDRESS'),
                'contract_abi_path': '../smart_contracts/build/IdentityVerification.json'
            },
            BlockchainPlatform.BINANCE: {
                'provider_url': os.environ.get('BSC_PROVIDER_URL', 'https://bsc-dataseed.binance.org/'),
                'contract_address': os.environ.get('BSC_CONTRACT_ADDRESS'),
                'contract_abi_path': '../smart_contracts/build/IdentityVerification.json'
            }
            # Solana and Hyperledger would need different handlers
        }
        
        # Initialize chain-specific managers
        self.chain_managers = {}
        for chain, config in self.chain_providers.items():
            # Only initialize chains that have contract addresses configured
            if chain in [BlockchainPlatform.ETHEREUM, BlockchainPlatform.POLYGON, BlockchainPlatform.BINANCE] and config['contract_address']:
                self.chain_managers[chain] = EthereumManager(
                    contract_address=config['contract_address'],
                    contract_abi_path=config['contract_abi_path'],
                    provider_url=config['provider_url']
                )
    
    def register_identity(self, platform, wallet_address, private_key, face_hash):
        """Register identity on the specified blockchain platform"""
        if platform not in self.chain_managers:
            raise ValueError(f"Blockchain platform {platform} not supported or not configured")
            
        manager = self.chain_managers[platform]
        return manager.register_identity(wallet_address, private_key, face_hash)
    
    def verify_identity(self, platform, user_address, face_hash):
        """Verify identity on the specified blockchain platform"""
        if platform not in self.chain_managers:
            raise ValueError(f"Blockchain platform {platform} not supported or not configured")
            
        manager = self.chain_managers[platform]
        return manager.verify_identity(user_address, face_hash)
    
    def register_cross_chain(self, platforms, wallet_addresses, private_keys, face_hash):
        """Register identity across multiple blockchains"""
        results = {}
        
        for i, platform in enumerate(platforms):
            try:
                wallet = wallet_addresses[i]
                key = private_keys[i]
                
                result = self.register_identity(platform, wallet, key, face_hash)
                results[platform.value] = {
                    'success': True,
                    'transaction_hash': result.transactionHash.hex() if hasattr(result, 'transactionHash') else str(result)
                }
            except Exception as e:
                results[platform.value] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def verify_cross_chain(self, platforms, wallet_addresses, face_hash):
        """Verify identity across multiple blockchains"""
        results = {}
        overall_verified = True
        
        for i, platform in enumerate(platforms):
            try:
                wallet = wallet_addresses[i]
                
                is_verified = self.verify_identity(platform, wallet, face_hash)
                results[platform.value] = {
                    'success': True,
                    'verified': is_verified
                }
                
                if not is_verified:
                    overall_verified = False
            except Exception as e:
                results[platform.value] = {
                    'success': False,
                    'error': str(e)
                }
                overall_verified = False
        
        return {
            'results': results,
            'verified': overall_verified
        }
    
    def get_supported_platforms(self):
        """Get list of supported and configured blockchain platforms"""
        return [chain.value for chain in self.chain_managers.keys()] 