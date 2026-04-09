from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HospitalViewSet, HealthProfessionalViewSet

router = DefaultRouter()
router.register(r'hospitals', HospitalViewSet, basename='hospital')
router.register(r'practitioners', HealthProfessionalViewSet, basename='practitioner')

urlpatterns = [
    path('', include(router.urls)),
]
