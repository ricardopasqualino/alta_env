import multiprocessing
import os

# Número de workers
workers = multiprocessing.cpu_count() * 2 + 1

# Timeout
timeout = 300  # 5 minutos

# Limites de memória
max_requests = 1000
max_requests_jitter = 50

# Configurações de timeout
graceful_timeout = 300
keepalive = 5

# Configurações de logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configurações de worker
worker_class = 'gthread'  # Usando worker thread ao invés de uvicorn
threads = 4
worker_connections = 1000

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de memória
worker_tmp_dir = '/dev/shm' 