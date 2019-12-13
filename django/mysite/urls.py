"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
import os
from django.contrib import admin
from django.urls import path
from fiscoAPP import views
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('test', views.test),
    path('login', views.login, name='login'),
    path('register', views.register, name='register'),
    path('signature', views.signature, name='signature'),
    path('registerCom', views.registerCom, name='registerCom'),
    path('queryCom', views.queryCom, name='queryCom'),
    path('eraseCom', views.eraseCom, name='eraseCom'),
    path('createReceipt', views.createReceipt, name='createReceipt'),
    path('queryReceipt', views.queryReceipt, name='queryReceipt'),
    path('queryReceiptOfCom', views.queryReceiptOfCom, name='queryReceiptOfCom'),
    path('transferReceipt', views.transferReceipt, name='transferReceipt'),
    path('deleteReceipt', views.deleteReceipt, name='deleteReceipt'),
    path('menu', views.menu, name="menu"),
    path('', views.menu),
]