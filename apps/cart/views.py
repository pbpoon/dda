from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .cart import Cart


@require_POST
def cart_add(request):
    slab_list = request.POST.getlist('select')
    product_id = request.POST.get('product')
    location_id = request.POST.get('location')
    quantity = request.POST.get('quantity', None)
    if product_id and location_id:
        cart = Cart(request)
        cart.add(product_id, location_id, slab_id_list=slab_list, quantity=quantity)
    return JsonResponse({'state': 'ok'})


@require_POST
def cart_remove(request):
    cart = Cart(request)
    product_id = request.POST.get('product_id')
    if product_id:
        cart.remove(product_id)
        # path = request.META.get('HTTP_REFERER')
        # return render(request, 'cart_detail.html')
        state = 'ok'
    else:
        state = 'error'
    cart_length = len(cart)
    return JsonResponse({'state': state, 'cart_length':cart_length})


@require_POST
def cart_clean(request):
    cart = Cart(request)
    cart.clean()
    # path = request.META.get('HTTP_REFERER')
    return render(request, 'cart_list.html', {'cart': cart})


def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart_list.html', {'cart': cart})
