from rest_framework.routers import DefaultRouter

from .views import LateFeeViewSet, LoanViewSet

router = DefaultRouter()
router.register("loans", LoanViewSet, basename="loan")
router.register("late-fees", LateFeeViewSet, basename="late-fee")

urlpatterns = router.urls