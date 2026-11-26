
from django.db import models
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP


# PRODUCT MODEL
class Product(models.Model):

    CATEGORY_CHOICES = [
        ('Dresses', 'Dresses'),
        ('Sarees', 'Sarees'),
        ('Kurtis', 'Kurtis'),
        ('Tops', 'Tops'),
        ('Shirts', 'Shirts'),
        ('Western Wear', 'Western Wear'),
        ('Pants & Trousers', 'Pants & Trousers'),
        ('Jeans', 'Jeans'),
        ('Skirts', 'Skirts'),
        ('Co-ord Sets', 'Co-ord Sets'),
        ('Party Wear', 'Party Wear'),
        ('Ethnic Wear', 'Ethnic Wear'),
        ('Jumpsuits', 'Jumpsuits'),
    ]

    name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=100,
        choices=CATEGORY_CHOICES
    )

    description = models.TextField()

    # ORIGINAL PRICE / MRP
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True
    )

    stock = models.IntegerField(default=10)

    # AUTOMATIC 30% DISCOUNT
    @property
    def discount_percentage(self):
        return 30 if self.price > 0 else 0

    # AUTOMATIC DISCOUNTED PRICE
    @property
    def discounted_price(self):
        return (self.price * Decimal('0.70')).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

    def __str__(self):
        return self.name


# ORDER MODEL
class Order(models.Model):

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    customer_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address = models.TextField()

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id}"


# ORDER ITEM MODEL
class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    variant = models.ForeignKey(
        'ProductVariant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='order_items'
    )

    quantity = models.PositiveIntegerField(default=1)

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    def __str__(self):
        return self.product.name


# WISHLIST MODEL
class Wishlist(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# PRODUCT VARIANT MODEL
class ProductVariant(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )

    color = models.CharField(
        max_length=50,
        blank=True
    )

    size = models.CharField(
        max_length=20,
        blank=True
    )

    image = models.ImageField(
        upload_to='product_variants/',
        blank=True,
        null=True
    )

    stock = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.product.name} - {self.color or self.size}"


# PRODUCT REVIEW MODEL
class ProductReview(models.Model):

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    rating = models.PositiveIntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"


# COUPON MODEL
class Coupon(models.Model):

    code = models.CharField(
        max_length=30,
        unique=True
    )

    discount = models.PositiveIntegerField()

    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code
