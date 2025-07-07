from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from alta.models import Profile


class Command(BaseCommand):
    help = 'Cria Profiles para usuários que não têm'

    def handle(self, *args, **options):
        users_without_profile = []
        
        for user in User.objects.all():
            try:
                # Tenta acessar o profile
                user.profile
            except Profile.DoesNotExist:
                users_without_profile.append(user)
        
        if users_without_profile:
            self.stdout.write(f"Encontrados {len(users_without_profile)} usuários sem Profile")
            
            for user in users_without_profile:
                Profile.objects.create(user=user)
                self.stdout.write(f"✅ Profile criado para {user.username}")
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ {len(users_without_profile)} Profiles criados com sucesso!')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Todos os usuários já têm Profile!')
            ) 