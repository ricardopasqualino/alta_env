from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Configura o cache e otimiza o banco de dados para produção'

    def handle(self, *args, **options):
        self.stdout.write('🔄 Configurando cache e otimizações...')
        
        # Criar tabela de cache se não existir
        try:
            call_command('createcachetable')
            self.stdout.write(self.style.SUCCESS('✅ Tabela de cache criada com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Erro ao criar tabela de cache: {e}'))
        
        # Limpar cache existente
        cache.clear()
        self.stdout.write(self.style.SUCCESS('✅ Cache limpo com sucesso!'))
        
        # Otimizar banco de dados
        try:
            with connection.cursor() as cursor:
                # Analisar tabelas para otimizar consultas
                cursor.execute("ANALYZE;")
                self.stdout.write(self.style.SUCCESS('✅ Análise do banco de dados concluída!'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Erro ao analisar banco: {e}'))
        
        # Verificar índices
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC;
                """)
                indexes = cursor.fetchall()
                
                self.stdout.write('\n📊 Estatísticas de índices:')
                for index in indexes[:10]:  # Top 10
                    self.stdout.write(f'   {index[2]}: {index[4]} leituras')
                    
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Erro ao verificar índices: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Configuração concluída!'))
        self.stdout.write('💡 Dicas para melhorar ainda mais a performance:')
        self.stdout.write('   - Considere usar Redis para cache em produção')
        self.stdout.write('   - Monitore as consultas lentas com django-debug-toolbar')
        self.stdout.write('   - Use select_related() e prefetch_related() em consultas relacionadas') 