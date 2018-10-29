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
from nino.api.models import User



router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.

urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls')),
    url(r'auth/verification_code', views.UserSendVerificationCodeView.as_view()),
    url(r'auth/verify', views.UserVerifyCodeView.as_view()),
    url(r'users/', views.UserList.as_view()),
    url(r'notes/', views.NoteList.as_view()),
    url(r'note/<int:pk>/', views.NoteDetail.as_view()),
    url(r'categories/', views.CategoryList.as_view()),
    url(r'category/<int:pk>/', views.CategoryDetail.as_view())
]
