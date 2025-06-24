from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.db.models import Sum, Avg, Count, Max, Min, Q
from django.core.cache import cache
from django.contrib import messages
import json
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .openai_utils import generate_price_embedding, calculate_similarity
from .ia_utils import processar_pergunta_ia, vetorizar_texto
from django.contrib.auth import authenticate, login
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models import F, ExpressionWrapper, DurationField

from .filters import MainFilter

from .forms import NewPrice, CreateUserForm

from .models import (
    AddPrice, 
    PesquisaOrigem, 
    Profile,
    Cidade,
    Estado,
    GasStation,
    Produto,
    PriceEmbedding
)


@login_required
def index(request):
    return render(request, 'index.html')


@login_required
def p_cartao_precos(request):
    fil = MainFilter(request.GET, queryset=AddPrice.objects.exclude(produto_id=3, pesquisa_origem_id=2, produto_id__isnull=True))
    cidade = request.GET.get('cidade')
    ano = request.GET.get('ano')
    mes = request.GET.get('mes')
    
    # Gerar uma chave de cache única baseada na cidade
    cache_key = f"precos_cidade_{cidade}_{ano}_{mes}"
    
    # Tentar obter todos os dados do cache
    cached_data = cache.get(cache_key)
    
    if cached_data:
        preco_min, preco_avg, preco_max = cached_data
    else:
        # Otimizar a query base
        base_query = AddPrice.objects.filter(
            gasstation_id__cidade=cidade,
            data_coleta__year=ano,
            data_coleta__month=mes
        ).exclude(produto_id=3).select_related(
            'produto_id'
        ).only(
            'produto_id__produto',
            'preco_revenda'
        )
        
        # Calcular todos os valores em uma única query
        preco_min = base_query.values(
            'produto_id__produto'
        ).annotate(
            preco_minimo=Min('preco_revenda')
        )
        
        preco_avg = base_query.values(
            'produto_id__produto'
        ).annotate(
            preco_medio=Avg('preco_revenda')
        )
        
        preco_max = base_query.values(
            'produto_id__produto'
        ).annotate(
            preco_maximo=Max('preco_revenda')
        )
        
        # Armazenar no cache
        cache.set(cache_key, (preco_min, preco_avg, preco_max), 3600)

    ultima_coleta = AddPrice.objects.aggregate(ultima_data_coleta=Max('data_coleta'))
    ultima_data = ultima_coleta['ultima_data_coleta']

    data = {
        'fil': fil,
        'cidade': cidade,
        'preco_min': preco_min,
        'preco_max': preco_max,
        'preco_avg': preco_avg,
        'ultima_data': ultima_data,
        'ano': ano,
        'mes': mes
    }

    return render(request, 'p_cartao_precos.html', data)


@login_required
def p_plans(request):
    return render(request, 'p_plans.html')


@login_required
def p_ia(request):
    return render(request, 'p_ia.html')


@login_required
def p_monitorar_concorrentes(request):
    
    filter = MainFilter(
        request.GET, 
        queryset=AddPrice.objects.exclude(
            produto_id=3, 
            pesquisa_origem_id=2, 
            produto_id__isnull=True
        ).filter(
            gasstation_id__cidade=request.user.profile.cidade,
            gasstation_id__estado=request.user.profile.estado
        )
    )

    cidade_usuario = request.user.profile.cidade
    uf_usuario = request.user.profile.estado

    total_linhas_pesquisa = filter.qs.distinct().count()

    # Obter lista de razões sociais dos postos
    razoes = filter.qs.values_list('gasstation_id__razao', flat=True).distinct()

    preco_medio_mensal = filter.qs.annotate(
        mes=ExtractMonth('data_coleta'),
        ano=ExtractYear('data_coleta')
    ).values('mes', 'ano').annotate(
        preco_medio=Avg('preco_revenda')
    ).order_by('ano', 'mes')

    aggregates = filter.qs.aggregate(
        min_price=Min('preco_revenda'),
        min_date=Min('data_coleta'),
        max_price=Max('preco_revenda'),
        max_date=Max('data_coleta'),
        avg_price=Avg('preco_revenda')
    )

    menor_preco = filter.qs.aggregate(min_price=Min('preco_revenda'))['min_price']
    data_menor_preco = filter.qs.aggregate(min_date=Min('data_coleta'))['min_date']
    maior_preco = filter.qs.aggregate(max_price=Max('preco_revenda'))['max_price']
    data_maior_preco = filter.qs.aggregate(max_date=Max('data_coleta'))['max_date']
    media_preco = filter.qs.aggregate(avg_price=Avg('preco_revenda'))['avg_price']

    variance = 0
    if maior_preco is not None and menor_preco is not None:
        variance = maior_preco - menor_preco

    data = {
        'filter': filter,
        'cidade_usuario': cidade_usuario,
        'uf_usuario': uf_usuario,
        'total_linhas_pesquisa': total_linhas_pesquisa,
        'menor_preco': menor_preco,
        'data_menor_preco': data_menor_preco,
        'maior_preco': maior_preco,
        'data_maior_preco': data_maior_preco,
        'media_preco': media_preco,
        'variance': variance,
        'razoes': razoes,
        'preco_medio_mensal': list(preco_medio_mensal)
    }
    
    return render(request, 'p_monitorar_concorrentes.html', data)


@login_required
def p_monitorar_produtos(request):

    filter = MainFilter(
        request.GET, 
        queryset=AddPrice.objects.exclude(
                produto_id=3, 
                pesquisa_origem_id=2, 
                produto_id__isnull=True
        ).filter(
                gasstation_id__cidade=request.user.profile.cidade
        )
    )

    profile = Profile.objects.all()

    cidade_usuario = request.user.profile.cidade
    uf_usuario = request.user.profile.estado

    aggregates = filter.qs.aggregate(
        min_price=Min('preco_revenda'),
        min_date=Min('data_coleta'),
        max_price=Max('preco_revenda'),
        max_date=Max('data_coleta'),
        avg_price=Avg('preco_revenda')
    )
    menor_preco = aggregates.get('min_price')
    menor_preco_count = filter.qs.filter(preco_revenda=menor_preco).count()
    data_menor_preco = aggregates.get('min_date')

    maior_preco = aggregates.get('max_price')
    data_maior_preco = aggregates.get('max_date')
    maior_preco_count = filter.qs.filter(preco_revenda=maior_preco).count()
    media_preco = aggregates.get('avg_price')

    variance = 0
    variance_percent = 0
    if maior_preco is not None and menor_preco is not None:
        variance = maior_preco - menor_preco
        if media_preco and media_preco > 0:
            variance_percent = (variance / media_preco) * 100

    total_linhas_pesquisa = filter.qs.distinct().count()
    total_postos = filter.qs.values('gasstation_id').distinct().count()

    preco_medio_mensal = filter.qs.annotate(
        mes=ExtractMonth('data_coleta'),
        ano=ExtractYear('data_coleta')
    ).values('mes', 'ano').annotate(
        preco_medio=Avg('preco_revenda')
    ).order_by('ano', 'mes')
    
    today = datetime.now()

    # Top 10 postos mais baratos
    top_10_postos_mais_baratos = filter.qs.values(
        'gasstation_id__razao', 'gasstation_id__id'
    ).annotate(
        preco_medio=Avg('preco_revenda')
    ).order_by('preco_medio')[:10]

    top_10_postos_mais_caros = filter.qs.order_by('-preco_revenda').values('gasstation_id__razao', 'preco_revenda')[:10]

    # Contar quantos postos estão praticando cada preço distinto
    precos_por_postos = filter.qs.values('preco_revenda').annotate(
        quantidade_postos=Count('gasstation_id', distinct=True)
    ).order_by('-quantidade_postos')[:9]

    # Agrupar preços por posto - nova estrutura
    postos_com_precos = filter.qs.values(
        'gasstation_id', 
        'gasstation_id__razao', 
        'gasstation_id__bandeira',
        'gasstation_id__cidade',
        'gasstation_id__estado'
    ).annotate(
        preco_minimo=Min('preco_revenda'),
        preco_maximo=Max('preco_revenda'),
        preco_medio=Avg('preco_revenda'),
        total_registros=Count('id'),
        data_primeira=Min('data_coleta'),
        data_ultima=Max('data_coleta')
    ).order_by('gasstation_id__razao')

    # Para cada posto, obter todos os preços distintos
    for posto in postos_com_precos:
        precos_distintos = filter.qs.filter(
            gasstation_id=posto['gasstation_id']
        ).values('preco_revenda').annotate(
            quantidade_dias=Count('data_coleta', distinct=True),
            data_inicio=Min('data_coleta'),
            data_fim=Max('data_coleta')
        ).order_by('preco_revenda')
        
        posto['precos_distintos'] = list(precos_distintos)

    # Obter min e max da data_coleta para cada posto e preço registrado (mantido para compatibilidade)
    postos_por_preco = filter.qs.values('gasstation_id', 'gasstation_id__razao', 'preco_revenda').annotate(
        data_minima=Min('data_coleta'),
        data_maxima=Max('data_coleta'),
        data_preco=F('data_maxima') - F('data_minima'),
        quantidade_postos=Count('preco_revenda') * 7
    ).order_by('gasstation_id__razao')

    data = {
        'filter': filter,
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
        'preco_medio_mensal': list(preco_medio_mensal),
        'top_10_postos_mais_baratos': list(top_10_postos_mais_baratos),
        'top_10_postos_mais_caros': list(top_10_postos_mais_caros),
        'menor_preco_count': menor_preco_count,
        'maior_preco_count': maior_preco_count,
        'precos_por_postos': list(precos_por_postos),
        'postos_por_preco': list(postos_por_preco),
        'postos_com_precos': list(postos_com_precos)
    }

    return render(request, 'p_mapeei.html', data)


@login_required
def p_lista_preco(request):
    # Query base otimizada com select_related e only
    base_queryset = AddPrice.objects.exclude(
        produto_id=3,
        pesquisa_origem_id=2
    ).select_related(
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
        'gasstation_id__bandeira',
        'produto_id__produto',
        'pesquisa_origem__origem'
    ).order_by('preco_revenda')

    # Aplicar filtros padrão se nenhum filtro específico for fornecido
    if not any(request.GET.get(param) for param in ['posto', 'cidade', 'produto', 'bandeira', 'mes', 'ano']):
        base_queryset = base_queryset.filter(
            data_coleta__gte=datetime.now() - timedelta(days=15),
            produto_id=1,
            pesquisa_origem_id=1,
            gasstation_id__cidade=request.user.profile.cidade,
        )

    # Aplicar filtros
    f = MainFilter(request.GET, queryset=base_queryset)

    # Otimizar contagem usando count() com distinct
    total_linhas_pesquisa = f.qs.distinct().count()

    
    # Preparar dados para o template
    data = {
        'list_price': f.qs,
        'filter': f,
        'total_linhas_pesquisa': total_linhas_pesquisa
    }
    
    return render(request, 'p_lista_preco.html', data)



@login_required
def add_price(request):
    form = NewPrice(request.POST or None)
    form.fields['gasstation_id'].queryset = GasStation.objects.filter(cidade=request.user.profile.cidade)

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

        # Gerar e salvar o embedding
        embedding_data = generate_price_embedding(addprice)
        if embedding_data:
            PriceEmbedding.objects.create(
                addprice=addprice,
                embedding=embedding_data['embedding']
            )

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
            user.username = form.cleaned_data.get('username')
            user.email = form.cleaned_data.get('email')
            user.save()
            
            # Verifica se o usuário já possui um perfil
            if hasattr(user, 'profile'):
                user.profile.telefone = form.cleaned_data.get('telefone')
                user.profile.cargo = form.cleaned_data.get('cargo')
                user.profile.empresa = form.cleaned_data.get('empresa')  # Certifica-se de que o campo empresa é atualizado
                user.profile.cidade = Cidade.objects.get(id=form.cleaned_data.get('cidade').id)
                user.profile.estado = Estado.objects.get(id=form.cleaned_data.get('estado').id)
                user.profile.save()
            else:
                # Cria um novo perfil se não existir
                novo_perfil = Profile.objects.create(
                    user=user,
                    telefone=form.cleaned_data.get('telefone'),
                    cargo=form.cleaned_data.get('cargo'),
                    cidade=Cidade.objects.get(id=form.cleaned_data.get('cidade').id),
                    estado=Estado.objects.get(id=form.cleaned_data.get('estado').id),
                )
                novo_perfil.empresa = form.cleaned_data.get('empresa')  # Corrige a gravação do dado de empresa
                novo_perfil.save()
            
            messages.success(request, 'Conta criada com sucesso! Você já pode fazer login.')
            return redirect('login')
        else:
            # Verifica especificamente os erros de cada campo
            if 'username' in form.errors:
                messages.error(request, 'Este nome de usuário já está em uso. Por favor, escolha outro.')
            elif 'email' in form.errors:
                messages.error(request, 'Este email já está cadastrado. Por favor, use outro email ou faça login.')
            elif 'posto' in form.errors:
                messages.error(request, 'Por favor, informe o nome da sua empresa.')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'Erro no campo {field}: {error}')

    context = {'form': form}
    return render(request, 'p_register.html', context)


def password_reset(request):
    return render(request, 'registration/password_form.html')


def enviar_email_recuperacao_senha(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                def send_password_reset_email(email):
                    from django.core.mail import send_mail
                    from django.conf import settings
                    from django.template.loader import render_to_string
                    from django.utils.html import strip_tags

                    subject = 'Redefinição de senha'
                    html_message = render_to_string('registration/password_email.html', {'email': email})
                    plain_message = strip_tags(html_message)
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to = email

                    send_mail(subject, plain_message, from_email, [to], html_message=html_message)

                send_password_reset_email(email)
                messages.success(request, 'Email de recuperação de senha enviado com sucesso.')
                return redirect('confirmacao_email_recuperacao')
            except Exception as e:
                messages.error(request, f'Erro ao enviar email: {str(e)}')
                return redirect('password_reset')
        else:
            messages.error(request, 'Por favor, insira um email válido.')
            return redirect('password_reset')

    return render(request, 'registration/password_form.html')


def confirmacao_email_recuperacao(request):
    return render(request, 'registration/password_done.html')


@login_required
@require_http_methods(["POST"])
def processar_pergunta(request):
    try:
        data = json.loads(request.body)
        pergunta = data.get('pergunta', '')
        
        print(f"Pergunta recebida: {pergunta}")
        
        if not pergunta:
            return JsonResponse({'erro': 'Pergunta não fornecida'}, status=400)

        # Extrair cidade e produto da pergunta
        cidade = None
        produto = None
        
        # Lista de variações comuns de cidades
        cidades_variacoes = {
            'COLOMBO': ['COLOMBO', 'COLOMBÓ'],
            'JUNDIAI': ['JUNDIAI', 'JUNDIAÍ', 'JUNDIAÍ'],
            # Adicione mais cidades conforme necessário
        }
        
        # Lista de variações comuns de produtos
        produtos_variacoes = {
            'ETANOL': ['ETANOL', 'ETANOL HIDRATADO', 'ETANOL COMUM'],
            'GASOLINA': ['GASOLINA', 'GASOLINA COMUM', 'GASOLINA ADITIVADA'],
            'DIESEL': ['DIESEL', 'DIESEL S10', 'DIESEL S500'],
            # Adicione mais produtos conforme necessário
        }
        
        # Buscar cidade na pergunta
        pergunta_upper = pergunta.upper()
        for cidade_base, variacoes in cidades_variacoes.items():
            if any(var in pergunta_upper for var in variacoes):
                cidade = cidade_base
                break
        
        # Buscar produto na pergunta
        for produto_base, variacoes in produtos_variacoes.items():
            if any(var in pergunta_upper for var in variacoes):
                produto = produto_base
                break
        
        print(f"Cidade identificada: {cidade}")
        print(f"Produto identificado: {produto}")

        # Buscar preços com filtros
        precos = AddPrice.objects.select_related(
            'gasstation_id',
            'produto_id'
        )
        
        # Aplicar filtros
        if cidade:
            precos = precos.filter(gasstation_id__cidade__iexact=cidade)
        if produto:
            precos = precos.filter(produto__icontains=produto)
            
        # Ordenar por data mais recente e limitar a 100 registros
        precos = precos.order_by('-data_coleta')[:100]

        print(f"Total de preços encontrados após filtros: {precos.count()}")

        # Verificar se há preços
        if precos.count() == 0:
            print("Nenhum preço encontrado")
            return JsonResponse({
                'erro': 'Não foram encontrados dados para processar sua pergunta.'
            }, status=404)

        # Preparar o contexto com os dados relevantes
        contexto = []
        for preco in precos:
            if preco.gasstation_id:  # Verificar se o posto existe
                try:
                    dados_preco = {
                        'data_coleta': preco.data_coleta.strftime('%d/%m/%Y'),
                        'produto': preco.produto_id.produto if preco.produto_id else preco.produto,
                        'preco_revenda': float(preco.preco_revenda),
                        'posto': preco.gasstation_id.razao,
                        'cidade': preco.gasstation_id.cidade.upper(),
                        'estado': preco.gasstation_id.estado,
                        'bandeira': preco.gasstation_id.bandeira
                    }
                    contexto.append(dados_preco)
                    print(f"Adicionado ao contexto: {dados_preco['posto']} - {dados_preco['cidade']} - R$ {dados_preco['preco_revenda']}")
                except Exception as e:
                    print(f"Erro ao processar preço {preco.id}: {str(e)}")
                    continue

        print(f"Total de registros no contexto: {len(contexto)}")
        
        if not contexto:
            print("Contexto vazio após processamento")
            return JsonResponse({
                'erro': 'Não foram encontrados dados para processar sua pergunta.'
            }, status=404)

        # Processar a pergunta usando a IA
        print("Iniciando processamento da pergunta com a IA...")
        resposta = processar_pergunta_ia(pergunta, contexto)
        print(f"Resposta gerada: {resposta[:200]}...")  # Mostrar os primeiros 200 caracteres da resposta

        if not resposta:
            print("Resposta vazia da IA")
            return JsonResponse({
                'erro': 'Não foi possível gerar uma resposta para sua pergunta.'
            }, status=500)

        return JsonResponse({
            'resposta': resposta
        })

    except json.JSONDecodeError:
        print("Erro: Dados inválidos no JSON")
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    except Exception as e:
        print(f"Erro ao processar pergunta: {str(e)}")
        return JsonResponse({'erro': str(e)}, status=500)
