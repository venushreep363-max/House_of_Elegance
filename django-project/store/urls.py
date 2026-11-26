




from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # HOME
    path('', views.home, name='home'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('track-order/<int:order_id>/', views.track_order, name='track_order'),
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('product/<int:product_id>/review/', views.submit_review, name='submit_review'),
    # FORGOT PASSWORD
path(
    'password-reset/',
    auth_views.PasswordResetView.as_view(
        template_name='store/password_reset.html',
        email_template_name='store/password_reset_email.html',
        subject_template_name='store/password_reset_subject.txt'
    ),
    name='password_reset'
),

path(
    'password-reset/done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='store/password_reset_done.html'
    ),
    name='password_reset_done'
),

path(
    'reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='store/password_reset_confirm.html'
    ),
    name='password_reset_confirm'
),

path(
    'reset/done/',
    auth_views.PasswordResetCompleteView.as_view(
        template_name='store/password_reset_complete.html'
    ),
    name='password_reset_complete'
),

    # SHOPPING CART
    path('cart/', views.cart_view, name='cart'),
    path('add-cart/<int:product_id>/', views.add_cart_item, name='add_cart'),
    path('cart/update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:product_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('sarees/', views.sarees_view, name='sarees'),
    path('kurtis/', views.kurtis_view, name='kurtis'),
    # CHECKOUT
    path('checkout/', views.checkout_view, name='checkout'),

    # PRODUCT DETAILS
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),

    # LOGIN AND SIGNUP
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # WISHLIST
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]
