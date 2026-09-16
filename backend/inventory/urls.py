from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, EquipmentModelViewSet, EquipmentUnitViewSet

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("equipment", EquipmentModelViewSet, basename="equipment-model")
router.register("equipment-units", EquipmentUnitViewSet, basename="equipment-unit")

urlpatterns = router.urls
