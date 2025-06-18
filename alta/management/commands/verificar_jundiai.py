from django.core.management.base import BaseCommand
from alta.models import AddPrice, GasStation, PriceEmbedding
from django.db.models import Q, Count

class Command(BaseCommand):
    help = 'Verifica dados e embeddings de postos em Jundiaí'

    def handle(self, *args, **options):
        # Buscar postos em Jundiaí
        jundiai_gasstations = GasStation.objects.filter(
            Q(cidade__icontains='JUNDIAI') | 
            Q(cidade__icontains='Jundiaí')
        )
        
        self.stdout.write("=== Postos em Jundiaí ===")
        postos_com_embedding = 0
        postos_sem_embedding = 0
        
        for posto in jundiai_gasstations:
            self.stdout.write(f"\nPosto: {posto.razao}")
            self.stdout.write(f"CNPJ: {posto.cnpj}")
            self.stdout.write(f"Cidade: {posto.cidade}")
            
            # Verificar preços deste posto
            precos = AddPrice.objects.filter(gasstation_id=posto)
            total_precos = precos.count()
            self.stdout.write(f"Total de registros de preço: {total_precos}")
            
            # Verificar embeddings
            precos_com_embedding = precos.filter(embedding__isnull=False)
            total_embeddings = precos_com_embedding.count()
            self.stdout.write(f"Registros com embedding: {total_embeddings}")
            
            # Verificar se o posto tem algum embedding
            if total_embeddings > 0:
                postos_com_embedding += 1
                self.stdout.write("Status: Posto com embeddings")
            else:
                postos_sem_embedding += 1
                self.stdout.write("Status: Posto sem embeddings")
            
            if precos_com_embedding.exists():
                self.stdout.write("\nÚltimos preços registrados:")
                for preco in precos_com_embedding.order_by('-data_coleta')[:5]:
                    self.stdout.write(f"- {preco.data_coleta}: {preco.produto} - R$ {preco.preco_revenda}")
            
            self.stdout.write("-" * 50)
        
        # Estatísticas gerais
        total_precos_jundiai = AddPrice.objects.filter(
            gasstation_id__in=jundiai_gasstations
        ).count()
        
        total_embeddings_jundiai = PriceEmbedding.objects.filter(
            addprice__gasstation_id__in=jundiai_gasstations
        ).count()
        
        self.stdout.write("\n=== Estatísticas ===")
        self.stdout.write(f"Total de postos em Jundiaí: {jundiai_gasstations.count()}")
        self.stdout.write(f"Postos com embeddings: {postos_com_embedding}")
        self.stdout.write(f"Postos sem embeddings: {postos_sem_embedding}")
        self.stdout.write(f"Total de registros de preço: {total_precos_jundiai}")
        self.stdout.write(f"Total de embeddings: {total_embeddings_jundiai}")
        
        # Calcular percentual de cobertura
        if total_precos_jundiai > 0:
            percentual_cobertura = (total_embeddings_jundiai / total_precos_jundiai) * 100
            self.stdout.write(f"\nPercentual de cobertura de embeddings: {percentual_cobertura:.2f}%") 