# gunicorn.conf.py
import os

#
# Basic Gunicorn configuration for a single-user Flask-SocketIO app
# using the threading async mode. This uses Gunicorn's default port (8000).
#

# Bind to all interfaces on default port 8080
bind = f"0.0.0.0:{os.environ.get('PORT', '8080')}"

# Single worker is sufficient since it's just you using the app
workers = 1

# Use threaded worker class so SocketIO(threading) works correctly
worker_class = "gthread"

# Number of threads per worker (10 is more than enough)
threads = 10

# Prevent request timeouts during long-polling
timeout = 90

# Logging
loglevel = "info"
accesslog = "-"   # log to stdout
errorlog = "-"    # log to stderr
