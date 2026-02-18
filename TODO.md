# TODO - Update Requirements and Configure SimpleJWT, Redis, Celery

## Task: Update project with specified dependencies

## Steps to Complete:

- [x] 1. Update requirements.txt with specified packages
- [x] 2. Update config/settings.py with:
  - [x] 2.1 SimpleJWT authentication configuration
  - [x] 2.2 Redis cache configuration
  - [x] 2.3 Celery configuration

## Completed Steps:

- Updated requirements.txt with:
  - Django==4.2.27
  - djangorestframework==3.14.0
  - djangorestframework-simplejwt==5.3.0
  - django-redis==5.4.0
  - celery==5.3.4
  - hiredis==2.2.3
  - redis==5.0.1
  - django-cors-headers==4.3.1

- Updated config/settings.py with:
  - SimpleJWT authentication (JWTAuthentication)
  - Redis cache configuration (CACHES)
  - Celery configuration (CELERY_BROKER_URL, CELERY_RESULT_BACKEND)


