from django.contrib import admin
from django.urls import path, include
from django.views.i18n import set_language
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('set-language/', set_language, name='set_language'),
    path('accounts/', include('accounts.urls')),

    # ── REST API (має бути ДО shop.urls!) ─────────────────────────────────────
    path('api/', include('shop.api.urls')),

    # ── JWT Auth ──────────────────────────────────────────────────────────────
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # ── API Documentation ─────────────────────────────────────────────────────
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ── Shop (звичайні views) — після API ─────────────────────────────────────
    path('', include('shop.urls')),
]
