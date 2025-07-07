import django_filters
from datetime import datetime
from django.core.cache import cache

from .models import ( 
    AddPrice, 
    GasStation
    )

MESES = {
    1: 'Janeiro',
    2: 'Fevereiro',
    3: 'Março',
    4: 'Abril',
    5: 'Maio',
    6: 'Junho',
    7: 'Julho',
    8: 'Agosto',
    9: 'Setembro',
    10: 'Outubro',
    11: 'Novembro',
    12: 'Dezembro'
}

class AddPriceFilter(django_filters.FilterSet):
    nome = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = AddPrice
        fields = [
            'gasstation_id__cidade',
            'gasstation_id__estado',
            'gasstation_id__bairro',
            'gasstation_id__endereco',
            'gasstation_id__complemento',
            'gasstation_id__cep',
            'gasstation_id__cnpj',
        ]
        

class MainFilter(django_filters.FilterSet):

    posto = django_filters.CharFilter(
        label='Posto',
        field_name='gasstation_id__razao',
        lookup_expr='icontains'
    )

    cidade = django_filters.ChoiceFilter(
        label='cidade',
        choices=lambda: MainFilter._get_cached_choices('cidades'),
        field_name='gasstation_id__cidade',
        lookup_expr='exact',
        empty_label='Selecione uma cidade',
    )

    bairro = django_filters.ChoiceFilter(
        label='bairro',
        choices=lambda: MainFilter._get_cached_choices('bairros'),
        field_name='gasstation_id__bairro',
        lookup_expr='exact',
        empty_label='Selecione um bairro',
    )

    produto = django_filters.ChoiceFilter(
        label='produto',
        choices=lambda: MainFilter._get_cached_choices('produtos'),
        field_name='produto_id__produto',
        lookup_expr='exact',
        empty_label='Selecione um produto',
    )

    bandeira = django_filters.ChoiceFilter(
        label='bandeira',
        choices=lambda: MainFilter._get_cached_choices('bandeiras'),
        field_name='gasstation_id__bandeira',
        lookup_expr='exact',
        empty_label='Todas as bandeiras',
    )
    
    razao = django_filters.ChoiceFilter(
        label='razao',
        choices=lambda: MainFilter._get_cached_choices('razoes'),
        field_name='gasstation_id__razao',
        lookup_expr='exact'
    )                  
        
    ano = django_filters.ChoiceFilter(
        field_name='data_coleta__year',
        label='Ano Coleta',
        choices=lambda: MainFilter._get_cached_choices('anos'),
        initial='2025',
        empty_label='Selecione um ano',
    )

    mes = django_filters.ChoiceFilter(
        field_name='data_coleta__month',
        label='Mes Coleta',
        choices=lambda: MainFilter._get_cached_choices('meses'),
        empty_label='Selecione um mês',
        initial='1',
    )

    data_inicio = django_filters.DateFilter(
        field_name='data_coleta', 
        lookup_expr='gte', 
        label='Data Inicial'
    )

    data_fim = django_filters.DateFilter(
        field_name='data_coleta', 
        lookup_expr='lte', 
        label='Data Final',
    )    

    @staticmethod
    def _get_cached_choices(choice_type):
        """Obtém choices do cache ou do banco de dados"""
        cache_key = f'filter_choices_{choice_type}'
        choices = cache.get(cache_key)
        
        if choices is None:
            if choice_type == 'cidades':
                choices = [(cidade, cidade) for cidade in AddPrice.objects.filter(
                    gasstation_id__cidade__isnull=False
                ).values_list('gasstation_id__cidade', flat=True).distinct().order_by('gasstation_id__cidade')]
            elif choice_type == 'bairros':
                choices = [(bairro, bairro) for bairro in AddPrice.objects.filter(
                    gasstation_id__bairro__isnull=False
                ).values_list('gasstation_id__bairro', flat=True).distinct().order_by('gasstation_id__bairro')]
            elif choice_type == 'produtos':
                choices = [(produto, produto) for produto in AddPrice.objects.filter(
                    produto_id__isnull=False
                ).exclude(produto_id=3).values_list('produto_id__produto', flat=True).distinct().order_by('produto_id__produto')]
            elif choice_type == 'bandeiras':
                choices = [(bandeira, bandeira) for bandeira in AddPrice.objects.filter(
                    gasstation_id__bandeira__isnull=False
                ).values_list('gasstation_id__bandeira', flat=True).distinct().order_by('gasstation_id__bandeira')]
            elif choice_type == 'razoes':
                choices = [(razao, razao) for razao in AddPrice.objects.filter(
                    gasstation_id__razao__isnull=False
                ).values_list('gasstation_id__razao', flat=True).distinct().order_by('gasstation_id__razao')]
            elif choice_type == 'anos':
                choices = [(ano, ano) for ano in AddPrice.objects.values_list(
                    'data_coleta__year', flat=True
                ).distinct().order_by('-data_coleta__year') if ano is not None]
            elif choice_type == 'meses':
                choices = [(cat, MESES[cat]) for cat in AddPrice.objects.values_list(
                    'data_coleta__month', flat=True
                ).distinct().order_by('data_coleta__month') if cat is not None]
            else:
                choices = []
            
            # Cache por 1 hora
            cache.set(cache_key, choices, 3600)
        
        return choices

    class Meta:
        model = AddPrice 
        fields = [
            'ano',
            'mes',
            'posto',
            'cidade',
            'produto',
            'bandeira',
            'razao',
            'data_inicio',
            'data_fim',
        ]        
