from django.contrib import admin
from django.urls import path, include
from thepopwinegdrives import views as thepopwinegdrives_views
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
def custom_404(request, exception=None):
    return render(request, '404.html', status=404)

handler404 = custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('thepopwinegdrives.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('slack/', include('slackbot.urls')),


    # JWT Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', thepopwinegdrives_views.home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
