from django.core.management.base import BaseCommand
from alta.models import AddPrice, GasStation

class Command(BaseCommand):
    help = 'Verifica os dados disponíveis no banco de dados'

    def handle(self, *args, **options):
        # Verificar dados gerais
        total_addprice = AddPrice.objects.count()
        total_gasstations = GasStation.objects.count()
        
        # Verificar dados de Jundiaí
        jundiai_gasstations = GasStation.objects.filter(cidade__icontains='JUNDIAI')
        jundiai_prices = AddPrice.objects.filter(gasstation_id__cidade__icontains='JUNDIAI')
        
        # Verificar embeddings
        total_embeddings = AddPrice.objects.filter(embedding__isnull=False).count()
        
        self.stdout.write("=== Estatísticas Gerais ===")
        self.stdout.write(f"Total de registros AddPrice: {total_addprice}")
        self.stdout.write(f"Total de postos cadastrados: {total_gasstations}")
        self.stdout.write(f"Total de registros com embedding: {total_embeddings}")
        
        self.stdout.write("\n=== Dados de Jundiaí ===")
        self.stdout.write(f"Total de postos em Jundiaí: {jundiai_gasstations.count()}")
        self.stdout.write(f"Total de preços em Jundiaí: {jundiai_prices.count()}")
        
        if jundiai_gasstations.exists():
            self.stdout.write("\nPostos em Jundiaí:")
            for posto in jundiai_gasstations:
                self.stdout.write(f"- {posto.razao} ({posto.cnpj})") 