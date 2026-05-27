import React, { useState, useRef, useEffect } from 'react';
import Web3 from 'web3';
import axios from 'axios';
import LivenessChallenge from './LivenessChallenge';

const FaceRegistration = () => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [walletAddress, setWalletAddress] = useState('');
  const [registrationStatus, setRegistrationStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [livenessVerified, setLivenessVerified] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  
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
      setRegistrationStatus('MetaMask is not installed. Please install it to use this feature.');
    }
  }, []);
  
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
    
    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to base64 image
    const imageDataUrl = canvas.toDataURL('image/jpeg');
    setCapturedImage(imageDataUrl);
    
    // Stop the video stream
    const stream = video.srcObject;
    const tracks = stream.getTracks();
    tracks.forEach(track => track.stop());
    setIsCapturing(false);
  };
  
  const registerFace = async () => {
    if (!capturedImage || !walletAddress) {
      setRegistrationStatus('Please capture an image and connect your wallet first');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Get private key from MetaMask
      // Note: In a production environment, you should NEVER send private keys to a server
      // This is just for demonstration - in reality, you would sign the transaction client-side
      const privateKey = await window.ethereum.request({
        method: 'eth_private_key', // This is not a real MetaMask method, just for demonstration
      });
      
      // Convert base64 image for API
      const base64Image = capturedImage.replace('data:image/jpeg;base64,', '');
      
      // Register identity
      const response = await axios.post('/api/register', {
        face_image: base64Image,
        wallet_address: walletAddress,
        private_key: privateKey,
      });
      
      if (response.data.success) {
        setRegistrationStatus('Face registered successfully!');
      } else {
        setRegistrationStatus(`Registration failed: ${response.data.error}`);
      }
    } catch (error) {
      console.error("Error registering face:", error);
      setRegistrationStatus('Error registering face. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="face-registration">
      <h2>Register Your Face</h2>
      
      <div className="wallet-info">
        <p>Connected Wallet: {walletAddress || 'Not Connected'}</p>
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
          <LivenessChallenge 
            onLivenessVerified={(verified) => {
              setLivenessVerified(verified);
              if (verified) {
                startCapture();
              }
            }} 
          />
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
            <button onClick={registerFace} disabled={isLoading || !walletAddress}>
              {isLoading ? 'Registering...' : 'Register Face'}
            </button>
          </>
        )}
      </div>
      
      {registrationStatus && (
        <div className="status-message">
          {registrationStatus}
        </div>
      )}
    </div>
  );
};

export default FaceRegistration; 