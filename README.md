# UEBA System - User and Entity Behavior Analytics

A comprehensive User and Entity Behavior Analytics (UEBA) system with machine learning capabilities for detecting suspicious login patterns and potential security threats.

## Features

- **Real-time Risk Scoring**: Advanced risk calculation based on multiple behavioral factors
- **Machine Learning**: Isolation Forest algorithm for anomaly detection
- **Interactive Dashboard**: Web-based dashboard with auto-refresh capabilities
- **Login Simulation**: CLI tool for testing various attack scenarios
- **SQLite Database**: Persistent storage for login attempts and user data

## Risk Detection Capabilities

- **Velocity Analysis**: Detects rapid login attempts
- **Device Switching**: Identifies users switching between multiple devices
- **Network Switching**: Monitors changes in network operators
- **Latency Anomalies**: Detects unusual response times
- **Timing Patterns**: Analyzes request timing patterns
- **Fingerprint Changes**: Monitors device fingerprint consistency
- **Device Spoofing**: Detects suspicious device identifiers
- **Flow Abandonment**: Tracks incomplete login flows

## Installation

1. Clone or download the project files
2. Install required dependencies:
```bash
pip install flask sqlite3 numpy scikit-learn
```

## Usage

### 1. Start the Dashboard
```bash
python dashboard.py
```
Open browser to `http://localhost:5000` to view the real-time dashboard.

### 2. Run Login Simulations
```bash
python login_simulator.py
```

Choose from:
- **Single User Login**: Test individual user scenarios
- **Bulk Testing**: Run predefined attack scenarios

### 3. Direct UEBA System Usage
```python
from ueba_system import UEBASystem

system = UEBASystem()
risk_score, breakdown = system.log_attempt('user1', 1, {
    'device_id': 'DEVICE_123',
    'latency': 150,
    'network_operator': '405854'
})
```

## Test Scenarios

### Normal Users
- Complete login flows with consistent parameters
- Expected risk scores: 0-30

### Bot Attacks
- Rapid attempts with low latency
- Suspicious device identifiers
- Expected risk scores: 70-95

### Device Switchers
- Multiple unique devices in short timeframes
- Expected risk scores: 40-80

### Abandonment Patterns
- Incomplete login flows
- Reconnaissance behavior
- Expected risk scores: 30-60


## File Structure

```
├── dashboard.py          # Flask web dashboard
├── ueba_system.py       # Core UEBA logic and ML
├── login_simulator.py   # Interactive testing tool
├── templates/
│   └── dashboard.html   # Dashboard UI
└── ueba.db             # SQLite database (auto-created)
```

## Machine Learning

The system uses Isolation Forest for unsupervised anomaly detection:
- Automatically trains on existing data
- Retrains every 50 login attempts
- Combines rule-based (70%) and ML-based (30%) scoring
- Requires scikit-learn (optional but recommended)

## Database Schema

### Users Table
- `username`: Unique user identifier
- `phone`: User phone number
- `created_at`: Account creation timestamp

### Login Attempts Table
- `username`: User identifier
- `step`: Login flow step (1-3)
- `device_id`: Device identifier
- `network_operator`: Mobile network operator
- `latency`: Response latency in ms
- `fingerprint`: Device fingerprint
- `ip_address`: Source IP address
- `user_agent`: Browser/app user agent
- `timestamp`: Attempt timestamp
- `success`: Success/failure flag
- `risk_score`: Calculated risk score

## Configuration

Default settings can be modified in `ueba_system.py`:
- Risk score weights
- Time windows for analysis
- ML model parameters
- Database path

## Requirements

- Python 3.7+
- Flask
- SQLite3 (built-in)
- NumPy
- scikit-learn (optional, for ML features)
