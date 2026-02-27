"""
Gunicorn configuration file for Salahtime Django application.
Production-ready settings optimized for performance and security.
"""

import multiprocessing
import os

# ===================================================================
# Server Socket Configuration
# ===================================================================

# Bind to localhost only for security (nginx will proxy)
bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8000")

# Maximum number of pending connections
backlog = 2048

# ===================================================================
# Worker Processes
# ===================================================================

# Number of worker processes
# Formula: CPU cores * 2 + 1 (for I/O bound applications)
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Worker class
# Options: sync, gevent, eventlet, tornado
worker_class = os.environ.get("GUNICORN_WORKER_CLASS", "sync")

# Number of concurrent connections per worker (for async workers)
worker_connections = 1000

# Maximum requests a worker will process before restarting
# Helps prevent memory leaks
max_requests = 1000

# Add random jitter to prevent all workers restarting at once
max_requests_jitter = 50

# ===================================================================
# Timeouts
# ===================================================================

# Worker timeout in seconds
timeout = 60

# Graceful timeout for worker shutdown
graceful_timeout = 30

# Keep-alive connections
keepalive = 2

# ===================================================================
# Logging
# ===================================================================

# Access log file
accesslog = os.environ.get("GUNICORN_ACCESS_LOG", "/var/log/salahtime/access.log")

# Error log file
errorlog = os.environ.get("GUNICORN_ERROR_LOG", "/var/log/salahtime/error.log")

# Log level: debug, info, warning, error, critical
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# ===================================================================
# Process Naming
# ===================================================================

# Process name (shown in ps output)
proc_name = "salahtime"

# ===================================================================
# Server Mechanics
# ===================================================================

# Daemon mode (run in background) - DON'T use with systemd
daemon = False

# PID file location
pidfile = "/var/run/salahtime.pid"

# File mode creation mask
umask = 0

# User and group for worker processes
user = os.environ.get("GUNICORN_USER", "www-data")
group = os.environ.get("GUNICORN_GROUP", "www-data")

# Directory for temporary files during uploads
tmp_upload_dir = os.environ.get("GUNICORN_TMP_UPLOAD_DIR", None)

# ===================================================================
# SSL Configuration (Optional - terminate SSL at Nginx instead)
# ===================================================================

# Uncomment if terminating SSL at Gunicorn
# keyfile = "/path/to/private.key"
# certfile = "/path/to/certificate.crt"

# ===================================================================
# Server Hooks
# ===================================================================

def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    print(f"Gunicorn server started with {workers} workers")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    pass

def pre_exec(server):
    """Called just before a new master process is forked."""
    pass

def pre_request(worker, req):
    """Called just before a worker processes the request."""
    worker.log.debug("%s %s" % (req.method, req.path))

def post_request(worker, req, environ, resp):
    """Called after a worker processes the request."""
    pass

def child_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def worker_exit(server, worker):
    """Called just after a worker has been exited."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called just after num_workers has been changed."""
    pass

def on_exit(server):
    """Called just before exiting Gunicorn."""
    pass

