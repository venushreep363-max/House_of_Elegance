
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse

from .models import (
    Product, Wishlist, Order, OrderItem,
    ProductVariant, ProductReview, Coupon
)
from .cart import add_to_cart


# HELPER: READ CART ENTRIES
def get_cart_entries(cart):
    entries = []

    for cart_key, item in cart.items():
        parts = cart_key.split('_', 1)

        try:
            product_id = int(parts[0])
        except (ValueError, IndexError):
            continue

        variant_id = item.get('variant_id')

        if variant_id is None and len(parts) > 1:
            variant_id = parts[1]

        try:
            variant_id = int(variant_id) if variant_id else None
            quantity = max(1, int(item.get('quantity', 1)))
        except (ValueError, TypeError):
            continue

        entries.append({
            'cart_key': cart_key,
            'product_id': product_id,
            'variant_id': variant_id,
            'quantity': quantity
        })

    return entries


# HOME PAGE
def home(request):
    search_query = request.GET.get('q', '').strip().lower()

    if search_query in ['saree', 'sarees']:
        return redirect('sarees')

    if search_query in ['kurti', 'kurtis']:
        return redirect('kurtis')

    products = Product.objects.all()

    if search_query:
        category_aliases = {
            'top': 'Tops',
            'tops': 'Tops',
            'shirt': 'Shirts',
            'shirts': 'Shirts',
            'western': 'Western Wear',
            'western wear': 'Western Wear',
            'pant': 'Pants & Trousers',
            'pants': 'Pants & Trousers',
            'trouser': 'Pants & Trousers',
            'trousers': 'Pants & Trousers',
            'jean': 'Jeans',
            'jeans': 'Jeans',
            'skirt': 'Skirts',
            'skirts': 'Skirts',
            'co-ord': 'Co-ord Sets',
            'co-ord sets': 'Co-ord Sets',
            'party wear': 'Party Wear',
            'ethnic wear': 'Ethnic Wear',
            'jumpsuit': 'Jumpsuits',
            'jumpsuits': 'Jumpsuits',
            'dress': 'Dresses',
            'dresses': 'Dresses'
        }

        matching_category = category_aliases.get(search_query)

        if matching_category:
            products = products.filter(
                Q(category=matching_category) |
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        else:
            products = products.filter(
                Q(name__icontains=search_query) |
                Q(category__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        wishlist_product_ids = []

        if request.user.is_authenticated:
            wishlist_product_ids = list(
                Wishlist.objects.filter(
                    user=request.user
                ).values_list('product_id', flat=True)
            )

        return render(request, 'store/search_results.html', {
            'products': products,
            'search_query': search_query,
            'wishlist_product_ids': wishlist_product_ids
        })

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )

    return render(request, 'store/home.html', {
        'products': products,
        'search_query': search_query,
        'wishlist_product_ids': wishlist_product_ids
    })


# SAREES COLLECTION
def sarees_view(request):
    sarees = Product.objects.filter(category='Sarees')

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )

    return render(request, 'store/sarees.html', {
        'products': sarees,
        'wishlist_product_ids': wishlist_product_ids
    })


# KURTIS COLLECTION
def kurtis_view(request):
    kurtis = Product.objects.filter(category='Kurtis')

    wishlist_product_ids = []

    if request.user.is_authenticated:
        wishlist_product_ids = list(
            Wishlist.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        )

    return render(request, 'store/kurtis.html', {
        'products': kurtis,
        'wishlist_product_ids': wishlist_product_ids
    })


# ADD PRODUCT TO CART
def add_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    variant_id = request.POST.get('variant_id')

    if variant_id:
        variant = get_object_or_404(
            ProductVariant,
            id=variant_id,
            product=product
        )

        if variant.stock <= 0:
            return redirect('product_detail', product_id=product.id)

        add_to_cart(request, product.id, variant.id)

    else:
        if product.stock <= 0:
            return redirect('product_detail', product_id=product.id)

        add_to_cart(request, product.id)

    return redirect('cart')


# SHOPPING CART
def cart_view(request):
    cart = request.session.get('cart', {})
    entries = get_cart_entries(cart)

    product_ids = [entry['product_id'] for entry in entries]

    products = Product.objects.filter(id__in=product_ids)
    product_map = {product.id: product for product in products}

    cart_items = []
    total = Decimal('0.00')
    original_total = Decimal('0.00')

    for entry in entries:
        product = product_map.get(entry['product_id'])

        if not product:
            continue

        variant = None

        if entry['variant_id']:
            variant = ProductVariant.objects.filter(
                id=entry['variant_id'],
                product=product
            ).first()

        quantity = entry['quantity']

        original_total += product.price * quantity

        subtotal = product.discounted_price * quantity
        total += subtotal

        cart_items.append({
            'product': product,
            'variant': variant,
            'quantity': quantity,
            'subtotal': subtotal,
            'cart_key': entry['cart_key']
        })

    return render(request, 'store/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'original_total': original_total,
        'product_discount': original_total - total
    })


# UPDATE CART QUANTITY
@require_POST
def update_cart(request, product_id):
    cart = request.session.get('cart', {})
    variant_id = request.POST.get('variant_id')
    cart_key = request.POST.get('cart_key')

    if not cart_key:
        cart_key = (
            f"{product_id}_{variant_id}"
            if variant_id else str(product_id)
        )

    if cart_key in cart:
        action = request.POST.get('action')

        if action == 'increase':
            cart[cart_key]['quantity'] += 1

        elif action == 'decrease':
            cart[cart_key]['quantity'] -= 1

            if cart[cart_key]['quantity'] <= 0:
                del cart[cart_key]

        request.session['cart'] = cart
        request.session.modified = True

    return redirect('cart')


# REMOVE CART ITEM
@require_POST
def remove_cart_item(request, product_id):
    cart = request.session.get('cart', {})
    variant_id = request.POST.get('variant_id')
    cart_key = request.POST.get('cart_key')

    if not cart_key:
        cart_key = (
            f"{product_id}_{variant_id}"
            if variant_id else str(product_id)
        )

    if cart_key in cart:
        del cart[cart_key]

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart')


# PRODUCT DETAILS
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    reviews = ProductReview.objects.filter(
        product=product
    ).select_related('customer')

    review_count = reviews.count()
    average_rating = 0

    if review_count > 0:
        average_rating = round(
            sum(review.rating for review in reviews) / review_count,
            1
        )

    return render(request, 'store/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'review_count': review_count,
        'average_rating': average_rating
    })


# CUSTOMER SIGNUP WITH WELCOME EMAIL
def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        email = request.POST.get('email', '').strip()

        if form.is_valid():

            if not email:
                form.add_error(
                    None,
                    'Please enter your email address.'
                )

            else:
                try:
                    validate_email(email)

                    user = form.save(commit=False)
                    user.email = email
                    user.save()

                    subject = 'Welcome to HOUSE OF ELEGANCE!'

                    message = f"""
Dear {user.username},

Welcome to HOUSE OF ELEGANCE!

Thank you for joining our fashion family.

We are delighted to have you as our customer.

Explore our beautiful collections and enjoy shopping
with HOUSE OF ELEGANCE.

Thank you for choosing us!

Warm regards,
HOUSE OF ELEGANCE Team
"""

                    try:
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL,
                            [user.email],
                            fail_silently=False
                        )

                        print(f"Welcome email sent to {user.email}")

                    except Exception as e:
                        print(f"Welcome email failed: {e}")

                    auth_login(request, user)
                    return redirect('home')

                except ValidationError:
                    form.add_error(
                        None,
                        'Please enter a valid email address.'
                    )

    else:
        form = UserCreationForm()

    return render(request, 'store/signup.html', {
        'form': form
    })


# CUSTOMER LOGIN
def login_view(request):
    error = ''

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            auth_login(request, user)
            return redirect('home')

        error = 'Invalid username or password.'

    return render(request, 'store/login.html', {
        'error': error
    })


# CUSTOMER LOGOUT
def logout_view(request):
    auth_logout(request)
    return redirect('home')


# ADD / REMOVE WISHLIST - MEESHO STYLE HEART
@login_required(login_url='login')
@require_POST
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()

    if wishlist_item:
        wishlist_item.delete()
        added = False
    else:
        Wishlist.objects.create(
            user=request.user,
            product=product
        )
        added = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'added': added
        })

    return redirect('home')


# VIEW WISHLIST
@login_required(login_url='login')
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product')

    return render(request, 'store/wishlist.html', {
        'wishlist_items': wishlist_items
    })


# REMOVE FROM WISHLIST
@login_required(login_url='login')
@require_POST
def remove_from_wishlist(request, product_id):
    wishlist_item = get_object_or_404(
        Wishlist,
        user=request.user,
        product_id=product_id
    )

    wishlist_item.delete()

    return redirect('wishlist')


# CHECKOUT WITH 30% DISCOUNT, COUPONS AND EMAIL
def checkout_view(request):
    cart = request.session.get('cart', {})

    if not cart:
        return redirect('cart')

    entries = get_cart_entries(cart)

    if not entries:
        return redirect('cart')

    product_ids = [entry['product_id'] for entry in entries]

    products = Product.objects.filter(id__in=product_ids)
    product_map = {product.id: product for product in products}

    # CALCULATE ORIGINAL AND DISCOUNTED TOTALS
    original_total = Decimal('0.00')
    total = Decimal('0.00')

    for entry in entries:
        product = product_map.get(entry['product_id'])

        if not product:
            continue

        quantity = entry['quantity']

        original_total += product.price * quantity
        total += product.discounted_price * quantity

    # AUTOMATIC PRODUCT DISCOUNT
    product_discount = original_total - total

    error = ''

    # FETCH ALL ACTIVE COUPONS
    available_coupons = Coupon.objects.filter(
        active=True
    ).order_by('-discount')

    # APPLY COUPON
    if (
        request.method == 'POST'
        and request.POST.get('action') == 'apply_coupon'
    ):
        code = request.POST.get(
            'coupon_code', ''
        ).strip().upper()

        coupon_to_apply = Coupon.objects.filter(
            code__iexact=code,
            active=True
        ).first()

        if (
            coupon_to_apply
            and 1 <= coupon_to_apply.discount <= 100
            and total >= coupon_to_apply.min_order_amount
        ):
            request.session['coupon_code'] = coupon_to_apply.code

        elif (
            coupon_to_apply
            and total < coupon_to_apply.min_order_amount
        ):
            request.session.pop('coupon_code', None)

            error = (
                f"This coupon requires a minimum order "
                f"of ₹{coupon_to_apply.min_order_amount}."
            )

        else:
            request.session.pop('coupon_code', None)
            error = 'Invalid or inactive coupon code.'

    # REMOVE COUPON
    elif (
        request.method == 'POST'
        and request.POST.get('action') == 'remove_coupon'
    ):
        request.session.pop('coupon_code', None)

    # GET APPLIED COUPON
    coupon = Coupon.objects.filter(
        code=request.session.get('coupon_code'),
        active=True
    ).first()

    discount = Decimal('0.00')

    if (
        coupon
        and 1 <= coupon.discount <= 100
        and total >= coupon.min_order_amount
    ):
        coupon_percentage = Decimal(str(coupon.discount))

        discount = (
            total * coupon_percentage / Decimal('100')
        ).quantize(Decimal('0.01'))

    else:
        if coupon:
            error = (
                f"This coupon requires a minimum order "
                f"of ₹{coupon.min_order_amount}."
            )

        request.session.pop('coupon_code', None)
        coupon = None

    # FINAL TOTAL
    final_total = total - discount

    # PLACE ORDER
    if (
        request.method == 'POST'
        and request.POST.get('action') not in [
            'apply_coupon', 'remove_coupon'
        ]
    ):
        customer_name = request.POST.get(
            'customer_name', ''
        ).strip()

        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        if not all([customer_name, email, phone, address]):
            error = 'Please fill in all delivery details.'

        else:
            try:
                validate_email(email)
            except ValidationError:
                error = 'Please enter a valid email address.'

            if not error:
                order_details = []

                # CREATE ORDER AND ORDER ITEMS
                with transaction.atomic():

                    order = Order.objects.create(
                        customer=(
                            request.user
                            if request.user.is_authenticated
                            else None
                        ),
                        customer_name=customer_name,
                        email=email,
                        phone=phone,
                        address=address,
                        total_amount=final_total
                    )

                    for entry in entries:
                        product = product_map.get(
                            entry['product_id']
                        )

                        if not product:
                            continue

                        variant = None

                        if entry['variant_id']:
                            variant = ProductVariant.objects.filter(
                                id=entry['variant_id'],
                                product=product
                            ).first()

                        # SAVE DISCOUNTED UNIT PRICE
                        OrderItem.objects.create(
                            order=order,
                            product=product,
                            variant=variant,
                            quantity=entry['quantity'],
                            price=product.discounted_price
                        )

                        variant_info = ''

                        if variant:
                            variant_info = (
                                f"\nColour: {variant.color}"
                                f"\nSize: {variant.size}"
                            )

                        order_details.append(
                            f"Product: {product.name}{variant_info}\n"
                            f"Original Price: Rs. {product.price}\n"
                            f"Discounted Price: Rs. {product.discounted_price}\n"
                            f"Quantity: {entry['quantity']}\n"
                        )

                # STORE OWNER EMAIL
                email_subject = (
                    f"New Order Received - Order #{order.id}"
                )

                email_message = f"""
HOUSE OF ELEGANCE - NEW ORDER

ORDER ID: #{order.id}

CUSTOMER DETAILS
-------------------------
Name: {customer_name}
Email: {email}
Phone: {phone}
Address: {address}

ORDERED PRODUCTS
-------------------------
{chr(10).join(order_details)}

PRICE SUMMARY
-------------------------
Original Total: Rs. {original_total}
Automatic 30% Discount: Rs. {product_discount}
Subtotal After Product Discount: Rs. {total}
Coupon: {coupon.code if coupon else 'No coupon'}
Additional Coupon Discount: Rs. {discount}
Final Amount: Rs. {final_total}

HOUSE OF ELEGANCE
"""

                try:
                    if not settings.ORDER_NOTIFICATION_EMAIL:
                        raise ValueError(
                            'ORDER_NOTIFICATION_EMAIL is not configured.'
                        )

                    send_mail(
                        subject=email_subject,
                        message=email_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[
                            settings.ORDER_NOTIFICATION_EMAIL
                        ],
                        fail_silently=False
                    )

                    print(
                        f"Order notification sent for order #{order.id}"
                    )

                except Exception as e:
                    print(
                        f"Order #{order.id} was saved, "
                        f"but email failed: {e}"
                    )

                # CLEAR CART AND COUPON
                request.session['cart'] = {}
                request.session.pop('coupon_code', None)
                request.session.modified = True

                return render(
                    request,
                    'store/order_success.html',
                    {'order': order}
                )

    # CHECKOUT DEBUG INFORMATION
    print("Original total:", original_total)
    print("Automatic product discount:", product_discount)
    print("Discounted subtotal:", total)
    print("Coupon discount:", discount)
    print("Final total:", final_total)

    return render(request, 'store/checkout.html', {
        'original_total': original_total,
        'product_discount': product_discount,
        'total': total,
        'discount': discount,
        'final_total': final_total,
        'coupon': coupon,
        'error': error,
        'available_coupons': available_coupons
    })


# CUSTOMER ORDER HISTORY
@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(
        customer=request.user
    ).order_by('-created_at')

    return render(request, 'store/my_orders.html', {
        'orders': orders
    })


# ORDER TRACKING
@login_required(login_url='login')
def track_order(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.user
    )

    return render(request, 'store/track_order.html', {
        'order': order
    })


# CUSTOMER PROFILE
@login_required(login_url='login')
def profile_view(request):
    return render(request, 'store/profile.html', {
        'user': request.user
    })


# EDIT CUSTOMER PROFILE
@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get(
            'first_name', ''
        ).strip()

        request.user.last_name = request.POST.get(
            'last_name', ''
        ).strip()

        request.user.email = request.POST.get(
            'email', ''
        ).strip()

        request.user.save()

        return redirect('profile')

    return render(request, 'store/profile_edit.html', {
        'user': request.user
    })


# SUBMIT PRODUCT REVIEW
@login_required(login_url='login')
def submit_review(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)

        try:
            rating = int(request.POST.get('rating', 0))
        except (ValueError, TypeError):
            rating = 0

        comment = request.POST.get('comment', '').strip()

        if 1 <= rating <= 5 and comment:
            ProductReview.objects.create(
                product=product,
                customer=request.user,
                rating=rating,
                comment=comment
            )

    return redirect('product_detail', product_id=product_id)
