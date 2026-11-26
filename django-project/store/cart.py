

from decimal import Decimal


def get_cart(request):
    return request.session.get('cart', {})


def add_to_cart(request, product_id, variant_id=None):
    cart = get_cart(request)

    product_id = str(product_id)
    variant_id = str(variant_id) if variant_id else None

    # Separate cart entry for each colour or size
    cart_key = f"{product_id}_{variant_id}" if variant_id else product_id

    if cart_key in cart:
        cart[cart_key]['quantity'] += 1
    else:
        cart[cart_key] = {
            'quantity': 1,
            'variant_id': variant_id
        }

    request.session['cart'] = cart
    request.session.modified = True


def remove_from_cart(request, product_id):
    cart = get_cart(request)

    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    request.session.modified = True


def update_quantity(request, product_id, quantity):
    cart = get_cart(request)

    product_id = str(product_id)
    quantity = int(quantity)

    if product_id in cart:
        if quantity > 0:
            cart[product_id]['quantity'] = quantity
        else:
            del cart[product_id]

    request.session['cart'] = cart
    request.session.modified = True
