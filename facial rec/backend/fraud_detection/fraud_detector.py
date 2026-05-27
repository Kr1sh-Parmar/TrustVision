import numpy as np
import pandas as pd
import time
from collections import defaultdict, deque
import joblib
from sklearn.ensemble import IsolationForest
import tensorflow as tf
from ..face_recognition.face_detector import FaceAuthenticator

class FraudDetector:
    def __init__(self):
        # Initialize the anomaly detection model
        self.model = IsolationForest(
            n_estimators=100,
            max_samples='auto',
            contamination=0.1,
            random_state=42
        )
        
        # Store user behavior patterns
        self.user_behaviors = defaultdict(lambda: {
            'login_times': deque(maxlen=20),
            'login_locations': deque(maxlen=20),
            'transaction_amounts': deque(maxlen=20),
            'devices': deque(maxlen=10),
            'failed_attempts': deque(maxlen=10),
            'ip_addresses': deque(maxlen=10)
        })
        
        # Activity logging
        self.recent_activities = deque(maxlen=1000)
        
        # Face verification history
        self.verification_history = defaultdict(lambda: deque(maxlen=20))
        
        # Load model or train a new one
        try:
            self.load_model()
        except:
            print("No pre-trained model found. A new model will be trained on first data.")
    
    def load_model(self, path="models/fraud_detection_model.pkl"):
        """Load a pre-trained anomaly detection model"""
        self.model = joblib.load(path)
        
    def save_model(self, path="models/fraud_detection_model.pkl"):
        """Save the trained model"""
        joblib.dump(self.model, path)
    
    def record_activity(self, user_id, activity_data):
        """Record user activity for behavioral analysis"""
        # Add timestamp
        activity_data['timestamp'] = time.time()
        activity_data['user_id'] = user_id
        
        # Update user behavior records
        behaviors = self.user_behaviors[user_id]
        
        if 'login_time' in activity_data:
            behaviors['login_times'].append(activity_data['login_time'])
            
        if 'location' in activity_data:
            behaviors['login_locations'].append(activity_data['location'])
            
        if 'transaction_amount' in activity_data:
            behaviors['transaction_amounts'].append(activity_data['transaction_amount'])
            
        if 'device' in activity_data:
            behaviors['devices'].append(activity_data['device'])
            
        if 'ip_address' in activity_data:
            behaviors['ip_addresses'].append(activity_data['ip_address'])
            
        if activity_data.get('failed', False):
            behaviors['failed_attempts'].append(activity_data['timestamp'])
        
        # Add to recent activities
        self.recent_activities.append(activity_data)
        
        # Return True so we can chain method calls
        return True
    
    def record_verification(self, user_id, verification_data):
        """Record face verification results"""
        verification_data['timestamp'] = time.time()
        self.verification_history[user_id].append(verification_data)
        return True
    
    def extract_features(self, user_id):
        """Extract behavioral features for anomaly detection"""
        behaviors = self.user_behaviors[user_id]
        
        # If we don't have enough data, return None
        if len(behaviors['login_times']) < 3:
            return None
            
        features = {}
        
        # Time-based features
        if behaviors['login_times']:
            login_times = list(behaviors['login_times'])
            # Convert to hour of day
            hours = [time.localtime(t).tm_hour for t in login_times]
            features['avg_login_hour'] = np.mean(hours)
            features['std_login_hour'] = np.std(hours)
            
            # Day of week
            days = [time.localtime(t).tm_wday for t in login_times]
            features['avg_login_day'] = np.mean(days)
            
        # Transaction amount features
        if behaviors['transaction_amounts']:
            amounts = list(behaviors['transaction_amounts'])
            features['avg_transaction'] = np.mean(amounts)
            features['max_transaction'] = max(amounts)
            features['min_transaction'] = min(amounts)
            features['std_transaction'] = np.std(amounts)
            
        # Device diversity
        if behaviors['devices']:
            features['device_count'] = len(set(behaviors['devices']))
            
        # IP diversity
        if behaviors['ip_addresses']:
            features['ip_count'] = len(set(behaviors['ip_addresses']))
            
        # Failed attempts
        features['recent_failures'] = len(behaviors['failed_attempts'])
        
        # Verification history
        if user_id in self.verification_history:
            verifications = list(self.verification_history[user_id])
            if verifications:
                # Calculate ratio of successful verifications
                success_count = sum(1 for v in verifications if v.get('success', False))
                features['verification_success_ratio'] = success_count / len(verifications)
        
        return features
    
    def train_model(self):
        """Train the anomaly detection model using collected user behaviors"""
        # Extract features for all users
        feature_rows = []
        for user_id, behaviors in self.user_behaviors.items():
            features = self.extract_features(user_id)
            if features:
                # Add user_id for reference
                features['user_id'] = user_id
                feature_rows.append(features)
        
        if not feature_rows:
            print("Not enough data to train model")
            return False
            
        # Convert to DataFrame
        df = pd.DataFrame(feature_rows)
        
        # Remove user_id before training
        user_ids = df['user_id']
        df = df.drop('user_id', axis=1)
        
        # Train the model
        self.model.fit(df)
        
        # Save the trained model
        self.save_model()
        
        return True
    
    def detect_anomalies(self, user_id, transaction_data=None):
        """Detect anomalous behavior for a user"""
        # Extract features for the user
        features = self.extract_features(user_id)
        
        if not features:
            # Not enough data to detect anomalies
            return {
                'is_fraud': False,
                'confidence': 0,
                'reason': "Insufficient data for anomaly detection"
            }
            
        # Add transaction data if provided
        if transaction_data:
            for key, value in transaction_data.items():
                features[key] = value
                
        # Convert to DataFrame
        df = pd.DataFrame([features])
        
        # Predict anomaly
        prediction = self.model.predict(df)
        # Get decision function (distance from separator)
        scores = self.model.decision_function(df)
        
        # In isolation forest, negative scores are anomalies
        is_anomaly = prediction[0] == -1
        
        # Convert score to confidence (0-1)
        # Lower scores are more anomalous in isolation forest
        confidence = 1 - (1 / (1 + np.exp(-scores[0])))
        
        # Find reason for anomaly
        reason = "Normal behavior"
        if is_anomaly:
            # Check common fraud patterns
            behaviors = self.user_behaviors[user_id]
            
            if len(behaviors['failed_attempts']) > 3:
                reason = "Multiple failed login attempts"
                
            elif transaction_data and 'transaction_amount' in transaction_data:
                amounts = list(behaviors['transaction_amounts'])
                if amounts and transaction_data['transaction_amount'] > 2 * max(amounts):
                    reason = "Unusually large transaction"
                    
            elif len(behaviors['devices']) > 3:
                reason = "Multiple devices used recently"
                
            elif len(behaviors['ip_addresses']) > 3:
                reason = "Multiple IP addresses used recently"
                
            else:
                reason = "Unusual activity pattern detected"
        
        return {
            'is_fraud': is_anomaly,
            'confidence': float(confidence),
            'reason': reason
        }
    
    def verify_transaction_security(self, user_id, transaction_data, verification_result):
        """Comprehensive security check for a transaction including face verification and behavior"""
        # Record verification result
        self.record_verification(user_id, {
            'success': verification_result,
            'transaction_id': transaction_data.get('transaction_id', None)
        })
        
        # If face verification failed, immediately flag as potentially fraudulent
        if not verification_result:
            return {
                'is_secure': False,
                'confidence': 0.9,
                'reason': "Face verification failed"
            }
            
        # Check for behavioral anomalies
        anomaly_result = self.detect_anomalies(user_id, transaction_data)
        
        # Return combined result
        return {
            'is_secure': not anomaly_result['is_fraud'],
            'confidence': anomaly_result['confidence'],
            'reason': anomaly_result['reason']
        } 