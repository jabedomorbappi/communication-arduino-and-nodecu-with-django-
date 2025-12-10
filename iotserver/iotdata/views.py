# iotdata/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
import json
import requests
from .models import ArduinoData, NodeMCUData

# =====================================
# UPLOAD ENDPOINTS (Arduino & NodeMCU)
# =====================================
@csrf_exempt
def upload_arduino(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            ArduinoData.objects.create(
                ir1=int(body.get("ir1", 0)),
                ir2=int(body.get("ir2", 0)),
                piezo=float(body.get("piezo", 0.0)),
                speed=float(body.get("speed", 0.0)),
                arduino_relay=bool(int(body.get("arduino_relay", 0))),
                piezo_relay=bool(int(body.get("piezo_relay", 0))),
            )
            return JsonResponse({"status": "arduino_ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST only"}, status=400)

@csrf_exempt
def upload_nodemcu(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            NodeMCUData.objects.create(
                ir1=int(body.get("ir1", 0)),
                ir2=int(body.get("ir2", 0)),
                nodemcu_relay=bool(int(body.get("nodemcu_relay", 0))),
            )
            return JsonResponse({"status": "nodemcu_ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "POST only"}, status=400)

# =====================================
# LIGHT CONTROL (Common + Individual)
# =====================================
@csrf_exempt
def control_relay(request):
    if request.method == "POST":
        body = json.loads(request.body)
        state = body.get("state", False)
        relay_type = body.get("type", "common")  # "common", "arduino", "nodemcu"

        try:
            if relay_type in ["common", "arduino"]:
                requests.get(f"http://vehicle.local/relay/arduino/{'on' if state else 'off'}", timeout=3)
            if relay_type in ["common", "nodemcu"]:
                requests.get(f"http://vehicle.local/relay/nodemcu/{'on' if state else 'off'}", timeout=3)
        except:
            pass  # ESP offline

        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "POST only"}, status=400)

# =====================================
# LATEST DATA (for real-time dashboard)
# =====================================
def latest_data(request):
    arduino = ArduinoData.objects.order_by('-timestamp').first()
    nodemcu = NodeMCUData.objects.order_by('-timestamp').first()

    last_seen = arduino.timestamp if arduino else None
    seconds_ago = (timezone.now() - last_seen).total_seconds() if last_seen else 999

    return JsonResponse({
        "arduino": {
            "ir1": arduino.ir1 if arduino else 0,
            "ir2": arduino.ir2 if arduino else 0,
            "piezo": arduino.piezo if arduino else 0.0,
            "speed": arduino.speed if arduino else 0.0,
            "arduino_relay": arduino.arduino_relay if arduino else False,
            "piezo_relay": arduino.piezo_relay if arduino else False,
        },
        "nodemcu": {
            "ir1": nodemcu.ir1 if nodemcu else 0,
            "ir2": nodemcu.ir2 if nodemcu else 0,
            "nodemcu_relay": nodemcu.nodemcu_relay if nodemcu else False,
        },
        "last_seen": seconds_ago,
        "is_connected": seconds_ago < 5
    })

# =====================================
# RECENT DATA (for tables & plots)
# =====================================
def recent_data_api(request):
    thirty_min_ago = timezone.now() - timedelta(minutes=30)
    arduino = ArduinoData.objects.filter(timestamp__gte=thirty_min_ago).order_by('timestamp')
    nodemcu = NodeMCUData.objects.filter(timestamp__gte=thirty_min_ago).order_by('timestamp')

    rows = []
    for a in arduino:
        rows.append({
            "source": "arduino",
            "ir1": a.ir1,
            "ir2": a.ir2,
            "piezo": a.piezo,
            "speed": a.speed,
            "arduino_relay": a.arduino_relay,
            "piezo_relay": a.piezo_relay,
            "timestamp": a.timestamp.isoformat()
        })
    for n in nodemcu:
        rows.append({
            "source": "nodemcu",
            "ir1": n.ir1,
            "ir2": n.ir2,
            "nodemcu_relay": n.nodemcu_relay,
            "timestamp": n.timestamp.isoformat()
        })

    return JsonResponse({"table_rows": rows})

# =====================================
# PAGE VIEWS
# =====================================
def dashboard_live_view(request):
    return render(request, 'dashboard_cyber.html')

def team_view(request):
    return render(request, 'team.html')

def live_table_view(request):
    return render(request, 'live_table.html')

def live_core_view(request):
    return render(request, 'live_core.html')

def live_ultra_view(request):
    return render(request, 'live_ultra.html')





def analytics_full(request):
    return render(request, 'analytics_full.html')

# iotdata/views.py
def recent_data_api(request):
    minutes = int(request.GET.get('minutes', 30))
    cutoff = timezone.now() - timedelta(minutes=minutes)

    # Get data from both models
    arduino_data = ArduinoData.objects.filter(timestamp__gte=cutoff).order_by('timestamp')
    nodemcu_data = NodeMCUData.objects.filter(timestamp__gte=cutoff).order_by('timestamp')

    # Merge and sort by timestamp
    combined = []
    for d in arduino_data:
        combined.append({
            "source": "arduino",
            "ir1": d.ir1,
            "ir2": d.ir2,
            "piezo": float(d.piezo),
            "speed": float(d.speed),
            "arduino_relay": d.arduino_relay,
            "piezo_relay": d.piezo_relay,
            "nodemcu_relay": False,
            "timestamp": d.timestamp.isoformat()
        })
    for d in nodemcu_data:
        combined.append({
            "source": "nodemcu",
            "ir1": d.ir1,
            "ir2": d.ir2,
            "piezo": 0.0,
            "speed": 0.0,
            "arduino_relay": False,
            "piezo_relay": False,
            "nodemcu_relay": d.nodemcu_relay,
            "timestamp": d.timestamp.isoformat()
        })

    # Sort all by time
    combined.sort(key=lambda x: x["timestamp"])

    return JsonResponse({"table_rows": combined})