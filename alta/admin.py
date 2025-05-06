from django.contrib import admin

from .models import ( 
    Produto, 
    GasStation, 
    AddPrice, 
    PesquisaOrigem, 
    FAQ, 
    Profile, 
    Contato 
    )

admin.site.register(Produto)
admin.site.register(GasStation)
admin.site.register(AddPrice)
admin.site.register(PesquisaOrigem)
admin.site.register(FAQ)
admin.site.register(Profile)
admin.site.register(Contato)

