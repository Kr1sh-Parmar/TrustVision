import cv2
import numpy as np
import dlib
import time
from collections import deque
import random

class LivenessDetector:
    def __init__(self):
        # Initialize face detector and landmark predictor
        self.face_detector = dlib.get_frontal_face_detector()
        # Path may need to be adjusted based on your installation
        self.landmark_predictor = dlib.shape_predictor('models/shape_predictor_68_face_landmarks.dat')
        
        # For blink detection
        self.eye_ar_thresh = 0.2
        self.eye_ar_consec_frames = 3
        self.counter = 0
        self.total_blinks = 0
        self.blink_history = deque(maxlen=10)
        
        # For head movement detection
        self.prev_landmarks = None
        self.movement_threshold = 5.0
        self.movement_history = deque(maxlen=10)
        
        # For texture analysis (to detect printed photos)
        self.lbp_threshold = 0.5
        
        # For random challenge generation
        self.challenge_types = ["blink", "nod", "turn_left", "turn_right"]
        self.current_challenge = None
        self.challenge_completed = False
        self.challenge_start_time = None
        self.challenge_timeout = 5  # 5 seconds to complete challenge
    
    def eye_aspect_ratio(self, eye_landmarks):
        """Calculate eye aspect ratio to detect blinks"""
        # Compute euclidean distances between two sets of vertical eye landmarks
        A = np.linalg.norm(eye_landmarks[1] - eye_landmarks[5])
        B = np.linalg.norm(eye_landmarks[2] - eye_landmarks[4])
        
        # Compute the euclidean distance between horizontal eye landmarks
        C = np.linalg.norm(eye_landmarks[0] - eye_landmarks[3])
        
        # Compute the eye aspect ratio
        ear = (A + B) / (2.0 * C)
        return ear
    
    def get_face_landmarks(self, frame):
        """Extract the 68 facial landmarks from a face image"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector(gray)
        
        if len(faces) == 0:
            return None
        
        # Get the largest face
        largest_face = max(faces, key=lambda rect: rect.width() * rect.height())
        
        # Get facial landmarks
        landmarks = self.landmark_predictor(gray, largest_face)
        landmarks_points = []
        
        for i in range(68):
            x = landmarks.part(i).x
            y = landmarks.part(i).y
            landmarks_points.append(np.array([x, y]))
            
        return np.array(landmarks_points)
    
    def detect_blink(self, landmarks):
        """Detect if the person blinked"""
        if landmarks is None:
            return False
        
        # Extract left and right eye landmarks
        left_eye = landmarks[42:48]
        right_eye = landmarks[36:42]
        
        # Calculate eye aspect ratios
        left_ear = self.eye_aspect_ratio(left_eye)
        right_ear = self.eye_aspect_ratio(right_eye)
        
        # Average the eye aspect ratio for both eyes
        ear = (left_ear + right_ear) / 2.0
        
        # Check if eye aspect ratio is below threshold (blink)
        if ear < self.eye_ar_thresh:
            self.counter += 1
        else:
            if self.counter >= self.eye_ar_consec_frames:
                self.total_blinks += 1
                self.blink_history.append(time.time())
                self.counter = 0
                return True
            self.counter = 0
        
        return False
    
    def detect_head_movement(self, landmarks):
        """Detect head movement between frames"""
        if landmarks is None or self.prev_landmarks is None:
            self.prev_landmarks = landmarks
            return False
        
        # Calculate the average movement of facial landmarks
        movement = np.mean(np.linalg.norm(landmarks - self.prev_landmarks, axis=1))
        self.prev_landmarks = landmarks
        
        # Record significant movements
        if movement > self.movement_threshold:
            self.movement_history.append(time.time())
            return True
        
        return False
    
    def detect_texture(self, frame):
        """Detect if the image is a printed photo by analyzing texture patterns"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply local binary pattern or other texture descriptor
        # Simplified version - in a real system, use a proper LBP implementation
        edges = cv2.Canny(blur, 100, 200)
        edge_density = np.sum(edges) / (frame.shape[0] * frame.shape[1])
        
        # Lower edge density often indicates a printed photo
        return edge_density > self.lbp_threshold
    
    def generate_challenge(self):
        """Generate a random liveness challenge for the user"""
        self.current_challenge = random.choice(self.challenge_types)
        self.challenge_completed = False
        self.challenge_start_time = time.time()
        return self.current_challenge
    
    def check_challenge_completion(self, frame):
        """Check if the user completed the challenge"""
        if self.current_challenge is None:
            return False
        
        landmarks = self.get_face_landmarks(frame)
        
        if landmarks is None:
            return False
        
        # Check if the challenge timed out
        if time.time() - self.challenge_start_time > self.challenge_timeout:
            self.current_challenge = None
            return False
        
        # Check if challenge was completed based on type
        if self.current_challenge == "blink":
            if self.detect_blink(landmarks):
                self.challenge_completed = True
                self.current_challenge = None
                return True
                
        elif self.current_challenge == "nod":
            # Detect vertical head movement
            if landmarks is not None and self.prev_landmarks is not None:
                vertical_movement = np.mean(landmarks[:, 1] - self.prev_landmarks[:, 1])
                if abs(vertical_movement) > 10:  # Threshold for nodding detection
                    self.challenge_completed = True
                    self.current_challenge = None
                    return True
                    
        elif self.current_challenge == "turn_left" or self.current_challenge == "turn_right":
            # Detect horizontal head movement
            if landmarks is not None and self.prev_landmarks is not None:
                horizontal_movement = np.mean(landmarks[:, 0] - self.prev_landmarks[:, 0])
                if (self.current_challenge == "turn_left" and horizontal_movement < -10) or \
                   (self.current_challenge == "turn_right" and horizontal_movement > 10):
                    self.challenge_completed = True
                    self.current_challenge = None
                    return True
        
        self.prev_landmarks = landmarks
        return False
    
    def check_liveness(self, frame, perform_challenge=True):
        """Comprehensive liveness detection"""
        # Extract facial landmarks
        landmarks = self.get_face_landmarks(frame)
        
        if landmarks is None:
            return False, "No face detected"
        
        # Check for natural eye blinks
        blink_detected = self.detect_blink(landmarks)
        
        # Check for natural head movements
        movement_detected = self.detect_head_movement(landmarks)
        
        # Check image texture to detect printed photos
        real_texture = self.detect_texture(frame)
        
        # If challenge mode is enabled, generate and verify challenge
        if perform_challenge:
            if self.current_challenge is None:
                challenge = self.generate_challenge()
                return False, f"Please {challenge.replace('_', ' ')} to verify liveness"
            
            challenge_passed = self.check_challenge_completion(frame)
            if challenge_passed:
                return True, "Challenge passed, liveness confirmed"
            else:
                return False, f"Complete the challenge: {self.current_challenge.replace('_', ' ')}"
        
        # Basic liveness check - has the person blinked and moved their head naturally?
        if len(self.blink_history) > 2 and len(self.movement_history) > 2 and real_texture:
            return True, "Liveness confirmed"
        
        return False, "Liveness check ongoing, please move naturally and blink" 