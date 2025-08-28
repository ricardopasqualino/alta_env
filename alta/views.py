import os
import json
import requests

from datetime import datetime, timedelta, timezone
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

from .forms import ( 
    NewPrice, 
    CreateUserForm,
    NewLeadForm
)

from .models import (
    AddPrice, 
    PesquisaOrigem, 
    Profile,
    GasStation,
    Produto,
    FAQ,
    Cidade
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

    fil = MainFilter(request.GET, queryset=AddPrice.objects.all())

    cidade = request.GET.get('cidade')
    mes = request.GET.get('mes')
    ano = request.GET.get('ano')
    
    # Gerar uma chave de cache única baseada nos filtros
    cache_key_min = f"preco_min_{cidade}_{mes}_{ano}"
    cache_key_avg = f"preco_avg_{cidade}_{mes}_{ano}"
    cache_key_max = f"preco_max_{cidade}_{mes}_{ano}"
    
    # Verificar se os valores já estão no cache
    preco_min = cache.get(cache_key_min)
    preco_avg = cache.get(cache_key_avg)
    preco_max = cache.get(cache_key_max)
    
    if not preco_min:
        preco_min = AddPrice.objects.filter(gasstation_id__cidade=cidade).values('produto_id__produto').annotate(preco_minimo=Min('preco_revenda'))
        if mes:
            preco_min = preco_min.filter(data_coleta__month=mes)
        if ano:
            preco_min = preco_min.filter(data_coleta__year=ano)
        cache.set(cache_key_min, preco_min, 3600)
    
    if not preco_avg:
        preco_avg = AddPrice.objects.filter(gasstation_id__cidade=cidade).values('produto_id__produto').annotate(preco_medio=Avg('preco_revenda'))
        if mes:
            preco_avg = preco_avg.filter(data_coleta__month=mes)
        if ano:
            preco_avg = preco_avg.filter(data_coleta__year=ano)
        cache.set(cache_key_avg, preco_avg, 3600)

    if not preco_max:
        preco_max = AddPrice.objects.filter(gasstation_id__cidade=cidade).values('produto_id__produto').annotate(preco_maximo=Max('preco_revenda'))
        if mes:
            preco_max = preco_max.filter(data_coleta__month=mes)
        if ano:
            preco_max = preco_max.filter(data_coleta__year=ano)
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

    # Verifica se o usuário está usando algum filtro
    filtros_ativos = any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano'])

    # Se não há filtros, filtra pela cidade do usuário e últimos 90 dias
    if not filtros_ativos:
        cidade_usuario = user_profile.cidade.cidade if user_profile.cidade else 'sem_cidade'
        cache_key = f"monitorar_produtos:{cidade_usuario}:{str(sorted(request.GET.items()))}"
    else:
        # Se há filtros, busca para todo o Brasil (não filtra por cidade)
        cidade_usuario = None
        cache_key = f"monitorar_produtos:brasil:{str(sorted(request.GET.items()))}"

    cached_result = cache.get(cache_key)
    
    if cached_result:
        # Recria o filter para o template
        if not filtros_ativos:
            # Query base: cidade do usuário e últimos 90 dias
            base_queryset = AddPrice.objects.exclude(
                produto_id=3, 
                pesquisa_origem_id=2, 
                produto_id__isnull=True
            ).filter(
                gasstation_id__cidade=user_profile.cidade,
                data_coleta__gte=datetime.now() - timedelta(days=90)
            )
            # Filtros padrão: últimos 90 dias, gasolina comum, pesquisa oficial
            base_queryset = base_queryset.filter(
                produto_id=1,
                pesquisa_origem_id=1
            )
        else:
            # Query base: todo o Brasil, últimos 90 dias
            base_queryset = AddPrice.objects.exclude(
                produto_id=3, 
                pesquisa_origem_id=2, 
                produto_id__isnull=True
            ).filter(
                data_coleta__gte=datetime.now() - timedelta(days=90)
            )
            # Não aplica filtro padrão, pois o usuário está filtrando

        filter = MainFilter(request.GET, queryset=base_queryset)
        cached_result['filter'] = filter
        return render(request, 'p_mapeei.html', cached_result)

    # Campos necessários para as listas
    CAMPOS_POSTO = [
        'gasstation_id', 'gasstation_id__razao', 'gasstation_id__bandeira',
        'gasstation_id__cidade', 'gasstation_id__estado'
    ]
    CAMPOS_PRECO = ['preco_revenda', 'data_coleta']

    # Monta a query base conforme filtros
    if not filtros_ativos:
        # Query base: cidade do usuário e últimos 90 dias
        base_queryset = AddPrice.objects.exclude(
            produto_id=3, 
            pesquisa_origem_id=2, 
            produto_id__isnull=True
        ).filter(
            gasstation_id__cidade=user_profile.cidade,
            data_coleta__gte=datetime.now() - timedelta(days=90)
        )
        # Filtros padrão: últimos 90 dias, gasolina comum, pesquisa oficial
        base_queryset = base_queryset.filter(
            produto_id=1,
            pesquisa_origem_id=1
        )
    else:
        # Query base: todo o Brasil, últimos 90 dias
        base_queryset = AddPrice.objects.exclude(
            produto_id=3, 
            pesquisa_origem_id=2, 
            produto_id__isnull=True
        ).filter(
            data_coleta__gte=datetime.now() - timedelta(days=90)
        )
        # Não aplica filtro padrão, pois o usuário está filtrando

    filter = MainFilter(request.GET, queryset=base_queryset)
    profile = Profile.objects.all()
    cidade_usuario = user_profile.cidade
    uf_usuario = user_profile.estado

    # Agregações principais (otimizadas)
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

    # Preço médio mensal (otimizado)
    preco_medio_mensal = list(
        filter.qs.annotate(
            mes=ExtractMonth('data_coleta'),
            ano=ExtractYear('data_coleta')
        ).values('mes', 'ano').annotate(
            preco_medio=Avg('preco_revenda')
        ).order_by('ano', 'mes')[:12]  # Limitar a 12 meses
    )
    today = datetime.now()

    # Top 10 postos mais baratos (otimizado)
    top_10_postos_mais_baratos = list(
        filter.qs.select_related('gasstation_id')
        .values('gasstation_id__razao', 'gasstation_id__id')
        .annotate(preco_medio=Avg('preco_revenda'))
        .order_by('preco_medio')[:10]
    )
    # Top 10 postos mais caros (otimizado)
    top_10_postos_mais_caros = list(
        filter.qs.select_related('gasstation_id')
        .values('gasstation_id__razao', 'preco_revenda')
        .order_by('-preco_revenda')[:10]
    )
    # Preços por postos (otimizado)
    precos_por_postos = list(
        filter.qs.values('preco_revenda')
        .annotate(quantidade_postos=Count('gasstation_id', distinct=True))
        .order_by('-quantidade_postos')[:9]
    )
    # Postos com preços (otimizado)
    postos_com_precos = list(
        filter.qs.select_related('gasstation_id')
        .values(*CAMPOS_POSTO)
        .annotate(
            preco_minimo=Min('preco_revenda'),
            preco_maximo=Max('preco_revenda'),
            preco_medio=Avg('preco_revenda'),
            total_registros=Count('id'),
            data_primeira=Min('data_coleta'),
            data_ultima=Max('data_coleta')
        ).order_by('gasstation_id__razao')
    )
    
    # Adicionar preços detalhados para cada posto (otimizado)
    for posto in postos_com_precos:
        precos_detalhados = list(
            filter.qs.filter(
                gasstation_id=posto['gasstation_id']
            ).values('preco_revenda').annotate(
                quantidade_vezes=Count('id'),
                data_inicio=Min('data_coleta'),
                data_fim=Max('data_coleta')
            ).order_by('-data_fim')[:10]  # Limitar a 10 preços por posto
        )
        
        posto['precos_detalhados'] = precos_detalhados

        
    # Postos por preço (otimizado)
    postos_por_preco = list(
        filter.qs.select_related('gasstation_id')
        .values('gasstation_id', 'gasstation_id__razao', 'preco_revenda')
        .annotate(
            data_minima=Min('data_coleta'),
            data_maxima=Max('data_coleta'),
            data_preco=F('data_maxima') - F('data_minima'),
            quantidade_postos=Count('preco_revenda') * 7
        ).order_by('gasstation_id__razao')[:20]  # Limitar a 20 postos
    )
    # Counts para menor e maior preço (otimizado)
    menor_preco_count = 0
    data_menor_preco = None
    maior_preco_count = 0
    data_maior_preco = None
    
    if menor_preco is not None:
        menor_preco_data = filter.qs.filter(preco_revenda=menor_preco).aggregate(
            count=Count('id'),
            min_date=Min('data_coleta')
        )
        menor_preco_count = menor_preco_data['count']
        data_menor_preco = menor_preco_data['min_date']
    
    if maior_preco is not None:
        maior_preco_data = filter.qs.filter(preco_revenda=maior_preco).aggregate(
            count=Count('id'),
            max_date=Max('data_coleta')
        )
        maior_preco_count = maior_preco_data['count']
        data_maior_preco = maior_preco_data['max_date']

    # Dados para cache (sem o objeto filter que contém funções lambda)
    cache_data = {
        'profile': profile,
        'cidade_usuario': user_profile.cidade,
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
    cache.set(cache_key, cache_data, 600)  # 10 minutos - cache mais longo para melhor performance
    
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
    # Otimização: buscar primeiro a cidade da tabela Cidade (menor) e depois filtrar GasStation
    if user_profile.cidade:
        # Busca o nome da cidade da tabela Cidade (mais eficiente)
        nome_cidade = user_profile.cidade.cidade
        # Filtra GasStation usando o nome da cidade
        form.fields['gasstation_id'].queryset = GasStation.objects.filter(cidade=nome_cidade)
    else:
        form.fields['gasstation_id'].queryset = GasStation.objects.none()
    
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
            # 1. PRIMEIRO: Salvar o usuário no banco de dados
            user = form.save(commit=False)
            email_value = form.cleaned_data.get('username')
            user.username = email_value
            user.email = email_value
            user = form.save()  # Agora o usuário está salvo no banco
            
            print(f"✅ Usuário criado com sucesso: {user.username}")
            
            # 2. SEGUNDO: Enviar email de notificação
            try:
                send_mail(
                    f'O cliente {user.first_name or "Não informado"} se cadastrou!',
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
                    ['ricardo.pasqualino@gmail.com', 'ricardo@alta.bi'],
                    fail_silently=False,
                )
                print("✅ Email de notificação enviado com sucesso")
            except Exception as e:
                print(f"⚠️ Erro ao enviar email: {str(e)}")
                print("📧 O cadastro foi realizado, mas o email de notificação falhou")
            
            # 3. TERCEIRO: Enviar dados para webhook N8N
            try:
                print("🔄 Iniciando integração com webhook N8N...")
                
                # Obter dados do usuário e profile após salvar no banco
                try:
                    profile = user.profile
                    print(f"✅ Profile encontrado para o usuário: {profile}")
                except Profile.DoesNotExist:
                    print("⚠️ Profile não encontrado para o usuário")
                    profile = None
                
                # Montar os dados do formulário no formato esperado pelo webhook
                payload = {
                    "nome": user.first_name or '',
                    "sobrenome": user.last_name or '',
                    "email": user.email or '',
                    "telefone": profile.telefone if profile and profile.telefone else form.cleaned_data.get('telefone', ''),
                    "empresa": profile.empresa if profile and profile.empresa else form.cleaned_data.get('empresa', ''),
                    "cargo": profile.cargo if profile and profile.cargo else form.cleaned_data.get('cargo', ''),
                    "cidade": profile.cidade.cidade if profile and profile.cidade else (form.cleaned_data.get('cidade').cidade if form.cleaned_data.get('cidade') else ''),
                    "estado": profile.estado.estado if profile and profile.estado else (form.cleaned_data.get('cidade').estado.estado if form.cleaned_data.get('cidade') and form.cleaned_data.get('cidade').estado else ''),
                    "data_cadastro": user.date_joined.strftime('%d/%m/%Y') if user.date_joined else '',
                    "plano": "Grátis",
                }

                webhook_url = "https://n8n-webhook-cadastro.onrender.com/webhook/03ab55a3-36a3-41c2-b585-082382181d7e"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "Django-Alta-Webhook/1.0"
                }

                print(f"📤 Enviando dados do formulário para o webhook: {webhook_url}")
                print(f"📋 Payload: {payload}")

                response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)

                print(f"📥 Resposta do webhook - Status: {response.status_code}")
                print(f"📥 Resposta do webhook - Conteúdo: {response.text}")

                if response.status_code == 200 or response.status_code == 201:
                    print("✅ Dados enviados com sucesso para o webhook")
                else:
                    print(f"❌ Erro ao enviar dados para o webhook - Status: {response.status_code}")
                    print(f"❌ Resposta de erro: {response.text}")
            except Exception as e:
                print(f"❌ Erro ao enviar dados para o webhook: {str(e)}")
                print(f"❌ Tipo de erro: {type(e).__name__}")
            
            # 4. QUARTO: Integração com RD Station
            try:
                print("🔄 Iniciando integração com RD Station...")
                
                # Verificar se as configurações do RD Station estão disponíveis
                if not hasattr(settings, 'RD_STATION_URL') or not hasattr(settings, 'RD_STATION_TOKEN'):
                    print("⚠️ Configurações do RD Station não encontradas")
                    messages.warning(request, 'Usuário cadastrado com sucesso, mas configurações do RD Station não encontradas. Faça login para acessar o sistema.')
                    return redirect('login')
                
                if not settings.RD_STATION_URL or not settings.RD_STATION_TOKEN:
                    print("⚠️ URL ou Token do RD Station não configurados")
                    messages.warning(request, 'Usuário cadastrado com sucesso, mas configurações do RD Station incompletas. Faça login para acessar o sistema.')
                    return redirect('login')
                
                url = f"{settings.RD_STATION_URL}?token={settings.RD_STATION_TOKEN}"
                
                # Validar dados antes de enviar
                if not user.first_name or not user.last_name or not user.email:
                    print("⚠️ Dados obrigatórios não encontrados para RD Station")
                    print(f"   Nome: {user.first_name}")
                    print(f"   Sobrenome: {user.last_name}")
                    print(f"   Email: {user.email}")
                    messages.warning(request, 'Usuário cadastrado com sucesso, mas dados obrigatórios não encontrados para integração. Faça login para acessar o sistema.')
                    return redirect('login')

                # Preparar payload básico com telefone no formato correto
                payload = { "contact": {
                        "name": f"{user.first_name} {user.last_name}",
                        "emails": [{ "email": user.email }]
                    } }
                
                # Adicionar telefone se disponível (no formato correto)
                telefone = form.cleaned_data.get('telefone', '')
                if telefone and telefone.strip():
                    # Limpar e formatar telefone (remover caracteres especiais)
                    telefone_limpo = ''.join(filter(str.isdigit, telefone))
                    if len(telefone_limpo) >= 10:  # Telefone deve ter pelo menos 10 dígitos
                        payload["contact"]["phones"] = [
                            {
                                "phone": telefone_limpo
                            }
                        ]
                        print(f"📞 Telefone adicionado: {telefone_limpo}")
                    else:
                        print(f"⚠️ Telefone inválido: {telefone} (muito curto)")
                else:
                    print("⚠️ Telefone não fornecido")
                
                # Adicionar campos customizados do RD Station
                custom_fields = {}
                
                try:
                    # Tentar obter o profile do usuário
                    profile = user.profile
                    
                    # Adicionar empresa
                    if profile.empresa:
                        custom_fields["empresa"] = profile.empresa
                        print(f"🏢 Empresa adicionada: {profile.empresa}")
                    
                    # Adicionar cargo
                    if profile.cargo:
                        custom_fields["cargo"] = profile.cargo
                        print(f"💼 Cargo adicionado: {profile.cargo}")
                    
                    # Adicionar cidade
                    if profile.cidade:
                        custom_fields["cidade"] = profile.cidade.cidade
                        print(f"🏙️ Cidade adicionada: {profile.cidade.cidade}")
                    
                    # Adicionar estado
                    if profile.estado:
                        custom_fields["estado"] = profile.estado.estado
                        print(f"🗺️ Estado adicionado: {profile.estado.estado}")
                        
                except Profile.DoesNotExist:
                    print("⚠️ Profile não encontrado para o usuário")
                
                # Adicionar campos customizados ao payload
                if custom_fields:
                    payload["contact"]["contact_custom_fields"] = custom_fields
                    print(f"📋 Campos customizados adicionados: {list(custom_fields.keys())}")
                
                headers = {
                    "accept": "application/json",
                    "content-type": "application/json"
                }

                print(f"📤 Enviando dados para RD Station: {url}")
                print(f"📋 Payload: {json.dumps(payload, indent=2)}")
                
                response = requests.post(url, json=payload, headers=headers, timeout=30)
                
                print(f"📥 Resposta do RD Station - Status: {response.status_code}")
                print(f"📥 Resposta do RD Station - Conteúdo: {response.text}")
                
                if response.status_code == 200 or response.status_code == 201:
                    print("✅ Contato criado com sucesso no RD Station")
                    messages.success(request, 'Usuário criado com sucesso! Faça login agora mesmo.')
                else:
                    print(f"❌ Erro ao criar contato no RD Station - Status: {response.status_code}")
                    print(f"❌ Resposta de erro: {response.text}")
                    messages.warning(request, 'Usuário cadastrado com sucesso, mas houve um problema na integração com o RD Station. Faça login para acessar o sistema.')
                    
            except requests.exceptions.Timeout:
                print("⏰ Timeout na requisição para RD Station")
                messages.warning(request, 'Usuário cadastrado com sucesso, mas houve timeout na integração com o RD Station. Faça login para acessar o sistema.')
            except requests.exceptions.ConnectionError:
                print("🔌 Erro de conexão com RD Station")
                messages.warning(request, 'Usuário cadastrado com sucesso, mas houve erro de conexão com o RD Station. Faça login para acessar o sistema.')
            except requests.exceptions.RequestException as e:
                print(f"❌ Erro na requisição para RD Station: {str(e)}")
                messages.warning(request, 'Usuário cadastrado com sucesso, mas houve erro na integração com o RD Station. Faça login para acessar o sistema.')
            except Exception as e:
                print(f"❌ Erro inesperado na integração com RD Station: {str(e)}")
                print(f"❌ Tipo de erro: {type(e).__name__}")
                messages.warning(request, 'Usuário cadastrado com sucesso, mas houve erro inesperado na integração com o RD Station. Faça login para acessar o sistema.')
            
            # 5. QUINTO: Redirecionar para a página de login após cadastro bem-sucedido
            return redirect('login')

    data = {'form': form}
    return render(request, 'p_register.html', data)


def password_reset(request):
    return render(request, 'registration/password_form.html')


def confirmacao_email_recuperacao(request):
    return render(request, 'registration/password_done.html')


def lp_topo(request):
    if request.method == 'POST':
        form = NewLeadForm(request.POST)
        if form.is_valid():
            lead = form.save()
            messages.success(request, 'Lead cadastrado com sucesso!')
            # Envia os dados do lead para o email ricardo@alta.bi
            from django.core.mail import send_mail

            assunto = "Novo Lead cadastrado no LP Topo"
            mensagem = f"""
            Novo lead cadastrado:

            Nome: {lead.nome}
            Telefone: {lead.telefone}
            Data de Cadastro: {lead.data_cadastro.strftime('%d/%m/%Y %H:%M')}
            """

            send_mail(
                assunto,
                mensagem,
                'nao-responda@alta.bi',  # Remetente
                ['ricardo@alta.bi'],     # Destinatário
                fail_silently=True,
            )
            return redirect('lp_topo')
        else:
            messages.error(request, 'Erro ao cadastrar lead. Verifique os dados.')
    else:
        form = NewLeadForm()
    data = {'form': form}
    return render(request, 'lp_topo.html', data)
