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
    password_reset
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

    path('login/', login_page, name='login'),
    path('login_view/', login_view, name='login_view'),
    path('logout/', logout, name='logout'),
    path('logout_view/', logout_view, name='logout_view'),
    path('new_register/', new_register, name='new_register'),
    path('password_reset/', password_reset, name='password_reset'),

]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
LOGOUT_REDIRECT_URL = 'login'
