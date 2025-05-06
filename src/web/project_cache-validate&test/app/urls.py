# my_app/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # DRF APIView를 사용하는 경우
    path('admin-api/', views.AdminOnlyAPIView.as_view(), name='admin_api'),
    # 일반 Django View를 사용하는 경우
    # path('admin-resource/', views.AdminOnlyView.as_view(), name='admin_resource'),
]
