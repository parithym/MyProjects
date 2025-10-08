from flask import Flask, render_template, jsonify, request
import requests
import json
from datetime import datetime, timedelta
from twilio.rest import Client

app = Flask(__name__)

# --- CONFIGURATION ---
# Your Firebase URL
FIREBASE_URL = "https://hca-project-172337-default-rtdb.asia-southeast1.firebasedatabase.app"

# Your Twilio credentials
# IMPORTANT: Replace these with your actual credentials
TWILIO_ACCOUNT_SID = "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_PHONE_NUMBER = "whatsapp:+14155238886"  # Example for WhatsApp, use regular number for SMS

# Initialize Twilio Client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# --- HELPER FUNCTIONS ---
def get_firebase_data(path):
    """Fetch data from Firebase"""
    try:
        response = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=10, verify=False)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Error fetching Firebase data: {e}")
        return None

def send_twilio_message(to_number, message_body): 
    """Sends a message via Twilio."""
    try:
        # NOTE: You can change the 'from_' number based on the channel (SMS, WhatsApp, etc.)
        # For SMS, use your Twilio phone number: from_='+15017122661'
        # For WhatsApp, use the Twilio sandbox number: from_='whatsapp:+14155238886'
        message = twilio_client.messages.create(
            to=to_number,
            from_=TWILIO_PHONE_NUMBER,
            body=message_body
        )
        print(f"Message sent successfully. SID: {message.sid}")
    except Exception as e:
        print(f"Failed to send Twilio message: {e}")

def check_vitals_and_alert(patient_id, latest_vitals, recipient_number="whatsapp:+919876543210"):
    """
    Checks vital signs against thresholds and sends an alert if exceeded.
    IMPORTANT: Replace 'recipient_number' with the actual number to receive alerts.
    """
    if not latest_vitals:
        return

    alerts = []
    
    # Define thresholds
    HEART_RATE_MAX = 120
    BLOOD_PRESSURE_SYSTOLIC_MAX = 140
    BLOOD_PRESSURE_DIASTOLIC_MAX = 90
    TEMPERATURE_MAX = 38.0
    OXYGEN_SATURATION_MIN = 92.0
    
    # Check vital signs against thresholds
    if latest_vitals.get('heart_rate', 0) > HEART_RATE_MAX:
        alerts.append(f"Heart Rate ({latest_vitals['heart_rate']} bpm) is too high.")
    if latest_vitals.get('blood_pressure_systolic', 0) > BLOOD_PRESSURE_SYSTOLIC_MAX:
        alerts.append(f"Blood Pressure Systolic ({latest_vitals['blood_pressure_systolic']}) is too high.")
    if latest_vitals.get('blood_pressure_diastolic', 0) > BLOOD_PRESSURE_DIASTOLIC_MAX:
        alerts.append(f"Blood Pressure Diastolic ({latest_vitals['blood_pressure_diastolic']}) is too high.")
    if latest_vitals.get('temperature', 0) > TEMPERATURE_MAX:
        alerts.append(f"Temperature ({latest_vitals['temperature']} °C) is too high.")
    if latest_vitals.get('oxygen_saturation', 100) < OXYGEN_SATURATION_MIN:
        alerts.append(f"Oxygen Saturation ({latest_vitals['oxygen_saturation']}%) is too low.")
        
    if alerts:
        alert_message = f"CRITICAL ALERT for Patient {patient_id}:\n" + "\n".join(alerts)
        print(alert_message)
        send_twilio_message(recipient_number, alert_message)
    else:
        print("Vitals are within normal range. No alert sent.")


# --- FLASK ROUTES ---
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/patients')
def get_patients():
    """Get list of patients"""
    patients_data = get_firebase_data('patients') or {}
    patients = []
    
    for patient_id, patient_info in patients_data.items():
        # Get latest vitals
        vitals = patient_info.get('vitals', {})
        latest_vital = None
        if vitals:
            latest_timestamp = sorted(vitals.keys())[-1]
            latest_vital = vitals[latest_timestamp]
        
        # Get alerts
        alerts = patient_info.get('alerts', {})
        active_alerts = [alert for alert in alerts.values() if not alert.get('resolved', False)]
        
        patients.append({
            'id': patient_id,
            'latest_vital': latest_vital,
            'alert_count': len(active_alerts),
            'has_critical_alerts': any('CRITICAL' in str(alert.get('alerts', [])) for alert in active_alerts)
        })
    
    return jsonify(patients)

@app.route('/api/patient/<patient_id>')
def get_patient_details(patient_id):
    """Get detailed patient information and check vitals for alerts"""
    patient_data = get_firebase_data(f'patients/{patient_id}') or {}
    
    # Process vitals data for charts
    vitals = patient_data.get('vitals', {})
    chart_data = {
        'timestamps': [],
        'heart_rate': [],
        'blood_pressure_systolic': [],
        'blood_pressure_diastolic': [],
        'temperature': [],
        'oxygen_saturation': []
    }
    
    # Sort timestamps to ensure charts are chronological
    sorted_vitals = sorted(vitals.items())
    for timestamp, data in sorted_vitals:
        chart_data['timestamps'].append(datetime.fromtimestamp(int(timestamp)/1000).strftime('%H:%M'))
        
        # Check if the key exists before appending to avoid errors
        chart_data['heart_rate'].append(data.get('heart_rate'))
        chart_data['blood_pressure_systolic'].append(data.get('blood_pressure_systolic'))
        chart_data['blood_pressure_diastolic'].append(data.get('blood_pressure_diastolic'))
        chart_data['temperature'].append(data.get('temperature'))
        chart_data['oxygen_saturation'].append(data.get('oxygen_saturation'))
    
    # Get latest vital for alert check
    latest_vital = sorted_vitals[-1][1] if sorted_vitals else None
    
    # Trigger the vital check and alert function
    if latest_vital:
        # You will need to replace the recipient number with a real phone number
        check_vitals_and_alert(patient_id, latest_vital, "whatsapp:+919876543210")
    
    # Get alerts
    alerts = patient_data.get('alerts', {})
    active_alerts = []
    for alert_id, alert in alerts.items():
        if not alert.get('resolved', False):
            active_alerts.append({
                'id': alert_id,
                'timestamp': alert.get('timestamp'),
                'alerts': alert.get('alerts', []),
                'priority': alert.get('priority', 'MEDIUM')
            })
    
    return jsonify({
        'name': patient_data.get('name', 'N/A'),
        'vitals': vitals,
        'chart_data': chart_data,
        'alerts': active_alerts,
        'latest_vital': latest_vital
    })

@app.route('/api/alerts')
def get_all_alerts():
    """Get all active alerts across patients"""
    patients_data = get_firebase_data('patients') or {}
    all_alerts = []
    
    for patient_id, patient_info in patients_data.items():
        alerts = patient_info.get('alerts', {})
        for alert_id, alert in alerts.items():
            if not alert.get('resolved', False):
                all_alerts.append({
                    'patient_id': patient_id,
                    'alert_id': alert_id,
                    'timestamp': alert.get('timestamp'),
                    'alerts': alert.get('alerts', []),
                    'priority': alert.get('priority', 'MEDIUM')
                })
    
    # Sort by priority and timestamp
    priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    all_alerts.sort(key=lambda x: (priority_order.get(x['priority'], 3), x['timestamp']))
    
    return jsonify(all_alerts)

@app.route('/api/alert/resolve', methods=['POST'])
def resolve_alert():
    """Mark an alert as resolved"""
    data = request.json
    patient_id = data.get('patient_id')
    alert_id = data.get('alert_id')
    
    if patient_id and alert_id:
        # Update alert in Firebase
        update_data = {'resolved': True}
        response = requests.patch(
            f"{FIREBASE_URL}/patients/{patient_id}/alerts/{alert_id}.json",
            data=json.dumps(update_data),
            verify=False
        )
        
        if response.status_code == 200:
            return jsonify({'success': True})
    
    return jsonify({'success': False})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

