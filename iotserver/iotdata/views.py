from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.utils import timezone
from .models import VehicleData
from datetime import timedelta
import json

@csrf_exempt
def upload(request):
    if request.method == "POST":
        body = json.loads(request.body.decode())
        VehicleData.objects.create(
            device=body.get("device", "Unknown"),
            ir1=int(body.get("ir1", 0)),
            ir2=int(body.get("ir2", 0)),
            piezo=float(body.get("piezo", 0.0)),
            relay=bool(int(body.get("relay", 0))),
            speed=float(body.get("speed", 0.0)),
            timestamp=timezone.now()  # Ensure timestamp is timezone-aware
        )
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "POST only"})

def dashboard(request):
    # Delete data older than 7 days (timezone-aware)
    VehicleData.objects.filter(timestamp__lt=timezone.now() - timedelta(days=7)).delete()

    # Last 50 rows for table
    table_data = VehicleData.objects.order_by('-timestamp')[:50]

    # Last 5 minutes for chart
    five_min_ago = timezone.now() - timedelta(minutes=5)
    recent_data = VehicleData.objects.filter(timestamp__gte=five_min_ago).order_by('timestamp')

    # Format timestamps as HH:MM:SS
    timestamps = [d.timestamp.strftime("%H:%M:%S") for d in recent_data]
    ir1_data = [d.ir1 for d in recent_data]
    ir2_data = [d.ir2 for d in recent_data]
    piezo_data = [d.piezo for d in recent_data]
    speed_data = [d.speed for d in recent_data]

    return render(request, "dashboard_full.html", {
        "table_data": table_data,
        "timestamps": timestamps,
        "ir1_data": ir1_data,
        "ir2_data": ir2_data,
        "piezo_data": piezo_data,
        "speed_data": speed_data
    })

def latest_data(request):
    """Return the most recent sensor values as JSON"""
    latest = VehicleData.objects.order_by('-timestamp').first()
    if latest:
        data = {
            "ir1": latest.ir1,
            "ir2": latest.ir2,
            "piezo": float(latest.piezo),
            "relay": bool(latest.relay),
            "speed": float(latest.speed)
        }
    else:
        # default if no data
        data = {"ir1": 0, "ir2": 0, "piezo": 0.0, "relay": False, "speed": 0.0}
    return JsonResponse(data)

def dashboard_live(request):
    from django.utils import timezone
    from datetime import timedelta

    # Keep last 50 rows for table
    table_data = VehicleData.objects.order_by('-timestamp')[:50]

    # Last 5 minutes for chart
    five_min_ago = timezone.now() - timedelta(minutes=5)
    recent_data = VehicleData.objects.filter(timestamp__gte=five_min_ago).order_by('timestamp')

    # Format timestamps
    timestamps = [d.timestamp.strftime("%H:%M:%S") for d in recent_data]
    ir1_data = [d.ir1 for d in recent_data]
    ir2_data = [d.ir2 for d in recent_data]
    piezo_data = [d.piezo for d in recent_data]
    speed_data = [d.speed for d in recent_data]

    return render(request, "dashboard_live.html", {
        "table_data": table_data,
        "timestamps": timestamps,
        "ir1_data": ir1_data,
        "ir2_data": ir2_data,
        "piezo_data": piezo_data,
        "speed_data": speed_data
    })


# views.py
from django.utils import timezone
from datetime import timedelta

def recent_data_api(request):
    """Return last 5 minutes data for charts and table"""
    five_min_ago = timezone.now() - timedelta(minutes=5)
    recent_data = VehicleData.objects.filter(timestamp__gte=five_min_ago).order_by('timestamp')

    data = {
        "timestamps": [d.timestamp.strftime("%H:%M:%S") for d in recent_data],
        "ir1": [d.ir1 for d in recent_data],
        "ir2": [d.ir2 for d in recent_data],
        "piezo": [d.piezo for d in recent_data],
        "speed": [d.speed for d in recent_data],
        "relay": [d.relay for d in recent_data],
        "table_rows": [
            {
                "device": d.device,
                "ir1": d.ir1,
                "ir2": d.ir2,
                "piezo": d.piezo,
                "relay": d.relay,
                "speed": d.speed,
                "timestamp": d.timestamp.strftime("%H:%M:%S")
            } for d in recent_data
        ]
    }
    return JsonResponse(data)

