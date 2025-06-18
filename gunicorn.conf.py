import multiprocessing
import os

# Número de workers - reduzindo para um número mais conservador
workers = 2  # Reduzindo o número de workers

# Timeout
timeout = 300  # 5 minutos

# Limites de memória - mais conservadores
max_requests = 500  # Reduzindo o número máximo de requisições
max_requests_jitter = 50

# Configurações de timeout
graceful_timeout = 300
keepalive = 5

# Configurações de logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Configurações de worker
worker_class = 'gthread'
threads = 2  # Reduzindo o número de threads
worker_connections = 500  # Reduzindo conexões por worker

# Configurações de segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Configurações de memória
worker_tmp_dir = '/dev/shm'

# Configurações adicionais para controle de memória
max_worker_lifetime = 3600  # Reiniciar workers após 1 hora
max_worker_lifetime_jitter = 60  # Adicionar variação aleatória ao tempo de vida 