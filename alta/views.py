import os
import json
import requests

from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count, Max, Min, Q, F, ExpressionWrapper, DurationField
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.db.models.functions import ExtractMonth, ExtractYear
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache

from .filters import MainFilter

from .forms import NewPrice, CreateUserForm

from .models import (
    AddPrice, 
    PesquisaOrigem, 
    Profile,
    GasStation,
    Produto,
    FAQ
)


@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def p_faq(request):
    faqs = FAQ.objects.all()
    data = {
        'faqs': faqs
    }
    return render(request, 'p_faq.html', data)


@login_required
def p_cartao_precos(request):
    
    cidade = request.GET.get('cidade')
    ano = request.GET.get('ano')
    mes = request.GET.get('mes')
    
    # Gerar chave de cache baseada nos filtros
    cache_key = f"cartao_precos:{cidade}:{ano}:{mes}:{str(sorted(request.GET.items()))}"
    cached_result = cache.get(cache_key)
    if cached_result:
        # Recriar o filter para o template
        base_queryset = AddPrice.objects.exclude(produto_id=3, pesquisa_origem_id=2, produto_id__isnull=True)
        fil = MainFilter(request.GET, queryset=base_queryset)
        cached_result['fil'] = fil
        return render(request, 'p_cartao_precos.html', cached_result)
    
    # Query base otimizada usando values
    base_query = AddPrice.objects.filter(
        gasstation_id__cidade=cidade,
        data_coleta__year=ano,
        data_coleta__month=mes
    ).exclude(produto_id=3).values(
        'produto_id__produto',
        'preco_revenda'
    )
    
    # Calcular todos os valores em uma única query otimizada
    precos_agregados = list(base_query.values(
        'produto_id__produto'
    ).annotate(
        preco_minimo=Min('preco_revenda'),
        preco_medio=Avg('preco_revenda'),
        preco_maximo=Max('preco_revenda')
    ))
    
    # Separar os dados
    preco_min = [{'produto_id__produto': item['produto_id__produto'], 'preco_minimo': item['preco_minimo']} for item in precos_agregados]
    preco_avg = [{'produto_id__produto': item['produto_id__produto'], 'preco_medio': item['preco_medio']} for item in precos_agregados]
    preco_max = [{'produto_id__produto': item['produto_id__produto'], 'preco_maximo': item['preco_maximo']} for item in precos_agregados]

    # Query otimizada para última coleta
    ultima_coleta = AddPrice.objects.values('data_coleta').aggregate(ultima_data_coleta=Max('data_coleta'))
    ultima_data = ultima_coleta['ultima_data_coleta']

    # Dados para cache (sem o objeto filter)
    cache_data = {
        'cidade': cidade,
        'preco_min': preco_min,
        'preco_max': preco_max,
        'preco_avg': preco_avg,
        'ultima_data': ultima_data,
        'ano': ano,
        'mes': mes
    }
    cache.set(cache_key, cache_data, 300)  # 5 minutos
    
    # Dados completos para o template (incluindo o filter)
    base_queryset = AddPrice.objects.exclude(produto_id=3, pesquisa_origem_id=2, produto_id__isnull=True)
    fil = MainFilter(request.GET, queryset=base_queryset)
    
    data = {
        'fil': fil,
        **cache_data
    }

    return render(request, 'p_cartao_precos.html', data)


@login_required
def p_plans(request):
    return render(request, 'p_plans.html')


@login_required
def p_monitorar_produtos(request):
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        user_profile = Profile.objects.create(user=request.user)
    
    if not user_profile.cidade:
        from django.contrib import messages
        messages.warning(request, 'Por favor, configure sua cidade no perfil para visualizar os dados.')
        return redirect('p_profile')

    # Gerar chave de cache baseada nos filtros e usuário
    cache_key = f"monitorar_produtos:{request.user.id}:{str(sorted(request.GET.items()))}:{user_profile.cidade}"
    cached_result = cache.get(cache_key)
    if cached_result:
        # Recriar o filter para o template
        base_queryset = AddPrice.objects.exclude(
            produto_id=3, 
            pesquisa_origem_id=2, 
            produto_id__isnull=True
        ).filter(
            gasstation_id__cidade=user_profile.cidade
        )
        
        # Aplicar filtros padrão se nenhum filtro específico for fornecido
        if not any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano']):
            base_queryset = base_queryset.filter(
                data_coleta__gte=datetime.now() - timedelta(days=15)
            )
        
        filter = MainFilter(request.GET, queryset=base_queryset)
        cached_result['filter'] = filter
        return render(request, 'p_mapeei.html', cached_result)

    # Campos necessários para as listas
    CAMPOS_POSTO = [
        'gasstation_id', 'gasstation_id__razao', 'gasstation_id__bandeira',
        'gasstation_id__cidade', 'gasstation_id__estado'
    ]
    CAMPOS_PRECO = ['preco_revenda', 'data_coleta']

    base_queryset = AddPrice.objects.exclude(
        produto_id=3, 
        pesquisa_origem_id=2, 
        produto_id__isnull=True
    ).filter(
        gasstation_id__cidade=user_profile.cidade
    )

    # Aplicar filtros padrão se nenhum filtro específico for fornecido
    if not any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano']):
        base_queryset = base_queryset.filter(
            data_coleta__gte=datetime.now() - timedelta(days=90)
        )

    filter = MainFilter(request.GET, queryset=base_queryset)
    profile = Profile.objects.all()
    cidade_usuario = user_profile.cidade
    uf_usuario = user_profile.estado

    # Agregações principais
    aggregates = filter.qs.aggregate(
        min_price=Min('preco_revenda'),
        min_date=Min('data_coleta'),
        max_price=Max('preco_revenda'),
        max_date=Max('data_coleta'),
        avg_price=Avg('preco_revenda'),
        total_count=Count('id'),
        total_postos=Count('gasstation_id', distinct=True)
    )
    menor_preco = aggregates.get('min_price')
    maior_preco = aggregates.get('max_price')
    media_preco = aggregates.get('avg_price')
    total_linhas_pesquisa = aggregates.get('total_count')
    total_postos = aggregates.get('total_postos')

    variance = 0
    variance_percent = 0
    if maior_preco is not None and menor_preco is not None:
        variance = maior_preco - menor_preco
        if media_preco and media_preco > 0:
            variance_percent = (variance / media_preco) * 100

    # Preço médio mensal
    preco_medio_mensal = list(
        filter.qs.annotate(
            mes=ExtractMonth('data_coleta'),
            ano=ExtractYear('data_coleta')
        ).values('mes', 'ano').annotate(
            preco_medio=Avg('preco_revenda')
        ).order_by('ano', 'mes')
    )
    today = datetime.now()

    # Top 10 postos mais baratos
    top_10_postos_mais_baratos = list(
        filter.qs.values('gasstation_id__razao', 'gasstation_id__id')
        .annotate(preco_medio=Avg('preco_revenda'))
        .order_by('preco_medio')[:10]
    )
    # Top 10 postos mais caros
    top_10_postos_mais_caros = list(
        filter.qs.values('gasstation_id__razao', 'preco_revenda')
        .order_by('-preco_revenda')[:10]
    )
    # Preços por postos
    precos_por_postos = list(
        filter.qs.values('preco_revenda')
        .annotate(quantidade_postos=Count('gasstation_id', distinct=True))
        .order_by('-quantidade_postos')[:9]
    )
    # Postos com preços
    postos_com_precos = list(
        filter.qs.values(*CAMPOS_POSTO)
        .annotate(
            preco_minimo=Min('preco_revenda'),
            preco_maximo=Max('preco_revenda'),
            preco_medio=Avg('preco_revenda'),
            total_registros=Count('id'),
            data_primeira=Min('data_coleta'),
            data_ultima=Max('data_coleta')
        ).order_by('gasstation_id__razao')
    )
    # Postos por preço
    postos_por_preco = list(
        filter.qs.values('gasstation_id', 'gasstation_id__razao', 'preco_revenda')
        .annotate(
            data_minima=Min('data_coleta'),
            data_maxima=Max('data_coleta'),
            data_preco=F('data_maxima') - F('data_minima'),
            quantidade_postos=Count('preco_revenda') * 7
        ).order_by('gasstation_id__razao')
    )
    # Counts para menor e maior preço
    menor_preco_count = 0
    data_menor_preco = None
    maior_preco_count = 0
    data_maior_preco = None
    if menor_preco is not None:
        menor_preco_count = filter.qs.filter(preco_revenda=menor_preco).count()
        data_menor_preco = filter.qs.filter(preco_revenda=menor_preco).aggregate(min_date=Min('data_coleta'))['min_date']
    if maior_preco is not None:
        maior_preco_count = filter.qs.filter(preco_revenda=maior_preco).count()
        data_maior_preco = filter.qs.filter(preco_revenda=maior_preco).aggregate(max_date=Max('data_coleta'))['max_date']

    # Dados para cache (sem o objeto filter que contém funções lambda)
    cache_data = {
        'profile': profile,
        'cidade_usuario': cidade_usuario,
        'uf_usuario': uf_usuario,
        'menor_preco': menor_preco,
        'data_menor_preco': data_menor_preco,
        'maior_preco': maior_preco,
        'data_maior_preco': data_maior_preco,
        'media_preco': media_preco,
        'variance': variance,
        'variance_percent': variance_percent,
        'total_linhas_pesquisa': total_linhas_pesquisa,
        'today': today,
        'total_postos': total_postos,
        'preco_medio_mensal': preco_medio_mensal,
        'top_10_postos_mais_baratos': top_10_postos_mais_baratos,
        'top_10_postos_mais_caros': top_10_postos_mais_caros,
        'menor_preco_count': menor_preco_count,
        'maior_preco_count': maior_preco_count,
        'precos_por_postos': precos_por_postos,
        'postos_por_preco': postos_por_preco,
        'postos_com_precos': postos_com_precos
    }
    cache.set(cache_key, cache_data, 300)  # 5 minutos
    
    # Dados completos para o template (incluindo o filter)
    data = {
        'filter': filter,
        **cache_data
    }
    return render(request, 'p_mapeei.html', data)


@login_required
def p_lista_preco(request):
    # Definir os campos realmente necessários para o template
    CAMPOS = [
        'id',
        'data_coleta',
        'preco_revenda',
        'cnpj',
        'gasstation_id__razao',
        'gasstation_id__cidade',
        'gasstation_id__estado',
        'gasstation_id__bairro',
        'gasstation_id__bandeira',
        'produto_id__produto',
        'pesquisa_origem__origem',
    ]

    # Query base otimizada
    base_queryset = AddPrice.objects.exclude(
        produto_id=3,
        pesquisa_origem_id=2
    ).select_related(
        'gasstation_id',
        'produto_id',
        'pesquisa_origem'
    ).values(*CAMPOS).order_by('preco_revenda')

    # Verificar se o usuário tem profile, se não tiver, criar um
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        user_profile = Profile.objects.create(user=request.user)
    
    # Aplicar filtros padrão se nenhum filtro específico for fornecido
    if not any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano']):
        base_queryset = base_queryset.filter(
            data_coleta__gte=datetime.now() - timedelta(days=15),
            produto_id=1,
            pesquisa_origem_id=1,
            gasstation_id__cidade=user_profile.cidade,
        )

    # Gerar chave de cache baseada nos filtros
    cache_key = f"lista_preco:{request.user.id}:{str(sorted(request.GET.items()))}"
    cached_result = cache.get(cache_key)
    if cached_result:
        list_price, total_linhas_pesquisa = cached_result
    else:
        # Aplicar filtros
        f = MainFilter(request.GET, queryset=base_queryset)
        list_price = list(f.qs)
        total_linhas_pesquisa = f.qs.distinct().count()
        cache.set(cache_key, (list_price, total_linhas_pesquisa), 300)  # 5 minutos

    # Preparar dados para o template
    data = {
        'list_price': list_price,
        'filter': MainFilter(request.GET, queryset=base_queryset),
        'total_linhas_pesquisa': total_linhas_pesquisa
    }
    
    return render(request, 'p_lista_preco.html', data)


@login_required
def add_price(request):
    
    try:
        user_profile = request.user.profile
    except Profile.DoesNotExist:
        user_profile = Profile.objects.create(user=request.user)
    
    form = NewPrice(request.POST or None)
    form.fields['gasstation_id'].queryset = GasStation.objects.filter(cidade=user_profile.cidade)

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
        
        pesquisa_origem = PesquisaOrigem.objects.get(id=2)
        addprice.pesquisa_origem = pesquisa_origem

        if addprice.produto_id_id == 3:
            addprice.unidade_medida = "R$ / 13 kg"
        elif addprice.produto_id_id == 7:
            addprice.unidade_medida = "R$ / m³"
        else:
            addprice.unidade_medida = "R$ / litro"

        gasstation = GasStation.objects.get(id=addprice.gasstation_id_id)
        addprice.cnpj = gasstation.cnpj

        produto = Produto.objects.get(id=addprice.produto_id_id)
        addprice.produto = produto.produto

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
def p_radar_precos(request):
    return render(request, 'p_radar_precos.html')

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


@login_required
def logout(request):
    return render(request, 'registration/logout.html')


@login_required
def logout_view(request):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    messages.success(request, 'Você saiu com sucesso.')
    return redirect('login')


def new_register(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            # Obtém o valor do email do formulário
            email_value = form.cleaned_data.get('username')
            user.username = email_value
            user.email = email_value  # Garante que o email seja salvo corretamente

            # Enviar email de notificação (com tratamento de erro)
            try:
                send_mail(
                    f'O cliente {form.cleaned_data.get("first_name", "Não informado")} se cadastrou!',
                    f'''Novo lead/usuário cadastrado em app.alta.bi!

                    Dados do cliente:
                    Nome: {form.cleaned_data.get('first_name', 'Não informado')}
                    Sobrenome: {form.cleaned_data.get('last_name', 'Não informado')}
                    Cargo: {form.cleaned_data.get('cargo', 'Não informado')}
                    Telefone: {form.cleaned_data.get('telefone', 'Não informado')}
                    Email: {form.cleaned_data.get('username', 'Não informado')}
                    Empresa: {form.cleaned_data.get('empresa', 'Não informada')}
                    Cidade: {form.cleaned_data.get('cidade', 'Não informada')}
                    Estado: {form.cleaned_data.get('estado', 'Não informado')}
                    Data de cadastro: {user.date_joined.strftime('%d/%m/%Y às %H:%M')}

                    Este é um email automático do sistema Alta.''',
                    settings.DEFAULT_FROM_EMAIL,
                    ['ricardo.pasqualino@gmail.com', 'ricardo@alta.bi', 'joao@alta.bi'],
                    fail_silently=False,
                )
                print("✅ Email de notificação enviado com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao enviar email: {str(e)}")
                print("📧 O cadastro foi realizado, mas o email de notificação falhou")
                
                # Análise detalhada do erro
                if "535" in str(e):
                    print("🔍 Erro 535: Problema de autenticação do Gmail")
                    print("   - Verifique se a verificação em duas etapas está ativada")
                    print("   - Gere uma nova senha de app em: https://myaccount.google.com/apppasswords")
                    print("   - Configure EMAIL_HOST_PASSWORD no Render com a senha de app")
                elif "587" in str(e):
                    print("🔍 Erro de conexão SMTP na porta 587")
                elif "timeout" in str(e).lower():
                    print("🔍 Timeout na conexão SMTP")
                elif "authentication" in str(e).lower():
                    print("🔍 Erro de autenticação SMTP")
                    print("   - Verifique EMAIL_HOST_USER e EMAIL_HOST_PASSWORD no Render")
                else:
                    print(f"🔍 Outro tipo de erro: {type(e).__name__}")
                    print(f"🔍 Mensagem completa: {str(e)}")
            
            user = form.save()
            
            # Atualiza o perfil com os dados adicionais se necessário
            if hasattr(user, 'profile'):
                user.profile.empresa = form.cleaned_data.get('empresa')
                user.profile.save()
            
            # Enviar webhook (opcional - não quebra o cadastro se falhar)
            try:
                # Usar HTTP para desenvolvimento local, HTTPS para produção
                protocol = 'http' if settings.DEBUG else 'https'
                
                # Limpar a URL para evitar duplicação de protocolo
                clean_url = settings.RENDER_EXTERNAL_URL
                if clean_url.startswith('https://'):
                    clean_url = clean_url.replace('https://', '')
                elif clean_url.startswith('http://'):
                    clean_url = clean_url.replace('http://', '')
                
                webhook_url = f"{protocol}://{clean_url}/webhook-test/79725962-e3a4-491e-8c56-852ee30e8f47/"
                
                if settings.DEBUG:
                    print(f"🔗 DEBUG: Protocolo = {protocol}")
                    print(f"🔗 DEBUG: RENDER_EXTERNAL_URL = {settings.RENDER_EXTERNAL_URL}")
                    print(f"🔗 DEBUG: URL limpa = {clean_url}")
                    print(f"🔗 DEBUG: URL completa = {webhook_url}")
                
                webhook_data = {
                    'nome': user.first_name,
                    'sobrenome': user.last_name,
                    'email': user.email,
                    'empresa': getattr(user.profile, 'empresa', ''),
                    'data_cadastro': user.date_joined.strftime('%d/%m/%Y %H:%M:%S')
                }
                
                response = requests.post(webhook_url, json=webhook_data, timeout=5)
                if response.status_code == 200:
                    print("✅ Webhook enviado com sucesso")
                else:
                    print(f"⚠️ Webhook retornou status {response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Erro ao enviar webhook: {str(e)}")
                print("🔗 O cadastro foi realizado, mas o webhook falhou")
            
            messages.success(request, 'Conta criada com sucesso! Você já pode fazer login.')
            return redirect('login')
        else:
            # Verifica especificamente os erros de cada campo
            if 'username' in form.errors:
                messages.error(request, 'Este email já está em uso. Por favor, escolha outro.')
            elif 'email' in form.errors:
                messages.error(request, 'Este email já está cadastrado. Por favor, use outro email ou faça login.')
            elif 'empresa' in form.errors:
                messages.error(request, 'Por favor, informe o nome da sua empresa.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Erro no campo {field}: {error}')

    data = {'form': form}
    return render(request, 'p_register.html', data)


def password_reset(request):
    return render(request, 'registration/password_form.html')


def confirmacao_email_recuperacao(request):
    return render(request, 'registration/password_done.html')