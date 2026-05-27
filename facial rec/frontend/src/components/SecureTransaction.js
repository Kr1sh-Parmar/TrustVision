import React, { useState, useEffect } from 'react';
import Web3 from 'web3';
import axios from 'axios';
import LivenessChallenge from './LivenessChallenge';

const SecureTransaction = () => {
  const [walletAddress, setWalletAddress] = useState('');
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [transactionStatus, setTransactionStatus] = useState('');
  const [securityWarning, setSecurityWarning] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showLivenessCheck, setShowLivenessCheck] = useState(false);
  const [livenessVerified, setLivenessVerified] = useState(false);
  const [identityVerified, setIdentityVerified] = useState(false);
  
  useEffect(() => {
    // Check if MetaMask is installed
    if (window.ethereum) {
      const web3 = new Web3(window.ethereum);
      
      // Request account access
      window.ethereum.request({ method: 'eth_requestAccounts' })
        .then(accounts => {
          setWalletAddress(accounts[0]);
        })
        .catch(error => {
          console.error("Error connecting to MetaMask:", error);
        });
    } else {
      setTransactionStatus('MetaMask is not installed. Please install it to use this feature.');
    }
  }, []);
  
  const verifyIdentity = async () => {
    setIsLoading(true);
    setTransactionStatus('Verifying identity...');
    
    try {
      // Call secure-verify endpoint
      const response = await axios.post('/api/secure-verify', {
        wallet_address: walletAddress,
        verification_type: 'transaction',
        zkp_enabled: true // Request ZKP verification
      });
      
      if (response.data.success && response.data.verified) {
        setIdentityVerified(true);
        
        // Check for security warnings
        if (response.data.security_warning) {
          setSecurityWarning({
            reason: response.data.warning_reason,
            confidence: response.data.warning_confidence
          });
        }
        
        setTransactionStatus('Identity verified! You can proceed with the transaction.');
      } else {
        setIdentityVerified(false);
        setTransactionStatus(`Identity verification failed: ${response.data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error("Error verifying identity:", error);
      setTransactionStatus('Error verifying identity. Please try again.');
      setIdentityVerified(false);
    } finally {
      setIsLoading(false);
    }
  };
  
  const initiateTransaction = async () => {
    // First check liveness if not already verified
    if (!livenessVerified) {
      setShowLivenessCheck(true);
      setTransactionStatus('Please complete liveness verification first');
      return;
    }
    
    // Then verify identity if not already verified
    if (!identityVerified) {
      await verifyIdentity();
      if (!identityVerified) {
        return;
      }
    }
    
    // Now proceed with transaction
    if (!recipient || !amount) {
      setTransactionStatus('Please enter recipient address and amount');
      return;
    }
    
    setIsLoading(true);
    setTransactionStatus('Processing transaction...');
    
    try {
      // Call secure-transaction endpoint
      const response = await axios.post('/api/secure-transaction', {
        wallet_address: walletAddress,
        transaction_amount: parseFloat(amount),
        transaction_to: recipient,
        verification_result: identityVerified,
        transaction_type: 'payment',
        transaction_id: `tx_${Date.now()}`
      });
      
      if (response.data.success && response.data.transaction_approved) {
        // Check for security warnings
        if (response.data.security_warning) {
          setSecurityWarning({
            reason: response.data.warning_reason,
            confidence: response.data.warning_confidence
          });
          setTransactionStatus('Transaction completed with security warning!');
        } else {
          setSecurityWarning(null);
          setTransactionStatus('Transaction completed successfully!');
        }
        
        // In a real app, you would now submit the actual blockchain transaction
        // For demo purposes, we're just simulating approval
        
      } else {
        setTransactionStatus(`Transaction failed: ${response.data.reason || 'Transaction rejected'}`);
      }
    } catch (error) {
      console.error("Error processing transaction:", error);
      setTransactionStatus('Error processing transaction. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleLivenessVerified = (verified) => {
    setLivenessVerified(verified);
    setShowLivenessCheck(false);
    
    if (verified) {
      // Proceed to identity verification
      verifyIdentity();
    }
  };
  
  return (
    <div className="secure-transaction">
      <h2>Secure Transaction</h2>
      
      <div className="wallet-info">
        <p>Connected Wallet: {walletAddress || 'Not Connected'}</p>
      </div>
      
      {showLivenessCheck ? (
        <LivenessChallenge onLivenessVerified={handleLivenessVerified} />
      ) : (
        <>
          <div className="transaction-form">
            <div className="form-group">
              <label htmlFor="recipient">Recipient Address:</label>
              <input
                id="recipient"
                type="text"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder="0x..."
                disabled={isLoading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="amount">Amount (ETH):</label>
              <input
                id="amount"
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.0"
                step="0.01"
                disabled={isLoading}
              />
            </div>
            
            <button 
              onClick={initiateTransaction} 
              disabled={isLoading || !walletAddress}
              className="transaction-button"
            >
              {isLoading ? 'Processing...' : 'Send Transaction'}
            </button>
          </div>
          
          {securityWarning && (
            <div className="security-warning">
              <h4>⚠️ Security Warning</h4>
              <p>{securityWarning.reason}</p>
              <p>Confidence: {Math.round(securityWarning.confidence * 100)}%</p>
            </div>
          )}
          
          {transactionStatus && (
            <div className="status-message">
              {transactionStatus}
            </div>
          )}
        </>
      )}
      
      <div className="verification-status">
        <p>Liveness Verification: {livenessVerified ? '✅ Verified' : '❌ Not Verified'}</p>
        <p>Identity Verification: {identityVerified ? '✅ Verified' : '❌ Not Verified'}</p>
      </div>
    </div>
  );
};

export default SecureTransaction; 