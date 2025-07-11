"""
Example usage of Celery tasks in Django views.

This shows how to call Celery tasks from your Django views.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .tasks import process_etl_data_async, send_email_task, cleanup_task


@require_http_methods(["POST"])
def process_etl_async_view(request):
    """
    Trigger ETL processing asynchronously.
    """
    filtered_data_ids = request.POST.getlist('ids')
    
    # Call the Celery task asynchronously
    task = process_etl_data_async.delay(filtered_data_ids)
    
    return JsonResponse({
        'status': 'success',
        'message': 'ETL processing started',
        'task_id': task.id
    })


@require_http_methods(["POST"])
def send_notification_view(request):
    """
    Send email notification asynchronously.
    """
    subject = request.POST.get('subject')
    message = request.POST.get('message')
    recipients = request.POST.getlist('recipients')
    
    # Call the Celery task asynchronously
    task = send_email_task.delay(subject, message, recipients)
    
    return JsonResponse({
        'status': 'success',
        'message': 'Email sending started',
        'task_id': task.id
    })


@require_http_methods(["POST"])
def trigger_cleanup_view(request):
    """
    Trigger cleanup task asynchronously.
    """
    task = cleanup_task.delay()
    
    return JsonResponse({
        'status': 'success',
        'message': 'Cleanup started',
        'task_id': task.id
    })


@require_http_methods(["GET"])
def task_status_view(request, task_id):
    """
    Check the status of a Celery task.
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id)
    
    return JsonResponse({
        'task_id': task_id,
        'status': task.status,
        'result': task.result
    })
