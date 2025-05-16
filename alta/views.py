from django.shortcuts import render, redirect
from venv import logger
from django.shortcuts import render
from django.db.models import Sum, Avg, Count, Max, Min, Q
from django.core.cache import cache
from django.conf import settings
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from django.db.models import OuterRef, Subquery, Min, F
from django.db.models.functions import TruncMonth
from django.conf import settings as config
from .models import AddPrice, GasStation, PesquisaOrigem
from .filters import MainFilter
from .forms import NewPrice, CreateUserForm
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def p_cartao_precos(request):
    fil = MainFilter(request.GET, queryset=AddPrice.objects.all())
    cidade = request.GET.get('cidade')
    
    # Log para debug
    print(f"Cidade selecionada: {cidade}")
    
    # Gerar uma chave de cache única baseada na cidade
    cache_key_min = f"preco_min_{cidade}"
    cache_key_avg = f"preco_avg_{cidade}"
    cache_key_max = f"preco_max_{cidade}"
    
    # Verificar se os valores já estão no cache
    preco_min = cache.get(cache_key_min)
    preco_avg = cache.get(cache_key_avg)
    preco_max = cache.get(cache_key_max)
    
    if not preco_min:
        preco_min = AddPrice.objects.filter(
            gasstation_id__cidade=cidade
        ).only(
            'gasstation_id__cidade', 
            'preco_revenda'
        ).values(
            'produto_id__produto'
        ).annotate(
            preco_minimo=Min('preco_revenda')
        )
        print(f"Preços mínimos: {list(preco_min)}")
        cache.set(cache_key_min, preco_min, 3600)
    
    if not preco_avg:
        preco_avg = AddPrice.objects.filter(
            gasstation_id__cidade=cidade
        ).only(
            'gasstation_id__cidade', 
            'preco_revenda'
        ).values(
            'produto_id__produto'
        ).annotate(
            preco_medio=Avg('preco_revenda')  # Corrigido de preco_minimo para preco_medio
        )
        print(f"Preços médios: {list(preco_avg)}")
        cache.set(cache_key_avg, preco_avg, 3600)

    if not preco_max:
        preco_max = AddPrice.objects.filter(
            gasstation_id__cidade=cidade
        ).only(
            'gasstation_id__cidade', 
            'preco_revenda'
        ).values(
            'produto_id__produto'
        ).annotate(
            preco_maximo=Max('preco_revenda')  # Corrigido de preco_minimo para preco_maximo
        )
        print(f"Preços máximos: {list(preco_max)}")
        cache.set(cache_key_max, preco_max, 3600)

    ultima_coleta = AddPrice.objects.aggregate(ultima_data_coleta=Max('data_coleta'))
    ultima_data = ultima_coleta['ultima_data_coleta']

    data = {
        'fil': fil,
        'cidade': cidade,
        'preco_min': preco_min,
        'preco_max': preco_max,
        'preco_avg': preco_avg,
        'ultima_data': ultima_data
    }

    print(f"Dados enviados ao template: {data}")

    return render(request, 'p_cartao_precos.html', data)


@login_required
def p_plans(request):
    return render(request, 'p_plans.html')


@login_required
def p_ia(request):
    return render(request, 'p_ia.html')


@login_required
def p_mapeei(request):
    return render(request, 'p_mapeei.html')


@login_required
def p_lista_preco(request):
    # Query base otimizada
    base_queryset = AddPrice.objects.all()

    # Se não houver filtros aplicados pelo usuário, filtra apenas os últimos 30 dias
    if not any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano']):
        base_queryset = base_queryset.filter(
            data_coleta__gte=datetime.now() - timedelta(days=10)
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


@login_required
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
    return render(request, 'p_adicionar.html', data)


@login_required
def new_price(request):
    form = NewPrice(request.POST or None)
    if form.is_valid():
        addprice = form.save(commit=False)  
        addprice.user = request.user 
        
        # Buscar a instância de PesquisaOrigem com id=1
        pesquisa_origem = PesquisaOrigem.objects.get(id=1)
        addprice.pesquisa_origem = pesquisa_origem

        # Converter a data do formato dd/mm/yyyy para yyyy-mm-dd
        data_coleta = request.POST.get('data_coleta')
        if data_coleta:
            try:
                data_coleta = datetime.strptime(data_coleta, '%d/%m/%Y').strftime('%Y-%m-%d')
                addprice.data_coleta = data_coleta
            except ValueError:
                messages.error(request, 'Formato de data inválido')
                return redirect('p_acompanhar')

        addprice.save() 
        messages.success(request, 'Preço adicionado com sucesso!')
        return redirect('p_acompanhar')
    else:
        messages.error(request, 'Erro ao adicionar preço. Verifique os dados.')
        return redirect('p_acompanhar')
    

@login_required
def p_profile(request):
    return render(request, 'p_profile.html')


@login_required
def login_page(request):
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'registration/login.html')


def login_view(request):    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'Login realizado com sucesso!')
                return redirect('index')
            else:
                messages.error(request, 'Usuário ou senha inválidos.')
                return redirect('login')
        else:
            messages.error(request, 'Por favor, preencha todos os campos.')
            return redirect('login')
    return redirect('login')


def logout(request):
    return render(request, 'registration/logout.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def new_register(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email
            user.save()
            messages.success(request, 'Conta criada com sucesso! Você já pode fazer login.')
            return redirect('login')
        else:
            messages.error(request, 'Erro no cadastro. Este email já está em uso.')

    context = {'form': form}
    return render(request, 'p_register.html', context)



def password_reset(request):
    return render(request, 'registration/password_form.html')

