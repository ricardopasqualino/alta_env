import django_filters
from datetime import datetime

from .models import ( 
    AddPrice, 
    GasStation
    )


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
        choices=lambda: [(cidade, cidade) for cidade in AddPrice.objects.filter(
            gasstation_id__cidade__isnull=False
        ).values_list('gasstation_id__cidade', flat=True).distinct().order_by('gasstation_id__cidade')],
        field_name='gasstation_id__cidade',
        lookup_expr='exact'
    )

    produto = django_filters.ChoiceFilter(
        label='produto',
        choices=lambda: [(produto, produto) for produto in AddPrice.objects.filter(
            produto_id__isnull=False
        ).values_list('produto_id__produto', flat=True).distinct().order_by('produto_id__produto')],
        field_name='produto_id__produto',
        lookup_expr='exact'
    )

    bandeira = django_filters.ChoiceFilter(
        label='bandeira',
        choices=lambda: [(bandeira, bandeira) for bandeira in AddPrice.objects.filter(
            gasstation_id__bandeira__isnull=False
        ).values_list('gasstation_id__bandeira', flat=True).distinct().order_by('gasstation_id__bandeira')],
        field_name='gasstation_id__bandeira',
        lookup_expr='exact'
    )
    
    razao = django_filters.ChoiceFilter(
        label='razao',
        choices=lambda: [(razao, razao) for razao in AddPrice.objects.filter(
            gasstation_id__razao__isnull=False
        ).values_list('gasstation_id__razao', flat=True).distinct().order_by('gasstation_id__razao')],
        field_name='gasstation_id__razao',
        lookup_expr='exact'
    )                  
        
    ano = django_filters.ChoiceFilter(
        field_name='data_coleta__year',
        label='Ano Coleta',
        choices=lambda: [(cat, cat) for cat in AddPrice.objects.values_list(
            'data_coleta__year', flat=True
        ).distinct().order_by('-data_coleta__year') if cat is not None]
    )

    mes = django_filters.ChoiceFilter(
        field_name='data_coleta__month',
        label='Mes Coleta',
        choices=lambda: [(cat, cat) for cat in AddPrice.objects.values_list(
            'data_coleta__month', flat=True
        ).distinct().order_by('data_coleta__month') if cat is not None]
    )

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
        ]        
        
class CompetitorFilter(django_filters.FilterSet):
    gas_station = django_filters.ModelChoiceFilter(
        queryset=GasStation.objects.all(),
        label='Posto',
        field_name='gas_station'
    )    
    
    produto = django_filters.ChoiceFilter(
        label='produto',
        choices='get_produto_choices',
        field_name='produto_id__produto',
        lookup_expr='exact'
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

    def get_produto_choices(self):
        return [(produto, produto) for produto in AddPrice.objects.filter(produto_id__isnull=False).values_list('produto_id__produto', flat=True).distinct()]

    class Meta:
        model = AddPrice
        fields = [
            'gas_station', 
            'produto', 
            'data_inicio',
            'data_fim',
            ]        
