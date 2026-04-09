from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Authentication (dj-rest-auth) ─────────────────────────────────────────
    # POST /api/auth/login/          → obtain JWT access + refresh tokens
    # POST /api/auth/logout/         → blacklist refresh token
    # POST /api/auth/password/change/
    # POST /api/auth/password/reset/
    path('api/auth/', include('dj_rest_auth.urls')),

    # POST /api/auth/registration/   → register a new hospital admin (JWT issued)
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),

    # POST /api/auth/token/refresh/  → simplejwt refresh (dj-rest-auth delegates to this)
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── Hospital & resource endpoints ─────────────────────────────────────────
    path('api/', include('hms_engine.urls')),

    # ── API Schema / Swagger docs ─────────────────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
