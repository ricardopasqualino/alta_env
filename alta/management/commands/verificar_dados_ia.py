from django.core.management.base import BaseCommand
from alta.models import AddPrice, PriceEmbedding
from django.db.models import Count, Max, Min, Avg

class Command(BaseCommand):
    help = 'Verifica os dados disponíveis para a IA'

    def handle(self, *args, **options):
        # Verificar total de registros
        total_addprice = AddPrice.objects.count()
        
        self.stdout.write("=== Estatísticas Gerais ===")
        self.stdout.write(f"Total de registros AddPrice: {total_addprice}")
        
        # Verificar dados por cidade
        cidades = AddPrice.objects.values(
            'gasstation_id__cidade'
        ).annotate(
            total=Count('id'),
            preco_medio=Avg('preco_revenda'),
            preco_min=Min('preco_revenda'),
            preco_max=Max('preco_revenda')
        ).order_by('-total')
        
        self.stdout.write("\n=== Dados por Cidade ===")
        for cidade in cidades:
            if cidade['gasstation_id__cidade']:
                self.stdout.write(f"\nCidade: {cidade['gasstation_id__cidade']}")
                self.stdout.write(f"Total de registros: {cidade['total']}")
                self.stdout.write(f"Preço médio: R$ {cidade['preco_medio']:.2f}")
                self.stdout.write(f"Preço mínimo: R$ {cidade['preco_min']:.2f}")
                self.stdout.write(f"Preço máximo: R$ {cidade['preco_max']:.2f}")
        
        # Verificar dados por produto
        produtos = AddPrice.objects.values(
            'produto_id__produto'
        ).annotate(
            total=Count('id'),
            preco_medio=Avg('preco_revenda'),
            preco_min=Min('preco_revenda'),
            preco_max=Max('preco_revenda')
        ).order_by('-total')
        
        self.stdout.write("\n=== Dados por Produto ===")
        for produto in produtos:
            if produto['produto_id__produto']:
                self.stdout.write(f"\nProduto: {produto['produto_id__produto']}")
                self.stdout.write(f"Total de registros: {produto['total']}")
                self.stdout.write(f"Preço médio: R$ {produto['preco_medio']:.2f}")
                self.stdout.write(f"Preço mínimo: R$ {produto['preco_min']:.2f}")
                self.stdout.write(f"Preço máximo: R$ {produto['preco_max']:.2f}")
        
        # Verificar dados mais recentes
        ultimos_registros = AddPrice.objects.select_related(
            'gasstation_id',
            'produto_id'
        ).order_by('-data_coleta')[:5]
        
        self.stdout.write("\n=== Últimos 5 Registros ===")
        for registro in ultimos_registros:
            self.stdout.write(
                f"\nData: {registro.data_coleta}, "
                f"Produto: {registro.produto_id.produto if registro.produto_id else registro.produto}, "
                f"Preço: R$ {registro.preco_revenda:.2f}, "
                f"Posto: {registro.gasstation_id.razao if registro.gasstation_id else 'N/A'}, "
                f"Cidade: {registro.gasstation_id.cidade if registro.gasstation_id else 'N/A'}"
            ) 