"""nino URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from nino.api import views
from django.contrib.auth.admin import UserAdmin
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.documentation import include_docs_urls

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls')),
    path('api/notes/', views.NoteList.as_view()),
    path('api/analyze_text/', views.text_analysis),
    url(r'^api/docs/', include_docs_urls(title='Nino API Documentation')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
