import React, { useState, useRef, useEffect } from 'react';
import Web3 from 'web3';
import axios from 'axios';
import LivenessChallenge from './LivenessChallenge';

const MultiChainRegistration = () => {
  const [walletInfo, setWalletInfo] = useState({
    ethereum: '',
    polygon: '',
    binance: ''
  });
  
  const [privateKeys, setPrivateKeys] = useState({
    ethereum: '',
    polygon: '',
    binance: ''
  });
  
  const [selectedChains, setSelectedChains] = useState(['ethereum']);
  const [registrationStatus, setRegistrationStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [livenessVerified, setLivenessVerified] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [platformStatus, setPlatformStatus] = useState({});
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  
  useEffect(() => {
    // Auto-detect MetaMask and other wallets
    detectWallets();
  }, []);
  
  const detectWallets = async () => {
    const info = { ...walletInfo };
    
    // Check for MetaMask/Ethereum
    if (window.ethereum) {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        info.ethereum = accounts[0];
      } catch (error) {
        console.error("Error connecting to Ethereum:", error);
      }
    }
    
    // Check for Polygon (often via same provider as Ethereum)
    if (window.ethereum && window.ethereum.isMetaMask) {
      try {
        // Try to switch to Polygon
        await window.ethereum.request({
          method: 'wallet_addEthereumChain',
          params: [{
            chainId: '0x89', // 137 in hex
            chainName: 'Polygon Mainnet',
            nativeCurrency: {
              name: 'MATIC',
              symbol: 'MATIC',
              decimals: 18
            },
            rpcUrls: ['https://polygon-rpc.com/'],
            blockExplorerUrls: ['https://polygonscan.com/']
          }]
        });
        
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        info.polygon = accounts[0];
      } catch (error) {
        console.error("Error connecting to Polygon:", error);
      }
    }
    
    // Check for Binance Smart Chain
    if (window.BinanceChain) {
      try {
        const accounts = await window.BinanceChain.request({ method: 'eth_requestAccounts' });
        info.binance = accounts[0];
      } catch (error) {
        console.error("Error connecting to Binance Smart Chain:", error);
      }
    }
    
    setWalletInfo(info);
  };
  
  const handleChainSelection = (chain) => {
    if (selectedChains.includes(chain)) {
      setSelectedChains(selectedChains.filter(c => c !== chain));
    } else {
      setSelectedChains([...selectedChains, chain]);
    }
  };
  
  const startCapture = async () => {
    if (!livenessVerified) {
      setRegistrationStatus('Please complete the liveness check first');
      return;
    }
    
    setIsCapturing(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = stream;
    } catch (err) {
      console.error("Error accessing camera:", err);
      setRegistrationStatus('Error accessing camera. Please make sure your camera is enabled.');
      setIsCapturing(false);
    }
  };
  
  const captureImage = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const imageDataUrl = canvas.toDataURL('image/jpeg');
    setCapturedImage(imageDataUrl);
    
    // Stop the video stream
    const stream = video.srcObject;
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
    
    setIsCapturing(false);
  };
  
  const registerMultiChain = async () => {
    if (selectedChains.length === 0) {
      setRegistrationStatus('Please select at least one blockchain platform');
      return;
    }
    
    // Make sure we have wallet addresses and private keys for selected chains
    const missingInfo = selectedChains.filter(chain => 
      !walletInfo[chain] || !privateKeys[chain]
    );
    
    if (missingInfo.length > 0) {
      setRegistrationStatus(`Missing wallet or private key for: ${missingInfo.join(', ')}`);
      return;
    }
    
    setIsLoading(true);
    setRegistrationStatus('Registering your identity across multiple blockchains...');
    setPlatformStatus({});
    
    try {
      // Prepare data for multi-chain registration
      const base64Image = capturedImage.replace('data:image/jpeg;base64,', '');
      
      const response = await axios.post('/api/multi-chain-register', {
        face_image: base64Image,
        platforms: selectedChains,
        wallet_addresses: selectedChains.map(chain => walletInfo[chain]),
        private_keys: selectedChains.map(chain => privateKeys[chain])
      });
      
      if (response.data.success) {
        setRegistrationStatus('Registration successful across selected blockchains!');
        
        // Update status for each platform
        const results = response.data.registration_results;
        const status = {};
        
        for (const [platform, result] of Object.entries(results)) {
          status[platform] = {
            success: result.success,
            message: result.success 
              ? `Registered (TX: ${result.transaction_hash.substring(0, 10)}...)` 
              : `Failed: ${result.error}`
          };
        }
        
        setPlatformStatus(status);
        
        // Store the protected template (in a real app, this would be securely stored)
        localStorage.setItem('protectedTemplate', JSON.stringify(response.data.protected_template));
      } else {
        setRegistrationStatus(`Registration failed: ${response.data.error}`);
      }
    } catch (error) {
      console.error("Registration error:", error);
      setRegistrationStatus('Error during registration. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleLivenessVerified = (verified) => {
    setLivenessVerified(verified);
    if (verified) {
      startCapture();
    }
  };
  
  return (
    <div className="multi-chain-registration">
      <h2>Multi-Chain Identity Registration</h2>
      
      <div className="chain-selection">
        <h3>Select Blockchains</h3>
        <div className="chain-options">
          <label>
            <input 
              type="checkbox" 
              checked={selectedChains.includes('ethereum')} 
              onChange={() => handleChainSelection('ethereum')}
              disabled={isLoading}
            />
            Ethereum {walletInfo.ethereum ? '✓' : ''}
          </label>
          
          <label>
            <input 
              type="checkbox" 
              checked={selectedChains.includes('polygon')} 
              onChange={() => handleChainSelection('polygon')}
              disabled={isLoading}
            />
            Polygon {walletInfo.polygon ? '✓' : ''}
          </label>
          
          <label>
            <input 
              type="checkbox" 
              checked={selectedChains.includes('binance')} 
              onChange={() => handleChainSelection('binance')}
              disabled={isLoading}
            />
            Binance Smart Chain {walletInfo.binance ? '✓' : ''}
          </label>
        </div>
      </div>
      
      <div className="wallet-inputs">
        {selectedChains.map(chain => (
          <div key={chain} className="chain-wallet-info">
            <h4>{chain.charAt(0).toUpperCase() + chain.slice(1)}</h4>
            
            <div className="form-group">
              <label>Wallet Address:</label>
              <input 
                type="text"
                value={walletInfo[chain]}
                onChange={(e) => setWalletInfo({...walletInfo, [chain]: e.target.value})}
                disabled={isLoading}
                placeholder={`${chain} wallet address`}
              />
            </div>
            
            <div className="form-group">
              <label>Private Key (never send to production servers):</label>
              <input 
                type="password"
                value={privateKeys[chain]}
                onChange={(e) => setPrivateKeys({...privateKeys, [chain]: e.target.value})}
                disabled={isLoading}
                placeholder={`${chain} private key`}
              />
            </div>
            
            {platformStatus[chain] && (
              <div className={`platform-status ${platformStatus[chain].success ? 'success' : 'error'}`}>
                {platformStatus[chain].message}
              </div>
            )}
          </div>
        ))}
      </div>
      
      <div className="video-container">
        {!livenessVerified && !isCapturing && !capturedImage && (
          <LivenessChallenge onLivenessVerified={handleLivenessVerified} />
        )}
        
        {isCapturing ? (
          <>
            <video 
              ref={videoRef} 
              autoPlay 
              style={{ width: '100%', maxWidth: '500px' }}
            />
            <button onClick={captureImage} disabled={isLoading}>
              Capture Face
            </button>
          </>
        ) : capturedImage ? (
          <div className="captured-image">
            <img 
              src={capturedImage} 
              alt="Captured face" 
              style={{ width: '100%', maxWidth: '500px' }}
            />
            <button onClick={() => setCapturedImage(null)} disabled={isLoading}>
              Retake
            </button>
          </div>
        ) : null}
        
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
      
      {capturedImage && (
        <button 
          onClick={registerMultiChain}
          disabled={isLoading || selectedChains.length === 0}
          className="register-button"
        >
          {isLoading ? 'Registering...' : 'Register on Selected Blockchains'}
        </button>
      )}
      
      {registrationStatus && (
        <div className="status-message">
          {registrationStatus}
        </div>
      )}
    </div>
  );
};

export default MultiChainRegistration; 