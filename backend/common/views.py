from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.decorators import permission_classes


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return Response(
            {
                "success": False,
                "message": "The API is running, but the database is unavailable.",
                "service": "avault-api",
                "database": "unavailable",
            },
            status=503,
        )

    return Response(
        {
            "success": True,
            "message": "AVault API is healthy.",
            "service": "avault-api",
            "database": "available",
        }
    )
