from django.urls import path

from .settings_views import SystemSettingsView
from .views import health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("settings/", SystemSettingsView.as_view(), name="system-settings"),
]
