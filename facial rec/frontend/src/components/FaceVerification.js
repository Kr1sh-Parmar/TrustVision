import React, { useState, useRef } from 'react';
import Web3 from 'web3';
import axios from 'axios';

const FaceVerification = () => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [walletAddress, setWalletAddress] = useState('');
  const [verificationStatus, setVerificationStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  
  const connectWallet = async () => {
    if (window.ethereum) {
      try {
        const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
        setWalletAddress(accounts[0]);
      } catch (error) {
        console.error("Error connecting to MetaMask:", error);
        setVerificationStatus('Error connecting to wallet. Please try again.');
      }
    } else {
      setVerificationStatus('MetaMask is not installed. Please install it to use this feature.');
    }
  };
  
  const startCapture = async () => {
    if (!walletAddress) {
      setVerificationStatus('Please connect your wallet first');
      return;
    }
    
    setIsCapturing(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = stream;
    } catch (err) {
      console.error("Error accessing camera:", err);
      setVerificationStatus('Error accessing camera. Please make sure your camera is enabled.');
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
    
    const stream = video.srcObject;
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
    setIsCapturing(false);
  };
  
  const verifyFace = async () => {
    if (!capturedImage || !walletAddress) {
      setVerificationStatus('Please capture an image and connect your wallet first');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Convert base64 image for API
      const base64Image = capturedImage.replace('data:image/jpeg;base64,', '');
      
      // Verify identity
      const response = await axios.post('/api/verify', {
        face_image: base64Image,
        wallet_address: walletAddress,
      });
      
      if (response.data.success) {
        if (response.data.verified) {
          setVerificationStatus('Identity verified successfully! You can proceed with the transaction.');
        } else {
          setVerificationStatus('Identity verification failed. Face does not match registered identity.');
        }
      } else {
        setVerificationStatus(`Verification failed: ${response.data.error}`);
      }
    } catch (error) {
      console.error("Error verifying face:", error);
      setVerificationStatus('Error verifying face. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="face-verification">
      <h2>Verify Your Identity</h2>
      
      <div className="wallet-info">
        {walletAddress ? (
          <p>Connected Wallet: {walletAddress}</p>
        ) : (
          <button onClick={connectWallet}>Connect Wallet</button>
        )}
      </div>
      
      <div className="video-container">
        {isCapturing ? (
          <video 
            ref={videoRef} 
            autoPlay 
            style={{ width: '100%', maxWidth: '500px' }}
          />
        ) : capturedImage ? (
          <img 
            src={capturedImage} 
            alt="Captured face" 
            style={{ width: '100%', maxWidth: '500px' }}
          />
        ) : (
          <div className="placeholder-box">Camera feed will appear here</div>
        )}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
      
      <div className="controls">
        {!isCapturing && !capturedImage && (
          <button onClick={startCapture} disabled={isLoading || !walletAddress}>
            Start Camera
          </button>
        )}
        
        {isCapturing && (
          <button onClick={captureImage} disabled={isLoading}>
            Capture Face
          </button>
        )}
        
        {capturedImage && (
          <>
            <button onClick={() => setCapturedImage(null)} disabled={isLoading}>
              Retake
            </button>
            <button onClick={verifyFace} disabled={isLoading}>
              {isLoading ? 'Verifying...' : 'Verify Identity'}
            </button>
          </>
        )}
      </div>
      
      {verificationStatus && (
        <div className="status-message">
          {verificationStatus}
        </div>
      )}
    </div>
  );
};

export default FaceVerification; 