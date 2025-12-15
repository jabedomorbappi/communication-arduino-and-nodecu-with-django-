# iotdata/views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import requests

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import ArduinoData, NodeMCUData
from .serializers import ArduinoDataSerializer, NodeMCUDataSerializer

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync



# Global cache for NodeMCU IP
LATEST_IP_INFO = {
    'nodemcu_ip': 'Unknown',
    'last_seen': timezone.now()
}

# ===================== 1. UPLOAD DATA =====================
@csrf_exempt
@api_view(['POST'])
def upload_data(request):
    body = request.data
    client_ip = request.META.get('REMOTE_ADDR')
    if client_ip:
        LATEST_IP_INFO['nodemcu_ip'] = client_ip
        LATEST_IP_INFO['last_seen'] = timezone.now()

    # Arduino Data
    arduino_data = body.get("arduino")
    if arduino_data:
        serializer = ArduinoDataSerializer(data=arduino_data)
        if serializer.is_valid():
            serializer.save()
        else:
            print("[UPLOAD] Arduino errors:", serializer.errors)

    # NodeMCU Data
    nodemcu_data = body.get("nodemcu")
    if nodemcu_data:
        serializer = NodeMCUDataSerializer(data=nodemcu_data)
        if serializer.is_valid():
            serializer.save()
        else:
            print("[UPLOAD] NodeMCU errors:", serializer.errors)

    return Response({"status": "data_received"}, status=status.HTTP_201_CREATED)

# ===================== 2. RELAY CONTROL =====================
@csrf_exempt
@api_view(['POST'])
def control_relay(request):
    """
    Handles common & individual relay control.
    NodeMCU forwards Arduino commands via TX/RX.
    """
    try:
        body = request.data
        state = body.get("state", False)
        relay_type = body.get("type", "common")
        action = "on" if state else "off"

        nodemcu_ip = LATEST_IP_INFO.get('nodemcu_ip', "192.168.1.100")  # fallback IP
        success = True

        # --- COMMON RELAY: Toggle both NodeMCU & Arduino ---
        if relay_type == "common":
            # NodeMCU relay
            try:
                requests.get(f"http://{nodemcu_ip}/relay/{action}", timeout=5)
            except Exception as e:
                print(f"[CONTROL FAIL] NodeMCU (common): {e}")
                success = False

            # Arduino via NodeMCU
            try:
                requests.get(f"http://{nodemcu_ip}/relay/arduino/{action}", timeout=5)
            except Exception as e:
                print(f"[CONTROL FAIL] Arduino via NodeMCU (common): {e}")
                success = False

        # --- INDIVIDUAL RELAYS ---
        elif relay_type == "nodemcu":
            try:
                requests.get(f"http://{nodemcu_ip}/relay/{action}", timeout=5)
            except Exception as e:
                print(f"[CONTROL FAIL] NodeMCU (individual): {e}")
                success = False

        elif relay_type == "arduino":
            try:
                requests.get(f"http://{nodemcu_ip}/relay/arduino/{action}", timeout=5)
            except Exception as e:
                print(f"[CONTROL FAIL] Arduino via NodeMCU (individual): {e}")
                success = False

        else:
            return Response({"error": "Unknown relay type"}, status=400)

        # --- Broadcast updated state ---
        if success:
            channel_layer = get_channel_layer()
            if channel_layer:
                fake_request = HttpRequest()
                fake_request.method = "GET"
                response = latest_data(fake_request)
                async_to_sync(channel_layer.group_send)(
                    "dashboard",
                    {"type": "dashboard_update", "data": response.data}
                )
            return Response({"status": "ok"})
        else:
            return Response({"error": "NodeMCU/Arduino unreachable"}, status=504)

    except Exception as e:
        print("[CONTROL CRASH]", e)
        return Response({"error": "Server error"}, status=500)

# ===================== 3. LATEST DATA =====================
from datetime import timedelta
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import ArduinoData, NodeMCUData

@api_view(['GET'])
def recent_data_api(request):
    minutes = int(request.GET.get('minutes', 30))
    cutoff = timezone.now() - timedelta(minutes=minutes)

    arduino_data = ArduinoData.objects.filter(server_receive_time__gte=cutoff).order_by('server_receive_time')
    nodemcu_data = NodeMCUData.objects.filter(server_receive_time__gte=cutoff).order_by('server_receive_time')

    combined = []

    # Arduino
    for d in arduino_data:
        combined.append({
            "source": "arduino",
            "sensor_id": d.sensor_id,
            "capture_time": str(d.device_capture_time),
            "ir1": d.ir1,
            "ir2": d.ir2,
            "piezo": float(d.piezo),
            "speed": float(d.speed),
            "arduino_relay": d.arduino_relay,
            "piezo_relay": d.piezo_relay,
            "nodemcu_relay": False,
            "timestamp": d.server_receive_time.isoformat()
        })

    # NodeMCU
    for d in nodemcu_data:
        combined.append({
            "source": "nodemcu",
            "sensor_id": d.sensor_id,
            "capture_time": str(d.device_capture_time),
            "ir1": d.ir1,
            "ir2": d.ir2,
            "piezo": 0.0,
            "speed": 0.0,
            "arduino_relay": False,
            "piezo_relay": False,
            "nodemcu_relay": d.nodemcu_relay,
            "timestamp": d.server_receive_time.isoformat()
        })

    # Sort by timestamp
    combined.sort(key=lambda x: x["timestamp"])
    return Response({"table_rows": combined})




@api_view(['GET'])
def latest_data(request):
    try:
        arduino = ArduinoData.objects.latest('server_receive_time')
    except ArduinoData.DoesNotExist:
        arduino = None

    try:
        nodemcu = NodeMCUData.objects.latest('server_receive_time')
    except NodeMCUData.DoesNotExist:
        nodemcu = None

    last_seen = LATEST_IP_INFO['last_seen']
    if nodemcu:
        last_seen = nodemcu.server_receive_time

    seconds_ago = (timezone.now() - last_seen).total_seconds()

    def format_data(data):
        if not data:
            return {
                "ir1": 0, "ir2": 0, "piezo": 0.0, "speed": 0.0,
                "arduino_relay": False, "piezo_relay": False, "nodemcu_relay": False
            }
        return {
            "sensor_id": data.sensor_id,
            "capture_time": str(data.device_capture_time) if data.device_capture_time else "N/A",
            "receive_time": str(data.server_receive_time),
            "ir1": getattr(data, 'ir1', 0),
            "ir2": getattr(data, 'ir2', 0),
            "piezo": float(getattr(data, 'piezo', 0.0)),
            "speed": float(getattr(data, 'speed', 0.0)),
            "arduino_relay": getattr(data, 'arduino_relay', False),
            "piezo_relay": getattr(data, 'piezo_relay', False),
            "nodemcu_relay": getattr(data, 'nodemcu_relay', False),
        }

    return Response({
        "arduino": format_data(arduino),
        "nodemcu": format_data(nodemcu),
        "nodemcu_ip": LATEST_IP_INFO.get('nodemcu_ip', 'Unknown'),
        "last_seen": seconds_ago,
        "is_connected": seconds_ago < 5
    })

# ===================== 4. PAGE VIEWS =====================
def dashboard_live_view(request): return render(request, 'dashboard.html')
def team_view(request): return render(request, 'team.html')
def live_table_view(request): return render(request, 'live_table.html')
def live_core_view(request): return render(request, 'live_core.html')
def live_ultra_view(request): return render(request, 'live_ultra.html')
def analytics_full(request): return render(request, 'analytics_full.html')
def cyber(request): return render(request, 'dashboard_cyber.html')
