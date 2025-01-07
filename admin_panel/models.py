from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
# -----------------------------------------------------

class Offer(models.Model):
    OFFER_TYPE_CHOICES = [
        ('PRODUCT', 'Product Offer'),
        ('CATEGORY', 'Category Offer')
    ]
    
    offer_name = models.CharField(max_length=50, null=True)
    description = models.TextField(null=True)
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    offer_type = models.CharField(max_length=30, choices=OFFER_TYPE_CHOICES, default='CATEGORY', null=True)
    is_active = models.BooleanField(default=True, null=True)
    
    product = models.ForeignKey(
        'Product', 
        on_delete=models.CASCADE, 
        related_name='offers', 
        null=True,  # Allow null to prevent issues with existing records
        blank=True
    )
    category = models.ForeignKey(
        'Catogery', 
        on_delete=models.CASCADE, 
        related_name='offers', 
        null=True,  # Allow null to prevent issues with existing records
        blank=True
    )



    def __str__(self) -> str:
        return self.offer_name or 'Unnamed Offer'




# ----------------------------------------------------
# Create your models here.

class Catogery(models.Model):
    STATUS_CHOICES = [
        ('Available','Available'),
        ('Not Available','Not Available'),
    ]

    id = models.AutoField(primary_key= True)
    name = models.CharField(max_length= 255)
    description = models.TextField()
    total_product = models.PositiveIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True, null=True)
    
    status = models.CharField(
        max_length = 15,
        choices=STATUS_CHOICES,
        default='Available'
    )

    earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

def __str__(self):
    return self.name


# -----------------------------------PRODUCT MODEL--------------------------------------------------------------------------------------------------

class Product(models.Model):
    id = models.AutoField(primary_key  = True)
    name = models.CharField(max_length=255)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True)  # Allow null values initially
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True)  # Allow null values initially
    stock_quantity = models.PositiveBigIntegerField(default=0)
    created_at = models.DateField(auto_now_add=True, null=True)
    
    catogery = models.ForeignKey(
        Catogery,
        on_delete=models.CASCADE,
        related_name = 'products'
    )
    is_delete = models.BooleanField(default=False) #for handling soft delete

    def __str__(self):
        return self.name
    
    @property
    def discount_price(self):
        if self.discount_percentage:
            discount = (self.base_price * self.discount_percentage)/ 100
            return self.base_price - discount
        return None
    # --------------------------added after varient came------------------------
    def get_default_variant(self):
        # Get the variant with the smallest weight
        variants = self.variants.all()
        
        if not variants.exists():
            return None
        
        # Sort variants by weight in ascending order
        def extract_weight(variant):
            try:
                # Extract numeric value from weight string
                return float(variant.weight.replace('kg', ''))
            except (ValueError, AttributeError):
                return float('inf')  # Put non-numeric weights at the end
        
        smallest_variant = min(variants, key=extract_weight)
        return smallest_variant

    def get_display_price(self):
        # Use offer_price if available, otherwise use base_price
        if self.offer_price:
            return self.offer_price
        return self.base_price
    
    def get_discounted_price(self):
        if hasattr(self, 'discounted_price'):
            return self.discounted_price
        if self.final_discount:
            return self.base_price * (1 - self.final_discount / 100)
        return self.base_price
    
     # Add a property to maintain backward compatibility
    @property
    def category(self):
        return self.catogery

    

class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete = models.CASCADE,
        related_name='images'        
    )
    images = models.ImageField(upload_to= 'product_image/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.product.name}"



# ------------------------------------------------------------------------------------------



class Variant(models.Model):
    CATEGORY_CHOICES = [
        ('WEIGHT', 'Weight-Based'),
        ('VOLUME', 'Volume-Based')
    ]

    WEIGHT_CHOICES = [
        ('0.5', '0.5 kg'),
        ('1', '1 kg'),
        ('1.5', '1.5 kg'),
        ('2', '2 kg')
    ]

    VOLUME_CHOICES = [
        ('0.5', '0.5 liter'),
        ('1', '1 liter')
    ]

    product = models.ForeignKey(
        'admin_panel.Product', 
        on_delete=models.CASCADE, 
        related_name='variants',
        null=True,
        blank=True
    )

    category = models.CharField(
        max_length=10, 
        choices=CATEGORY_CHOICES,
        null=True,
        blank=True
    )

    weight = models.CharField(
        max_length=10, 
        choices=WEIGHT_CHOICES, 
        null=True,
        blank=True
    )

    volume = models.CharField(
        max_length=10, 
        choices=VOLUME_CHOICES, 
        null=True,
        blank=True
    )

    variant_name = models.CharField(
        max_length=50, 
        null=True,
        blank=True
    )

    variant_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    stock_quantity = models.PositiveIntegerField(
        default=0,
        null=True,
        blank=True
    )

    sku = models.CharField(
        max_length=100, 
        unique=True, 
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True, 
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'product_variants'
        unique_together = ['product', 'weight', 'volume']

    def __str__(self):
        if self.category == 'WEIGHT':
            return f"{self.product.name} - {self.get_weight_display()}"
        elif self.category == 'VOLUME':
            return f"{self.product.name} - {self.get_volume_display()}"
        return f"{self.product.name} - Variant"

    @property
    def display_name(self):
        if self.category == 'WEIGHT':
            return self.get_weight_display()
        elif self.category == 'VOLUME':
            return self.get_volume_display()
        return self.variant_name

    def save(self, *args, **kwargs):
        # Automatically set variant name based on category
        if self.category == 'WEIGHT' and self.weight:
            self.variant_name = self.get_weight_display()
        elif self.category == 'VOLUME' and self.volume:
            self.variant_name = self.get_volume_display()
        
        super().save(*args, **kwargs)

# --------------------------------------------------------newly added for transaction
 
    
# ---------------------------------------------------------------------------
    from decimal import Decimal

    def calculate_price(self):
        base_price = self.product.base_price  # Decimal
        base_variant_weight = Decimal('0.5')  # Convert to Decimal
    
    # Weight-based pricing (10% increment)
        if self.category == 'WEIGHT':
            weight = Decimal(self.weight)  # Convert to Decimal
        
            if weight > base_variant_weight:
                price_multiplier = Decimal('1') + (Decimal('0.1') * (weight / base_variant_weight - Decimal('1')))
                return base_price * price_multiplier
    
    # Volume-based pricing (similar changes)
        elif self.category == 'VOLUME':
            base_variant_volume = Decimal('0.5')
            volume = Decimal(self.volume)
        
            if volume > base_variant_volume:
                price_multiplier = Decimal('1') + (Decimal('0.1') * (volume / base_variant_volume - Decimal('1')))
                return base_price * price_multiplier
    
        return base_price
    

    def save(self, *args, **kwargs):
        # Automatically calculate and set variant price
        self.variant_price = self.calculate_price()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------------------------------------------------------------------------

from django.db import models
from uuid import uuid4  # For UUID generation

class CouponTable(models.Model):
    code = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Unique code for the coupon
    coupon_type = models.CharField(
        max_length=20,
        choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')],
        default='percentage',
        null=True, blank=True
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_purchase_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"Coupon {self.code} ({self.coupon_type}: {self.discount_value})"

class CouponUsage(models.Model):
    user = models.ForeignKey('user.CustomUser', on_delete=models.CASCADE, null=True, blank=True)  # Links to your custom user model
    coupon = models.ForeignKey(CouponTable, on_delete=models.CASCADE, null=True, blank=True)  
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  
    used_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  

    def __str__(self):
        return f"{self.user.username} used {self.coupon.code} on {self.used_at}"


# ----------------------------------------------------------------------------------------------------------------------------

# class Offer(models.Model):
#     OFFER_TYPE_CHOICES = [
#         ('PRODUCT', 'Product Offer'),
#         ('CATEGORY', 'Category Offer')
#     ]
    
#     offer_name = models.CharField(max_length=50, null=True)
#     description = models.TextField(null=True)
#     discount_percentage = models.DecimalField(max_digits=10, decimal_places=2, null=True)
#     start_date = models.DateField(null=True)
#     end_date = models.DateField(null=True)
#     offer_type = models.CharField(max_length=30, choices=OFFER_TYPE_CHOICES, default='CATEGORY', null=True)
#     is_active = models.BooleanField(default=True, null=True)
    
#     def __str__(self) -> str:
#         return self.offer_name or 'Unnamed Offer'


































