from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail import urls as wagtail_urls

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico', permanent=True)),
    path('admin/', admin.site.urls),
    path('hijack/', include('hijack.urls')),
    path('cms/', include(wagtailadmin_urls)),
    path('doc/', include(wagtaildocs_urls)),
    path('accounts/', include('allauth.urls')),
    path('', include('main.urls')),
    path('', include(wagtail_urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
