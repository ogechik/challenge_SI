from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import CustomerViewSet, OrderViewSet, GoogleLoginView, GoogleCallbackView

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'orders', OrderViewSet)

urlpatterns = [
    path('login/', GoogleLoginView.as_view(), name='login'),
    path('auth2callback/', GoogleCallbackView.as_view(), name='auth2callback'),
    path('', include(router.urls)),
]
