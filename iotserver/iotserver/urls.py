from django.contrib import admin
from django.urls import path
from iotdata.views import upload, dashboard,latest_data,dashboard_live,recent_data_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('upload/', upload),
    path('', dashboard_live, name='dashboard_live'),
    path('dashboard/', dashboard),
    path('api/latest/', latest_data, name='latest_data'),
      path('api/recent/', recent_data_api, name='recent_data_api'),
]
