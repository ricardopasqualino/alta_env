from django.core.management.base import BaseCommand
from django.db import connection
from alta.models import AddPrice

class Command(BaseCommand):
    help = 'Executa queries SQL personalizadas no banco de dados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--query',
            type=str,
            default='SELECT * FROM alta_addprice LIMIT 5',
            help='Query SQL a ser executada'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Limite de registros a serem exibidos'
        )

    def handle(self, *args, **options):
        query = options['query']
        limit = options['limit']
        
        # Se a query não tiver LIMIT, adicionar automaticamente
        if 'LIMIT' not in query.upper():
            query += f' LIMIT {limit}'
        
        self.stdout.write(f"Executando query: {query}")
        self.stdout.write("-" * 80)
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                
                # Obter nomes das colunas
                columns = [desc[0] for desc in cursor.description]
                
                # Exibir cabeçalho
                header = " | ".join(f"{col:<20}" for col in columns)
                self.stdout.write(header)
                self.stdout.write("-" * len(header))
                
                # Exibir dados
                rows = cursor.fetchall()
                for row in rows:
                    formatted_row = " | ".join(f"{str(value):<20}" for value in row)
                    self.stdout.write(formatted_row)
                
                self.stdout.write("-" * len(header))
                self.stdout.write(f"Total de registros retornados: {len(rows)}")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao executar query: {str(e)}"))
            
        # Também mostrar usando ORM do Django como alternativa
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write("ALTERNATIVA USANDO ORM DO DJANGO:")
        self.stdout.write("=" * 80)
        
        try:
            # Usar ORM do Django para mostrar os mesmos dados
            registros = AddPrice.objects.select_related(
                'gasstation_id', 
                'produto_id', 
                'pesquisa_origem', 
                'user'
            )[:limit]
            
            self.stdout.write(f"Usando ORM Django - Primeiros {limit} registros:")
            self.stdout.write("-" * 80)
            
            for registro in registros:
                self.stdout.write(f"ID: {registro.id}")
                self.stdout.write(f"Data: {registro.data_coleta}")
                self.stdout.write(f"CNPJ: {registro.cnpj}")
                self.stdout.write(f"Posto: {registro.gasstation_id.razao if registro.gasstation_id else 'N/A'}")
                self.stdout.write(f"Produto: {registro.produto_id.produto if registro.produto_id else registro.produto}")
                self.stdout.write(f"Preço Revenda: R$ {registro.preco_revenda}")
                self.stdout.write(f"Preço Compra: R$ {registro.preco_compra if registro.preco_compra else 'N/A'}")
                self.stdout.write(f"Usuário: {registro.user.username if registro.user else 'N/A'}")
                self.stdout.write("-" * 40)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao usar ORM: {str(e)}")) 