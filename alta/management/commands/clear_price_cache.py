from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Limpa cache específico da função add_price'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username específico para limpar cache (opcional)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Limpar cache de todos os usuários'
        )

    def handle(self, *args, **options):
        if options['user']:
            # Limpar cache de um usuário específico
            try:
                user = User.objects.get(username=options['user'])
                self._clear_user_cache(user)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cache limpo para o usuário: {user.username}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Usuário não encontrado: {options["user"]}')
                )
        
        elif options['all']:
            # Limpar cache de todos os usuários
            users = User.objects.all()
            cleared_count = 0
            
            for user in users:
                self._clear_user_cache(user)
                cleared_count += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Cache limpo para {cleared_count} usuários')
            )
        
        else:
            # Limpar cache geral
            cache.clear()
            self.stdout.write(self.style.SUCCESS('✅ Cache geral limpo com sucesso!'))

    def _clear_user_cache(self, user):
        """Limpa cache específico de um usuário"""
        # Padrões de chaves de cache para limpar
        cache_patterns = [
            f'add_price_form:{user.id}:*',
            f'user_prices:{user.id}:*',
        ]
        
        # Limpar cache por padrão (simulação - Django não tem limpeza por padrão)
        # Em produção, considere usar Redis com KEYS pattern
        cache.delete(f'add_price_form:{user.id}:none')
        
        # Limpar páginas de preços (primeiras 10 páginas)
        for page in range(1, 11):
            cache.delete(f'user_prices:{user.id}:{page}')
        
        # Se o usuário tem perfil com cidade, limpar também
        try:
            if user.profile.cidade:
                cache.delete(f'add_price_form:{user.id}:{user.profile.cidade.id}')
        except:
            pass 