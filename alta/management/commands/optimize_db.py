from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Otimiza o banco de dados e limpa cache'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Analisar tabelas para otimizar queries
            self.stdout.write('Analisando tabelas...')
            cursor.execute("ANALYZE alta_addprice;")
            cursor.execute("ANALYZE alta_gasstation;")
            cursor.execute("ANALYZE alta_produto;")
            
            # Verificar estatísticas das tabelas
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup, n_dead_tup
                FROM pg_stat_user_tables 
                WHERE tablename IN ('alta_addprice', 'alta_gasstation', 'alta_produto')
                ORDER BY tablename;
            """)
            
            stats = cursor.fetchall()
            self.stdout.write('\nEstatísticas das tabelas:')
            for stat in stats:
                self.stdout.write(f'{stat[1]}: {stat[5]} registros vivos, {stat[6]} registros mortos')
            
            # Limpar cache
            cache.clear()
            self.stdout.write('\nCache limpo com sucesso!')
            
            self.stdout.write(
                self.style.SUCCESS('Otimização concluída com sucesso!')
            ) 