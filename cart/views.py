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


def cart_remove(request, product_id, slab_id_list=None):
    cart = Cart(request)
    cart.remove(product_id, slab_id_list=slab_id_list)
    path = request.META.get('HTTP_REFERER')
    return redirect(path)


def cart_clean(request):
    cart = Cart(request)
    cart.clean()
    path = request.META.get('HTTP_REFERER')
    return redirect(path)


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})
