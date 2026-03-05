#!/bin/bash
# ============================================================
# Start Celery Worker + Beat for Salahtime
# Usage: ./start_celery.sh
# ============================================================

VENV=/home/mdraselbackenddev/Rasel/zuhha/.venv
PROJECT_DIR=/home/mdraselbackenddev/Rasel/zuhha/salahtime

source "$VENV/bin/activate"
cd "$PROJECT_DIR"

echo "=== Stopping old Celery processes ==="
pkill -f "celery -A config" 2>/dev/null || true
sleep 1

echo "=== Starting Celery Worker ==="
celery -A config worker -l info --logfile=logs/celery_worker.log --detach

echo "=== Starting Celery Beat ==="
celery -A config beat -l info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --logfile=logs/celery_beat.log --detach

echo ""
echo "✓ Celery worker + beat started"
echo "  Worker log : $PROJECT_DIR/logs/celery_worker.log"
echo "  Beat log   : $PROJECT_DIR/logs/celery_beat.log"
echo ""
echo "To test notifications:"
echo "  python manage.py dispatch_notifications --status"
echo "  python manage.py dispatch_notifications"
