import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

const LivenessChallenge = ({ onLivenessVerified }) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [challenge, setChallenge] = useState(null);
  const [challengeStatus, setChallengeStatus] = useState('');
  const [isVerified, setIsVerified] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  
  useEffect(() => {
    // Cleanup function to stop video when component unmounts
    return () => {
      if (streamRef.current) {
        const tracks = streamRef.current.getTracks();
        tracks.forEach(track => track.stop());
      }
    };
  }, []);
  
  const startLivenessCheck = async () => {
    setIsCapturing(true);
    setChallengeStatus('Starting liveness check...');
    
    try {
      // Start camera
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = stream;
      streamRef.current = stream;
      
      // Start the challenge loop
      requestChallenge();
    } catch (err) {
      console.error("Error accessing camera:", err);
      setChallengeStatus('Error accessing camera. Please make sure your camera is enabled.');
      setIsCapturing(false);
    }
  };
  
  const captureFrame = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    return canvas.toDataURL('image/jpeg');
  };
  
  const requestChallenge = async () => {
    if (!isCapturing) return;
    
    try {
      const frameDataUrl = captureFrame();
      const base64Image = frameDataUrl.replace('data:image/jpeg;base64,', '');
      
      const response = await axios.post('/api/liveness-challenge', {
        face_image: base64Image
      });
      
      if (response.data.success) {
        if (response.data.is_live) {
          // Liveness verified!
          setChallengeStatus('Liveness verified! You are a real person.');
          setIsVerified(true);
          
          // Stop the video stream
          const tracks = streamRef.current.getTracks();
          tracks.forEach(track => track.stop());
          setIsCapturing(false);
          
          // Notify parent component
          if (onLivenessVerified) {
            onLivenessVerified(true);
          }
        } else {
          // Challenge in progress
          setChallenge(response.data.challenge);
          setChallengeStatus(`Please ${response.data.challenge.replace('_', ' ')} to verify liveness`);
          
          // Continue checking for challenge completion
          setTimeout(requestChallenge, 500);
        }
      } else {
        setChallengeStatus(`Error: ${response.data.error}`);
        setTimeout(requestChallenge, 1000);
      }
    } catch (error) {
      console.error("Error during liveness check:", error);
      setChallengeStatus('Connection error. Retrying...');
      setTimeout(requestChallenge, 2000);
    }
  };
  
  return (
    <div className="liveness-challenge">
      <h3>Liveness Verification</h3>
      
      <div className="video-container">
        {isCapturing ? (
          <video 
            ref={videoRef} 
            autoPlay 
            style={{ width: '100%', maxWidth: '500px' }}
          />
        ) : (
          <div className="placeholder-box">Camera will appear here</div>
        )}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
      
      <div className="challenge-status">
        {challengeStatus && (
          <div className={`status-message ${isVerified ? 'success' : ''}`}>
            {challengeStatus}
          </div>
        )}
      </div>
      
      <div className="controls">
        {!isCapturing && !isVerified ? (
          <button onClick={startLivenessCheck}>
            Start Liveness Check
          </button>
        ) : isVerified ? (
          <button className="success-button" disabled>
            Verification Complete ✓
          </button>
        ) : null}
      </div>
    </div>
  );
};

export default LivenessChallenge; 