import requests
import json
import time
import random
from datetime import datetime
import ssl
import certifi
import urllib3
from warnings import filterwarnings

# Disable SSL warnings (this is safe for development)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
filterwarnings('ignore')

# Firebase configuration - REPLACE WITH YOUR ACTUAL URL
FIREBASE_URL = "https://hca-project-172337-default-rtdb.asia-southeast1.firebasedatabase.app"
# You might need to add your database secret here if you have one
# DATABASE_SECRET = "your_secret_here"

# Patient vital thresholds
THRESHOLDS = {
    "heart_rate": {"min": 60, "max": 100},
    "blood_pressure_systolic": {"min": 90, "max": 120},
    "blood_pressure_diastolic": {"min": 60, "max": 80},
    "temperature": {"min": 36.1, "max": 37.2},
    "oxygen_saturation": {"min": 95, "max": 100}
}

def send_to_firebase(patient_id, data):
    """
    Send patient data to Firebase Realtime Database
    """
    # Create a unique timestamp for the data
    timestamp = int(time.time() * 1000)
    url = f"{FIREBASE_URL}/patients/{patient_id}/vitals/{timestamp}.json"
    
    print(f"Trying to send data to: {url}")
    
    # Try with SSL verification first
    try:
        response = requests.put(  # Using PUT instead of POST for simplicity
            url,
            data=json.dumps(data),
            verify=certifi.where()  # Use certifi's certificate bundle
        )
        response.raise_for_status()
        print(f"✅ Data sent successfully for {patient_id}")
        return True
        
    except requests.exceptions.SSLError:
        # If SSL verification fails, try without verification
        print(f"⚠️ SSL verification failed for {patient_id}. Trying without verification...")
        try:
            response = requests.put(
                url,
                data=json.dumps(data),
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            print(f"✅ Data sent successfully for {patient_id} (without SSL verification)")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send data for {patient_id}: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to send data for {patient_id}: {e}")
        return False

def generate_patient_data(patient_id):
    """
    Generate simulated patient vital signs data
    """
    return {
        "patient_id": patient_id,
        "timestamp": datetime.now().isoformat(),
        "heart_rate": random.randint(55, 130),
        "blood_pressure_systolic": random.randint(85, 160),
        "blood_pressure_diastolic": random.randint(50, 100),
        "temperature": round(random.uniform(35.5, 39.0), 1),
        "oxygen_saturation": random.randint(90, 100)
    }

def analyze_with_ml_model(data):
    """
    Simulate ML model analysis of patient data
    """
    alerts = []
    
    # Check each vital sign against thresholds
    for vital, value in data.items():
        if vital in THRESHOLDS:
            threshold = THRESHOLDS[vital]
            if value < threshold["min"]:
                alerts.append(f"{vital} too low: {value} (min: {threshold['min']})")
            elif value > threshold["max"]:
                alerts.append(f"{vital} too high: {value} (max: {threshold['max']})")
    
    # Simulate more complex ML analysis
    if data["heart_rate"] > 120 and data["oxygen_saturation"] < 92:
        alerts.append("CRITICAL: Possible cardiac distress detected")
    
    return alerts

def display_dashboard(patient_id, data, alerts):
    """
    Display patient data and alerts in a dashboard format
    """
    print(f"\n{'='*50}")
    print(f"PATIENT DASHBOARD: {patient_id}")
    print(f"Timestamp: {data['timestamp']}")
    print(f"{'='*50}")
    
    print("VITAL SIGNS:")
    print(f"  Heart Rate: {data['heart_rate']} bpm")
    print(f"  Blood Pressure: {data['blood_pressure_systolic']}/{data['blood_pressure_diastolic']} mmHg")
    print(f"  Temperature: {data['temperature']} °C")
    print(f"  Oxygen Saturation: {data['oxygen_saturation']}%")
    
    if alerts:
        print(f"\n🔴 ALERTS:")
        for alert in alerts:
            print(f"  ⚠️ {alert}")
        
        # Send alert notifications
        send_alerts(patient_id, alerts)
    else:
        print(f"\n✅ All vitals within normal range")

def send_alerts(patient_id, alerts):
    """
    Send alert notifications
    """
    print(f"\n🚨 SENDING ALERTS for {patient_id}:")
    for alert in alerts:
        print(f"   ALERT: {alert}")
    # In a real system, this would send emails or SMS messages

def main():
    """
    Main function to run the patient monitoring system
    """
    print("Starting Patient Monitoring System...")
    print("Press Ctrl+C to stop.\n")
    
    patient_ids = ["patient_001", "patient_002", "patient_003", "patient_004", "patient_005", "patient_006", "patient_007", "patient_008", "patient_009", "patient_010" ]
    
    try:
        while True:
            for patient_id in patient_ids:
                # Generate patient data
                data = generate_patient_data(patient_id)
                
                # Send to Firebase
                success = send_to_firebase(patient_id, data)
                
                if success:
                    # Analyze with ML model
                    alerts = analyze_with_ml_model(data)
                    
                    # Display dashboard  
                    display_dashboard(patient_id, data, alerts)
                else:
                    # If sending failed, just display the data locally
                    print(f"\nDisplaying data for {patient_id} (not sent to Firebase):")
                    print(f"Heart Rate: {data['heart_rate']} bpm")
                    print(f"Oxygen Saturation: {data['oxygen_saturation']}%")
                
                # Wait before next reading
                time.sleep(10)
                
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")

if __name__ == "__main__":
    # Test SSL certificates
    try:
        # Set SSL certificate path
        import os
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()
        
        print("Testing SSL connection...")
        response = requests.get("https://www.google.com", verify=certifi.where(), timeout=5)
        print("SSL certificate test passed")
    except Exception as e:
        print(f"SSL certificate test failed: {e}")
        print("We'll try to continue anyway...")
    
    # Start the main program
    main()