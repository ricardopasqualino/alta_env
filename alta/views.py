from django.shortcuts import render
from venv import logger
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count, Max, Min, Q
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from django.db.models import OuterRef, Subquery, Min, F
from django.db.models.functions import TruncMonth
from django.conf import settings as config


from .models import AddPrice

from .filters import MainFilter


def index(request):
    return render(request, 'index.html')


def p_cartao_precos(request):
    
    fil = MainFilter(request.GET, queryset=AddPrice.objects.all())

    cidade = request.GET.get('cidade')
    
    # Gerar uma chave de cache única baseada na cidade
    cache_key_min = f"preco_min_{cidade}"
    cache_key_avg = f"preco_avg_{cidade}"
    cache_key_max = f"preco_max_{cidade}"
    
    # Verificar se os valores já estão no cache
    preco_min = cache.get(cache_key_min)
    preco_avg = cache.get(cache_key_avg)
    preco_max = cache.get(cache_key_max)
    
    if not preco_min:
        preco_min = AddPrice.objects.filter(gasstation_id__cidade=cidade).only('gasstation_id__cidade', 'preco_revenda').values('produto').annotate(preco_minimo=Min('preco_revenda'))
        cache.set(cache_key_avg, preco_min, 3600)
    
    if not preco_avg:
        preco_avg = AddPrice.objects.filter(gasstation_id__cidade=cidade).only('gasstation_id__cidade', 'preco_revenda').values('produto').annotate(preco_medio=Avg('preco_revenda'))
        cache.set(cache_key_avg, preco_avg, 3600)

    if not preco_max:
        preco_max = AddPrice.objects.filter(gasstation_id__cidade=cidade).only('gasstation_id__cidade', 'preco_revenda').values('produto').annotate(preco_maximo=Max('preco_revenda'))
        cache.set(cache_key_max, preco_max, 3600)

    ultima_coleta = AddPrice.objects.aggregate(ultima_data_coleta=Max('data_coleta'))
    ultima_data = ultima_coleta['ultima_data_coleta']

    data = {
        'fil': fil,
        'cidade': cidade,
        'preco_min': preco_min,
        'preco_max': preco_max,
        'preco_avg': preco_avg,
        'ultima_data':ultima_data
    }

    return render(request, 'p_cartao_precos.html', data)


def p_plans(request):
    return render(request, 'p_plans.html')


def p_ia(request):
    return render(request, 'p_ia.html')


def p_mapeei(request):
    return render(request, 'p_mapeei.html')


def p_lista_preco(request):
    # Gerar uma chave de cache única para a lista de preços
    cache_key = "lista_preco_cache"
    
    # Tentar obter os dados do cache
    cached_data = cache.get(cache_key)
    
    if not cached_data:
        # Otimização: Usar select_related para carregar as relações em uma única query
        # Otimização: Usar only() para selecionar apenas os campos necessários
        # Otimização: Limitar o número de registros iniciais
        base_queryset = AddPrice.objects.filter(
            preco_revenda__isnull=False
        ).select_related(
            'gasstation_id',
            'produto_id',
            'pesquisa_origem'
        ).only(
            'data_coleta',
            'preco_revenda',
            'preco_compra',
            'gasstation_id__razao',
            'gasstation_id__cidade',
            'gasstation_id__bandeira',
            'produto_id__produto',
            'pesquisa_origem__origem'
        ).order_by('-data_coleta')[:50]  # Limitar a 50 registros iniciais

        # Armazenar apenas os dados necessários no cache
        cached_data = {
            'list_price': list(base_queryset.values()),
        }
        
        # Armazenar os dados no cache por 7 dias (604800 segundos)
        cache.set(cache_key, cached_data, 604800)
    
    # Criar o filtro com os dados do cache
    f = MainFilter(request.GET, queryset=AddPrice.objects.filter(id__in=[item['id'] for item in cached_data['list_price']]))

    data = {
        'list_price': AddPrice.objects.filter(id__in=[item['id'] for item in cached_data['list_price']]),
        'filter': f,
    }
    
    return render(request, 'p_lista_preco.html', data)


def p_acompanhar(request):
    return render(request, 'p_acompanhar.html')

