# Third-party packages
from rest_framework.routers import DefaultRouter

# Local / project imports
from apps.appointments.views import AvailabilityViewSet

router = DefaultRouter()
router.register(
    prefix="doctor/availability",
    viewset=AvailabilityViewSet,
    basename="availability",
)

urlpatterns = router.urls