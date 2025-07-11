# Celery Configuration for GAIA Project

This document explains how to use Celery with Redis as the message broker for asynchronous task processing.

## Services Added

1. **Redis** - Message broker for Celery
2. **Celery Worker** - Processes background tasks
3. **Celery Beat** - Scheduler for periodic tasks

## Starting the Services

### Development Mode
```bash
docker compose -f docker-compose-no-nginx-debug.yml up
```

### Production Mode
```bash
docker compose -f docker-compose-no-nginx.yml up
```

## Using Celery Tasks

### 1. Calling Tasks from Views

```python
from animal.tasks import process_etl_data_async

# Call task asynchronously
task = process_etl_data_async.delay([1, 2, 3])
task_id = task.id
```

### 2. Checking Task Status

```python
from celery.result import AsyncResult

task = AsyncResult(task_id)
status = task.status
result = task.result
```

### 3. Available Tasks

- `process_etl_data_async(filtered_data_ids)` - Process ETL data asynchronously
- `send_email_task(subject, message, recipient_list)` - Send emails asynchronously
- `cleanup_task()` - Periodic cleanup task

## Testing Celery

Use the management command to test tasks:

```bash
# Test ETL processing
python manage.py test_celery --task etl

# Test email sending
python manage.py test_celery --task email

# Test cleanup
python manage.py test_celery --task cleanup
```

## Monitoring

### Celery Worker Status
```bash
# Check worker status
docker exec -it <container_name> celery -A gaia status

# Monitor tasks
docker exec -it <container_name> celery -A gaia monitor
```

### Redis Status
```bash
# Connect to Redis CLI
docker exec -it <redis_container> redis-cli

# Check Redis info
INFO
```

## Configuration

Celery settings are configured in `gaia/settings.py`:

- **Broker URL**: `redis://redis:6379/0`
- **Result Backend**: `redis://redis:6379/0`
- **Task Serializer**: JSON
- **Result Serializer**: JSON
- **Timezone**: Same as Django `TIME_ZONE`

## Periodic Tasks

To schedule periodic tasks, you can use Celery Beat. Example:

```python
from celery.schedules import crontab
from django.conf import settings

# Add to settings.py
CELERY_BEAT_SCHEDULE = {
    'cleanup-every-hour': {
        'task': 'animal.tasks.cleanup_task',
        'schedule': crontab(minute=0),  # Run every hour
    },
}
```

## Troubleshooting

1. **Redis Connection Issues**
   - Ensure Redis service is running
   - Check if Redis is accessible on port 6379

2. **Task Not Executing**
   - Check if Celery worker is running
   - Verify task is properly imported
   - Check worker logs for errors

3. **Import Errors**
   - Ensure all dependencies are installed in the conda environment
   - Check if Django settings are properly configured

## Files Added/Modified

- `gaia/celery.py` - Celery configuration
- `gaia/__init__.py` - Import Celery app
- `gaia/settings.py` - Celery settings
- `animal/tasks.py` - Celery tasks
- `animal/celery_examples.py` - Example usage
- `animal/management/commands/test_celery.py` - Test command
- `docker-compose-no-nginx.yml` - Added Redis and Celery services
- `docker-compose-no-nginx-debug.yml` - Added Redis and Celery services
- `environment.yml` - Added redis-py dependency
