"""
Flask Web Dashboard for UEBA Metrics
"""

from flask import Flask, render_template, jsonify
from ueba_system import UEBASystem
from datetime import datetime

app = Flask(__name__)
system = UEBASystem()


@app.route('/')
def dashboard():
    return render_template('dashboard.html')


@app.route('/api/metrics')
def get_metrics():
    """API endpoint for dashboard metrics"""
    metrics = system.get_ueba_metrics()
    
    # Format recent attempts
    formatted_attempts = []
    for username, step, device_id, risk_score, timestamp in metrics['recent_attempts']:
        formatted_attempts.append({
            'username': username,
            'step': step,
            'device_id': device_id[:20] + '...' if len(device_id) > 20 else device_id,
            'risk_score': round(risk_score, 1),
            'timestamp': datetime.fromtimestamp(timestamp/1000).strftime('%H:%M:%S'),
            'risk_class': 'critical' if risk_score >= 80 else 'high' if risk_score >= 60 else 'medium' if risk_score >= 40 else 'low'
        })
    
    # Format risky users
    formatted_risky = []
    for username, avg_risk, attempts in metrics['risky_users']:
        formatted_risky.append({
            'username': username,
            'avg_risk': round(avg_risk, 1),
            'attempts': attempts
        })
    
    # Format device switchers
    formatted_switchers = []
    for username, devices in metrics['device_switchers']:
        formatted_switchers.append({
            'username': username,
            'devices': devices
        })
    
    # Format high velocity
    formatted_velocity = []
    for username, attempts in metrics['high_velocity']:
        formatted_velocity.append({
            'username': username,
            'attempts': attempts
        })
    
    # Format abandonment patterns
    formatted_abandonment = []
    for username, abandonments in metrics['abandonment_patterns']:
        formatted_abandonment.append({
            'username': username,
            'abandonments': abandonments
        })
    
    # Check ML status
    ml_enabled = system.ml_model is not None
    
    return jsonify({
        'total_attempts': metrics['total_attempts'],
        'high_risk_attempts': metrics['high_risk_attempts'],
        'active_users': metrics['active_users'],
        'avg_risk_score': metrics['avg_risk_score'],
        'ml_enabled': ml_enabled,
        'recent_attempts': formatted_attempts,
        'risky_users': formatted_risky,
        'device_switchers': formatted_switchers,
        'high_velocity': formatted_velocity,
        'abandonment_patterns': formatted_abandonment
    })


if __name__ == '__main__':
    print("="*80)
    print("UEBA Dashboard Starting...")
    print("="*80)
    print("\n🌐 Open browser: http://localhost:5000")
    print("🔄 Auto-refresh: Every 3 seconds")
    print("\n")
    app.run(debug=True, host='0.0.0.0', port=5000)
