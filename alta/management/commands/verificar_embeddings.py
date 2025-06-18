from django.core.management.base import BaseCommand
from alta.models import AddPrice, PriceEmbedding

class Command(BaseCommand):
    help = 'Verifica se todos os registros de AddPrice têm embeddings correspondentes'

    def handle(self, *args, **options):
        total_addprice = AddPrice.objects.count()
        total_embeddings = PriceEmbedding.objects.count()
        registros_sem_embedding = AddPrice.objects.exclude(embedding__isnull=False).count()
        
        self.stdout.write(f"Total de registros em AddPrice: {total_addprice}")
        self.stdout.write(f"Total de embeddings: {total_embeddings}")
        self.stdout.write(f"Registros sem embedding: {registros_sem_embedding}")
        
        if registros_sem_embedding > 0:
            self.stdout.write(self.style.WARNING(
                f"Existem {registros_sem_embedding} registros sem embedding!"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Todos os registros possuem embeddings!"
            )) 