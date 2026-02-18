from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MosqueViewSet, MosqueImageViewSet

router = DefaultRouter()
router.register(r'', MosqueViewSet, basename='mosque')

urlpatterns = [
    path('', include(router.urls)),
    path('<int:mosque_pk>/images/', MosqueImageViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='mosque-images'),
    path('<int:mosque_pk>/images/<int:pk>/', MosqueImageViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='mosque-image-detail'),
]

