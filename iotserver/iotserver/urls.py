# iotserver/iotserver/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('iotdata.urls')),   # This includes your app's URLs
]