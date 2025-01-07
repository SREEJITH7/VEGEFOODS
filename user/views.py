# from urllib import request
import uuid
from django.shortcuts import render , redirect, get_object_or_404
from django.urls import reverse
from user.forms import UserRegForm
from user.models import CustomUser
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
import random 
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import logout
from .decorators import login_required 
from django.http import HttpResponse
from django.http import JsonResponse
from django.db.models import Prefetch
from datetime import timedelta
from admin_panel.models import Product, ProductImage ,Catogery ,Variant,CouponTable, CouponUsage , Offer
from django.utils.timezone import now
from datetime import datetime
from .decorators import user_required
from .forms import AddressForm
from .models import Address
from .models import Cart,Order, OrderItem , Wishlist , OrderReturn, Wallet, WalletTransaction, WalletWithdrawal
import json
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
import environ
import razorpay
# Create your views here.



def beforelogin(request):
    return render(request, 'beforeloginpage.html')




##################################################################################################################################################




def index(request):
    # Log out the user if they are already logged in
    if request.user.is_authenticated:
        logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                messages.error(request, "Superuser accounts are not allowed to log in here.")
                return redirect('login')  # Redirect back to the login page

            login(request, user)
            return redirect('welcome')  # Redirect to the desired page
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')
# ------

@require_POST
def custom_logout(request):
    try:
        logout(request)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

##################################################################################################################################################

@user_required
@login_required
def welcome(request):
    response = render(request, 'welcome.html')
    response['Cache-Control'] = 'no-chache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache, no-store, must-revalifate'
    response['Expries'] = '0'
    return response
##################################################################################################################################################
# this view is for signup page 

def registrationPage(request):
    if request.method == 'POST':
        form = UserRegForm(request.POST)
        if form.is_valid():
            try:
                email = form.cleaned_data['email']
                otp = random.randint(100000, 999999)
                request.session['form_data'] = request.POST
                request.session['email_otp'] = otp

                send_mail(
                    'Your OTP for Registration',
                    f'Your OTP is {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                return redirect('verify_otp')
            except Exception as e:
                print(f"Email error: {str(e)}")  # This will help debug the issue
                messages.error(request, "Failed to send OTP email. Please try again.")
        else:
            messages.error(request, "There were errors in your form. Please correct them.")
    else:
        form = UserRegForm()
    return render(request, 'registration.html', {'form': form})


# this is for otp varification 
##################################################################################################################################################



def verify_otp(request):
    if request.method == 'POST':
        user_otp = request.POST.get('otp')
        session_otp = request.session.get('email_otp')

        if str(user_otp) == str(session_otp):
            form_data = request.session.get('form_data')
            form = UserRegForm(form_data)

            if form.is_valid():
                user = form.save(commit= False)
                user.set_password(form.cleaned_data['password'])
                user.save()
                messages.success(request,'Registration successful! Please log in.')
                # clearing the data that stored in the session before like the otp and form data
                del request.session['form_data']
                del request.session['email_otp']
                return redirect('login')
            else:
                messages.error(request, "There was an error saving your data.")
        else:
            messages.error(request,"invalid OTP.Please try again.")
    return render(request, 'verify_otp.html')        



# to ensure the user sessions are cleared after logout 
##################################################################################################################################################


def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'You have successfully logged out')
    return redirect('login')


##################################################################################################################################################

# for resending otp after timeout 

def resend_otp(request):
    if request.method == "POST":
        # Generate a new OTP and store it in the session
        otp = random.randint(100000, 999999)
        request.session['email_otp'] = otp
        
        # Retrieve the email from session data and send the new OTP
        email = request.session.get('form_data').get('email')
        send_mail(
            'Your OTP for Registration',
            f'Your new OTP is {otp}',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        
        return JsonResponse({"success": "OTP resent successfully"})
    else:
        return JsonResponse({"error": "Invalid request method"}, status=400)




##### shop pages  #############################################################################################################################################


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger




def shopsection(request):
    search_query = request.GET.get('q', '').lower()
    sort_option = request.GET.get('sort', '')
    


        # Category-specific redirection
    category_mapping = {
        'vegetable': 'shopvegetables',
        'vegetables': 'shopvegetables',
        'fruit': 'shopfruits',
        'fruits': 'shopfruits',
        'juice': 'shopjuice',
        'juices': 'shopjuice',
        'dried': 'shopdried',
        'nuts': 'shopdried',
    }

    for category, url_name in category_mapping.items():
        if category in search_query:
            return redirect(url_name)





    products = Product.objects.filter(is_delete=False).prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all(), to_attr='all_images'),
        Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer'),
    )
    
    # Fetch all active category offers
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )
    
    # Search functionality
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    # Sorting functionality
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    
    # Compare the discount percentages and set the highest one
    for product in products:
        # Initialize variables
        product_offer_discount = 0
        category_offer_discount = 0
        
        # Check product-specific offers
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        # Check category offers
        category_offers = active_category_offers.filter(category=product.catogery)
        
        # Only apply category offer if product belongs to the category
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        # Compare all discounts
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )
    

        # Calculate the final price after discount
        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)

    # Pagination logic
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  # 16 products per page
        page = request.GET.get('page', 1)
        
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)
    
    return render(request, 'shop.html', {
        'products': products,
        'paginate': paginate,
        'total_products': products.count() if paginate else products.count()
    })



##### shop vegetables  ###########################################################################################################################################################

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def shopvegetables(request):
    search_query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', '')


    category_mapping = {
        'vegetable': 'shopvegetables',
        'vegetables': 'shopvegetables',
        'fruit': 'shopfruits',
        'fruits': 'shopfruits',
        'juice': 'shopjuice',
        'juices': 'shopjuice',
        'dried': 'shopdried',
        'nuts': 'shopdried',
    }

    for category, url_name in category_mapping.items():
        if category in search_query:
            return redirect(url_name)



    # Get the "Vegetables" category
    vegetable_category = Catogery.objects.filter(name__iexact="Vegetables").first()
    
    # Fetch products from the "Vegetables" category with prefetch for images and active offers
    products = Product.objects.filter(
        catogery=vegetable_category, 
        is_delete=False
    ).prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all(), to_attr='all_images'),
        Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')  # Fetch active offers
    )

     # Fetch all active category offers
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    # Sorting options
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    # Search filtering
    if search_query:
        products = products.filter(name__icontains=search_query)

      # Compare the discount percentages and set the highest one
    for product in products:
        # Initialize variables
        product_offer_discount = 0
        category_offer_discount = 0
        
        # Check product-specific offers
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        # Check category offers
        category_offers = active_category_offers.filter(category=product.catogery)
        
        # Only apply category offer if product belongs to the category
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        # Compare all discounts
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)


    # Pagination logic
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  # 16 products per page
        page = request.GET.get('page', 1)
        
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

    return render(request, 'shopvegetables.html', {
        'products': products,
        'paginate': paginate,
        'search_query': search_query,
        'sort_option': sort_option,
        'total_products': products.count() if paginate else products.count()
    })

##### shop fruits  ###########################################################################################################################################################


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def shopfruits(request):
    search_query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', '')
    

    category_mapping = {
        'vegetable': 'shopvegetables',
        'vegetables': 'shopvegetables',
        'fruit': 'shopfruits',
        'fruits': 'shopfruits',
        'juice': 'shopjuice',
        'juices': 'shopjuice',
        'dried': 'shopdried',
        'nuts': 'shopdried',
    }

    for category, url_name in category_mapping.items():
        if category in search_query:
            return redirect(url_name)






    fruits_category = Catogery.objects.filter(name__iexact="Fruits").first()

    products = Product.objects.filter(
        catogery=fruits_category, 
        is_delete=False
    ).prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all(), to_attr='all_images'),
        Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')
    )

     # Fetch all active category offers
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    # Sorting options
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    # Search filtering
    if search_query:
        products = products.filter(name__icontains=search_query)


    # Compare the discount percentages and set the highest one
    for product in products:
        # Initialize variables
        product_offer_discount = 0
        category_offer_discount = 0
        
        # Check product-specific offers
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        # Check category offers
        category_offers = active_category_offers.filter(category=product.catogery)
        
        # Only apply category offer if product belongs to the category
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        # Compare all discounts
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)



    # Pagination logic
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  # 16 products per page
        page = request.GET.get('page', 1)
        
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

    return render(request, 'shopfruits.html', {
        'products': products,
        'paginate': paginate,
        'search_query': search_query,
        'sort_option': sort_option,
        'total_products': products.count() if paginate else products.count()
    })
###### shop juice #####################################################################################################################################################


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def shopjuice(request):
    search_query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', '')


    category_mapping = {
        'vegetable': 'shopvegetables',
        'vegetables': 'shopvegetables',
        'fruit': 'shopfruits',
        'fruits': 'shopfruits',
        'juice': 'shopjuice',
        'juices': 'shopjuice',
        'dried': 'shopdried',
        'nuts': 'shopdried',
    }

    for category, url_name in category_mapping.items():
        if category in search_query:
            return redirect(url_name)



    juice_category = Catogery.objects.filter(name__iexact="juice").first()

    products = Product.objects.filter(
        catogery=juice_category, 
        is_delete=False
    ).prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all(), to_attr='all_images'),
        Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')
    )

    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    # Sorting options
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    # Search filtering
    if search_query:
        products = products.filter(name__icontains=search_query)


    # Compare the discount percentages and set the highest one
    for product in products:
        # Initialize variables
        product_offer_discount = 0
        category_offer_discount = 0
        
        # Check product-specific offers
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        # Check category offers
        category_offers = active_category_offers.filter(category=product.catogery)
        
        # Only apply category offer if product belongs to the category
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        # Compare all discounts
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)



    # Pagination logic
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  # 16 products per page
        page = request.GET.get('page', 1)
        
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

    return render(request, 'shopjuice.html', {
        'products': products,
        'paginate': paginate,
        'search_query': search_query,
        'sort_option': sort_option,
        'total_products': products.count() if paginate else products.count()
    })

###### shop dried #####################################################################################################################################################



def shopdried(request):
    search_query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', '')


    category_mapping = {
        'vegetable': 'shopvegetables',
        'vegetables': 'shopvegetables',
        'fruit': 'shopfruits',
        'fruits': 'shopfruits',
        'juice': 'shopjuice',
        'juices': 'shopjuice',
        'dried': 'shopdried',
        'nuts': 'shopdried',
    }

    for category, url_name in category_mapping.items():
        if category in search_query:
            return redirect(url_name)






    dried_category = Catogery.objects.filter(name__iexact="dried").first()

    products = Product.objects.filter(
        catogery=dried_category, 
        is_delete=False
    ).prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all(), to_attr='all_images'),
        Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')

    )

    # Fetch all active category offers
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    # Sorting options
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    # Search filtering
    if search_query:
        products = products.filter(name__icontains=search_query)


    # Compare the discount percentages and set the highest one
    for product in products:
        # Initialize variables
        product_offer_discount = 0
        category_offer_discount = 0
        
        # Check product-specific offers
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        # Check category offers
        category_offers = active_category_offers.filter(category=product.catogery)
        
        # Only apply category offer if product belongs to the category
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        # Compare all discounts
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)




    # Pagination logic
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  # 16 products per page
        page = request.GET.get('page', 1)
        
        try:
            products = paginator.page(page)
        except PageNotAnInteger:
            products = paginator.page(1)
        except EmptyPage:
            products = paginator.page(paginator.num_pages)

    return render(request, 'shopdried.html', {
        'products': products,
        'paginate': paginate,
        'search_query': search_query,
        'sort_option': sort_option,
        'total_products': products.count() if paginate else products.count()
    })

###### single product #####################################################################################################################################################


# def product_details(request, product_id):
#     # Fetch the product with its images
#     product = get_object_or_404(
#         Product.objects.prefetch_related('images'), 
#         id=product_id, 
#         is_delete=False
#     )


#      # Determine size options based on category
#     category_name = product.catogery.name.lower()
#     if category_name in ['vegetables', 'fruits', 'dried']:
#         size_options = ['0.1kg', '0.5kg', '1kg', '1.5kg', '2kg']
#     elif category_name == 'juice':
#         size_options = ['0.5 liter', '1 liter']
#     else:
#         size_options = ['Small', 'Medium', 'Large', 'Extra Large']



#     # Get the primary image (if exists)
#     main_image = product.images.filter(is_primary=True).first() or product.images.first()

#     # Fetch related products
#     related_products = Product.objects.filter(
#         catogery=product.catogery, 
#         is_delete=False
#     ).exclude(id=product_id).prefetch_related('images')[:4]


#     # Get variants for the product
#     variants = product.variants.all()

#     # Select the first variant as the default (if exists)
#     selected_variant = variants.first() if variants.exists() else None


#     return render(request, 'singleproduct.html', {
#         'product': product, 
#         'related_products': related_products,
#         'main_image': main_image,
#         'size_options': size_options,
#         'variants': variants,
#         'selected_variant': selected_variant,
#     })


# --------implementing offer price in single product page----------------------------------------------------


def product_details(request, product_id):
    # Fetch the product with its images and offers
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'images',
            Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')
        ),
        id=product_id,
        is_delete=False
    )

    # Fetch all active category offers
    active_category_offers = Offer.objects.filter(
        is_active=True,
        offer_type='CATEGORY'
    )

    # Initialize discount variables
    product_offer_discount = 0
    category_offer_discount = 0

    # Check product-specific offers
    if hasattr(product, 'active_product_offer') and product.active_product_offer:
        product_offer_discount = product.active_product_offer[0].discount_percentage

    # Check category offers
    category_offers = active_category_offers.filter(category=product.catogery)
    
    # Only apply category offer if product belongs to the category
    valid_category_offers = [
        offer for offer in category_offers 
        if offer.category == product.catogery
    ]

    if valid_category_offers:
        category_offer_discount = max(
            offer.discount_percentage for offer in valid_category_offers
        )

    # Compare all discounts and set the final discount
    product.final_discount = max(
        product.discount_percentage or 0,
        product_offer_discount,
        category_offer_discount
    )

    # Calculate the final price after discount
    product.final_price = product.base_price - (product.base_price * product.final_discount / 100)

    # Determine size options based on category
    category_name = product.catogery.name.lower()
    if category_name in ['vegetables', 'fruits', 'dried']:
        size_options = ['0.1kg', '0.5kg', '1kg', '1.5kg', '2kg']
    elif category_name == 'juice':
        size_options = ['0.5 liter', '1 liter']
    else:
        size_options = ['Small', 'Medium', 'Large', 'Extra Large']

    # Get the primary image (if exists)
    main_image = product.images.filter(is_primary=True).first() or product.images.first()

    # Fetch related products
    related_products = Product.objects.filter(
        catogery=product.catogery,
        is_delete=False
    ).exclude(id=product_id).prefetch_related('images')[:4]

    # Get variants for the product
    variants = product.variants.all()

    # Select the first variant as the default (if exists)
    selected_variant = variants.first() if variants.exists() else None

    return render(request, 'singleproduct.html', {
        'product': product,
        'related_products': related_products,
        'main_image': main_image,
        'size_options': size_options,
        'variants': variants,
        'selected_variant': selected_variant,
    })





























from django.contrib import messages
from django.utils.timezone import now

import random

# Simulating email sending function (you can integrate an email service)
def send_otp_via_email(email, otp):
    print(f"OTP sent to {email}: {otp}")  # Replace with actual email sending code


# -----------------------------------------------------------------



def forgotpassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = CustomUser.objects.filter(email=email).first()
        if user:
            # Generate OTP
            otp = random.randint(1000, 9999)
            
            # Store OTP and expiration in session
            request.session['reset_otp'] = otp
            request.session['reset_otp_expiration'] = (now() + timedelta(seconds=20)).isoformat()
            request.session['reset_email'] = email
            
            # Send OTP to email
            send_otp_via_email(email, otp)
            messages.success(request, "OTP sent successfully!")
            return redirect("validate_email", email=email)
        else:
            messages.error(request, "Email not registered!")

    return render(request, "forgotpassword.html")

def validate_email(request, email):
    # Retrieve session data
    session_email = request.session.get('reset_email')
    session_otp = request.session.get('reset_otp')
    session_otp_expiration = request.session.get('reset_otp_expiration')
    
    if not session_email or session_email != email:
        messages.error(request, "Invalid email!")
        return redirect('forgotpassword')
    
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        
        # Check if OTP is correct and not expired
        if session_otp == int(entered_otp):
            otp_expiration = datetime.fromisoformat(session_otp_expiration)
            if otp_expiration > now():
                # Clear OTP from session
                del request.session['reset_otp']
                del request.session['reset_otp_expiration']
                
                return redirect('enter_new_password')
            else:
                messages.error(request, "OTP has expired!")
        else:
            messages.error(request, "Invalid OTP!")
    
    return render(request, 'validate_email.html', {'email': email})

def enter_new_password(request):
    email = request.session.get('reset_email')

    if not email:
        messages.error(request, "Session expired. Please try again.")
        return redirect('forgotpassword')

    user = CustomUser.objects.filter(email=email).first()

    if not user:
        messages.error(request, "User not found.")
        return redirect('forgotpassword')

    if request.method == "POST":
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return render(request, 'enter_new_password.html')

        # Update the user's password
        user.password = make_password(new_password)
        user.save()

        # Clear session after password reset
        del request.session['reset_email']

        messages.success(request, "Password updated successfully!")
        return redirect('login')

    return render(request, 'enter_new_password.html')


#---------------------------------------------------------------------------------------------------------
@user_required
@login_required
def profile(request):
    return render(request ,'userprofile.html')


#-------User Profile--------------------------------------------------------------------------------------------------



from django.contrib.auth import get_user_model


def update_profile(request):


    User = get_user_model()

    if request.method == 'POST':
        user = request.user  # Get the currently logged-in user

        # Fetch data from the POST request, stripping any unnecessary whitespace
        first_name = request.POST.get('firstName', '').strip()
        last_name = request.POST.get('lastName', '').strip()
        username = request.POST.get('UserName', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirmPassword', '').strip()

        # Flag to track if any changes were made
        changes_made = False

        # Validate password and confirmation
        if password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect('profile')
            
            # If passwords match, update password
            user.set_password(password)
            changes_made = True

        # Update fields only if they are provided and different from current values
        if first_name and first_name != user.first_name:
            user.first_name = first_name
            changes_made = True
        
        if last_name and last_name != user.last_name:
            user.last_name = last_name
            changes_made = True
        
        if username and username != user.username:
            # Optional: Add a check to ensure username is unique
            if User.objects.exclude(pk=user.pk).filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('profile')
            user.username = username
            changes_made = True
        
        if email and email != user.email:
            # Optional: Add a check to ensure email is unique
            if User.objects.exclude(pk=user.pk).filter(email=email).exists():
                messages.error(request, "Email already in use.")
                return redirect('profile')
            user.email = email
            changes_made = True
        
        if phone_number and phone_number != getattr(user, 'phone_number', ''):
            user.phone_number = phone_number
            changes_made = True

        # Save only if changes were made
        if changes_made:
            user.save()

            # Re-authenticate the user if password was updated
            if password:
                update_session_auth_hash(request, user)

            messages.success(request, "Profile updated successfully!")
        else:
            messages.info(request, "No changes were made to your profile.")

        return redirect('profile')

    return render(request, 'profile.html')


# ----------Address Book-------------------------------------------------------------------------------------------------------------------------
@user_required
def addressbook(request):
    if request.user.is_authenticated:
        addresses = Address.objects.filter(user=request.user)
    else:
        addresses = []    

    return render(request , 'addressbook.html',{'addresses': addresses})

# ------------------------------------------------------------------------------------------------------------------------------------------------



def add_address(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user 
            address.save()
            return JsonResponse({'success': True, 'message': 'Address saved successfully!'}, status=200)
        else:
            
            errors = form.errors.as_json()
            return JsonResponse({'success': False, 'message': 'Form validation failed!', 'errors': errors}, status=400)
    else:
        form = AddressForm()
        return render(request, 'AddAddress.html', {'form': form})




# ------------------------------------------------------------------------------------------------------------------
@user_required
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    # Set all other addresses as not default
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    
    # Set the selected address as default
    address.is_default = True
    address.save()
    
    return redirect('addressbook')


#---------------------------------------------------------------------------------------------------------------------

@user_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address deleted successfully!")
    return redirect('addressbook')

#---------------------------------------------------------------------------------------------------------------------

@user_required
def edit_address(request, address_id):
    try:
        address = Address.objects.get(id=address_id, user=request.user)
    except Address.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Address not found.'
        }, status=404)

    if request.method == "POST":
        try:
            
            address.full_name = request.POST.get("full_name")
            address.street_address = request.POST.get("street_address")
            address.apartment_suite = request.POST.get("apartment_suite", "")
            address.landmark = request.POST.get("landmark", "")
            address.city = request.POST.get("city")
            address.postal_code = request.POST.get("postal_code")
            address.phone_number = request.POST.get("phone_number")
            address.state = request.POST.get("state")
            
            address.save()

            return JsonResponse({
                'success': True, 
                'message': 'Address updated successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': str(e)
            }, status=400)

    return render(request, "EditAddress.html", {"address": address})


#-------------------------------------------------------------------------------------------------------------------



# ------------cart after including varients before coupons working cart latest ------------------------------------------------------

from decimal import Decimal, InvalidOperation


# -----------------for adding coupon ------------------------------------------------------------------------------


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from django.http import JsonResponse
import logging
import traceback
logger = logging.getLogger(__name__)

# @require_http_methods(["GET", "POST"])
# def cart(request):
#     try:
#         cart_items = Cart.objects.select_related('product', 'variant', 'product__catogery').filter(user=request.user)
#         cart_total = sum(item.total_price for item in cart_items)
#         cart_empty = not cart_items.exists()

#         # Prepare formatted cart items
#         formatted_cart_items = []
#         for item in cart_items:
#             variant_display = ''
#             if item.variant:
#                 # Determine variant display based on category
#                 if item.product.category.name in ['vegetables', 'fruits', 'dried']:
#                     variant_display = f"{item.variant.weight} kg"
#                 elif item.product.category.name == 'juice':
#                     variant_display = f"{item.variant.volume} liter" if item.variant.volume else ''
#                 else:
#                     variant_display = item.variant.weight or ''
#             formatted_item = {
#                 'cart_item': item,
#                 'variant_display': variant_display,
#                 'item_total': float(item.total_price)
#             }
#             formatted_cart_items.append(formatted_item)

#         # Handle coupon application
#         if request.method == 'POST':
#             coupon_code = request.POST.get('coupon_code')
#             discount_amount = 0
#             final_total = cart_total

#             if coupon_code:
#                 try:
#                     coupon = get_object_or_404(CouponTable, code=coupon_code, is_active=True)
#                     if coupon.max_uses is None or coupon.max_uses > 0:
#                         if cart_total >= coupon.min_purchase_amount:
#                             if coupon.coupon_type == 'percentage':
#                                 discount_amount = cart_total * (coupon.discount_value / 100)
#                             else:
#                                 discount_amount = min(coupon.discount_value, cart_total)
#                             final_total = cart_total - discount_amount

#                             # Create CouponUsage record
#                             CouponUsage.objects.create(
#                                 user=request.user,
#                                 coupon=coupon,
#                                 discount_value=discount_amount
#                             )

#                             # Update coupon usage
#                             if coupon.max_uses is not None:
#                                 coupon.max_uses -= 1
#                                 coupon.save()

#                             return JsonResponse({
#                                 'success': True,
#                                 'message': f"Coupon '{coupon_code}' applied successfully!",
#                                 'discount_amount': discount_amount,
#                                 'final_total': final_total
#                             })
#                         else:
#                             return JsonResponse({
#                                 'success': False,
#                                 'message': f"Minimum purchase amount of ₹{coupon.min_purchase_amount:.2f} is required to use this coupon."
#                             })
#                     else:
#                         return JsonResponse({
#                             'success': False,
#                             'message': "This coupon has been exhausted."
#                         })
#                 except CouponTable.DoesNotExist:
#                     return JsonResponse({
#                         'success': False,
#                         'message': "Invalid coupon code."
#                     })
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'message': "Please enter a coupon code."
#                 })

#         context = {
#             'cart_items': formatted_cart_items,  # Now contains formatted cart items
#             'cart_total': cart_total,
#             'cart_empty': cart_empty,
#         }
#         return render(request, 'cart.html', context)

#     except Exception as e:
#         logger.error("Error in cart view: %s", traceback.format_exc())
#         return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.'})


#-------------------------this is working on cart page commented for checkout page should also render the totalss expiriment------------------------------------------------------------------------------------------
import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods


# @require_http_methods(["GET", "POST"])
# def cart(request):
#     try:
#         # Clear any previous applied coupons
#         Cart.objects.filter(user=request.user).update(applied_coupon=None, discount_amount=0)

#         cart_items = Cart.objects.select_related('product', 'variant', 'product__catogery').filter(user=request.user)
#         cart_total = sum(item.total_price for item in cart_items)
#         cart_empty = not cart_items.exists()
#         delivery_charge = 10  # Fixed delivery charge
        

#         # Handle coupon application
#         if request.method == 'POST':
#             coupon_code = request.POST.get('coupon_code')
            
#             if coupon_code:
#                 try:
#                     coupon = CouponTable.objects.get(code=coupon_code, is_active=True)
                    
#                     if coupon.max_uses is None or coupon.max_uses > 0:
#                         if cart_total >= coupon.min_purchase_amount:
#                             # Calculate discount
#                             if coupon.coupon_type == 'percentage':
#                                 discount_amount = round(cart_total * (coupon.discount_value / 100), 2)
#                             else:
#                                 discount_amount = round(min(coupon.discount_value, cart_total), 2)
                            
#                             final_total = round(cart_total - discount_amount, 2)

#                             # Distribute discount across cart items
#                             if cart_items.exists():
#                                 discount_per_item = round(discount_amount / len(cart_items), 2)
#                                 for item in cart_items:
#                                     item.applied_coupon = coupon
#                                     item.discount_amount = discount_per_item
#                                     item.save()

#                             # Create CouponUsage record
#                             CouponUsage.objects.create(
#                                 user=request.user,
#                                 coupon=coupon,
#                                 discount_value=discount_amount
#                             )

#                             # Update coupon usage
#                             if coupon.max_uses is not None:
#                                 coupon.max_uses -= 1
#                                 coupon.save()

#                             return JsonResponse({
#                                 'success': True,
#                                 'message': f"Coupon '{coupon_code}' applied successfully!",
#                                 'discount_amount': float(discount_amount),
#                                 'final_total': float(final_total)
#                             })
#                         else:
#                             return JsonResponse({
#                                 'success': False,
#                                 'message': f"Minimum purchase amount of ₹{coupon.min_purchase_amount:.2f} is required to use this coupon."
#                             })
#                     else:
#                         return JsonResponse({
#                             'success': False,
#                             'message': "This coupon has been exhausted."
#                         })
#                 except CouponTable.DoesNotExist:
#                     return JsonResponse({
#                         'success': False,
#                         'message': "Invalid coupon code."
#                     })
#                 except Exception as e:
#                     logger.error(f"Coupon application error: {str(e)}")
#                     return JsonResponse({
#                         'success': False,
#                         'message': f"An error occurred: {str(e)}"
#                     })
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'message': "Please enter a coupon code."
#                 })

#         # Prepare formatted cart items
#         formatted_cart_items = []
#         for item in cart_items:
#             variant_display = ''
#             if item.variant:
#                 # Determine variant display based on category
#                 if item.product.category.name in ['vegetables', 'fruits', 'dried']:
#                     variant_display = f"{item.variant.weight} kg"
#                 elif item.product.category.name == 'juice':
#                     variant_display = f"{item.variant.volume} liter" if item.variant.volume else ''
#                 else:
#                     variant_display = item.variant.weight or ''
            
#             formatted_item = {
#                 'cart_item': item,
#                 'variant_display': variant_display,
#                 'item_total': round(float(item.total_price), 2),
#                 'discount_amount': round(float(item.discount_amount or 0), 2)
#             }
#             formatted_cart_items.append(formatted_item)

#         context = {
#             'cart_items': formatted_cart_items,
#             'cart_total': cart_total,
#             'cart_empty': cart_empty,
#         }
#         return render(request, 'cart.html', context)

#     except Exception as e:
#         # More detailed error logging
#         logger.error(f"Error in cart view: {traceback.format_exc()}")
#         print(f"Error in cart view: {traceback.format_exc()}")  # For server console
#         return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})



# @require_http_methods(["GET", "POST"])
# def cart(request):
#     try:
#         # Clear any previous applied coupons
#         Cart.objects.filter(user=request.user).update(applied_coupon=None, discount_amount=0)

#         cart_items = Cart.objects.select_related('product', 'variant', 'product__catogery').filter(user=request.user)
#         cart_subtotal = sum(item.total_price for item in cart_items)
#         delivery_charge = 10  # Fixed delivery charge
#         cart_total = cart_subtotal + delivery_charge
#         cart_empty = not cart_items.exists()

#         # Handle coupon application
#         if request.method == 'POST':
#             coupon_code = request.POST.get('coupon_code')
            
#             if coupon_code:
#                 try:
#                     coupon = CouponTable.objects.get(code=coupon_code, is_active=True)
                    
#                     if coupon.max_uses is None or coupon.max_uses > 0:
#                         if cart_total >= coupon.min_purchase_amount:
#                             # Calculate discount
#                             if coupon.coupon_type == 'percentage':
#                                 discount_amount = round(cart_subtotal * (coupon.discount_value / 100), 2)
#                             else:
#                                 discount_amount = round(min(coupon.discount_value, cart_subtotal), 2)
                            
#                             final_total = round(cart_total - discount_amount, 2)

#                             # Distribute discount across cart items
#                             if cart_items.exists():
#                                 discount_per_item = round(discount_amount / len(cart_items), 2)
#                                 for item in cart_items:
#                                     item.applied_coupon = coupon
#                                     item.discount_amount = discount_per_item
#                                     item.save()

#                             # Create CouponUsage record
#                             CouponUsage.objects.create(
#                                 user=request.user,
#                                 coupon=coupon,
#                                 discount_value=discount_amount
#                             )

#                             # Update coupon usage
#                             if coupon.max_uses is not None:
#                                 coupon.max_uses -= 1
#                                 coupon.save()

#                             return JsonResponse({
#                                 'success': True,
#                                 'message': f"Coupon '{coupon_code}' applied successfully!",
#                                 'discount_amount': float(discount_amount),
#                                 'final_total': float(final_total)
#                             })
#                         else:
#                             return JsonResponse({
#                                 'success': False,
#                                 'message': f"Minimum purchase amount of ₹{coupon.min_purchase_amount:.2f} is required to use this coupon."
#                             })
#                     else:
#                         return JsonResponse({
#                             'success': False,
#                             'message': "This coupon has been exhausted."
#                         })
#                 except CouponTable.DoesNotExist:
#                     return JsonResponse({
#                         'success': False,
#                         'message': "Invalid coupon code."
#                     })
#                 except Exception as e:
#                     logger.error(f"Coupon application error: {str(e)}")
#                     return JsonResponse({
#                         'success': False,
#                         'message': f"An error occurred: {str(e)}"
#                     })
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'message': "Please enter a coupon code."
#                 })

#         # Prepare formatted cart items
#         formatted_cart_items = []
#         for item in cart_items:
#             variant_display = ''
#             if item.variant:
#                 # Determine variant display based on category
#                 if item.product.category.name in ['vegetables', 'fruits', 'dried']:
#                     variant_display = f"{item.variant.weight} kg"
#                 elif item.product.category.name == 'juice':
#                     variant_display = f"{item.variant.volume} liter" if item.variant.volume else ''
#                 else:
#                     variant_display = item.variant.weight or ''
            
#             formatted_item = {
#                 'cart_item': item,
#                 'variant_display': variant_display,
#                 'item_total': round(float(item.total_price), 2),
#                 'discount_amount': round(float(item.discount_amount or 0), 2)
#             }
#             formatted_cart_items.append(formatted_item)

#         context = {
#             'cart_items': formatted_cart_items,
#             'cart_subtotal': cart_subtotal,
#             'delivery_charge': delivery_charge,
#             'cart_total': cart_total,
#             'cart_empty': cart_empty,
#         }
#         return render(request, 'cart.html', context)

#     except Exception as e:
#         # More detailed error logging
#         logger.error(f"Error in cart view: {traceback.format_exc()}")
#         print(f"Error in cart view: {traceback.format_exc()}")  # For server console
#         return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

@require_http_methods(["GET", "POST"])
def cart(request):
    try:
        # Clear any previous applied coupons
        Cart.objects.filter(user=request.user).update(applied_coupon=None, discount_amount=0)

        # Fetch all cart items
        cart_items = Cart.objects.select_related('product', 'variant', 'product__catogery').filter(user=request.user)
        
        # Calculate cart subtotal (only product prices)
        cart_subtotal = sum(item.total_price for item in cart_items)

        # Fixed delivery charge
        delivery_charge = 10
        
        # Calculate cart total (subtotal + delivery charge)
        cart_total = cart_subtotal + delivery_charge
        
        # Check if cart is empty
        cart_empty = not cart_items.exists()

        # Handle coupon application if POST request
        if request.method == 'POST':
            coupon_code = request.POST.get('coupon_code')
            
            if coupon_code:
                try:
                    coupon = CouponTable.objects.get(code=coupon_code, is_active=True)
                    
                    # Check coupon usage limits and minimum purchase
                    if coupon.max_uses is None or coupon.max_uses > 0:
                        if cart_subtotal >= coupon.min_purchase_amount:  # Validate against subtotal
                            # Calculate discount
                            if coupon.coupon_type == 'percentage':
                                discount_amount = round(cart_subtotal * (coupon.discount_value / 100), 2)
                            else:
                                discount_amount = round(min(coupon.discount_value, cart_subtotal), 2)
                            
                            final_total = round(cart_total - discount_amount, 2)

                            # Distribute discount across cart items
                            if cart_items.exists():
                                discount_per_item = round(discount_amount / len(cart_items), 2)
                                for item in cart_items:
                                    item.applied_coupon = coupon
                                    item.discount_amount = discount_per_item
                                    item.save()

                            # Record coupon usage
                            CouponUsage.objects.create(
                                user=request.user,
                                coupon=coupon,
                                discount_value=discount_amount
                            )

                            # Update coupon usage limit
                            if coupon.max_uses is not None:
                                coupon.max_uses -= 1
                                coupon.save()

                            return JsonResponse({
                                'success': True,
                                'message': f"Coupon '{coupon_code}' applied successfully!",
                                'discount_amount': float(discount_amount),
                                'final_total': float(final_total)
                            })
                        else:
                            return JsonResponse({
                                'success': False,
                                'message': f"Minimum purchase amount of ₹{coupon.min_purchase_amount:.2f} is required to use this coupon."
                            })
                    else:
                        return JsonResponse({
                            'success': False,
                            'message': "This coupon has been exhausted."
                        })
                except CouponTable.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': "Invalid coupon code."
                    })
                except Exception as e:
                    logger.error(f"Coupon application error: {str(e)}")
                    return JsonResponse({
                        'success': False,
                        'message': f"An error occurred: {str(e)}"
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': "Please enter a coupon code."
                })

        # Prepare formatted cart items for rendering in the template
        formatted_cart_items = []
        for item in cart_items:
            variant_display = ''
            if item.variant:
                # Determine variant display based on category
                if item.product.category.name in ['vegetables', 'fruits', 'dried']:
                    variant_display = f"{item.variant.weight} kg"
                elif item.product.category.name == 'juice':
                    variant_display = f"{item.variant.volume} liter" if item.variant.volume else ''
                else:
                    variant_display = item.variant.weight or ''
            
            formatted_item = {
                'cart_item': item,
                'variant_display': variant_display,
                'item_total': round(float(item.total_price), 2),
                'discount_amount': round(float(item.discount_amount or 0), 2)
            }
            formatted_cart_items.append(formatted_item)

        # Render the template with context
        context = {
            'cart_items': formatted_cart_items,
            'cart_subtotal': cart_subtotal,
            'delivery_charge': delivery_charge,
            'cart_total': cart_total,
            'cart_empty': cart_empty,
        }
        return render(request, 'cart.html', context)

    except Exception as e:
        # Log detailed error
        logger.error(f"Error in cart view: {traceback.format_exc()}")
        print(f"Error in cart view: {traceback.format_exc()}")  # Debug output
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})



# --------add to cart ajax new for varient ---------------------------------------------------------------------------------------






# ----------above code is working for single productpage --------------------------------------------------------------------------------------------------------
# -----------------------------recently comnted know to transaction--------------------------------------------






from django.db import transaction
from django.core.exceptions import ValidationError

# @login_required
# def add_to_cart_ajax(request):
#     if request.method == "POST":
#         product_id = request.POST.get('product_id')
#         variant_id = request.POST.get('variant_id')
#         quantity = request.POST.get('quantity', 1)
        
#         try:
#             # Fetch the product
#             product = Product.objects.get(id=product_id)

#             # If no variant ID is provided, find the smallest weight variant
#             if not variant_id or variant_id == 'None':
#                 # Get variants for this product
#                 variants = Variant.objects.filter(product=product)
                
#                 if not variants.exists():
#                     return JsonResponse({
#                         'success': False,
#                         'error': "No variants available for this product."
#                     })
                
#                 # Find the variant with the smallest weight
#                 def extract_weight(variant):
#                     try:
#                         # Extract numeric value from weight string
#                         weight_str = str(variant.weight).replace('kg', '').strip()
#                         return float(weight_str) if weight_str else float('inf')
#                     except (ValueError, AttributeError):
#                         return float('inf')  # Put non-numeric weights at the end
                
#                 variant = min(variants, key=extract_weight)
#             else:
#                 # If variant ID is provided, use that specific variant
#                 try:
#                     variant = Variant.objects.get(id=int(variant_id), product=product)
#                 except Variant.DoesNotExist:
#                     return JsonResponse({
#                         'success': False,
#                         'error': "Invalid variant selected."
#                     })

#             # Ensure quantity is a positive integer
#             try:
#                 quantity = int(quantity)
#                 if quantity <= 0:
#                     raise ValueError("Quantity must be positive")
#             except (TypeError, ValueError):
#                 return JsonResponse({
#                     'success': False,
#                     'error': "Invalid quantity provided."
#                 })

#             # Use atomic transaction to ensure consistency
#             with transaction.atomic():
#                 # Check if the variant has sufficient stock
#                 if variant.stock_quantity < quantity:
#                     return JsonResponse({
#                         'success': False,
#                         'error': f"Only {variant.stock_quantity} items available for this variant."
#                     })

#                 # Dynamic price calculation with type-safe conversions
#                 try:
#                     # Convert variant and base prices to Decimal
#                     base_price = Decimal(str(variant.variant_price or product.base_price))
                    
#                     # Safe weight handling
#                     base_weight = Decimal(str(variant.weight or 0))
#                     standard_weight = Decimal('0.1')  # 0.1 kg as base

#                     # Price multiplier calculation
#                     price_multiplier = Decimal('1') + (base_weight / standard_weight - Decimal('1')) * Decimal('0.1')
#                     variant_price = base_price * price_multiplier

#                     # Try to get an existing cart item with the same product and variant
#                     cart_item = Cart.objects.filter(
#                         user=request.user,
#                         product=product,
#                         variant=variant
#                     ).first()

#                     if cart_item:
#                         # If item exists, update quantity
#                         total_quantity = cart_item.quantity + quantity
                        
#                         # Check if total quantity exceeds available stock
#                         if total_quantity > variant.stock_quantity:
#                             return JsonResponse({
#                                 'success': False,
#                                 'error': f"Cannot add more. Only {variant.stock_quantity} items available."
#                             })
                        
#                         cart_item.quantity = total_quantity
#                         cart_item.save()
                        
#                         created = False

#                     else:
#                         # Create new cart item
#                         cart_item = Cart.objects.create(
#                             user=request.user,
#                             product=product,
#                             variant=variant,
#                             quantity=quantity
#                         )
                        
#                         created = True

#                     return JsonResponse({
#                         'success': True,
#                         'message': f"{'Added' if created else 'Updated'} {product.name} ({variant.weight}) to your cart.",
#                         'variant_price': float(variant_price),  # Convert to float for JSON serialization
#                         'total_price': float(variant_price * Decimal(str(cart_item.quantity)))
#                     })

#                 except (TypeError, ValueError, InvalidOperation) as price_error:
#                     print(f"Price calculation error: {price_error}")
#                     return JsonResponse({
#                         'success': False,
#                         'error': "Error calculating price. Please try again."
#                     })

#         except Product.DoesNotExist:
#             return JsonResponse({
#                 'success': False,
#                 'error': "Product does not exist."
#             })
#         except Exception as e:
#             print("Error:", e)
#             return JsonResponse({
#                 'success': False,
#                 'error': "An error occurred. Please try again."
#             })

#     return JsonResponse({
#         'success': False,
#         'error': "Invalid request method."
#     })


@login_required
@transaction.atomic
def add_to_cart_ajax(request):
    try:
        product_id = request.POST.get('product_id')
        variant_id = request.POST.get('variant_id')
        quantity = int(request.POST.get('quantity', 1))

        if not all([product_id, variant_id]):
            return JsonResponse({
                'success': False,
                'message': 'Product and variant are required'
            }, status=400)

        product = get_object_or_404(Product, id=product_id)
        variant = get_object_or_404(Variant, id=variant_id, product=product)

        # Check for existing cart item
        cart_item = Cart.objects.filter(
            user=request.user,
            product=product,
            variant=variant
        ).first()

        try:
            if cart_item:
                # Update existing cart item
                cart_item.quantity += quantity
                cart_item.save()
            else:
                # Create new cart item
                cart_item = Cart.objects.create(
                    user=request.user,
                    product=product,
                    variant=variant,
                    quantity=quantity
                )

            return JsonResponse({
                'success': True,
                'message': 'Product added to cart successfully',
                'cart_count': Cart.objects.filter(user=request.user).count()
            })

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while adding to cart'
        }, status=400)


# ------------------------------------------------------------------------------



import logging

logger = logging.getLogger(__name__)


# ----------------------------transaction below ------------------------------------------




# @login_required
# @transaction.atomic
# def update_cart_quantity_ajax(request, cart_id):
#     try:
#         data = json.loads(request.body)
#         quantity = int(data.get('quantity', 1))
#         variant_id = data.get('variant_id')

#         cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        
#         # Optional: Validate new variant if changed
#         if variant_id and variant_id != cart_item.variant_id:
#             new_variant = get_object_or_404(Variant, id=variant_id, product=cart_item.product)
            
#             # Check new variant stock
#             if new_variant.stock_quantity < quantity:
#                 return JsonResponse({
#                     'success': False,
#                     'message': f'Only {new_variant.stock_quantity} items available for this variant.'
#                 }, status=400)
            
#             cart_item.variant = new_variant

#         # Update quantity
#         cart_item.quantity = quantity
#         cart_item.save()

#         # Recalculate totals
#         cart_items = Cart.objects.filter(user=request.user)
#         cart_total = sum(item.total_price for item in cart_items)

#         return JsonResponse({
#             'success': True,
#             'cart_total': cart_total,
#             'item_total': cart_item.total_price,
#         })

#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'message': str(e)
#         }, status=400)



@login_required
@transaction.atomic
def update_cart_quantity_ajax(request, cart_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        variant_id = data.get('variant_id')

        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be at least 1'
            }, status=400)

        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        
        try:
            # Optional: Validate new variant if changed
            if variant_id and variant_id != cart_item.variant_id:
                new_variant = get_object_or_404(Variant, id=variant_id, product=cart_item.product)
                cart_item.variant = new_variant

            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()

            # Recalculate totals
            cart_items = Cart.objects.filter(user=request.user)
            cart_total = sum(item.total_price for item in cart_items)

            return JsonResponse({
                'success': True,
                'cart_total': float(cart_total),
                'item_total': float(cart_item.total_price),
                'message': 'Cart updated successfully'
            })

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating the cart'
        }, status=400)



# ------------------------------------------------------------------------------------------------------------

# ----CART DELETION -----------------------------------------------------------------------------------------------------
# ----------transaction-----------------------------------------------------------------------------------------------------------------------
#------actually the stck quantity in models updations is hanlded in methods under model cart so here no need to again add to stock ----------------------
# -------commented code is again adding to stock quantity even its handled in cart model method ---------------------------



# def remove_cart_item(request, item_id):
#     if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
#         try:
#             with transaction.atomic():
#                 # Fetch the cart item
#                 cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
                
#                 # Restore stock if variant exists
#                 if cart_item.variant:
#                     cart_item.variant.stock_quantity += cart_item.quantity
#                     cart_item.variant.save()
                    
#                     cart_item.product.stock_quantity += cart_item.quantity
#                     cart_item.product.save()
                
#                 # Delete the cart item
#                 cart_item.delete()
                
#                 return JsonResponse({"success": True})
        
#         except Exception as e:
#             return JsonResponse({"success": False, "error": str(e)}, status=500)
    
#     return JsonResponse({"success": False, "error": "Invalid request method or not AJAX."}, status=400)

def remove_cart_item(request, item_id):
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
            with transaction.atomic():
                # Fetch and delete the cart item
                # Stock restoration will happen automatically in the delete() method
                cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
                cart_item.delete()
                
                return JsonResponse({"success": True})
        
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    
    return JsonResponse({"success": False, "error": "Invalid request method or not AJAX."}, status=400)
# ------ checkout ------------------------------------------------------------------




# def checkout(request):
#     cart_items = Cart.objects.filter(user=request.user)
#     cart_total = sum(item.product.base_price * item.quantity for item in cart_items)

#     if not request.user.is_authenticated:
#         return redirect('login') 
    
    
#     addresses = Address.objects.filter(user=request.user)

#     return render(request, 'checkout.html', {'addresses': addresses ,
#                                              'cart_total': cart_total,
#                                              'cart_items' : cart_items,
#                                              })

def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    # Calculate cart total before discount
    cart_total = sum(item.total_price for item in cart_items)
    
    # Calculate total discount
    total_discount = sum(item.discount_amount or 0 for item in cart_items)
    
    delivery_charge = 10

    # Calculate final total
    final_total = cart_total - total_discount + delivery_charge

    if not request.user.is_authenticated:
        return redirect('login') 
    
    addresses = Address.objects.filter(user=request.user)

    return render(request, 'checkout.html', {
        'addresses': addresses,
        'cart_total': cart_total,
        'cart_items': cart_items,
        'total_discount': total_discount,
        'final_total': final_total
    })







#------------ order placing    normal working without razorpay ---------------------------------------------------------------
# ----------adding wallet payment ---------------------------------------------------------------------------------------------

from django.views.decorators.csrf import ensure_csrf_cookie


import logging
logger = logging.getLogger(__name__)
@ensure_csrf_cookie


def place_order(request):
    if request.method == "POST":
        user = request.user
        cart_items = Cart.objects.filter(user=user)
        default_address = Address.objects.filter(user=user, is_default=True).first()

        # Validate cart and address
        if not cart_items.exists():
            return JsonResponse({'success': False, 'message': 'Your cart is empty.'})

        if not default_address:
            return JsonResponse({'success': False, 'message': 'Please select a shipping address.'})

        payment_method = request.POST.get("payment_method")
        if not payment_method:
            return JsonResponse({'success': False, 'message': 'Please select a payment method.'})

        cart_total = sum(item.total_price for item in cart_items)
        total_discount = sum(item.discount_amount or 0 for item in cart_items)
        total_price = cart_total - total_discount


        if payment_method == 'COD' and total_price > 1000:
            return JsonResponse({
                'success': False,
                'message': 'Cash on Delivery is not available for orders above ₹1000. Please choose another payment method.',
                'cod_limit_exceeded': True  # Add this flag to handle specific SweetAlert
            })

        # Handle Wallet Payment
        if payment_method == 'Wallet':
            try:
                wallet = Wallet.objects.get(user=user)
                if wallet.balance < total_price:
                    return JsonResponse({
                        'success': False,
                        'message': f'Insufficient wallet balance. Available: ₹{wallet.balance}, Required: ₹{total_price}'
                    })

                # Create order with success payment status
                order = Order.objects.create(
                    user=user,
                    address=default_address,
                    payment_method='WALLET',
                    total_amount=total_price,
                    payment_status='success'
                )

                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price_per_unit=cart_item.product.base_price,
                        total_price=cart_item.product.base_price * cart_item.quantity
                    )

                # Create wallet transaction
                WalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='DEBIT',
                    amount=total_price,
                    payment_method='INTERNAL'
                )

                # Update wallet balance
                wallet.balance -= total_price
                wallet.save()

                # Clear cart
                cart_items.delete()

                return JsonResponse({
                'success': True,
                'message': 'Order placed successfully using wallet balance!',
                'new_balance': wallet.balance
                })
            except Wallet.DoesNotExist:
                logger.error("Wallet not found for user.")
                return JsonResponse({
                'success': False,
                'message': 'Wallet not found for this user.'
                })
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                return JsonResponse({
                    "success": False,
                    "message": "Internal server error"
            }, status=500)

        # Create order for COD
        elif payment_method == 'COD':
            order = Order.objects.create(
                user=user,
                address=default_address,
                payment_method='COD',
                total_amount=total_price,
                payment_status='success'
            )

            # Create order items
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price_per_unit=cart_item.product.base_price,
                    total_price=cart_item.product.base_price * cart_item.quantity
                )

            # Clear cart
            cart_items.delete()

            return JsonResponse({
                'success': True, 
                'message': 'Order placed successfully!',
                'is_cod': True
            })

        # Handle Online Payment
        elif payment_method == 'Online':
            env = environ.Env()
            client = razorpay.Client(
                auth=(env('RAZORPAY_KEY_ID'), env('RAZORPAY_KEY_SECRET'))
            )
            
            order = Order.objects.create(
                user=user,
                address=default_address,
                payment_method='ONLINE',
                total_amount=total_price,
                payment_status='pending'
            )

            razorpay_order = client.order.create({
                'amount': int(total_price * 100),
                'currency': 'INR',
                'receipt': str(order.id),
                'payment_capture': 1
            })

            order.razorpay_order_id = razorpay_order['id']
            order.save()

            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price_per_unit=cart_item.product.base_price,
                    total_price=cart_item.product.base_price * cart_item.quantity
                )

            return JsonResponse({
                'success': True,
                'is_cod': False,
                'razorpay_key': env('RAZORPAY_KEY_ID'),
                'razorpay_order_id': razorpay_order['id'],
                'amount': int(total_price * 100),
                'name': user.username,
                'email': user.email,
                'contact': user.phone_number
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})










# Razorpay Payment Verification View
def verify_payment(request):
    if request.method == "POST":
        try:
            # Get payment details from request
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            # Initialize Razorpay client
            env = environ.Env()
            client = razorpay.Client(
                auth=(env('RAZORPAY_KEY_ID'), env('RAZORPAY_KEY_SECRET'))
            )

            # Verify payment signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            # Verify signature
            try:
                client.utility.verify_payment_signature(params_dict)
                
                # Find the order
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                
                # Mark payment as successful
                order.payment_status = 'success'
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.save()

                # Clear cart items
                Cart.objects.filter(user=request.user).delete()

                return JsonResponse({
                    'success': True,
                    'message': 'Payment successful'
                })

            except Exception as e:
                # Signature verification failed
                return JsonResponse({
                    'success': False,
                    'message': 'Payment verification failed'
                }, status=400)

        except Order.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Order not found'
            }, status=404)

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    }, status=400)






# ----USER ORDER DETAILS-------------------------------------------------------------------------------------------



# @login_required
# def order_details(request):
#     user_orders = Order.objects.filter(user=request.user).order_by('-order_date')
#     context = {
#         'orders': user_orders,
#     }
#     return render(request, 'user_order_details.html', context)




@user_required 
def order_details(request):
    user_orders = Order.objects.filter(
        user=request.user
    ).order_by('-order_date')
    
    # Initialize payment windows
    for order in user_orders:
        if not order.payment_retry_window:
            order.payment_retry_window = order.order_date + timedelta(minutes=10)
            order.save()
    
    return render(request, 'user_order_details.html', {'orders': user_orders})


# @login_required
# def retry_payment(request, order_id):
#     try:
#         order = get_object_or_404(Order, id=order_id, user=request.user)

#         if not order.can_retry_payment():
#             messages.error(request, "Payment retry window has expired")
#             return JsonResponse({
#                 'error': 'Payment retry window has expired'
#             }, status=400)

#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

#         payment_data = {
#             'amount': int(order.total_amount * 100),
#             'currency': 'INR',
#             'receipt': str(order.id)
#         }

#         try:
#             payment = client.order.create(data=payment_data)
#             order.razorpay_order_id = payment['id']
#             order.save()

#             context = {
#                 'order': order.id,
#                 'razorpay_key': settings.RAZORPAY_KEY_ID,
#                 'razorpay_order_id': payment['id'],
#                 'amount': int(order.total_amount * 100),
#                 'success': True
#             }

#             return JsonResponse(context)

#         except razorpay.errors.BadRequestError as e:
#             return JsonResponse({
#                 'error': 'Failed to create Razorpay order',
#                 'details': str(e)
#             }, status=400)

#     except Order.DoesNotExist:
#         return JsonResponse({
#             'error': 'Order not found'
#         }, status=404)

#     except Exception as e:
#         return JsonResponse({
#             'error': 'An unexpected error occurred',
#             'details': str(e)
#         }, status=500)
    



def retry_payment(request, order_id):
    """
    View to handle both payment initialization and verification
    """
    # Get the order or return 404
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "GET":
        # Initialize new payment
        if order.payment_status == 'success':
            return JsonResponse({
                'status': 'error',
                'message': 'Order is already paid'
            }, status=400)

        try:
            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Create new order in Razorpay
            payment_data = {
                'amount': int(order.total_amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'notes': {
                    'order_id': order.id
                }
            }
            
            razorpay_order = client.order.create(data=payment_data)

            # Update order with new Razorpay order ID
            order.razorpay_order_id = razorpay_order['id']
            order.save()

            # Return the necessary data to initialize payment
            return JsonResponse({
                'status': 'success',
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': payment_data['amount'],
                'razorpay_order_id': razorpay_order['id']
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
            
    elif request.method == "POST":
        # Verify payment
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Initialize Razorpay client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # Verify the payment signature
            params_dict = {
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': razorpay_signature
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            # Update order payment details
            order.payment_status = 'success'
            order.razorpay_payment_id = razorpay_payment_id
            order.razorpay_signature = razorpay_signature
            order.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Payment verified successfully',
                'redirect_url': reverse('order_details')
            })
                
        except razorpay.errors.SignatureVerificationError:
            # Mark payment as failed
            order.payment_status = 'failed'
            order.save()
            
            return JsonResponse({
                'status': 'error',
                'message': 'Payment signature verification failed'
            }, status=400)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    }, status=405)

# @login_required
# def single_order_detail(request, order_id):
#     # Fetch the specific order for the user
#     order = get_object_or_404(Order, id=order_id, user=request.user)
#     order_items = order.order_items.prefetch_related('product__images')

#     for item in order_items:
#         item.primary_image = item.product.images.filter(is_primary=True).first()

#     context = {
#         'order': order,
#         'order_items': order_items,
#     }
#     return render(request, 'single_order_details.html', context)



def single_order_detail(request, order_id):
    # Fetch the specific order for the user
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.order_items.select_related('product').prefetch_related('product__images')

    # Add primary image to each order item
    for item in order_items:
        # Retrieve the primary image for the product
        primary_image = item.product.images.filter(is_primary=True).first()
        item.primary_image = primary_image  # Attach it as an attribute for easy template access

    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'single_order_details.html', context)



# --------------------------------------------------------------------------------------------------------------------------


@user_required
@require_POST
def cancel_order_item(request, order_item_id):
    try:
        # Fetch the specific order item
        order_item = OrderItem.objects.get(
            id=order_item_id, 
            order__user=request.user
        )
        
        # Check if the order is still cancellable (e.g., not shipped or delivered)
        if order_item.order.order_status in ['delivered', 'shipped']:
            return JsonResponse({
                'success': False, 
                'message': 'Cannot cancel items in delivered or shipped orders'
            }, status=400)
        
        # Optional: Create a cancellation record or update inventory
        # You might want to add more complex logic here
        
        # Mark the order item as cancelled
        order_item.is_cancelled = True
        order_item.save()
        
        # Recalculate order total
        order_item.order.calculate_total()
        
        return JsonResponse({
            'success': True, 
            'message': 'Product successfully cancelled'
        })
    
    except OrderItem.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Order item not found'
        }, status=404)


# ---------------------------------------------------------------------------------------------------
@login_required
def wishlist(request):
    if request.user.is_authenticated:
        # Get the wishlist items for the logged-in user
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
        context = {
            "wishlist_items": wishlist_items,
            "rating_range": range(5),
        }
        return render(request, "User_wishlist.html", context)
    else:
        # Redirect to login page if user is not authenticated
        return redirect("login")

# ------------------------------------------------------------------------------------------
# Use only if you don't want CSRF token validation (not recommended for production)
def add_to_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)

        product = get_object_or_404(Product, id=product_id)

        # Check if the product is already in the user's wishlist
        wishlist_item, created = Wishlist.objects.get_or_create(user=user, product=product)

        if not created:
            return JsonResponse({"status": "exists", "message": "Product already in wishlist"}, status=400)

        return JsonResponse({"status": "success", "message": "Product added to wishlist"}, status=201)

    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# ----------------------------------------------------------

def delete_wishlist_item(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            item_id = data.get("id")
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)

            wishlist_item = Wishlist.objects.filter(id=item_id, user=request.user).first()
            if wishlist_item:
                wishlist_item.delete()
                return JsonResponse({"status": "success", "message": "Item deleted successfully"})
            else:
                return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
    return JsonResponse({"status": "error", "message": "Invalid request"}, status=400)


# --------------------------------------------------------------------------------------------------------------



from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from decimal import Decimal
# -------------------------------- below working def ------------------------------------
# @login_required
# def wallet(request):
#     # Get the logged-in user's wallet
#     user_wallet = Wallet.objects.filter(user=request.user).first()

#     # Check if the wallet exists; if not, set balance to 0
#     wallet_balance = user_wallet.balance if user_wallet else Decimal('0.00')

#     # Pass the balance to the template
#     return render(request, 'User_wallet.html', {'wallet_balance': wallet_balance})

import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@user_required
def wallet(request):
    user_wallet = Wallet.objects.get_or_create(user=request.user)[0]

    wallet_balance = user_wallet.update_balance()
    
    # Calculate different wallet components
    wallet_balance = user_wallet.balance
    total_refunds = user_wallet.get_total_refunds()
    total_added_funds = user_wallet.get_total_added_funds()


    withdrawal_history = WalletWithdrawal.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10] 

    # Razorpay client setup
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    # Generate Razorpay order for adding funds
    razorpay_order = client.order.create({
        'amount': int(1000),  # Amount in paise (e.g., 1000 paise = 10 INR)
        'currency': 'INR',
        'payment_capture': 1
    })

    context = {
        'wallet_balance': wallet_balance,
        'total_refunds': total_refunds,
        'total_added_funds': total_added_funds,
        'razorpay_order': razorpay_order,
        'razorpay_key': settings.RAZORPAY_KEY_ID,
        'withdrawal_history': withdrawal_history
    }
    
    return render(request, 'User_wallet.html', context)

@csrf_exempt
def verify_razorpay_payment(request):
    if request.method == 'POST':
        try:
            # Determine the input method (JSON or form data)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                payment_id = data.get('razorpay_payment_id')
                order_id = data.get('razorpay_order_id')
                signature = data.get('razorpay_signature')
                amount = data.get('amount')
            else:
                # Fallback to form data
                payment_id = request.POST.get('razorpay_payment_id')
                order_id = request.POST.get('razorpay_order_id')
                signature = request.POST.get('razorpay_signature')
                amount = request.POST.get('amount')

            # Validate required parameters
            if not all([payment_id, order_id, signature, amount]):
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Missing required payment parameters'
                }, status=400)

            # Verify payment details
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
                # Verify payment signature
                client.utility.verify_payment_signature({
                    'razorpay_order_id': order_id,
                    'razorpay_payment_id': payment_id,
                    'razorpay_signature': signature
                })
            except Exception as signature_error:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Payment signature verification failed'
                }, status=400)

            # Fetch the payment details from Razorpay to double-check
            payment_details = client.payment.fetch(payment_id)
            
            # Additional verification
            if payment_details['status'] != 'captured':
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Payment not captured'
                }, status=400)

            # Create wallet transaction
            user_wallet = Wallet.objects.get(user=request.user)
            
            # Convert amount from paise to rupees (assuming amount is in paise)
            amount_in_rupees = Decimal(amount) / 100

            # Check if this payment has already been processed
            if WalletTransaction.objects.filter(
                razorpay_payment_id=payment_id,
                transaction_type='FUND_ADDED'
            ).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Payment already processed'
                }, status=400)

            # Create wallet transaction
            wallet_transaction = WalletTransaction.create_razorpay_fund_transaction(
                wallet=user_wallet, 
                amount=amount_in_rupees,
                razorpay_payment_id=payment_id
            )

            # Update wallet balance
            # user_wallet.balance += wallet_transaction.amount
            # user_wallet.save()

            new_balance = user_wallet.update_balance()

            return JsonResponse({
                'status': 'success', 
                'message': 'Funds added successfully',
                'balance': float(user_wallet.balance)
            })

        except Wallet.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': 'Wallet not found'
            }, status=404)
        
        except Exception as e:
            # Log the full error for debugging
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)



def generate_razorpay_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = int(data.get('amount'))  # Amount in paise
        
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        try:
            razorpay_order = client.order.create({
                'amount': amount,
                'currency': 'INR',
                'payment_capture': 1
            })
            
            return JsonResponse({
                'id': razorpay_order['id'],
                'amount': amount
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
#-------------------------------------------------



from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


@require_POST
def submit_return_request(request):
    try:
        # Get form data
        order_item_id = request.POST.get('order_item_id')
        return_reason = request.POST.get('return_reason')  # Matches the name in HTML form
        return_explanation = request.POST.get('explanation')  # Matches the name in HTML form
        return_proof = request.FILES.get('proof_image')  # Matches the name in HTML form

        # Validate data
        if not order_item_id or not return_reason:
            return JsonResponse({
                'status': 'error', 
                'message': 'Missing required information'
            }, status=400)

        # Fetch the order item
        order_item = OrderItem.objects.get(
            id=order_item_id, 
            order__user=request.user
        )

        # Create return request
        return_request = OrderReturn.objects.create(
            order_item=order_item,
            return_reason=return_reason,  # Correct field name
            return_explanation=return_explanation,  # Correct field name
            return_proof=return_proof,  # Correct field name
            status='REQUESTED'
        )

        return JsonResponse({
            'status': 'success', 
            'message': 'Return request submitted successfully'
        })

    except OrderItem.DoesNotExist:
        return JsonResponse({
            'status': 'error', 
            'message': 'Invalid order item'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)




# ----printing invoice for order details ----------------------------------------------------------

from django.http import HttpResponse
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

# def generate_invoice(request, order_id):
#     try:
#         # Fetch the order details
#         order = Order.objects.get(id=order_id)
#         order_items = order.order_items.all()

#         # Calculate total and any refunds
#         total_product_amount = sum(item.total_price for item in order_items)
#         refunded_amount = sum(item.total_price for item in order_items if item.is_cancelled)
#         remaining_amount = total_product_amount - refunded_amount

#         # Create PDF
#         buffer = BytesIO()
#         p = canvas.Canvas(buffer, pagesize=letter)
#         width, height = letter

#         # Title and Header
#         p.setFont("Helvetica-Bold", 24)
#         p.drawCentredString(width / 2, height - 30, "Vegeefoods")
#         p.setFont("Helvetica-Bold", 14)
#         p.drawCentredString(width / 2, height - 60, f"Invoice for Order-{order_id}")

#         # Customer Info
#         p.setFont("Helvetica", 12)
#         p.drawCentredString(width / 2, height - 80, f"Customer: {order.user.username} ({order.user.phone_number})")
#         p.drawCentredString(width / 2, height - 100, 
#             f"Shipping Address: {order.address.street_address}, {order.address.city}, {order.address.state} - {order.address.postal_code}")

#         # Line Separator
#         p.setLineWidth(1)
#         p.line(50, height - 120, width - 50, height - 120)

#         # Order Items Header
#         y = height - 150
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(100, y, "Product")
#         p.drawString(300, y, "Variant")
#         p.drawString(400, y, "Quantity")
#         p.drawString(500, y, "Price")
#         y -= 20

#         # Order Items
#         p.setFont("Helvetica", 10)
#         for item in order_items:
#             product_name = item.product.name

#             # variant_info = f"({item.variant.display_name})" if item.variant else ""

#             if item.variant:
#                 if item.variant.category == 'WEIGHT':
#                     variant_info = f"{item.variant.get_weight_display()}"
#                 elif item.variant.category == 'VOLUME':
#                     variant_info = f"{item.variant.get_volume_display()}"
#                 else:
#                     variant_info = item.variant.variant_name or "Standard"
#             else:
#                 variant_info = "Standard"


#             p.drawString(100, y, f"{product_name}")
#             p.drawString(300, y, f"{variant_info}")
#             p.drawString(400, y, f"{item.quantity}")
#             p.drawString(500, y, f"₹{item.total_price}")
#             y -= 20

#         # Line Separator
#         p.line(50, y, width - 50, y)
#         y -= 20

#         # Payment Details
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(100, y, "Payment Method:")
#         p.setFont("Helvetica", 12)
#         p.drawString(300, y, f"{order.get_payment_method_display()}")
#         y -= 20

#         # Payment Status
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(100, y, "Payment Status:")
#         p.setFont("Helvetica", 12)
#         p.drawString(300, y, f"{order.get_payment_status_display()}")
#         y -= 20

#         # Total Amount
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(100, y, "Total Amount:")
#         p.setFont("Helvetica", 12)
#         p.drawString(300, y, f"₹{total_product_amount}")
#         y -= 20

#         # Refunded Amount (if any)
#         if refunded_amount > 0:
#             p.setFont("Helvetica-Bold", 12)
#             p.drawString(100, y, "Refunded Amount:")
#             p.setFont("Helvetica", 12)
#             p.drawString(300, y, f"₹{refunded_amount}")
#             y -= 20

#             p.drawString(100, y, "Final Amount:")
#             p.drawString(300, y, f"₹{remaining_amount}")
#             y -= 20

#         # Order Status
#         p.setFont("Helvetica-Bold", 12)
#         p.drawString(100, y, "Order Status:")
#         p.setFont("Helvetica", 12)
#         p.drawString(300, y, f"{order.get_order_status_display()}")
#         y -= 20

#         if order.is_canceled:
#             p.setFont("Helvetica", 12)
#             p.drawString(100, y, f"Canceled on: {order.cancel_date}")
#             p.drawString(100, y - 20, f"Reason: {order.cancel_description}")
#             y -= 40

#         # Footer
#         p.setFont("Helvetica", 10)
#         p.drawCentredString(width / 2, 30, "Thank you for shopping with us!")

#         # Save PDF
#         p.save()
#         buffer.seek(0)

#         # Create the HTTP response with PDF content
#         response = HttpResponse(content_type='application/pdf')
#         response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
#         response.write(buffer.getvalue())
#         buffer.close()

#         return response

#     except Order.DoesNotExist:
#         return HttpResponse('Order not found.', status=404)
#     except Exception as e:
#         return HttpResponse(f'Error generating invoice: {str(e)}', status=500) 



def generate_invoice(request, order_id):
    try:
        # Fetch the order details
        order = Order.objects.get(id=order_id)
        order_items = order.order_items.all()

        # Calculate total and any refunds
        total_product_amount = sum(item.total_price for item in order_items)
        refunded_amount = sum(item.total_price for item in order_items if item.is_cancelled)
        remaining_amount = total_product_amount - refunded_amount

        # Create PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        # Title and Header
        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width / 2, height - 30, "VEGEFOODS")
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width / 2, height - 60, f"Invoice for Order-{order_id}")

        # Customer Info
        p.setFont("Helvetica", 12)
        p.drawCentredString(width / 2, height - 80, f"Customer: {order.user.username} ({order.user.phone_number})")
        p.drawCentredString(width / 2, height - 100, 
            f"Shipping Address: {order.address.street_address}, {order.address.city}, {order.address.state} - {order.address.postal_code}")

        # Line Separator
        p.setLineWidth(1)
        p.line(50, height - 120, width - 50, height - 120)

        # Order Items Header
        y = height - 150
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "Product")
        p.drawString(300, y, "Variant")
        p.drawString(400, y, "Quantity")
        p.drawString(500, y, "Price")
        y -= 20

        # Order Items with fixed variant display
        p.setFont("Helvetica", 10)
        for item in order_items:
            product_name = item.product.name
            
            # Use the display_name property from Variant model
            if item.variant:
                variant_info = item.variant.display_name
            else:
                # Check if product has a default variant
                default_variant = item.product.get_default_variant()
                variant_info = default_variant.display_name if default_variant else "Standard"
            
            # Draw item information
            p.drawString(100, y, f"{product_name}")
            p.drawString(300, y, variant_info)
            p.drawString(400, y, f"{item.quantity}")
            p.drawString(500, y, f"Rs.{item.total_price}")
            y -= 20

        # Line Separator
        p.line(50, y, width - 50, y)
        y -= 20

        # Payment Details
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "Payment Method:")
        p.setFont("Helvetica", 12)
        p.drawString(300, y, f"{order.get_payment_method_display()}")
        y -= 20

        # Payment Status
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "Payment Status:")
        p.setFont("Helvetica", 12)
        p.drawString(300, y, f"{order.get_payment_status_display()}")
        y -= 20

        # Total Amount
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "Total Amount:")
        p.setFont("Helvetica", 12)
        p.drawString(300, y, f"₹{total_product_amount}")
        y -= 20

        # Refunded Amount (if any)
        if refunded_amount > 0:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, y, "Refunded Amount:")
            p.setFont("Helvetica", 12)
            p.drawString(300, y, f"₹{refunded_amount}")
            y -= 20

            p.drawString(100, y, "Final Amount:")
            p.drawString(300, y, f"₹{remaining_amount}")
            y -= 20

        # Order Status
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y, "Order Status:")
        p.setFont("Helvetica", 12)
        p.drawString(300, y, f"{order.get_order_status_display()}")
        y -= 20

        if order.is_canceled:
            p.setFont("Helvetica", 12)
            p.drawString(100, y, f"Canceled on: {order.cancel_date}")
            p.drawString(100, y - 20, f"Reason: {order.cancel_description}")
            y -= 40

        # Footer
        p.setFont("Helvetica", 10)
        p.drawCentredString(width / 2, 30, "Thank you for shopping with us!")

        # Save PDF
        p.save()
        buffer.seek(0)

        # Create the HTTP response with PDF content
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()

        return response

    except Order.DoesNotExist:
        return HttpResponse('Order not found.', status=404)
    except Exception as e:
        return HttpResponse(f'Error generating invoice: {str(e)}', status=500)


# ------ withdrawal ------------------------------------------------------------------



# @login_required
# def request_withdrawal(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             amount = Decimal(data.get('amount'))
#             bank_account = data.get('bank_account')
#             ifsc_code = data.get('ifsc_code')
#             account_holder = data.get('account_holder')

#             # Validate amount
#             if amount <= 0:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Invalid withdrawal amount'
#                 }, status=400)

#             # Get user's wallet
#             wallet = Wallet.objects.get(user=request.user)

#             # Check if user has sufficient balance
#             if wallet.balance < amount:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Insufficient balance'
#                 }, status=400)

#             # Create withdrawal request
#             withdrawal = WalletWithdrawal.objects.create(
#                 user=request.user,
#                 wallet=wallet,
#                 amount=amount,
#                 bank_account_number=bank_account,
#                 bank_ifsc_code=ifsc_code,
#                 account_holder_name=account_holder,
#                 reference_id=f"WD-{uuid.uuid4().hex[:8].upper()}"
#             )

#             # Create corresponding transaction
#             WalletTransaction.objects.create(
#                 wallet=wallet,
#                 transaction_type='DEBIT',
#                 amount=amount,
#                 payment_method='BANK_TRANSFER',
#                 withdrawal=withdrawal
#             )

#             # Update wallet balance
#             wallet.update_balance()

#             return JsonResponse({
#                 'status': 'success',
#                 'message': 'Withdrawal request submitted successfully',
#                 'withdrawal_id': withdrawal.reference_id,
#                 'new_balance': float(wallet.balance)
#             })

#         except Wallet.DoesNotExist:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': 'Wallet not found'
#             }, status=404)
#         except Exception as e:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': str(e)
#             }, status=400)
    
#     elif request.method == 'GET':
#         user_wallet = Wallet.objects.get(user=request.user)
#         withdrawals = WalletWithdrawal.objects.filter(user=request.user).order_by('-created_at')
        
#         context = {
#             'wallet_balance': user_wallet.balance,
#             'withdrawals': withdrawals,
#             'min_withdrawal': 100,  # You can set your minimum withdrawal amount
#             'max_withdrawal': user_wallet.balance  # Maximum they can withdraw is their balance
#         }
        
#         return render(request, 'User_wallet', context)





def request_withdrawal(request):
    return render(request, 'withdraw.html')



# @login_required
# def process_withdrawal(request):
#     if request.method == 'POST':
#         try:
#             amount = Decimal(request.POST.get('amount'))
#             account_holder = request.POST.get('account_holder_name')
#             account_number = request.POST.get('bank_account_number')
#             ifsc_code = request.POST.get('bank_ifsc_code')
#             remarks = request.POST.get('remarks', '')

#             # Get user's wallet
#             wallet = request.user.wallet

#             # Check if amount is valid
#             if amount <= 0:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Invalid withdrawal amount'
#                 })

#             # Check if user has sufficient balance
#             if amount > wallet.balance:
#                 return JsonResponse({
#                     'status': 'error',
#                     'message': 'Insufficient wallet balance'
#                 })

#             # Create withdrawal request
#             withdrawal = WalletWithdrawal.objects.create(
#                 user=request.user,
#                 wallet=wallet,
#                 amount=amount,
#                 bank_account_number=account_number,
#                 bank_ifsc_code=ifsc_code,
#                 account_holder_name=account_holder,
#                 reference_id=str(uuid.uuid4()),
#                 remarks=remarks
#             )

#             # Create wallet transaction
#             WalletTransaction.objects.create(
#                 wallet=wallet,
#                 amount=amount,
#                 transaction_type='DEBIT',
#                 payment_method='BANK_TRANSFER' 
#             )

#             # Update wallet balance
#             wallet.update_balance()

#             return JsonResponse({
#                 'status': 'success',
#                 'message': 'Your withdrawal request has been submitted successfully',
#                 'new_balance': str(wallet.balance)
#             })

#         except Exception as e:
#             return JsonResponse({
#                 'status': 'error',
#                 'message': str(e)
#             })

#     return JsonResponse({
#         'status': 'error',
#         'message': 'Invalid request method'
#     })






import logging

logger = logging.getLogger(__name__)

@user_required
def process_withdrawal(request):
    if request.method == 'POST':
        try:
            # Fetch data from the form
            amount = Decimal(request.POST.get('amount'))
            account_holder = request.POST.get('account_holder_name')
            account_number = request.POST.get('bank_account_number')
            ifsc_code = request.POST.get('bank_ifsc_code')
            remarks = request.POST.get('remarks', '')

            # Validate and process
            wallet = request.user.wallet
            if amount <= 0:
                return JsonResponse({'status': 'error', 'message': 'Invalid withdrawal amount'})
            if amount > wallet.balance:
                return JsonResponse({'status': 'error', 'message': 'Insufficient wallet balance'})

            # Create withdrawal request
            withdrawal = WalletWithdrawal.objects.create(
                user=request.user,
                wallet=wallet,
                amount=amount,
                bank_account_number=account_number,
                bank_ifsc_code=ifsc_code,
                account_holder_name=account_holder,
                reference_id=str(uuid.uuid4()),
                remarks=remarks
            )

            # Create wallet transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='DEBIT',
                payment_method='BANK_TRANSFER'
            )

            # Update wallet balance
            wallet.update_balance()

            return JsonResponse({
                'status': 'success',
                'message': f'Withdrawal of ₹{amount} has been processed successfully.',
                'new_balance': str(wallet.balance),
                'withdrawal_amount': str(amount)
            })

        except Exception as e:
            logger.error(f"Error processing withdrawal: {str(e)}")  # Log the error
            return JsonResponse({'status': 'error', 'message': 'An internal server error occurred.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

















