"""
Views for Celery task management.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from celery.result import AsyncResult
from config.celery import app


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_prayer_notification_view(request):
    """
    Manually trigger prayer notification task.
    """
    prayer_name = request.data.get('prayer_name')
    city_id = request.data.get('city_id')
    
    if not prayer_name or not city_id:
        return Response(
            {'error': 'prayer_name and city_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    from push_notification.tasks import send_prayer_notification
    task = send_prayer_notification.delay(prayer_name, city_id)
    
    return Response({
        'task_id': task.id,
        'status': 'Task queued successfully',
        'prayer_name': prayer_name,
        'city_id': city_id
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def send_daily_summary_view(request):
    """
    Manually trigger daily summary task.
    """
    city_id = request.data.get('city_id', 1)
    
    from push_notification.tasks import send_daily_summary
    task = send_daily_summary.delay(city_id)
    
    return Response({
        'task_id': task.id,
        'status': 'Task queued successfully',
        'city_id': city_id
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_status_view(request, task_id):
    """
    Check the status of a Celery task.
    """
    task_result = AsyncResult(task_id, app=app)
    
    return Response({
        'task_id': task_id,
        'status': task_result.status,
        'result': task_result.result if task_result.ready() else None
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def celery_health_check(request):
    """
    Health check endpoint for Celery.
    """
    from push_notification.tasks import debug_task
    
    # Inspect the workers
    inspect = app.control.inspect()
    active_tasks = inspect.active()
    registered_tasks = inspect.registered()
    
    return Response({
        'status': 'healthy',
        'celery_online': True,
        'active_workers': list(inspect.active().keys()) if inspect.active() else [],
        'registered_tasks': list(registered_tasks.keys()) if registered_tasks else []
    })

