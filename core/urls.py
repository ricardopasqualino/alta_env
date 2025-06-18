from django.contrib import admin
from django.urls import path, include

from alta.views import (
    index, 
    p_cartao_precos, 
    p_plans, 
    p_ia, 
    p_mapeei, 
    p_lista_preco,
    add_price,
    new_price,
    p_profile,
    login_page,
    logout,
    logout_view,
    login_view,
    new_register,
    password_reset,
    enviar_email_recuperacao_senha,
    confirmacao_email_recuperacao,
    processar_pergunta,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('', p_cartao_precos, name='index'),
    
    path('cartao-precos/', p_cartao_precos, name='p_cartao_precos'),
    path('mapear-precos/', p_mapeei, name='p_mapeei'),
    path('listar-precos/', p_lista_preco, name='p_lista_preco'),
    path('acompanhar-precos/', add_price, name='p_acompanhar'),
    path('adicionar-novo-preco/', new_price, name='new_price'),
    path('perfil/', p_profile, name='p_profile'),

    path('ia/', p_ia, name='p_ia'),
    path('planos/', p_plans, name='p_plans'),

    path('acessar-conta/', login_page, name='login'),
    path('login_view/', login_view, name='login_view'),
    path('sair/', logout, name='logout'),
    path('sair-conta/', logout_view, name='logout_view'),
    path('criar-conta/', new_register, name='new_register'),
    path('recuperar-senha/', password_reset, name='password_reset'),
    path('enviar-email-recuperacao-senha/', enviar_email_recuperacao_senha, name='enviar_email_recuperacao_senha'),
    path('confirmacao-email-recuperacao/', confirmacao_email_recuperacao, name='confirmacao_email_recuperacao'),
    path('processar_pergunta/', processar_pergunta, name='processar_pergunta'),
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'
