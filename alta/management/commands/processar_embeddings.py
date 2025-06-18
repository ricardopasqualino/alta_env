from django.core.management.base import BaseCommand
from alta.models import AddPrice
from alta.ia_utils import criar_ou_atualizar_embedding
from django.db.models import Q
import time

class Command(BaseCommand):
    help = 'Processa embeddings para registros AddPrice que ainda não possuem embedding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Número de registros para processar por lote'
        )
        parser.add_argument(
            '--max-records',
            type=int,
            default=None,
            help='Número máximo de registros para processar'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        max_records = options['max_records']
        
        # Buscar registros sem embedding
        registros_sem_embedding = AddPrice.objects.filter(
            Q(embedding__isnull=True) | Q(embedding__embedding__isnull=True)
        )
        
        if max_records:
            registros_sem_embedding = registros_sem_embedding[:max_records]
            
        total_registros = registros_sem_embedding.count()
        self.stdout.write(f"Total de registros para processar: {total_registros}")
        
        registros_processados = 0
        sucessos = 0
        falhas = 0
        
        # Processar em lotes
        for i in range(0, total_registros, batch_size):
            lote = registros_sem_embedding[i:i + batch_size]
            self.stdout.write(f"Processando lote {i//batch_size + 1} de {(total_registros + batch_size - 1)//batch_size}")
            
            for registro in lote:
                try:
                    resultado = criar_ou_atualizar_embedding(registro)
                    if resultado:
                        sucessos += 1
                    else:
                        falhas += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Erro ao processar registro {registro.id}: {str(e)}"))
                    falhas += 1
                
                registros_processados += 1
                
                # Mostrar progresso a cada 10 registros
                if registros_processados % 10 == 0:
                    self.stdout.write(f"Progresso: {registros_processados}/{total_registros} "
                                    f"(Sucessos: {sucessos}, Falhas: {falhas})")
            
            # Pausa entre lotes para evitar sobrecarga da API
            time.sleep(2)
        
        self.stdout.write(self.style.SUCCESS(
            f"\nProcessamento concluído!\n"
            f"Total processado: {registros_processados}\n"
            f"Sucessos: {sucessos}\n"
            f"Falhas: {falhas}"
        )) 