from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAdmin

from .models import SystemSettings
from .serializers import SystemSettingsSerializer


class SystemSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(SystemSettingsSerializer(SystemSettings.get_solo()).data)

    def patch(self, request):
        self.permission_classes = [IsAdmin]
        self.check_permissions(request)
        settings = SystemSettings.get_solo()
        serializer = SystemSettingsSerializer(settings, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
