# gunicorn_conf.py
workers = 4  # Number of worker processes (adjust as needed)
bind = "unix:/home/malachi/json_to_pydantic/app.sock"
timeout = 120  # Timeout for requests (in seconds)
keepalive = 2  # Keep-alive connections
