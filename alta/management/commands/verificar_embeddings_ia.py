from django.core.management.base import BaseCommand
from alta.models import AddPrice, PriceEmbedding
from alta.ia_utils import vetorizar_texto, calcular_similaridade
import json

class Command(BaseCommand):
    help = 'Verifica o processamento dos embeddings para a IA'

    def handle(self, *args, **options):
        # Verificar total de registros
        total_addprice = AddPrice.objects.count()
        total_embeddings = PriceEmbedding.objects.count()
        
        self.stdout.write("=== Estatísticas Gerais ===")
        self.stdout.write(f"Total de registros AddPrice: {total_addprice}")
        self.stdout.write(f"Total de embeddings: {total_embeddings}")
        
        # Verificar embeddings por cidade
        self.stdout.write("\n=== Embeddings por Cidade ===")
        cidades = AddPrice.objects.filter(
            embedding__isnull=False
        ).values_list(
            'gasstation_id__cidade', flat=True
        ).distinct()
        
        for cidade in cidades:
            if cidade:
                total = AddPrice.objects.filter(
                    gasstation_id__cidade=cidade,
                    embedding__isnull=False
                ).count()
                
                self.stdout.write(f"\nCidade: {cidade}")
                self.stdout.write(f"Total de embeddings: {total}")
                
                # Testar uma pergunta simples
                pergunta = f"Quais são os preços em {cidade}?"
                pergunta_embedding = vetorizar_texto(pergunta)
                
                if pergunta_embedding:
                    # Buscar embeddings da cidade
                    embeddings = PriceEmbedding.objects.filter(
                        addprice__gasstation_id__cidade=cidade
                    ).select_related('addprice')
                    
                    # Calcular similaridade
                    similaridades = []
                    for emb in embeddings:
                        sim = calcular_similaridade(pergunta_embedding, emb.embedding)
                        similaridades.append((emb, sim))
                    
                    # Ordenar por similaridade
                    similaridades.sort(key=lambda x: x[1], reverse=True)
                    
                    # Mostrar os 3 mais relevantes
                    self.stdout.write("\nTop 3 resultados mais relevantes:")
                    for emb, sim in similaridades[:3]:
                        self.stdout.write(f"- {emb.addprice.gasstation_id.razao}: {sim:.4f}")
                else:
                    self.stdout.write("Erro ao vetorizar a pergunta de teste")
        
        # Verificar qualidade dos embeddings
        self.stdout.write("\n=== Qualidade dos Embeddings ===")
        embeddings_invalidos = PriceEmbedding.objects.filter(
            embedding__isnull=True
        ).count()
        
        self.stdout.write(f"Embeddings inválidos: {embeddings_invalidos}")
        
        # Verificar estrutura dos embeddings
        embedding_exemplo = PriceEmbedding.objects.first()
        if embedding_exemplo:
            self.stdout.write("\nEstrutura do embedding:")
            self.stdout.write(f"Tamanho do vetor: {len(embedding_exemplo.embedding)}")
            self.stdout.write(f"Tipo do embedding: {type(embedding_exemplo.embedding)}") 