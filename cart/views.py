from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .cart import Cart


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    slab_id_list = request.POST.getlist('select_slab_list', None)
    cart.add(product_id, slab_id_list=slab_id_list)
    path = request.META.get('HTTP_REFERER')
    return redirect(path)


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    cart.remove(product_id)
    # path = request.META.get('HTTP_REFERER')
    # return render(request, 'cart_detail.html')
    return JsonResponse({'state': 'ok'})


@require_POST
def cart_clean(request):
    cart = Cart(request)
    cart.clean()
    # path = request.META.get('HTTP_REFERER')
    return render(request, 'cart_detail.html', {'cart': cart})


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart_detail.html', {'cart': cart})
