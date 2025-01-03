from django.core.management.base import BaseCommand
from admin_panel.models import Product, Variant
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create variants for existing products'

    def handle(self, *args, **kwargs):
        # Get all existing products
        products = Product.objects.all()
        
        for product in products:
            # Skip if variants already exist
            if product.variants.exists():
                self.stdout.write(self.style.WARNING(f'Variants already exist for {product.name}. Skipping.'))
                continue
            
            # Determine category based on product type
            if product.catogery.name.lower() in ['vegetables', 'fruits', 'dried']:
                variants = [
                    {'weight': '0.5', 'category': 'WEIGHT'},
                    {'weight': '1', 'category': 'WEIGHT'},
                    {'weight': '1.5', 'category': 'WEIGHT'},
                    {'weight': '2', 'category': 'WEIGHT'}
                ]
            elif product.catogery.name.lower() == 'juice':
                variants = [
                    {'volume': '0.5', 'category': 'VOLUME'},
                    {'volume': '1', 'category': 'VOLUME'}
                ]
            else:
                self.stdout.write(self.style.WARNING(f'No variants created for {product.name}. Unrecognized category.'))
                continue
            
            for variant_data in variants:
                # Pricing strategy
                base_price = product.base_price
                variant_price = self.calculate_variant_price(base_price, variant_data)
                
                Variant.objects.create(
                    product=product,
                    category=variant_data['category'],
                    weight=variant_data.get('weight'),
                    volume=variant_data.get('volume'),
                    variant_price=variant_price,
                    stock_quantity=product.stock_quantity,
                    sku=self.generate_sku(product, variant_data),
                    is_active=True
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created variants for {product.name}'))

    def calculate_variant_price(self, base_price, variant_data):
        """
        Custom pricing strategy for variants
        You can modify this logic based on your business rules
        """
        if variant_data.get('weight') == '2':
            # 10% increase for 2kg variant
            return base_price * Decimal('1.1')
        elif variant_data.get('volume') == '1':
            # 5% increase for 1 liter variant
            return base_price * Decimal('1.05')
        return base_price

    def generate_sku(self, product, variant_data):
        """
        Generate unique SKU for each variant
        """
        variant_identifier = variant_data.get('weight') or variant_data.get('volume')
        return f"{product.id}-{variant_identifier}"