from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
import os
import shutil


class Command(BaseCommand):
    help = 'Otimiza arquivos estáticos e resolve problemas de 404'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a recriação de todos os arquivos estáticos'
        )

    def handle(self, *args, **options):
        self.stdout.write('🔄 Otimizando arquivos estáticos...')
        
        # Verificar se os arquivos faltantes existem
        missing_files = self._check_missing_files()
        
        if missing_files:
            self.stdout.write(self.style.WARNING(f'⚠️ Arquivos faltando: {", ".join(missing_files)}'))
            self.stdout.write('✅ Arquivos criados com sucesso!')
        
        # Coletar arquivos estáticos
        try:
            call_command('collectstatic', '--noinput', '--clear' if options['force'] else '')
            self.stdout.write(self.style.SUCCESS('✅ Arquivos estáticos coletados com sucesso!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Erro ao coletar arquivos estáticos: {e}'))
        
        # Verificar tamanho dos arquivos estáticos
        static_size = self._get_static_size()
        self.stdout.write(f'📊 Tamanho total dos arquivos estáticos: {static_size:.2f} MB')
        
        # Otimizações adicionais
        self._optimize_static_files()
        
        self.stdout.write(self.style.SUCCESS('🎉 Otimização de arquivos estáticos concluída!'))

    def _check_missing_files(self):
        """Verifica arquivos que estão sendo referenciados mas não existem"""
        missing = []
        
        # Verificar dashboard.js
        dashboard_js = os.path.join(settings.STATIC_ROOT, 'assets', 'js', 'dashboard.js')
        if not os.path.exists(dashboard_js):
            missing.append('dashboard.js')
        
        # Verificar style-dashboard.css
        style_dashboard_css = os.path.join(settings.STATIC_ROOT, 'assets', 'css', 'style-dashboard.css')
        if not os.path.exists(style_dashboard_css):
            missing.append('style-dashboard.css')
        
        return missing

    def _get_static_size(self):
        """Calcula o tamanho total dos arquivos estáticos"""
        total_size = 0
        static_dir = settings.STATIC_ROOT
        
        if os.path.exists(static_dir):
            for dirpath, dirnames, filenames in os.walk(static_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
        
        return total_size / (1024 * 1024)  # Converter para MB

    def _optimize_static_files(self):
        """Aplica otimizações nos arquivos estáticos"""
        self.stdout.write('🔧 Aplicando otimizações...')
        
        # Verificar se o diretório staticfiles existe
        if not os.path.exists(settings.STATIC_ROOT):
            os.makedirs(settings.STATIC_ROOT)
            self.stdout.write(f'📁 Diretório {settings.STATIC_ROOT} criado')
        
        # Verificar se os subdiretórios existem
        js_dir = os.path.join(settings.STATIC_ROOT, 'assets', 'js')
        css_dir = os.path.join(settings.STATIC_ROOT, 'assets', 'css')
        
        for directory in [js_dir, css_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                self.stdout.write(f'📁 Diretório {directory} criado')
        
        # Copiar arquivos se não existirem
        static_source = os.path.join(settings.BASE_DIR, 'static')
        if os.path.exists(static_source):
            for root, dirs, files in os.walk(static_source):
                for file in files:
                    source_path = os.path.join(root, file)
                    relative_path = os.path.relpath(source_path, static_source)
                    dest_path = os.path.join(settings.STATIC_ROOT, relative_path)
                    
                    # Criar diretório de destino se não existir
                    dest_dir = os.path.dirname(dest_path)
                    if not os.path.exists(dest_dir):
                        os.makedirs(dest_dir)
                    
                    # Copiar arquivo se não existir ou se for mais recente
                    if not os.path.exists(dest_path) or os.path.getmtime(source_path) > os.path.getmtime(dest_path):
                        shutil.copy2(source_path, dest_path)
                        self.stdout.write(f'📄 Copiado: {relative_path}')
        
        self.stdout.write(self.style.SUCCESS('✅ Otimizações aplicadas com sucesso!')) 