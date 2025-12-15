import time
from iotdata.models import ArduinoData, NodeMCUData

# --- Configuration ---
UPDATE_INTERVAL_SECONDS = 0.1  # Matches your 100 ms update rate

def monitor_data():
    """Fetches and displays the latest data from both models."""
    try:
        # Fetch latest Arduino Data
        latest_arduino = ArduinoData.objects.latest('server_receive_time')

        # Fetch latest NodeMCU Data
        latest_nodemcu = NodeMCUData.objects.latest('server_receive_time')

        # --- Print Results ---

        # Clear screen (optional, but makes output cleaner)
        # print('\033[H\033[J') 

        print("=========================================================================")
        print(f"LATEST DATA STREAM ({time.strftime('%H:%M:%S')})")
        print("-------------------------------------------------------------------------")

        # Arduino Data Display
        print("ARDUINO DATA:")
        print(f"  Speed: {latest_arduino.speed:.1f} km/h | Piezo: {latest_arduino.piezo:.2f} V")
        print(f"  IR1/IR2: {latest_arduino.ir1}/{latest_arduino.ir2} | Relay: {'ON' if latest_arduino.arduino_relay else 'OFF'} | Piezo Relay: {'ON' if latest_arduino.piezo_relay else 'OFF'}")
        print(f"  Received: {latest_arduino.server_receive_time.strftime('%H:%M:%S.%f')[:-3]} UTC")

        print("-------------------------------------------------------------------------")

        # NodeMCU Data Display
        print("NODEMCU DATA:")
        print(f"  IR1/IR2: {latest_nodemcu.ir1}/{latest_nodemcu.ir2} | Relay: {'ON' if latest_nodemcu.nodemcu_relay else 'OFF'}")
        print(f"  Received: {latest_nodemcu.server_receive_time.strftime('%H:%M:%S.%f')[:-3]} UTC")
        print("=========================================================================")

    except (ArduinoData.DoesNotExist, NodeMCUData.DoesNotExist):
        print(f"[{time.strftime('%H:%M:%S')}] Waiting for data...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# --- Start the continuous loop ---
print(f"Starting live data monitor. Updating every {UPDATE_INTERVAL_SECONDS} seconds...")

while True:
    monitor_data()
    time.sleep(UPDATE_INTERVAL_SECONDS)