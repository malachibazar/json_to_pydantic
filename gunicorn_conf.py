# gunicorn_conf.py
workers = 4  # Number of worker processes (adjust as needed)
bind = "0.0.0.0:8000"  # Bind to all interfaces on port 8000
timeout = 120  # Timeout for requests (in seconds)
keepalive = 2  # Keep-alive connections
