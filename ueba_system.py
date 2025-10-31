"""
Simple UEBA System with Database + ML
"""

import sqlite3
import time
import json
from datetime import datetime
import numpy as np
try:
    from sklearn.ensemble import IsolationForest
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("scikit-learn not installed. Run: pip install scikit-learn")
    print("   ML features will be disabled.")


class UEBASystem:
    def __init__(self, db_path='ueba.db'):
        self.db_path = db_path
        self.ml_model = None
        self.init_db()
        self.populate_mock_users()
        if ML_AVAILABLE:
            self.train_ml_model()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            phone TEXT,
            created_at INTEGER
        )''')
        
        # Login attempts table
        c.execute('''CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            step INTEGER,
            device_id TEXT,
            network_operator TEXT,
            latency INTEGER,
            fingerprint TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp INTEGER,
            success BOOLEAN,
            risk_score REAL
        )''')
        
        conn.commit()
        conn.close()
    
    def populate_mock_users(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        users = [
            ('user1', '9990000001'),
            ('user2', '9990000002'),
            ('user3', '9990000003'),
            ('user4', '9990000004'),
            ('user5', '9990000005'),
            ('user6', '9990000006'),
            ('user7', '9990000007'),
            ('user8', '9990000008'),
            ('user9', '9990000009'),
            ('user10', '9990000010'),
            ('user11', '9990000011'),
            ('user12', '9990000012'),
            ('user13', '9990000013'),
            ('user14', '9990000014'),
            ('user15', '9990000015'),
            ('user16', '9990000016'),
            ('user17', '9990000017'),
            ('user18', '9990000018'),
            ('user19', '9990000019'),
            ('user20', '9990000020'),
        ]
        
        for username, phone in users:
            try:
                c.execute('INSERT INTO users (username, phone, created_at) VALUES (?, ?, ?)',
                         (username, phone, int(time.time() * 1000)))
            except:
                pass
        
        conn.commit()
        conn.close()
    
    def calculate_risk_score(self, username, params):
        """Calculate UEBA risk score based on historical data"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = int(time.time() * 1000)
        scores = {}
        
        # 1. Velocity 
        c.execute('''SELECT COUNT(*) FROM login_attempts 
                     WHERE username = ? AND timestamp > ?''',
                  (username, now - 300000))
        attempts_5min = c.fetchone()[0]
        
        if attempts_5min > 10:
            scores['velocity'] = 95
        elif attempts_5min > 5:
            scores['velocity'] = 70
        elif attempts_5min > 3:
            scores['velocity'] = 40
        else:
            scores['velocity'] = 0
        
        # 2. Device switching - unique devices in last 30 minutes
        c.execute('''SELECT COUNT(DISTINCT device_id) FROM login_attempts 
                     WHERE username = ? AND timestamp > ?''',
                  (username, now - 1800000))
        devices_30min = c.fetchone()[0]
        
        if devices_30min > 5:
            scores['device_switching'] = 90
        elif devices_30min > 3:
            scores['device_switching'] = 60
        elif devices_30min > 1:
            scores['device_switching'] = 30
        else:
            scores['device_switching'] = 0
        
        # 3. Network switching - operator changes in last 30 minutes
        c.execute('''SELECT COUNT(DISTINCT network_operator) FROM login_attempts 
                     WHERE username = ? AND timestamp > ? AND network_operator != ''
                  ''', (username, now - 1800000))
        networks_30min = c.fetchone()[0]
        
        if networks_30min > 3:
            scores['network_switching'] = 85
        elif networks_30min > 1:
            scores['network_switching'] = 50
        else:
            scores['network_switching'] = 0
        
        # 4. Latency anomaly - compare with user's average
        c.execute('''SELECT AVG(latency) FROM login_attempts 
                     WHERE username = ? AND latency > 0''', (username,))
        avg_latency = c.fetchone()[0] or 150
        
        current_latency = params.get('latency', 150)
        
        if current_latency < 50:
            scores['latency_anomaly'] = 70
        elif abs(current_latency - avg_latency) > 200:
            scores['latency_anomaly'] = 50
        else:
            scores['latency_anomaly'] = 0
        
        # 5. Request timing - time between last two requests
        c.execute('''SELECT timestamp FROM login_attempts 
                     WHERE username = ? ORDER BY timestamp DESC LIMIT 2''',
                  (username,))
        timestamps = [row[0] for row in c.fetchall()]
        
        if len(timestamps) == 2:
            time_diff = timestamps[0] - timestamps[1]
            if time_diff < 1000:  # Less than 1 second
                scores['timing_pattern'] = 80
            elif time_diff < 5000:  # Less than 5 seconds
                scores['timing_pattern'] = 50
            else:
                scores['timing_pattern'] = 0
        else:
            scores['timing_pattern'] = 0
        
        # 6. Fingerprint consistency
        c.execute('''SELECT fingerprint FROM login_attempts 
                     WHERE username = ? AND fingerprint != '' 
                     ORDER BY timestamp DESC LIMIT 1''', (username,))
        last_fp = c.fetchone()
        
        if last_fp and params.get('fingerprint'):
            if last_fp[0] != params['fingerprint']:
                scores['fingerprint_change'] = 60
            else:
                scores['fingerprint_change'] = 0
        else:
            scores['fingerprint_change'] = 0
        
        # 7. Device ID pattern detection
        device_id = params.get('device_id', '')
        if 'BYPASS' in device_id.upper() or 'TEST' in device_id.upper() or 'EMULATOR' in device_id.upper():
            scores['device_spoofing'] = 85
        else:
            scores['device_spoofing'] = 0
        
        conn.close()
        
        # Calculate weighted total
        weights = {
            'velocity': 0.25,
            'device_switching': 0.20,
            'network_switching': 0.15,
            'latency_anomaly': 0.15,
            'timing_pattern': 0.10,
            'fingerprint_change': 0.10,
            'device_spoofing': 0.05
        }
        
        total = sum(scores[k] * weights[k] for k in scores)
        
        return round(total, 2), scores
    
    def log_attempt(self, username, step, params, success=True):
        """Log login attempt and calculate risk"""
        risk_score, breakdown = self.calculate_risk_score(username, params)
        
        # Get ML risk score if available
        ml_risk = 0
        if ML_AVAILABLE and self.ml_model is not None:
            ml_risk = self.get_ml_risk_score(username, params)
            breakdown['ml_anomaly'] = ml_risk
            
            # Combine rule-based and ML scores (70% rules, 30% ML)
            combined_risk = (risk_score * 0.7) + (ml_risk * 0.3)
            risk_score = round(combined_risk, 2)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''INSERT INTO login_attempts 
                     (username, step, device_id, network_operator, latency, 
                      fingerprint, ip_address, user_agent, timestamp, success, risk_score)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (username, step, params.get('device_id', ''), 
                   params.get('network_operator', ''), params.get('latency', 0),
                   params.get('fingerprint', ''), params.get('ip_address', ''),
                   params.get('user_agent', ''), int(time.time() * 1000), 
                   success, risk_score))
        
        # Retrain ML model periodically (every 50 attempts)
        c.execute('SELECT COUNT(*) FROM login_attempts')
        total = c.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        if ML_AVAILABLE and total % 50 == 0 and total > 0:
            print("\n♻️  Retraining ML model...")
            self.train_ml_model()
        
        return risk_score, breakdown
    
    def get_users(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT username, phone FROM users ORDER BY username')
        users = c.fetchall()
        conn.close()
        return users
    
    def get_ueba_metrics(self):
        """Get all UEBA metrics for dashboard"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = int(time.time() * 1000)
        
        metrics = {}
        
        # Total attempts
        c.execute('SELECT COUNT(*) FROM login_attempts')
        metrics['total_attempts'] = c.fetchone()[0]
        
        # High risk attempts (last hour)
        c.execute('SELECT COUNT(*) FROM login_attempts WHERE risk_score > 70 AND timestamp > ?',
                 (now - 3600000,))
        metrics['high_risk_attempts'] = c.fetchone()[0]
        
        # Unique users (last hour)
        c.execute('SELECT COUNT(DISTINCT username) FROM login_attempts WHERE timestamp > ?',
                 (now - 3600000,))
        metrics['active_users'] = c.fetchone()[0]
        
        # Average risk score
        c.execute('SELECT AVG(risk_score) FROM login_attempts WHERE timestamp > ?',
                 (now - 3600000,))
        metrics['avg_risk_score'] = round(c.fetchone()[0] or 0, 2)
        
        # Recent attempts
        c.execute('''SELECT username, step, device_id, risk_score, timestamp 
                     FROM login_attempts ORDER BY timestamp DESC LIMIT 20''')
        metrics['recent_attempts'] = c.fetchall()
        
        # Top risky users
        c.execute('''SELECT username, AVG(risk_score) as avg_risk, COUNT(*) as attempts
                     FROM login_attempts WHERE timestamp > ?
                     GROUP BY username ORDER BY avg_risk DESC LIMIT 10''',
                  (now - 3600000,))
        metrics['risky_users'] = c.fetchall()
        
        # Device switching stats
        c.execute('''SELECT username, COUNT(DISTINCT device_id) as devices
                     FROM login_attempts WHERE timestamp > ?
                     GROUP BY username HAVING devices > 1
                     ORDER BY devices DESC LIMIT 10''',
                  (now - 1800000,))
        metrics['device_switchers'] = c.fetchall()
        
        # Velocity stats
        c.execute('''SELECT username, COUNT(*) as attempts
                     FROM login_attempts WHERE timestamp > ?
                     GROUP BY username HAVING attempts > 3
                     ORDER BY attempts DESC LIMIT 10''',
                  (now - 300000,))
        metrics['high_velocity'] = c.fetchall()
        
        # Abandonment patterns
        c.execute('''SELECT username, COUNT(*) as abandonments
                     FROM login_attempts WHERE timestamp > ? AND step < 3 AND success = 0
                     GROUP BY username HAVING abandonments > 1
                     ORDER BY abandonments DESC LIMIT 10''',
                  (now - 3600000,))
        metrics['abandonment_patterns'] = c.fetchall()
        
        conn.close()
        return metrics
    
    def check_abandonment(self, username, last_step):
        """Check for flow abandonment and calculate additional risk"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = int(time.time() * 1000)
        
        # Check if user has pattern of abandoning flows
        c.execute('''SELECT COUNT(*) FROM login_attempts 
                     WHERE username = ? AND timestamp > ? AND step < 3 AND success = 0''',
                  (username, now - 3600000))
        abandonment_count = c.fetchone()[0]
        
        conn.close()
        
        # Stackable abandonment risk 
        if last_step == 1:
            base_risk = 12  # Abandoned at step 1
        elif last_step == 2:
            base_risk = 18  # Abandoned at step 2
        else:
            base_risk = 0
        

        if abandonment_count > 5:
            base_risk += 15  # Consistent pattern
        elif abandonment_count > 3:
            base_risk += 10  # Multiple abandonments
        elif abandonment_count > 1:
            base_risk += 6   # Starting to show pattern
        
        return base_risk
    
    def train_ml_model(self):
        """Train Isolation Forest on existing data"""
        if not ML_AVAILABLE:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get training data
        c.execute('''SELECT latency, risk_score, step,
                     (SELECT COUNT(*) FROM login_attempts l2 
                      WHERE l2.username = l1.username AND l2.timestamp > l1.timestamp - 300000) as velocity,
                     (SELECT COUNT(DISTINCT device_id) FROM login_attempts l3
                      WHERE l3.username = l1.username AND l3.timestamp > l1.timestamp - 1800000) as device_count
                     FROM login_attempts l1
                     WHERE latency > 0''')
        
        data = c.fetchall()
        conn.close()
        
        if len(data) < 10:
            print("   Not enough data for ML training (need 10+ samples)")
            return
        
        # Prepare features
        X = np.array(data)
        
        # Train Isolation Forest
        self.ml_model = IsolationForest(
            contamination=0.15,  # Expect 15% anomalies
            random_state=42,
            n_estimators=100
        )
        self.ml_model.fit(X)
        
        print(f"ML model trained on {len(data)} samples")
    
    def get_ml_risk_score(self, username, params):
        """Get ML-based anomaly score"""
        if not ML_AVAILABLE or self.ml_model is None:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = int(time.time() * 1000)
        
        # Calculate velocity
        c.execute('''SELECT COUNT(*) FROM login_attempts 
                     WHERE username = ? AND timestamp > ?''',
                  (username, now - 300000))
        velocity = c.fetchone()[0]
        
        # Calculate device count
        c.execute('''SELECT COUNT(DISTINCT device_id) FROM login_attempts 
                     WHERE username = ? AND timestamp > ?''',
                  (username, now - 1800000))
        device_count = c.fetchone()[0]
        
        conn.close()
        
        # Prepare features
        features = [[
            params.get('latency', 150),
            self.calculate_risk_score(username, params)[0],
            params.get('step', 1),
            velocity,
            device_count
        ]]
        
        # Get prediction
        prediction = self.ml_model.predict(features)[0]
        anomaly_score = self.ml_model.score_samples(features)[0]
        
        # Convert to 0-100 risk scale
        ml_risk = max(0, min(100, (-anomaly_score) * 100))
        
        return round(ml_risk, 2)


if __name__ == "__main__":
    system = UEBASystem()
    print("initialized with mock users")
