from django.db.models import OuterRef, Count

prices = AddPrice.objects.filter(user=request.user).only(
        'gasstation_id_id', 
        'produto_id', 
        'preco_revenda', 
        'data_coleta'
    ).order_by('-data_coleta')

gas_station_name = item.values_list('gasstation_id_id__razao', flat=True).distinct().first()
gas_station_cnpj = item.values_list('gasstation_id_id__cnpj', flat=True).distinct().first()
gas_station_cidade = item.values_list('gasstation_id_id__cidade', flat=True).distinct().first()
gas_station_endereco = item.values_list('gasstation_id_id__endereco', flat=True).distinct().first()
gas_station_bandeira = item.values_list('gasstation_id_id__bandeira', flat=True).distinct().first()

# Subconsulta para pegar o último preco_revenda com base na data_coleta
ultimo_preco_subquery = (
    item.filter(gasstation_id_id=OuterRef('gasstation_id_id'))  # Ajuste o filtro conforme o necessário
    .order_by('-data_coleta')  # Ordena pela data mais recente
    .values('preco_revenda')[:1]  # Pega o último preço
)

price_competitor = (
        item
        .values('gasstation_id_id')
        .annotate(total=Count('id'))
        .order_by('-total')
    ) 