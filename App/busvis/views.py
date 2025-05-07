@login_required
def add_price(request):
    form = NewPrice(request.POST or None)

    prices = AddPrice.objects.filter(user=request.user).select_related(
        'gasstation_id',
        'produto_id'
    ).only(
        'gasstation_id__razao',
        'produto_id__produto',
        'preco_revenda',
        'data_coleta'
    ).order_by('-data_coleta')

    data = {
        'form': form,
        'prices': prices,
    }

    return render(request, 'p_acompanhar.html', data) 