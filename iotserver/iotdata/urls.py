# iotdata/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ---- PAGE VIEWS ----
    path('', views.dashboard_live_view, name='home'),
    path('dashboard_cyber/', views.dashboard_live_view, name='dashboard_cyber'),
    path('team/', views.team_view, name='team_view'),
    path('live-table/', views.live_table_view, name='live_table_view'),
    path('live-core/', views.live_core_view, name='live_core_view'),
    path('ultra/', views.live_ultra_view, name='live_ultra_view'),
    path('analytics/', views.analytics_full, name='analytics_full'),
    path('design/', views.cyber, name='cyber'),

    # ---- API ----
    path('api/upload/', views.upload_data, name='upload_data'),
    path('api/latest/', views.latest_data, name='latest_data'),
    path('api/control/relay/', views.control_relay, name='control_relay'),
    path('api/recent/', views.recent_data_api, name='recent_data_api'),
]
