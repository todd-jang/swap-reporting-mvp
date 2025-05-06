# my_django_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('my-app/', include('my_app.urls')), # my_app의 URL 포함
    # ... 다른 URL 패턴 ...
]
