import time
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


class PerformanceMonitorMiddleware:
    """
    Middleware para monitorar performance de views em produção
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Tempo inicial
        start_time = time.time()
        
        # Processar a requisição
        response = self.get_response(request)
        
        # Calcular tempo de execução
        execution_time = time.time() - start_time
        
        # Log apenas em produção e para views lentas (> 1 segundo)
        if not settings.DEBUG and execution_time > 1.0:
            logger.warning(
                f'View lenta detectada: {request.path} - {execution_time:.2f}s - '
                f'User: {request.user.username if request.user.is_authenticated else "Anonymous"}'
            )
        
        # Adicionar header de performance (apenas em desenvolvimento)
        if settings.DEBUG:
            response['X-Execution-Time'] = f'{execution_time:.3f}s'
        
        return response


class CacheMiddleware:
    """
    Middleware para cache inteligente baseado em headers
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se a resposta pode ser cachead
        response = self.get_response(request)
        
        # Cache para páginas estáticas (não autenticadas)
        if (not request.user.is_authenticated and 
            response.status_code == 200 and
            request.method == 'GET'):
            
            # Adicionar headers de cache
            response['Cache-Control'] = 'public, max-age=300'  # 5 minutos
            response['Vary'] = 'Accept-Language'
        
        return response 