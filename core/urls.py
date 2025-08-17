from django.contrib import admin
from django.urls import path, include

from alta.views import (
    p_cartao_precos, 
    p_plans, 
    p_monitorar_produtos, 
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
    confirmacao_email_recuperacao,
    p_radar_precos,
    p_faq,
    lp_topo,
    index,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    
    path('', index, name='index'),
    
    path('cartao-precos/', p_cartao_precos, name='p_cartao_precos'),
    path('monitorar-produtos/', p_monitorar_produtos, name='p_monitorar_produtos'),
    path('listar-precos/', p_lista_preco, name='p_lista_preco'),
    path('acompanhar-precos/', add_price, name='p_acompanhar'),
    path('adicionar-novo-preco/', new_price, name='new_price'),
    path('perfil/', p_profile, name='p_profile'),

    path('planos/', p_plans, name='p_plans'),

    path('acessar-conta/', login_page, name='login'),
    path('login_view/', login_view, name='login_view'),
    path('sair/', logout, name='logout'),
    path('sair-conta/', logout_view, name='logout_view'),
    path('criar-conta/', new_register, name='new_register'),
    path('recuperar-senha/', password_reset, name='password_reset'),
    path('confirmacao-email-recuperacao/', confirmacao_email_recuperacao, name='confirmacao_email_recuperacao'),
    path('radar-precos/', p_radar_precos, name='p_radar_precos'),
    path('faq/', p_faq, name='p_faq'),
    path('lp-topo/', lp_topo, name='lp_topo'),
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'
