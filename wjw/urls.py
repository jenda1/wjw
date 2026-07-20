from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('main.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
