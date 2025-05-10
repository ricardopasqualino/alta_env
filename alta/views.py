from django.shortcuts import render, redirect
from venv import logger
from django.shortcuts import render
from django.db.models import Sum, Avg, Count, Max, Min, Q
from django.core.cache import cache
from django.conf import settings
from django.core.paginator import Paginator
from datetime import datetime, timedelta



from django.db.models import OuterRef, Subquery, Min, F
from django.db.models.functions import TruncMonth
from django.conf import settings as config
from .models import AddPrice
from .filters import MainFilter
from .forms import NewPrice
from django.contrib.auth.decorators import login_required

def index(request):
    return render(request, 'index.html')


def p_cartao_precos(request):
    fil = MainFilter(request.GET, queryset=AddPrice.objects.all())
    cidade = request.GET.get('cidade', '').strip().lower()
    
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
    # Query base otimizada
    base_queryset = AddPrice.objects.all()

    # Se não houver filtros aplicados pelo usuário, filtra apenas os últimos 30 dias
    if not any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano']):
        base_queryset = base_queryset.filter(
            data_coleta__gte=datetime.now() - timedelta(days=30)
        )

    base_queryset = base_queryset.select_related(
        'gasstation_id',
        'produto_id',
        'pesquisa_origem'
    ).only(
        'id',
        'data_coleta',
        'preco_revenda',
        'cnpj',
        'gasstation_id__razao',
        'gasstation_id__cidade',
        'gasstation_id__estado',
        'gasstation_id__bairro',
        'gasstation_id__endereco',
        'gasstation_id__complemento',
        'gasstation_id__cep',
        'gasstation_id__bandeira',
        'produto_id__produto',
        'pesquisa_origem__origem'
    ).order_by('-data_coleta')

    # Aplicar filtros
    f = MainFilter(request.GET, queryset=base_queryset)
    
    # Adicionar paginação
    paginator = Paginator(f.qs, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Log para debug
    logger.info(f"Total de registros: {f.qs.count()}")
    logger.info(f"Registros na página atual: {len(page_obj)}")
    
    data = {
        'list_price': f.qs,
        'filter': f,
        'page_obj': page_obj,
    }
    
    return render(request, 'p_lista_preco.html', data)



def add_price(request):
    form = NewPrice(request.POST or None)

    prices = AddPrice.objects.filter(user=request.user).only(
            'gasstation_id', 
            'produto_id', 
            'preco_revenda', 
            'data_coleta'
        ).order_by('-data_coleta')

    data = {
        'form': form,
        'prices': prices,
    }
    return render(request, 'p_acompanhar.html', data)


def new_price(request):
    form = NewPrice(request.POST or None)
    if form.is_valid():
        addprice = form.save(commit=False)  
        addprice.user = request.user 
        
        # Usando o objeto PesquisaOrigem diretamente do form
        addprice.pesquisa_origem = form.cleaned_data['pesquisa_origem']
        addprice.save() 
        return redirect('p_acompanhar')
    else:
        return redirect('p_acompanhar')
