from datetime import datetime, timezone

from venv import logger
from django.shortcuts import render
from django.shortcuts import render, redirect ,get_object_or_404
from django.contrib.auth import authenticate, login ,logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from user.models import CustomUser, Address , OrderItem ,Order,OrderReturn,Refund
from .models import Catogery, ProductImage, Product , CouponTable,CouponUsage, Offer
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .forms import CategoryForm, ProductForm
from django.core.exceptions import ValidationError
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .decorators import admin_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Product, ProductImage, Catogery ,Variant
from .forms import ProductForm  # Assuming you have a form for product
from django.utils.timezone import now
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Q
from user.models import Order,Wallet, WalletTransaction,OrderReturn

from django.db.models import Prefetch, Exists, OuterRef, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# from .decorators import user_required

# Create your views here.


def admin_login(request):
    return render(request, 'admin_login.html')


###########################################################################################################

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin1')
        else:
            messages.error(request, 'Invalid credentials or not an admin user.')


    return render(request , 'admin_login.html')


##########################################################################################################

# @never_cache
# @login_required(login_url='admin_login')
# def admin_dashboard(request):
#     response = render(request, 'index.html')
#     response['Cache-Control'] = 'no-store , no-cache, must-revalidate, max-age=0'
#     response['Pragma'] = 'no-cache'
#     response['Expires'] = '0'
#     return response

from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDay, TruncMonth
from collections import Counter, defaultdict


@never_cache
@login_required(login_url='admin_login')
def admin_dashboard(request):
    # Get all orders
    order_data = Order.objects.all()
    
    # Get active users count
    active_users_count = CustomUser.objects.filter(is_deleted=False).count()
    
    # Calculate current time periods
    current_date = timezone.now()
    current_year = current_date.year
    current_month = current_date.month

    # Calculate total revenue and total discount
    total_revenue = order_data.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    total_discount = OrderItem.objects.annotate(
        discount=ExpressionWrapper(
            F('product__base_price') - F('price_per_unit'),
            output_field=DecimalField()
        )
    ).aggregate(total_discount=Sum(F('discount') * F('quantity')))['total_discount'] or 0

    # Previous month revenue calculation
    previous_month_end = current_date.replace(day=1) - timedelta(days=1)
    previous_month_start = previous_month_end.replace(day=1)
    previous_month_revenue = order_data.filter(
        order_date__gte=previous_month_start,
        order_date__lte=previous_month_end
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    # calculate revenue 
    percentage_change = 0
    if previous_month_revenue > 0:
        percentage_change = ((total_revenue - previous_month_revenue) / previous_month_revenue) * 100

    # daily revenue data
    daily_data = order_data.annotate(
        day=TruncDay('order_date')
    ).values('day').annotate(
        total_amount_sum=Sum('total_amount')
    ).order_by('day')

    # monthly revenue data
    monthly_data = order_data.annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        total_amount_sum=Sum('total_amount')
    ).order_by('month')


    yearly_data = order_data.annotate(
        year=TruncYear('order_date')
    ).values('year').annotate(
        total_amount_sum=Sum('total_amount')
    ).order_by('year')

    # Product and Category Analysis
    product_sales = Counter()
    category_sales = Counter()
    for order in order_data:
        for item in order.order_items.all():
            product_sales[item.product.name] += item.quantity
            category_sales[item.product.catogery.name] += item.quantity

    top_products = product_sales.most_common(3)
    top_categories = category_sales.most_common(3)

    # Payment method analysis
    payment_methods = defaultdict(int)
    for order in order_data:
        payment_methods[order.payment_method] += 1

    payment_method_data = [
        {"label": "Online", "count": payment_methods.get("ONLINE", 0)},
        {"label": "COD", "count": payment_methods.get("COD", 0)},
        {"label": "Wallet", "count": payment_methods.get("WALLET", 0)},
    ]

    # Order status analysis
    cancelled_count = order_data.filter(order_status='cancelled').count()
    delivered_count = order_data.filter(order_status='delivered').count()
    total_orders = order_data.count()

    cancellation_rate = (cancelled_count / total_orders * 100) if total_orders > 0 else 0

    context = {
        'order_data': order_data,
        'total_revenue': total_revenue,
        'total_discount': total_discount,
        'percentage_change': round(percentage_change, 2),
        'active_users_count': active_users_count,
        
        # Time series data
        'daily_data': json.dumps([{
            'date': entry['day'].strftime('%d %b'),
            'amount': float(entry['total_amount_sum'])
        } for entry in daily_data if entry['day'].month == current_month]),
        
        'monthly_data': json.dumps([{
            'month': entry['month'].strftime('%B %Y'),
            'amount': float(entry['total_amount_sum'])
        } for entry in monthly_data]),


        'yearly_data': json.dumps([{
            'year': entry['year'].strftime('%Y'),
            'amount': float(entry['total_amount_sum'])
        } for entry in yearly_data]),

        # Product and category analysis
        'top_products': json.dumps(top_products),
        'top_categories': json.dumps(top_categories),
        'products': top_products,
        'categories': top_categories,

        # Payment and order status
        'payment_method_data': json.dumps(payment_method_data),
        'cancelled_count': cancelled_count,
        'delivered_count': delivered_count,
        'total_orders': total_orders,
        'cancellation_rate': round(cancellation_rate, 2),
    }

    response = render(request, 'index.html', context)
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

##########################################################################################
# @login_required(login_url='admin_login')

def admin_logout(request):
    logout(request)
    return redirect('admin_login')

##################################################################################################################################

def base(request):
    return render(request,'admin_base.html')

########## FOR FETCHING DATA ########################################################################################################################




########## FOR FETCHING DATA & FOR PAGINATOR ########################################################################################################################

@admin_required
def admin_user(request):
    user_list = CustomUser.objects.all() 

    paginator = Paginator(user_list,10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'admin_user.html', {'page_obj': page_obj})


########## blocking and unblocking user ########################################################################################################################
@admin_required
@require_POST
def toggle_user_status(request, user_id):
    try:
        # Add authentication check

        if not request.user.is_superuser:
            messages.error(request, "You don't have permission to perform this action.")
            return redirect('admin_user')
            
        user = CustomUser.objects.get(user_id=user_id)
        # Prevent blocking yourself
        if user.user_id == request.user.user_id:
            messages.error(request, "You cannot block your own account.")
            return redirect('admin_user')
            
        user.is_active = not user.is_active
        user.save()
        
        status = "unblocked" if user.is_active else "blocked"
        messages.success(request, f"User has been {status} successfully.")
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
    
    return redirect('admin_user')


#############       admin-category             #####################################################################################################################

@admin_required
def admin_category(request):

    categories = Catogery.objects.all() 

    return render(request,'admin_category.html' , {'categories': categories})



#############       admin-add-category             #####################################################################################################################

@admin_required
def add_category(request):
    return render(request,'admin_addcategory.html')



#############       admin-add-submit-category             #####################################################################################################################

@admin_required
def add_submit_category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_category')  
    else:
        form = CategoryForm()
    return render(request, "admin_addcategory.html", {"form": form})


#############    block unblock category      #####################################################################################################################

@admin_required
def toggle_category_status(request, category_id):
    if request.method == "POST":

        #fetch category id 

        category = get_object_or_404(Catogery, id=category_id)

        if category.status == 'Available':
            category.status = 'Not Available'

        else:
            category.status = 'Available'    


        category.save()
        messages.success(request, f"Category '{category.name}' status updated to {category.status}.")
    
    return redirect('admin_category')


#############    edit category   #####################################################################################################################

@admin_required
def edit_category(request, category_id):
    category = get_object_or_404(Catogery,id=category_id)


    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.save()

        return redirect('admin_category')

    return render(request, 'admin_editcategory.html', {'category': category})


#############    product   #####################################################################################################################
@admin_required
def admin_product(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                product.is_delete = not product.is_delete  # Toggle the status
                product.save()
                
                status = "inactive" if product.is_delete else "active"
                messages.success(request, f'Product has been marked as {status}')
            except Product.DoesNotExist:
                messages.error(request, 'Product not found')
        
    #product acc to date of creation
    products = Product.objects.all().order_by('-created_at')

    #page no.
    page_number = request.GET.get('page', 1)

    #number of items per page
    items_per_page = 15

    #object of paginator
    paginator = Paginator(products, items_per_page)

    #for getting page
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_products': products.count(),
    }
    return render(request, 'admin_product.html', context)



#############   add product   #####################################################################################################################

# @admin_required
# @csrf_exempt  # remove in production  
# @require_http_methods(["GET", "POST"])
# def add_product(request):
#     if request.method == 'GET':
#         categories = Catogery.objects.all()
#         return render(request, 'admin_addproduct.html', {'categories': categories})
    
#     elif request.method == 'POST':
#         try:
#             #debugging 
#             print("Request POST data:", request.POST)
#             print("Request FILES:", request.FILES)
            
#             #get from data
#             name = request.POST.get('name')
#             base_price = request.POST.get('base_price')  
#             stock_quantity = request.POST.get('stock_quantity')
#             category_id = request.POST.get('category')

#             #validate data
#             if not all([name, base_price, stock_quantity, category_id]):  # Updated 'price' to 'base_price'
#                 missing_fields = []
#                 if not name: missing_fields.append('name')
#                 if not base_price: missing_fields.append('base_price')  # Updated field name
#                 if not stock_quantity: missing_fields.append('stock_quantity')
#                 if not category_id: missing_fields.append('category')
                
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Missing required fields: {", ".join(missing_fields)}'
#                 }, status=400)

#             #validate daata
#             images = []
#             for i in range(3):
#                 if f'image_{i}' in request.FILES:
#                     images.append(request.FILES[f'image_{i}'])

#             if not images:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'At least one image is required'
#                 }, status=400)

#             try:
#                 #fetch category instance
#                 category = Catogery.objects.get(id=int(category_id))

#                 #create productt
#                 product = Product.objects.create(
#                     name=name,
#                     base_price=float(base_price),  
#                     stock_quantity=int(stock_quantity),
#                     catogery=category 
#                 )

#                 #save image 
#                 for image in images:
#                     ProductImage.objects.create(
#                         product=product,
#                         images=image
#                     )

#                 return JsonResponse({
#                     'success': True,
#                     'message': 'Product added successfully',
#                     'product_id': product.id
#                 })

#             except ValueError as ve:
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Invalid data format: {str(ve)}'
#                 }, status=400)

#             except Catogery.DoesNotExist:
#                 return JsonResponse({
#                     'success': False,
#                     'message': 'Invalid category ID'
#                 }, status=400)

#             except Exception as e:
#                 print(f"Error creating product: {str(e)}")
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Error creating product: {str(e)}'
#                 }, status=500)

#         except Exception as e:
#             print(f"Unexpected error: {str(e)}")
#             return JsonResponse({
#                 'success': False,
#                 'message': f'Server error: {str(e)}'
#             }, status=500)



# ------------------above is working code ---------------------

# -------------after adding the varients-----------------------

@admin_required
@csrf_exempt  
@require_http_methods(["GET", "POST"])
def add_product(request):
    if request.method == 'GET':
        categories = Catogery.objects.all()
        return render(request, 'admin_addproduct.html', {'categories': categories})
    
    elif request.method == 'POST':
        try:
            # Get basic product data
            name = request.POST.get('name')
            base_price = request.POST.get('base_price')
            stock_quantity = request.POST.get('stock_quantity')
            category_id = request.POST.get('category')
            
            # Get variant prices
            variant_prices = {
                '1': request.POST.get('variant_1kg_price'),
                '1.5': request.POST.get('variant_1_5kg_price'),
                '2': request.POST.get('variant_2kg_price')
            }

            # Validate basic fields
            if not all([name, base_price, stock_quantity, category_id]):
                missing_fields = []
                if not name: missing_fields.append('name')
                if not base_price: missing_fields.append('base_price')
                if not stock_quantity: missing_fields.append('stock_quantity')
                if not category_id: missing_fields.append('category')
                
                return JsonResponse({
                    'success': False,
                    'message': f'Missing required fields: {", ".join(missing_fields)}'
                }, status=400)

            # Process images
            images = []
            for i in range(3):
                if f'image_{i}' in request.FILES:
                    images.append(request.FILES[f'image_{i}'])

            if not images:
                return JsonResponse({
                    'success': False,
                    'message': 'At least one image is required'
                }, status=400)

            try:
                with transaction.atomic():
                    # Create product with Decimal price
                    category = Catogery.objects.get(id=int(category_id))
                    product = Product.objects.create(
                        name=name,
                        base_price=Decimal(base_price),
                        stock_quantity=int(stock_quantity),
                        catogery=category
                    )

                    # Save images
                    for image in images:
                        ProductImage.objects.create(
                            product=product,
                            images=image
                        )


                     #    Save images and set the first one as primary
                    for index, image in enumerate(images):
                        ProductImage.objects.create(
                            product=product,
                            images=image,
                            is_primary=(index == 0)  # Set first image as primary
                        )


                    # Create base variant (0.5 kg)
                    Variant.objects.create(
                        product=product,
                        category='WEIGHT',
                        weight='0.5',
                        variant_price=Decimal(base_price),
                        stock_quantity=int(stock_quantity)
                    )

                    # Create other variants using the same stock quantity
                    for weight, price in variant_prices.items():
                        if price:  # Only create variant if price is provided
                            Variant.objects.create(
                                product=product,
                                category='WEIGHT',
                                weight=weight,
                                variant_price=Decimal(price),
                                stock_quantity=int(stock_quantity)
                            )

                    return JsonResponse({
                        'success': True,
                        'message': 'Product and variants added successfully',
                        'product_id': product.id
                    })

            except ValueError as ve:
                return JsonResponse({
                    'success': False,
                    'message': f'Invalid data format: {str(ve)}'
                }, status=400)

            except Catogery.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid category ID'
                }, status=400)

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Server error: {str(e)}'
            }, status=500)



# -----------------EDIT PRODUCT -------------------------------------------------------------------------------------------------------------



@admin_required
def edit_product(request, pk):

    #fetch the product to be edited..

    product = get_object_or_404(Product, id=pk)
    
    
    #get the existing imagess
    existing_images = product.images.all()

    if request.method == 'POST':
        

        name = request.POST.get('name', None)
        base_price = request.POST.get('base_price', None)
        stock_quantity = request.POST.get('stock_quantity', None)
        category = request.POST.get('category', None)
        discount_percentage = request.POST.get('discount_percentage', None) # add discoun
        images = request.FILES.getlist('images') 
        
        #updating the needed fields..

        if name:
            product.name = name
        if base_price:
            product.base_price = base_price
        if stock_quantity:
            product.stock_quantity = stock_quantity
        if category:
            product.catogery = Catogery.objects.get(id = category) #by id
        if discount_percentage: 
            product.discount_percentage = discount_percentage



        product.save()

        #new image are uploaded then remove old one and mark 1st image main primaryyy

        if images:  
            product.images.all().delete()  
            for i, image in enumerate(images):
                is_primary = i == 0  
                ProductImage.objects.create(product=product, images=image, is_primary=is_primary)


        else:
            for i, image_obj in enumerate(existing_images):
                image_obj.is_primary = i ==0
                image_obj.save()

        return redirect('admin_product') 


    
    categories = Catogery.objects.all()

    context = {
        'product': product,
        'categories': categories,
        'existing_images': existing_images,
    }
    return render(request, 'admin_editproduct.html', context)

#------------admin order  workingg admin order-------------------------------------------------------------------------------------------





# -----------------old working above . below new new try for return request-------------------------------------------------




@admin_required
def admin_order(request):
    # Annotate orders with the return request status dynamically
    orders_queryset = Order.objects.select_related('user').annotate(
        has_return_request=Exists(
            OrderReturn.objects.filter(
                order_item__order=OuterRef('pk'),
                status='REQUESTED'
            )
        ),
        is_returning=Exists(
            OrderReturn.objects.filter(
                order_item__order=OuterRef('pk'),
                status='APPROVED'
            )
        )
    )

    # Filtering logic
    status = request.GET.get('status')
    payment_method = request.GET.get('payment_method')
    search_query = request.GET.get('search')

    if status and status != 'all':
        orders_queryset = orders_queryset.filter(order_status=status)

    if payment_method and payment_method != 'all':
        orders_queryset = orders_queryset.filter(payment_method=payment_method)

    if search_query:
        orders_queryset = orders_queryset.filter(
            Q(id__icontains=search_query) | 
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    # Pagination logic
    entries_per_page = request.GET.get('entries', 15)
    try:
        entries_per_page = int(entries_per_page)
    except (ValueError, TypeError):
        entries_per_page = 15

    paginator = Paginator(orders_queryset, entries_per_page)
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,
        'total_orders': orders_queryset.count(),
        'status_choices': Order.ORDER_STATUS_CHOICES,
        'payment_method_choices': Order.PAYMENT_METHOD_CHOICES,
        'current_status': status,
        'current_payment_method': payment_method,
        'current_search': search_query,
        'current_entries': entries_per_page,
        # Annotated fields added to context for display in templates
        'has_return_request': True,  # Used to signify the existence of a requested return
        'is_returning': True  # Used to signify the existence of an approved return
    }

    return render(request, 'admin_orderdetails.html', context)

# -------------------------testing for above ----------------------------------------------------------------


@admin_required
def admin_orderdetails(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    user = order.user  
    address = Address.objects.filter(user=user, is_default=True).first()  
    order_items = order.order_items.all()  

    for item in order_items:
        

        
        # Check if variants exist for this product
        product_variants = item.product.variants.all()
        print(f"Product Variants: {list(product_variants)}")

        item.primary_image = (
            item.product.images.filter(is_primary=True).first()
        )

        # Attempt to assign variant if not already assigned
        if not item.variant and product_variants.exists():
            # Assign the first variant if available
            item.variant = product_variants.first()
            item.save()

        item.variant_display = ''
        if item.variant:
            # Your existing variant display logic
            if item.product.catogery.name in ['Vegetables', 'fruits', 'dried']:
                item.variant_display = f"{item.variant.weight} kg"
            elif item.product.catogery.name == 'juice':
                item.variant_display = f"{item.variant.volume} liter"
            else:
                item.variant_display = str(item.variant.weight) if item.variant.weight else ''
    


    subtotal = sum(item.product.base_price * item.quantity for item in order_items)
    
    shipping = 0
    total_discount = sum(
        ((item.product.base_price * item.product.discount_percentage / 100) if item.product.discount_percentage else 0) * item.quantity
        for item in order_items
    )
    total_amount = subtotal + shipping - total_discount

    
    context = {
        'order': order,
        'user': user,
        'address': address,
        'order_items': order_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total_discount': total_discount,
        'total_amount': total_amount,
    }
    return render(request, 'order_details.html', context)


# ---------------------------------------------------------------------------------------------------------------------------------

@admin_required
def admin_edit_order(request, order_id):
    
    order = get_object_or_404(Order, id=order_id)
    user = order.user  
    address = Address.objects.filter(user=user, is_default=True).first()  
    order_items = order.order_items.all()  

    
    for item in order_items:
        item.primary_image = (
            item.product.images.filter(is_primary=True).first()  
        )

    
    subtotal = sum(item.product.base_price * item.quantity for item in order_items)
    
    shipping = 0  
    total_discount = sum(
        ((item.product.base_price * item.product.discount_percentage / 100) if item.product.discount_percentage else 0) * item.quantity
        for item in order_items
    )
    total_amount = subtotal + shipping - total_discount


    for item in order_items:
        product = item.product
        stock_quantity = product.stock_quantity - item.quantity  
        item.available_stock = stock_quantity  

    
    context = {
        'order': order,
        'user': user,
        'address': address,
        'order_items': order_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'total_discount': total_discount,
        'total_amount': total_amount,
    }

    return render(request, 'admin_edit_order.html', context)

# ----------------------------------------------------------------------------


from django.http import JsonResponse
from django.shortcuts import get_object_or_404

import json

@csrf_exempt
# @admin_required
def update_order_status(request, order_id):
    try:
        
        data = json.loads(request.body)
        new_status = data.get('status')

        
        if not request.user.is_staff:
            return JsonResponse({
                'success': False, 
                'message': 'Unauthorized access'
            }, status=403)

        
        order = get_object_or_404(Order, id=order_id)

        
        valid_statuses = [status[0] for status in Order.ORDER_STATUS_CHOICES]
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid status value'
            }, status=400)

       
        order.order_status = new_status
        order.save()

        return JsonResponse({
            'success': True, 
            'message': f'Order status updated to {new_status} successfully!'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': str(e)
        }, status=500)

# ------------------------------
from django.utils import timezone

@csrf_exempt
# @admin_required
def admin_cancel_order(request, order_id):
    
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        
        order.order_status = 'Cancelled'  
        order.is_canceled = True  
        order.cancel_date = timezone.now()  
        order.save()

        
        return redirect('admin_edit_order', order_id=order.id)

    return render(request, 'admin_cancel.html', {'order': order})




import logging




def create_coupon(request):
    logger.info(f"Request method: {request.method}")
    logger.info(f"Received POST data: {request.POST}")
    if request.method == 'POST':
        logger.info("Coupon creation request received")
        coupon_code = request.POST.get('couponCode')
        discount_type = request.POST.get('discountType')
        discount_value = request.POST.get('discountValue')
        min_purchase_amount = request.POST.get('minPurchaseAmount')
        valid_from = request.POST.get('validFrom')
        valid_to = request.POST.get('validUntil')
        max_uses = request.POST.get('maxUses')
        is_active = bool(request.POST.get('isActive'))

        coupon = CouponTable.objects.create(
            code=coupon_code,
            coupon_type=discount_type,
            discount_value=discount_value,
            min_purchase_amount=min_purchase_amount,
            valid_from=valid_from,
            valid_to=valid_to,
            max_uses=max_uses,
            is_active=is_active
        )
        coupon.save()

        # Return a JSON response with a success message
        return JsonResponse({'success': 'Coupon created successfully.'})

    # Render the coupon management template
    return render(request, 'admin_add_coupons.html')


# -----------------------------------------------------------------------------------------------------------------------------------
from django.db.models import Count, F
from django.db.models import Count

# added here

@admin_required
def coupons(request):
    # Calculate uses left in the view
    coupons = CouponTable.objects.annotate(
        uses_count=Count('couponusage'),
        uses_left=F('max_uses') - Count('couponusage')
    )

    context = {
        'coupons': coupons,
    }
    return render(request, 'admin_coupons_list.html', context)

# -----------------------------------------------------------------------------------------------------------------------

@admin_required
def edit_coupon(request, coupon_id):
    try:
        coupon = CouponTable.objects.annotate(
            uses_left=F('max_uses') - Count('couponusage')
        ).get(id=coupon_id)
        
        context = {
            'coupon': coupon,
        }
        return render(request, 'admin_coupon_edit.html', context)
    
    except CouponTable.DoesNotExist:
        # Handle case where coupon is not found
        messages.error(request, 'Coupon not found.')
        return redirect('coupon_list')

# --------------------------------------------------------------------------




from django.views.decorators.csrf import csrf_protect

import logging
import json
from datetime import datetime
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db import transaction

# Configure logging
logger = logging.getLogger(__name__)

@csrf_protect
@require_POST
@admin_required
def update_coupon(request):
    try:
        # Parse the JSON data from the request
        data = json.loads(request.body)
        
        # Validate input
        if not data.get('id'):
            return JsonResponse({
                'status': 'error',
                'message': 'Coupon ID is required'
            }, status=400)
        
        # Retrieve the coupon by ID
        coupon = CouponTable.objects.get(id=data['id'])
        
        # Use a transaction to ensure atomic updates
        with transaction.atomic():
            # Update fields with validation
            coupon.code = data.get('code', coupon.code)
            coupon.coupon_type = data.get('couponType', coupon.coupon_type)  # Updated field name
            
            # Discount Value
            if data.get('discountValue'):
                try:
                    coupon.discount_value = float(data['discountValue'])
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid discount value'
                    }, status=400)
            
            # Valid Until Date
            if data.get('validUntil'):
                try:
                    coupon.valid_to = datetime.strptime(data['validUntil'], '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid date format'
                    }, status=400)
            
            # Uses Left
            if data.get('usesLeft') is not None:
                try:
                    # Ensure uses_left doesn't exceed max_uses
                    uses_left = int(data['usesLeft'])
                    if uses_left < 0:
                        return JsonResponse({
                            'status': 'error',
                            'message': 'Uses left cannot be negative'
                        }, status=400)
                    coupon.max_uses = uses_left  # Assuming max_uses is the intended field
                except ValueError:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Invalid uses left value'
                    }, status=400)
            
            # Active Status
            if data.get('isActive') is not None:
                coupon.is_active = data['isActive']
            
            # Validate the entire model
            try:
                coupon.full_clean()
            except ValidationError as ve:
                return JsonResponse({
                    'status': 'error',
                    'message': str(ve)
                }, status=400)
            
            # Save the updated coupon
            coupon.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Coupon updated successfully'
        })
    
    except CouponTable.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Coupon not found'
        }, status=404)
    
    except Exception as e:
        # Log the full error for server-side debugging
        logger.error(f"Unexpected error in update_coupon: {str(e)}", exc_info=True)
        
        return JsonResponse({
            'status': 'error',
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)



# ---------------------------------------------------------------------------------
# added here
@admin_required
@csrf_exempt
def delete_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            coupon_id = data.get('id')

            if not coupon_id:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Coupon ID is required'
                }, status=400)

            # Delete the coupon
            coupon = CouponTable.objects.get(id=coupon_id)
            coupon.delete()

            return JsonResponse({
                'status': 'success',
                'message': 'Coupon deleted successfully'
            })

        except CouponTable.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Coupon not found'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'An unexpected error occurred: {str(e)}'
            }, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)



# ----------------





# added here

@admin_required
def admin_return_requests(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        return_requests = OrderReturn.objects.filter(
            order_item__order=order, 
            status='REQUESTED'
        )

        context = {
            'order': order,
            'return_requests': return_requests
        }

        return render(request, 'return_request_details.html', context)
    except Order.DoesNotExist:
        # Handle case where order doesn't exist
        messages.error(request, "Order not found")
        return redirect('admin_order')



# added here 

from decimal import Decimal
@admin_required
@transaction.atomic
def process_return_request(request, return_request_id):
    # Ensure only admin can access this view
    if not request.user.is_staff:
        messages.error(request, "Unauthorized access")
        return redirect('admin_login')
    
    if request.method == 'POST':
        try:
            return_request = OrderReturn.objects.get(id=return_request_id)
            action = request.POST.get('action')

            if action == 'approve':
                # Approve the return request
                return_request.status = 'APPROVED' 
                
                # Ensure order item and product exist
                if not return_request.order_item or not return_request.order_item.product:
                    messages.error(request, "Invalid order item or product.")
                    return redirect('admin_order')

                # Get or create user's wallet
                wallet, created = Wallet.objects.get_or_create(
                    user=return_request.order_item.order.user
                )
                
                # Calculate refund amount 
                refund_amount = return_request.refund_amount
                
                # Validate refund amount
                if refund_amount <= 0:
                    messages.error(request, "Invalid refund amount.")
                    return redirect('admin_order')

                # Create Refund record
                # This will now create a new Refund for each return
                refund = Refund.objects.create(
                    order_return=return_request,
                    refund_amount=refund_amount,
                    refund_method='WALLET',
                    refund_status='PROCESSED'
                )
                
                # Update wallet balance
                wallet.balance = (wallet.balance or Decimal('0.00')) + refund_amount
                wallet.save()
                
                # Create wallet transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='REFUND',
                    amount=refund_amount
                )
                
                # Process return
                return_request.save()
            
            elif action == 'reject':
                return_request.status = 'REJECTED'
            
            return_request.save()

            # Print debug information
            print(f"Return request {return_request_id} processed. Redirecting...")
            
            # Add success message with specific action
            messages.success(request, f"Return request {action}d successfully.")
            
            return redirect('admin_order')
        
        except OrderReturn.DoesNotExist:
            messages.error(request, "Return request not found.")
            return redirect('admin_order')
        
        except Exception as e:
            # More comprehensive error handling
            import traceback
            print(traceback.format_exc())
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('admin_order')
    
    return redirect('admin_order')



# -----------------------------------------------------------------------------------------------------------
# added here 

logger = logging.getLogger(__name__)

@admin_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def offer(request):
    # Move this line before the GET request handling
    all_offers = Offer.objects.all()

    if request.method == 'POST':
        try:
            # Existing POST method logic remains the same
            offer_name = request.POST.get('offer_name')
            description = request.POST.get('description')
            discount_percentage = request.POST.get('discount_percentage')
            offer_type = request.POST.get('offer_type')
            product_selection = request.POST.get('product_selection')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_active = request.POST.get('is_active') == 'on'

            # Create new Offer instance
            new_offer = Offer.objects.create(
                offer_name=offer_name,
                description=description,
                discount_percentage=float(discount_percentage),
                offer_type=offer_type,
                start_date=start_date,
                end_date=end_date,
                is_active=is_active
            )

            # Return JSON response for AJAX
            return JsonResponse({
                'status': 'success', 
                'message': f'Offer {offer_name} is created'
            })
        
        except Exception as e:
            print(f"Error creating offer: {str(e)}")
            
            return JsonResponse({
                'status': 'error', 
                'message': f'Error creating offer: {str(e)}'
            }, status=400)
    
    # Render the page for GET requests
    return render(request, 'admin_offer.html', {'all_offers': all_offers})




# ------------------------------


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404


# ----------------------------------




from django.shortcuts import render
from django.db.models import Sum, Count, Value, FloatField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear, Cast
from django.http import JsonResponse, HttpResponse
# from .models import Order, OrderItem, CouponUsage
from decimal import Decimal
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Sum, Count, F, DecimalField

from django.db.models import OuterRef, Subquery, Value
from decimal import Decimal
from datetime import datetime


# added here

@admin_required
def report(request):
    return render(request, 'admin_sales_report.html')





import io
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd




# ----------new both test set -----------------------------------------------

from django.db.models import (
    F, Sum, Count, Value, Q, 
    FloatField, IntegerField, 
    Case, When
)
from django.db.models.functions import (
    Cast, 
    TruncDate, TruncWeek, TruncMonth, TruncYear
)

from django.core.serializers.json import DjangoJSONEncoder
import json

def generate_sales_report(request):
    try:
        # Get filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        report_type = request.GET.get('report_type', 'daily')

        # Validate input
        if not (start_date and end_date):
            return JsonResponse({
                'error': 'Start and end dates are required'
            }, status=400)

        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Base queryset - filter successful orders
        orders = Order.objects.filter(payment_status='success')
        orders = orders.filter(order_date__range=[start_date, end_date])

        # Dynamically group by period based on report type
        if report_type == 'daily':
            grouping = TruncDate('order_date')
        elif report_type == 'weekly':
            grouping = TruncWeek('order_date')
        elif report_type == 'monthly':
            grouping = TruncMonth('order_date')
        else:  # yearly
            grouping = TruncYear('order_date')

        # Detailed sales aggregation
        sales_data = orders.annotate(
            period=grouping
        ).annotate(
            total_orders=Count('id'),
            total_revenue=Cast(Sum('total_amount'), FloatField()),
            total_items_sold=Cast(Sum('order_items__quantity'), IntegerField()),
            total_base_price=Cast(Sum(
                F('order_items__quantity') * 
                Case(
                    When(order_items__variant__isnull=False, 
                         then=F('order_items__variant__variant_price')),
                    default=F('order_items__product__base_price')
                )
            ), FloatField()),
            total_returns=Cast(
                Count('order_items__return_request', 
                      filter=Q(order_items__return_request__status='APPROVED')), 
                IntegerField()
            ),
            total_return_amount=Cast(
                Sum(
                    F('order_items__return_request__refunds__refund_amount'),
                    filter=Q(order_items__return_request__status='APPROVED')
                ), 
                FloatField()
            )
        ).order_by('period').values(
            'period', 'total_orders', 'total_revenue', 
            'total_items_sold', 'total_base_price', 
            'total_returns', 'total_return_amount'
        )

        # Convert period to string for JSON serialization
        sales_data = [
            {**item, 'period': item['period'].strftime('%Y-%m-%d') if item['period'] else None}
            for item in sales_data
        ]

        # Overall summary
        overall_summary = {
            'total_orders': orders.count(),
            'total_revenue': float(orders.aggregate(total=Sum('total_amount'))['total'] or 0.00),
            'total_items_sold': int(orders.aggregate(
                total_items=Sum('order_items__quantity')
            )['total_items'] or 0),
            'total_base_price': float(orders.aggregate(
                base_total=Sum(
                    F('order_items__quantity') * 
                    Case(
                        When(order_items__variant__isnull=False, 
                             then=F('order_items__variant__variant_price')),
                        default=F('order_items__product__base_price')
                    )
                )
            )['base_total'] or 0.00),
            'total_returns': int(orders.filter(
                order_items__return_request__status='APPROVED'
            ).count()),
            'total_return_amount': float(
                Refund.objects.filter(
                    order_return__order_item__order__in=orders,
                    order_return__status='APPROVED'
                ).aggregate(
                    return_total=Sum('refund_amount')
                )['return_total'] or 0.00
            ),
        }

        # Prepare response data
        data = {
            'sales_data': sales_data,
            'overall_summary': overall_summary
        }

        return JsonResponse(data, safe=True)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e)
        }, status=500)
    




from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, F, Q, Case, When, FloatField, IntegerField
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear, Cast
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import io
# added here
@admin_required
def download_sales_report(request):
    try:
        # Get filter parameters
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        report_type = request.GET.get('report_type', 'daily')
        file_format = request.GET.get('format', 'excel')

        # Validate input
        if not (start_date and end_date):
            return JsonResponse({
                'error': 'Start and end dates are required'
            }, status=400)

        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Base queryset - filter successful orders
        orders = Order.objects.filter(payment_status='success')
        orders = orders.filter(order_date__range=[start_date, end_date])

        # Dynamically group by period based on report type
        if report_type == 'daily':
            grouping = TruncDate('order_date')
        elif report_type == 'weekly':
            grouping = TruncWeek('order_date')
        elif report_type == 'monthly':
            grouping = TruncMonth('order_date')
        else:  # yearly
            grouping = TruncYear('order_date')

        # Detailed sales aggregation
        sales_data = orders.annotate(
            period=grouping
        ).annotate(
            total_orders=Count('id'),
            total_revenue=Cast(Sum('total_amount'), FloatField()),
            total_items_sold=Cast(Sum('order_items__quantity'), IntegerField()),
            total_base_price=Cast(Sum(
                F('order_items__quantity') * 
                Case(
                    When(order_items__variant__isnull=False, 
                         then=F('order_items__variant__variant_price')),
                    default=F('order_items__product__base_price')
                )
            ), FloatField()),
            total_returns=Cast(
                Count('order_items__return_request', 
                      filter=Q(order_items__return_request__status='APPROVED')), 
                IntegerField()
            ),
            total_return_amount=Cast(
                Sum(
                    F('order_items__return_request__refunds__refund_amount'),
                    filter=Q(order_items__return_request__status='APPROVED')
                ), 
                FloatField()
            )
        ).order_by('period')

        # Convert to list for DataFrame
        sales_list = [
            {
                'period': item.period.strftime('%Y-%m-%d') if item.period else None,
                'total_orders': item.total_orders,
                'total_revenue': item.total_revenue,
                'total_items_sold': item.total_items_sold,
                'total_base_price': item.total_base_price,
                'total_returns': item.total_returns,
                'total_return_amount': item.total_return_amount,
            }
            for item in sales_data
        ]

        # Create DataFrame
        df = pd.DataFrame(sales_list)

        # Rename columns for clarity
        df.columns = [
            'Period',
            'Total Orders',
            'Total Revenue',
            'Total Items Sold',
            'Total Base Price',
            'Total Returns',
            'Total Return Amount'
        ]

        # Format currency values
        currency_columns = ['Total Revenue', 'Total Base Price', 'Total Return Amount']
        for col in currency_columns:
            df[col] = df[col].apply(lambda x: f'₹{x:,.2f}' if pd.notnull(x) else '₹0.00')

        if file_format == 'excel':
            # Excel export
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = (
                f'attachment; filename=sales_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
            )
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Write main data
                df.to_excel(writer, index=False, sheet_name='Sales Report')
                
                # Get the worksheet
                worksheet = writer.sheets['Sales Report']
                
                # Adjust column widths
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2

            response.write(buffer.getvalue())
            return response
            
        else:  # PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename=sales_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )

            # Create PDF using matplotlib
            plt.figure(figsize=(12, len(df) * 0.5 + 2))  # Adjust figure size based on data
            plt.axis('tight')
            plt.axis('off')
            
            # Create table
            table = plt.table(
                cellText=df.values,
                colLabels=df.columns,
                loc='center',
                cellLoc='center',
                colColours=['#f2f2f2'] * len(df.columns)
            )
            
            # Adjust table style
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.2, 1.5)  # Adjust cell size
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='pdf', bbox_inches='tight', dpi=300)
            buffer.seek(0)
            
            response.write(buffer.getvalue())
            return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'error': str(e)
        }, status=500)
# ----------------------------------------
# added here
@admin_required
def add_product_offer(request, product_id):
    # Get the specific product
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Extract form data
            offer_name = request.POST.get('offer_name')
            description = request.POST.get('description')
            discount_percentage = request.POST.get('discount_percentage')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            is_active = request.POST.get('is_active') == 'on'

            # Validate required fields
            if not offer_name:
                messages.error(request, 'Offer name is required.')
                return render(request, 'add_product_offer.html', {'product': product})

            # Convert and validate discount percentage
            try:
                discount_percentage = float(discount_percentage)
                if discount_percentage < 0 or discount_percentage > 100:
                    raise ValueError("Discount must be between 0 and 100")
            except ValueError:
                messages.error(request, 'Invalid discount percentage. Please enter a number between 0 and 100.')
                return render(request, 'add_product_offer.html', {'product': product})

            # Validate dates
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, 'Invalid date format. Please use YYYY-MM-DD format.')
                return render(request, 'add_product_offer.html', {'product': product})

            # Additional date validations
            today = timezone.now().date()
            if start_date < today:
                messages.error(request, 'Start date cannot be in the past.')
                return render(request, 'add_product_offer.html', {'product': product})

            if end_date < start_date:
                messages.error(request, 'End date must be after start date.')
                return render(request, 'add_product_offer.html', {'product': product})

            # Check for existing offer for this product
            existing_offer = Offer.objects.filter(product=product).first()

            if existing_offer:
                # Update existing offer
                existing_offer.offer_name = offer_name
                existing_offer.description = description
                existing_offer.discount_percentage = discount_percentage
                existing_offer.start_date = start_date
                existing_offer.end_date = end_date
                existing_offer.is_active = is_active
                existing_offer.save()
                
                messages.success(request, f'Offer for {product.name} has been successfully updated.')
            else:
                # Create new offer
                new_offer = Offer.objects.create(
                    product=product,
                    offer_name=offer_name,
                    description=description,
                    discount_percentage=discount_percentage,
                    start_date=start_date,
                    end_date=end_date,
                    is_active=is_active,
                    offer_type='PRODUCT'
                )
                
                messages.success(request, f'New offer for {product.name} has been successfully created.')

            # Update product's offer price if the offer is active
            if is_active:
                discount_factor = Decimal(discount_percentage) / Decimal(100)  # Convert to Decimal
                product.offer_price = product.base_price * (1 - discount_factor)  # Perform Decimal-safe calculation
                product.save()
                messages.info(request, f'Product price updated to {product.offer_price} with {discount_percentage}% discount.')

            # Redirect to product list or wherever appropriate
            return redirect('admin_product')  # Replace with your actual product list view name

        except Exception as e:
            # Catch any unexpected errors
            messages.error(request, f'An unexpected error occurred: {str(e)}. Please try again.')
            return render(request, 'add_product_offer.html', {'product': product})

    # GET request: render the form
    return render(request, 'add_product_offer.html', {'product': product})





# added here

@admin_required
def edit_product_offer(request, offer_id):
    # Retrieve the offer based on the provided offer_id
    offer = get_object_or_404(Offer, id=offer_id)

    if request.method == 'POST':
        # Collect the form data
        offer_name = request.POST.get('offer_name')
        description = request.POST.get('description')
        discount_percentage = request.POST.get('discount_percentage')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        is_active = request.POST.get('is_active') == 'on'

        # Update the offer instance with the new values
        offer.offer_name = offer_name if offer_name else offer.offer_name
        offer.description = description if description else offer.description
        offer.discount_percentage = discount_percentage if discount_percentage else offer.discount_percentage
        offer.start_date = start_date if start_date else offer.start_date
        offer.end_date = end_date if end_date else offer.end_date
        offer.is_active = is_active

        # Save the updated offer
        offer.save()

        # Redirect to a relevant page (e.g., admin_product or the offer list)
        return redirect('admin_product')

    # Pass the existing offer data to the template for placeholders
    return render(request, 'edit_product_offer.html', {'offer': offer, 'product': offer.product})





@admin_required
def delete_product_offer(request):
    if request.method == 'POST':
        offer_id = request.POST.get('offer_id')
        try:
            offer = Offer.objects.get(id=offer_id)
            offer.delete()
            messages.success(request, 'Offer has been deleted successfully.')
        except Offer.DoesNotExist:
            messages.error(request, 'Offer not found.')
    return redirect('admin_product')


# ----------add_offer_to_category----------------------------------------------------------------------------------------
# added here

@admin_required
def add_offer_to_category(request, category_id):
    category = get_object_or_404(Catogery, id=category_id)
    
    # Check if offer already exists
    if category.offers.exists():
        return HttpResponse("Offer already exists for this category", status=400)
    
    if request.method == 'POST':
        offer_name = request.POST.get('offer_name')
        description = request.POST.get('description')
        discount_percentage = request.POST.get('discount_percentage')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        offer = Offer.objects.create(
            offer_name=offer_name,
            description=description,
            discount_percentage=discount_percentage,
            start_date=start_date,
            end_date=end_date,
            offer_type='CATEGORY',
            category=category,
        )

        messages.success(request, f"Offer added to the {category.name} category successfully!")
        
        return redirect('admin_category')  # Redirect to the category offers list page

    return render(request, 'add_cetegory_offer.html', {'category': category})

# ------------edit_offer_for_category-------------------------------------------------------------------------------------------------------


def edit_offer_for_category(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)

    if request.method == 'POST':
        offer.offer_name = request.POST.get('offer_name', offer.offer_name)
        offer.description = request.POST.get('description', offer.description)
        offer.discount_percentage = request.POST.get('discount_percentage', offer.discount_percentage)
        offer.start_date = request.POST.get('start_date', offer.start_date)
        offer.end_date = request.POST.get('end_date', offer.end_date)

        offer.save()

        # Optionally, add a success message
        messages.success(request, f"Offer for category '{offer.category.name}' has been updated successfully.")

        return redirect('admin_category')  # Replace with your category offers list URL name

    return render(request, 'edit_offer_for_category.html', {'offer': offer})




def delete_offer_for_category(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)

    if request.method == 'POST':
        offer.delete()
        # Optionally, add a success message
        messages.success(request, f"Offer '{offer.offer_name}' for '{offer.category.name}' has been deleted successfully.")

    return redirect('admin_category')  # Replace 'admin_category' with the correct URL name for your category list page


# --------------------------------------------------------------



