
from django.contrib import admin
from .models import (
    Product,
    Order,
    OrderItem,
    Wishlist,
    ProductVariant,
    ProductReview,
    Coupon
)

COLOURS = ['Red', 'Black', 'Pink', 'Blue', 'Green']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'stock')
    search_fields = ('name', 'category')
    list_filter = ('category',)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        for colour in COLOURS:
            if not ProductVariant.objects.filter(
                product=obj,
                color=colour
            ).exists():
                ProductVariant.objects.create(
                    product=obj,
                    color=colour,
                    stock=obj.stock
                )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'email',
        'total_amount', 'status', 'created_at'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'email', 'phone')
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'added_at')
    search_fields = ('user__username', 'product__name')


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'color', 'size', 'stock')
    list_filter = ('color', 'size')
    search_fields = ('product__name', 'color', 'size')


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'customer', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'customer__username', 'comment')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount', 'active')
    list_filter = ('active',)
    search_fields = ('code',)
