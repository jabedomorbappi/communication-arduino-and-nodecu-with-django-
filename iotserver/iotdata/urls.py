# iotdata/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_live_view),
    path('dashboard_cyber/', views.dashboard_live_view),
    path('team/', views.team_view),
    path('live-table/', views.live_table_view),
    path('live-core/', views.live_core_view),
    path('ultra/', views.live_ultra_view),
    path('upload/arduino/', views.upload_arduino),
    path('upload/nodemcu/', views.upload_nodemcu),
    path('api/control/relay/', views.control_relay),
    path('api/latest/', views.latest_data),
    path('api/recent/', views.recent_data_api),
    path('analytics/', views.analytics_full),
]