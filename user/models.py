from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.db import models
from django.conf import settings  
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal

class CustomUser(AbstractUser):
    user_id = models.UUIDField(primary_key=True, unique=True, default=uuid.uuid4, editable=False)
    phone_number = models.CharField(max_length=15)
    create_at = models.DateField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_permissions',  
        blank=True,
    )

    class Meta:
        db_table = 'Custom_User'  

    def __str__(self):
        return self.username


# ----AddressBook---------------------------------------------------------------------------------------------------------------------


class Address(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  
        on_delete=models.CASCADE,  
        related_name='addresses'  
    )
    full_name = models.CharField(max_length=255, null=True, blank=True)
    street_address = models.TextField(null=True, blank=True)
    apartment_suite = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)  
    state = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  
    is_default = models.BooleanField(default=False)  

    class Meta:
        db_table = 'user_address'  
        ordering = ['-created_at']  

    def __str__(self):
        return f"{self.full_name}, {self.city}"



#----- CART MODEL ----- working og -----------------------------------------------------------------------------------------------------------------------




from decimal import Decimal, InvalidOperation
class Cart(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        'CustomUser',  
        on_delete=models.SET_NULL,  
        related_name="cart_items",
        null=True,
        blank=True
    )
    product = models.ForeignKey(
        'admin_panel.Product',  
        on_delete=models.CASCADE,  
        related_name="cart_entries",
        null=True,
        blank=True
    )

    variant = models.ForeignKey(
        'admin_panel.Variant',  
        on_delete=models.CASCADE,
        related_name="cart_items",
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1, null=True, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  


    applied_coupon = models.ForeignKey(
        'admin_panel.CouponTable',  
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cart_items'
    )
    discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        null=True, 
        blank=True
    )








    class Meta:
        db_table = "Cart"  
        unique_together = ("user", "product", "variant")  

    def __str__(self):
        return f"Cart({self.user}, {self.product}, {self.quantity})"

    # def save(self, *args, **kwargs):
    #     """
    #     Override save method to validate stock and manage stock levels
    #     """
    #     # Determine if this is a new cart item or an existing one being updated
    #     is_new_item = self.pk is None
        
    #     # If it's an existing item, get the previous quantity
    #     old_quantity = 0
    #     if not is_new_item:
    #         try:
    #             old_cart_item = Cart.objects.get(pk=self.pk)
    #             old_quantity = old_cart_item.quantity or 0
    #         except Cart.DoesNotExist:
    #             old_quantity = 0

    #     # Validate stock before saving
    #     if self.variant and self.quantity:
    #         # Check if there's enough stock
    #         if self.variant.stock_quantity < self.quantity:
    #             raise ValidationError(f"Insufficient stock. Only {self.variant.stock_quantity} available.")

    #         # If the item exists, adjust stock based on quantity change
    #         if not is_new_item:
    #             quantity_difference = self.quantity - old_quantity
                
    #             # Reduce stock if quantity increased, increase stock if reduced
    #             if quantity_difference > 0:
    #                 if self.variant.stock_quantity < quantity_difference:
    #                     raise ValidationError(f"Cannot increase quantity. Only {self.variant.stock_quantity} additional items available.")
    #                 self.variant.stock_quantity -= quantity_difference
    #             elif quantity_difference < 0:
    #                 self.variant.stock_quantity += abs(quantity_difference)
                
    #             self.variant.save()
    #         else:
    #             # For new items, reduce stock
    #             self.variant.stock_quantity -= self.quantity
    #             self.variant.save()

    #     # Call the parent save method
    #     super().save(*args, **kwargs)

    # def delete(self, *args, **kwargs):
    #     """
    #     Override delete method to restore stock when cart item is removed
    #     """
    #     # Restore stock when item is deleted
    #     if self.variant and self.quantity:
    #         self.variant.stock_quantity += self.quantity
    #         self.variant.save()
        
    #     super().delete(*args, **kwargs)














    def _update_stock_quantities(self, quantity_difference):
        """
        Helper method to update stock quantities for both Variant and Product
        """
        if not self.variant or not self.product:
            return

        
        if quantity_difference > 0:
            if self.variant.stock_quantity < quantity_difference:
                raise ValidationError(f"Cannot increase quantity. Only {self.variant.stock_quantity} items available.")
            
            if self.product.stock_quantity < quantity_difference:
                raise ValidationError(f"Cannot increase quantity. Only {self.product.stock_quantity} items available in product stock.")
            
            self.variant.stock_quantity -= quantity_difference
            self.product.stock_quantity -= quantity_difference
        elif quantity_difference < 0:
            self.variant.stock_quantity += abs(quantity_difference)
            self.product.stock_quantity += abs(quantity_difference)
        
        self.variant.save()
        self.product.save()

    def save(self, *args, **kwargs):
        """
        Override save method with improved error handling
        """
        with transaction.atomic():
            is_new_item = self.pk is None
            old_quantity = 0

            if not is_new_item:
                try:
                    old_cart_item = Cart.objects.get(pk=self.pk)
                    old_quantity = old_cart_item.quantity or 0
                except Cart.DoesNotExist:
                    old_quantity = 0

            if not self.quantity or self.quantity < 1:
                raise ValidationError("Quantity must be at least 1")

            if not self.variant or not self.product:
                raise ValidationError("Both product and variant must be specified")

            if is_new_item:
                if self.variant.stock_quantity < self.quantity:
                    raise ValidationError(f"Insufficient variant stock. Only {self.variant.stock_quantity} available.")
                if self.product.stock_quantity < self.quantity:
                    raise ValidationError(f"Insufficient product stock. Only {self.product.stock_quantity} available.")
                self._update_stock_quantities(self.quantity)
            else:
                quantity_difference = self.quantity - old_quantity
                if quantity_difference != 0:
                    self._update_stock_quantities(quantity_difference)

            super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete method to restore stock
        """
        with transaction.atomic():
            if self.variant and self.product and self.quantity:
                self.variant.stock_quantity += self.quantity
                self.product.stock_quantity += self.quantity
                self.variant.save()
                self.product.save()
            
            super().delete(*args, **kwargs)








    @property
    def total_price(self):
        """
        Calculates the total price with dynamic pricing based on variant
        """
        try:
            if self.variant and self.variant.variant_price:
                base_price = Decimal(str(self.variant.variant_price))
            elif self.product and self.product.base_price:
                base_price = Decimal(str(self.product.base_price))
            else:
                return Decimal('0.00')

            if self.variant and self.variant.weight:
                base_weight = float(self.variant.weight)
                standard_weight = 0.1  # 0.1 kg as base

                price_multiplier = 1 + (base_weight / standard_weight - 1) * 0.1
                base_price *= Decimal(str(price_multiplier))

            quantity = Decimal(str(self.quantity or 1))
            return base_price * quantity

        except (TypeError, InvalidOperation, AttributeError) as e:
            print(f"Price calculation error: {e}")
            return Decimal('0.00')

    def clean(self):
        """
        Additional validation method
        """
        if self.quantity and self.quantity < 1:
            raise ValidationError("Quantity must be at least 1")

        if self.variant and self.quantity:
            if self.variant.stock_quantity < self.quantity:
                raise ValidationError(f"Insufficient stock. Only {self.variant.stock_quantity} available.")
            

    @property
    def total_price_with_discount(self):
        """
        Calculate total price after applying discount
        """
        try:
            total_price = self.total_price
            discount = Decimal(str(self.discount_amount or '0'))
            return max(total_price - discount, Decimal('0.00'))
        except Exception as e:
            print(f"Error calculating discounted price: {e}")
            return self.total_price



# -------trying to implement variant neew %------------------------------


# @property
# def total_price(self):
#     """
#     Calculates the total price with incremental pricing based on variant weight:
#     - 0.5 kg: base price (product.final_price)
#     - 1.0 kg: 0.5 kg price + 10%
#     - 1.5 kg: 1.0 kg price + 10%
#     - 2.0 kg: 1.5 kg price + 10%
#     """
#     try:
#         # Start with base price from product (considering any active offers)
#         if not self.product or not self.variant:
#             return Decimal('0.00')
        
#         base_price = Decimal(str(self.product.final_price))
        
#         # Apply weight-based pricing if variant has weight
#         if self.variant and self.variant.weight:
#             variant_weight = Decimal(str(self.variant.weight))
            
#             # Define weight tiers and their corresponding prices
#             if variant_weight == Decimal('0.5'):
#                 final_price = base_price
#             elif variant_weight == Decimal('1.0'):
#                 # 10% more than 0.5 kg price
#                 final_price = base_price * Decimal('1.1')
#             elif variant_weight == Decimal('1.5'):
#                 # 10% more than 1.0 kg price
#                 final_price = base_price * Decimal('1.1') * Decimal('1.1')
#             elif variant_weight == Decimal('2.0'):
#                 # 10% more than 1.5 kg price
#                 final_price = base_price * Decimal('1.1') * Decimal('1.1') * Decimal('1.1')
#             else:
#                 # Default to base price if weight doesn't match any tier
#                 final_price = base_price
#         else:
#             # If no weight specified, use base price
#             final_price = base_price

#         # Multiply by quantity
#         quantity = Decimal(str(self.quantity or 1))
#         return final_price * quantity

#     except (TypeError, InvalidOperation, AttributeError) as e:
#         print(f"Price calculation error: {e}")
#         return Decimal('0.00')

# @property
# def total_price_with_discount(self):
#     """
#     Calculate total price after applying discount
#     """
#     try:
#         total_price = self.total_price
#         discount = Decimal(str(self.discount_amount or '0'))
#         return max(total_price - discount, Decimal('0.00'))
#     except Exception as e:
#         print(f"Error calculating discounted price: {e}")
#         return self.total_price






#-----Order--------------------------------------------------------------------------------------------------------







class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        # ('out_of_delivery', 'Out of Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('COD', 'Cash on Delivery'),
        ('ONLINE', 'Online Payment'),
        ('WALLET', 'Wallet Payment'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    applied_coupon = models.ForeignKey('admin_panel.CouponTable' , on_delete=models.SET_NULL, null=True, blank=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="orders", 
        null=True, blank=True
    )
    
    address = models.ForeignKey(
        Address,  
        on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    total_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=Decimal('0.00')
    )
    payment_method = models.CharField( 
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='COD'
    )
    order_status = models.CharField(
        max_length=20, 
        choices=ORDER_STATUS_CHOICES, 
        default='pending'
    )
    
    

    order_date = models.DateTimeField(auto_now_add=True)
    
    is_canceled = models.BooleanField(default=False)
    cancel_description = models.TextField(blank=True, null=True)
    cancel_date = models.DateTimeField(blank=True, null=True)
    is_refund = models.BooleanField(default=False)
    refund_date = models.DateTimeField(blank=True, null=True)
    
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, null=True, blank=True)
    
    razorpay_signature = models.CharField(
        max_length=100, 
        null=True, 
        blank=True
    )
    
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        null=True,
        blank=True
    )

    payment_retry_window = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-order_date']

    def __str__(self):
        return f"Order {self.id} by {self.user.username if self.user else 'Anonymous'}"
    
    def calculate_total(self):
        total = sum(item.total_price for item in self.order_items.all())
        self.total_amount = total
        self.save()

    def mark_payment_success(self, payment_id, signature):
        """
        Mark the order payment as successful
        """
        self.payment_status = 'success'
        self.razorpay_payment_id = payment_id
        self.razorpay_signature = signature
        self.save()

    def mark_payment_failed(self):
        """
        Mark the order payment as failed
        """
        self.payment_status = 'failed'
        self.save()

    @property
    def dynamic_status(self):
        if self.orderreturn_set.filter(status='APPROVED').exists():
            return "Returning"
        return self.get_order_status_display()

    def __str__(self):
        return f"Order {self.id} - {self.dynamic_status}"
    


    def process_refund(self):
        """
        Process refund for the order
        """
        if self.payment_status == 'success':
            self.payment_status = 'refunded'
            self.is_refund = True
            self.refund_date = timezone.now()
            self.save()
            return True
        return False    

    def has_return_request(self):
        """
        Check if any order item has an active return request
        """
        return self.order_items.filter(
            return_request__status__in=['REQUESTED', 'APPROVED']
        ).exists()

    def can_request_return(self):
        """
        Check if the order is eligible for return
        """
        return (
            self.order_status == 'delivered' and 
            not self.has_return_request()
        )
    
    def can_retry_payment(self):
        """Check if payment can be retried within 10 minutes window"""
        if not self.payment_retry_window:
            self.payment_retry_window = self.order_date + timedelta(minutes=10)
            self.save()
        
        return (
            self.payment_status == 'pending' and 
            timezone.now() <= self.payment_retry_window
        )
    

# ------------order item -------------------------------------------------------------------------------------------------


from datetime import timedelta

class OrderItem(models.Model):
    order = models.ForeignKey(
        'Order',  
        on_delete=models.CASCADE,
        related_name='order_items'  
    )
    product = models.ForeignKey(
        'admin_panel.Product',  
        on_delete=models.CASCADE,
        related_name='order_items'  
    )

    is_cancelled = models.BooleanField(default=False, null=True)
    
    variant = models.ForeignKey(
        'admin_panel.Variant',  
        on_delete=models.SET_NULL,
        related_name='order_items',
        null=True,
        blank=True
    )

    quantity = models.PositiveIntegerField(default=1)
    price_per_unit = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('0.00')
    )

    
    class Meta:
        db_table = 'order_items'  


    def __str__(self):
        variant_info = f" ({self.variant.display_name})" if self.variant else ""
        return f"{self.quantity} x {self.product.name}{variant_info} for Order {self.order.id}"

    def save(self, *args, **kwargs):
        """Override save method to calculate total price automatically."""
        if self.variant:
            self.price_per_unit = self.variant.variant_price
        else:
            self.price_per_unit = self.product.base_price
        
        self.total_price = self.quantity * self.price_per_unit
        super().save(*args, **kwargs)

    # def can_retry_payment(self):
    #     if not self.payment_retry_window:
    #         self.payment_retry_window = self.order_date + timedelta(minutes=10)
    #         self.save()
    #     return (
    #         self.payment_status == 'pending' and 
    #         timezone.now() <= self.payment_retry_window
    #     )
    

# --------Wishlist model------------------------------------------------------------------------------------------------

class Wishlist(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='wishlists',
        null=True  
    )
    product = models.ForeignKey(
        'admin_panel.Product',  
        on_delete=models.CASCADE,
        related_name='wishlisted_by',
        null=True  
    )
    added_at = models.DateTimeField(auto_now_add=True, null=True)  
    is_deleted = models.BooleanField(default=False, null=True)  

    class Meta:
        db_table = 'Wishlist'  

    def __str__(self):
        return f"Wishlist of {self.user} for {self.product}"


# --------------------------------------------------------------------------

class OrderReturn(models.Model):
    RETURN_STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]

    RETURN_REASON_CHOICES = [
        ('DEFECTIVE', 'Defective Product'),
        ('WRONG_ITEM', 'Wrong Item Delivered'),
        ('SIZE_ISSUE', 'Size/Fit Issue'),
        ('QUALITY_ISSUE', 'Poor Quality'),
        ('NOT_NEEDED', 'No Longer Needed')
    ]

    order_item = models.OneToOneField(
        OrderItem, 
        on_delete=models.CASCADE,
        related_name='return_request',
        null=True  
    )
    
    return_reason = models.CharField(
        max_length=20, 
        choices=RETURN_REASON_CHOICES,
        null=True  
    )
    
    return_explanation = models.TextField(
        null=True, 
        blank=True
    )
    
    status = models.CharField(
        max_length=20, 
        choices=RETURN_STATUS_CHOICES, 
        default='REQUESTED',
        null=True 
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True  
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True  
    )

    return_proof = models.ImageField(
        upload_to='return_proofs/', 
        null=True, 
        blank=True
    )

    class Meta:
        db_table = 'order_returns'
        ordering = ['-created_at']

    def __str__(self):
        return f"Return for {self.order_item} - {self.status}"

    def save(self, *args, **kwargs):
        if self.status == 'APPROVED':
            if self.order_item:
                self.order_item.is_cancelled = True
                self.order_item.save()

                order = self.order_item.order
                order.calculate_total()  
                order_items = order.order_items.all()
                if all(item.is_cancelled for item in order_items):
                    order.order_status = 'cancelled'
                    order.is_canceled = True
                    order.cancel_date = timezone.now()
                    order.save()

        super().save(*args, **kwargs)

    def process_refund(self):
        """
        Method to handle refund processing
        Can be extended to integrate with payment systems
        """
        if self.status == 'APPROVED' and self.order_item:
            refund_amount = self.order_item.total_price
            
            
            return True
        return False

    @property
    def refund_amount(self):
        """
        Calculate refund amount for the returned item
        Considers product price, variant price, and quantity
        """
        try:
            if not self.order_item:
                return Decimal('0.00')
            
            if self.order_item.variant:
                item_price = self.order_item.variant.variant_price or self.order_item.product.base_price
            else:
                item_price = self.order_item.product.base_price
            
            refund = item_price * self.order_item.quantity
            return Decimal(refund)
        
        except Exception as e:
            print(f"Error calculating refund amount: {e}")
            return Decimal('0.00')



class Wallet(models.Model):
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )  
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0.00, 
        null=True, 
        blank=True
    )  
    
    def __str__(self) -> str:
        if self.user:
            return f"{self.user.first_name} {self.user.last_name}'s Wallet"
        return "Wallet (No User Assigned)"
    

    def update_balance(self):
        """
        Update wallet balance based on all transactions.
        Balance = (Refunds + Credits) - Debits
        """
        credits = self.wallettransaction_set.filter(
            transaction_type__in=['REFUND', 'CREDIT']
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        debits = self.wallettransaction_set.filter(
            transaction_type='DEBIT'
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

        self.balance = credits - debits
        self.save()
        return self.balance





    def get_total_refunds(self, start_date=None, end_date=None):
        """
        Calculate total refunds for the wallet
        Optionally filter by date range
        """
        transactions = self.wallettransaction_set.filter(
            transaction_type='REFUND'
        )
        
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        return transactions.aggregate(
            total_refunds=models.Sum('amount')
        )['total_refunds'] or Decimal('0.00')
    
# ------------------------------------------------
    def get_total_added_funds(self, start_date=None, end_date=None):
        """
        Calculate total funds added through Razorpay
        """
        transactions = self.wallettransaction_set.filter(
            transaction_type='CREDIT',
            payment_method='RAZORPAY'
        )
        
        if start_date:
            transactions = transactions.filter(created_at__gte=start_date)
        
        if end_date:
            transactions = transactions.filter(created_at__lte=end_date)
        
        return transactions.aggregate(
            total_added_funds=models.Sum('amount')
        )['total_added_funds'] or Decimal('0.00')

    
# -------------------------------------------------------------------
from django.db.models.signals import post_save
from django.dispatch import receiver

class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('REFUND', 'Refund'),
        ('CANCELLATION', 'Cancellation'),
        ('CREDIT', 'Credited'),
        ('DEBIT', 'Debited'),
        ('REFERRAL', 'Referral')
    ]
    PAYMENT_METHOD_CHOICES = [
        ('RAZORPAY', 'Razorpay'),
        ('STRIPE', 'Stripe'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('INTERNAL', 'Internal Transfer')
    ]

    wallet = models.ForeignKey(
        Wallet, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )  
    transaction_type = models.CharField(
        max_length=20, 
        choices=TRANSACTION_TYPE_CHOICES, 
        null=True, 
        blank=True
    )  
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )  
    created_at = models.DateTimeField(
        auto_now_add=True, 
        null=True, 
        blank=True
    )  

    payment_method = models.CharField(
        max_length=20, 
        choices=PAYMENT_METHOD_CHOICES, 
        null=True, 
        blank=True
    )
    razorpay_payment_id = models.CharField(
        max_length=100, 
        null=True, 
        blank=True
    )





    @classmethod
    def create_refund_transaction(cls, wallet, refund_amount, order_return=None):
        """
        Convenient method to create a refund transaction
        """
        return cls.objects.create(
            wallet=wallet,
            transaction_type='REFUND',
            amount=refund_amount,
            
            order_return=order_return
        )



    @classmethod
    def create_razorpay_fund_transaction(cls, wallet, amount, razorpay_payment_id):
        """
        Create a transaction for Razorpay fund addition
        """
        return cls.objects.create(
            wallet=wallet,
            transaction_type='CREDIT',
            amount=amount,
            payment_method='RAZORPAY',
            razorpay_payment_id=razorpay_payment_id
        )

# ----------------------------------------------

#     def save(self, *args, **kwargs):
#         """
#         Override save method to update wallet balance after transaction
#         """
#         super().save(*args, **kwargs)
#         if self.wallet:
#             self.wallet.update_balance()

# # Signal to update wallet balance when a transaction is created
# @receiver(post_save, sender=WalletTransaction)
# def update_wallet_balance(sender, instance, created, **kwargs):
#     """
#     Signal handler to update wallet balance after transaction save
#     """
#     if instance.wallet:
#         instance.wallet.update_balance()

# -------------------------------------------------------------------------------------------------


class Refund(models.Model):
    order_return = models.ForeignKey(
        OrderReturn, 
        on_delete=models.CASCADE, 
        related_name='refunds', 
        null=True, 
        blank=True
    )  
    refund_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )  
    refund_method = models.CharField(
        max_length=20, 
        choices=[
            ('ORIGINAL_PAYMENT', 'Original Payment Method'),
            ('STORE_CREDIT', 'Store Credit'),
            ('WALLET', 'Wallet Balance')
        ], 
        null=True, 
        blank=True
    )  
    refund_date = models.DateTimeField(
        auto_now_add=True, 
        null=True, 
        blank=True
    )  
    refund_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSED', 'Processed'),
            ('FAILED', 'Failed')
        ],
        default='PENDING', 
        null=True, 
        blank=True
    )  
    def __str__(self):
        
        if self.order_return and self.order_return.order_item and self.order_return.order_item.product:
            return f"Refund for {self.order_return.order_item.product.name}" 
        return "Refund (Incomplete Data)"






class WalletWithdrawal(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]
    
    user = models.ForeignKey(
        CustomUser,  # Your user model
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    bank_account_number = models.CharField(max_length=50)
    bank_ifsc_code = models.CharField(max_length=20)
    account_holder_name = models.CharField(max_length=100)
    reference_id = models.CharField(max_length=100, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Withdrawal #{self.id} - {self.user.email} - {self.amount} - {self.status}"
    








class OrderAddress(models.Model):
    order = models.OneToOneField(
        'Order',
        on_delete=models.CASCADE,
        related_name='shipping_address'
    )
    full_name = models.CharField(max_length=255, null=True, blank=True)
    street_address = models.TextField(null=True, blank=True)
    apartment_suite = models.CharField(max_length=255, null=True, blank=True)
    landmark = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'order_address'

    def __str__(self):
        return f"Order #{self.order.id} - {self.full_name or 'No Name'}, {self.city or 'No City'}"

    @classmethod
    def create_from_address(cls, order, address):
        """
        Create OrderAddress from user's Address instance
        """
        return cls.objects.create(
            order=order,
            full_name=address.full_name,
            street_address=address.street_address,
            apartment_suite=address.apartment_suite,
            landmark=address.landmark,
            city=address.city,
            postal_code=address.postal_code,
            phone_number=address.phone_number,
            state=address.state
        )        








