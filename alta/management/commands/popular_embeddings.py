from django.core.management.base import BaseCommand
from django.db.models import Q
from alta.models import AddPrice, PriceEmbedding
from alta.ia_utils import criar_ou_atualizar_embedding
import time

class Command(BaseCommand):
    help = 'Popula a tabela de embeddings com os dados existentes em AddPrice'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Número de registros para processar por vez'
        )
        parser.add_argument(
            '--sleep',
            type=float,
            default=1.0,
            help='Tempo de espera entre lotes (em segundos)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        sleep_time = options['sleep']
        
        # Contar total de registros
        total_registros = AddPrice.objects.count()
        self.stdout.write(f"Total de registros para processar: {total_registros}")
        
        # Processar em lotes
        offset = 0
        while True:
            # Buscar lote de registros
            registros = AddPrice.objects.all()[offset:offset + batch_size]
            if not registros:
                break
                
            self.stdout.write(f"Processando registros {offset + 1} até {offset + len(registros)}...")
            
            # Processar cada registro
            for registro in registros:
                try:
                    embedding = criar_ou_atualizar_embedding(registro)
                    if embedding:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Embedding criado/atualizado para registro {registro.id}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Falha ao criar embedding para registro {registro.id}"
                            )
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Erro ao processar registro {registro.id}: {str(e)}"
                        )
                    )
            
            offset += batch_size
            
            # Aguardar antes do próximo lote para evitar rate limits
            if offset < total_registros:
                self.stdout.write(f"Aguardando {sleep_time} segundos antes do próximo lote...")
                time.sleep(sleep_time)
        
        self.stdout.write(self.style.SUCCESS("Processamento concluído!")) 