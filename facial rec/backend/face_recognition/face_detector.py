import cv2
import numpy as np
from deepface import DeepFace
import time
from .liveness_detection import LivenessDetector

class FaceAuthenticator:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.model_name = "VGG-Face"  # Options: "VGG-Face", "Facenet", "OpenFace", "DeepFace", "ArcFace"
        self.liveness_detector = LivenessDetector()
        
    def detect_face(self, frame):
        """Detect faces in frame and return the largest face region"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return None
        
        # Find largest face
        largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
        x, y, w, h = largest_face
        
        return frame[y:y+h, x:x+w]
    
    def check_liveness(self, face_img, perform_challenge=True):
        """Enhanced liveness detection using the advanced detector"""
        if face_img is None:
            return False
            
        is_live, message = self.liveness_detector.check_liveness(face_img, perform_challenge)
        return is_live
        
    def get_liveness_challenge(self):
        """Get the current liveness challenge"""
        return self.liveness_detector.current_challenge
    
    def generate_face_embedding(self, face_img):
        """Generate facial embedding using DeepFace"""
        if face_img is None:
            return None
            
        try:
            embedding = DeepFace.represent(face_img, model_name=self.model_name)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def verify_identity(self, face_img, stored_embedding):
        """Verify if the captured face matches the stored embedding"""
        if face_img is None:
            return False
            
        new_embedding = self.generate_face_embedding(face_img)
        if new_embedding is None:
            return False
            
        # In a production system, you'd use a proper distance metric 
        # and threshold for verification
        result = DeepFace.verify(new_embedding, stored_embedding, 
                                model_name=self.model_name)
        
        return result["verified"]
        
    def face_hash(self, embedding):
        """Generate a hash of the face embedding that can be stored on blockchain"""
        import hashlib
        
        # Convert embedding to bytes and create a SHA-256 hash
        embedding_bytes = str(embedding).encode('utf-8')
        embedding_hash = hashlib.sha256(embedding_bytes).hexdigest()
        
        return embedding_hash 