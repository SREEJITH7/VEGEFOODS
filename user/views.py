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
from datetime import timedelta, timezone
from admin_panel.models import Product, ProductImage ,Catogery ,Variant,CouponTable, CouponUsage , Offer
from django.utils.timezone import now
from datetime import datetime
from .decorators import user_required
from .forms import AddressForm
from .models import Address
from .models import Cart,Order, OrderItem , Wishlist , OrderReturn, Wallet, WalletTransaction, WalletWithdrawal, OrderAddress
import json
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth import update_session_auth_hash
import environ
import razorpay
from django.utils import timezone
# Create your views here.



def beforelogin(request):
    return render(request, 'beforeloginpage.html')




##################################################################################################################################################




def index(request):
    
    if request.user.is_authenticated:
        logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_superuser:
                messages.error(request, "Superuser accounts are not allowed to log in here.")
                return redirect('login')  

            login(request, user)
            return redirect('welcome')  
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

# @user_required
# @login_required
# def welcome(request):
#     response = render(request, 'welcome.html')
#     response['Cache-Control'] = 'no-chache, no-store, must-revalidate'
#     response['Pragma'] = 'no-cache, no-store, must-revalifate'
#     response['Expries'] = '0'
#     return response

@user_required
@login_required
def welcome(request):
    
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()
    
    
    response = render(request, 'welcome.html', {
        'cart_count': cart_count
    })
    
    
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache, no-store, must-revalidate'  
    response['Expires'] = '0'  
    
    return response

##################################################################################################################################################
 

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
                print(f"Email error: {str(e)}")  
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
                
                del request.session['form_data']
                del request.session['email_otp']
                return redirect('login')
            else:
                messages.error(request, "There was an error saving your data.")
        else:
            messages.error(request,"invalid OTP.Please try again.")
    return render(request, 'verify_otp.html')        



##################################################################################################################################################


def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, 'You have successfully logged out')
    return redirect('login')


##################################################################################################################################################


def resend_otp(request):
    if request.method == "POST":
        
        otp = random.randint(100000, 999999)
        request.session['email_otp'] = otp
        
        
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
    
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()

        
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
    
    
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )
    
    
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')
    
    
    for product in products:
        
        product_offer_discount = 0
        category_offer_discount = 0
        
        
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        
        category_offers = active_category_offers.filter(category=product.catogery)
        
        
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )
    

        
        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)

    
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  
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
        'total_products': products.count() if paginate else products.count(),
        'cart_count': cart_count
    })



##### shop vegetables  ###########################################################################################################################################################

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def shopvegetables(request):
    search_query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', '')

    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()

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



    
    vegetable_category = Catogery.objects.filter(name__iexact="Vegetables").first()
    
    
    products = Product.objects.filter(
        catogery=vegetable_category, 
        is_delete=False
    ).prefetch_related(
        Prefetch('images', queryset=ProductImage.objects.all(), to_attr='all_images'),
        Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')  
    )

     
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    
    if search_query:
        products = products.filter(name__icontains=search_query)

      
    for product in products:
        
        product_offer_discount = 0
        category_offer_discount = 0
        
        
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        
        category_offers = active_category_offers.filter(category=product.catogery)
        
        
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)


    
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  
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
        'total_products': products.count() if paginate else products.count(),
        'cart_count': cart_count
    })

##### shop fruits  ###########################################################################################################################################################


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def shopfruits(request):
    search_query = request.GET.get('q', '')
    sort_option = request.GET.get('sort', '')
    
    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()

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

     
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    
    if search_query:
        products = products.filter(name__icontains=search_query)


    
    for product in products:
        
        product_offer_discount = 0
        category_offer_discount = 0
        
        
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        
        category_offers = active_category_offers.filter(category=product.catogery)
        
        
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)



    
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  
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
        'total_products': products.count() if paginate else products.count(),
        'cart_count': cart_count
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

    
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    
    if search_query:
        products = products.filter(name__icontains=search_query)


    
    for product in products:
        
        product_offer_discount = 0
        category_offer_discount = 0
        
        
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        
        category_offers = active_category_offers.filter(category=product.catogery)
        
        
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)



    
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  
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

    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()

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

    
    active_category_offers = Offer.objects.filter(
        is_active=True, 
        offer_type='CATEGORY'
    )

    
    if sort_option == 'price_asc':
        products = products.order_by('base_price')
    elif sort_option == 'price_desc':
        products = products.order_by('-base_price')
    elif sort_option == 'name_asc':
        products = products.order_by('name')
    elif sort_option == 'name_desc':
        products = products.order_by('-name')

    
    if search_query:
        products = products.filter(name__icontains=search_query)


    
    for product in products:
        
        product_offer_discount = 0
        category_offer_discount = 0
        
        
        if product.active_product_offer:
            product_offer_discount = product.active_product_offer[0].discount_percentage
        
        
        category_offers = active_category_offers.filter(category=product.catogery)
        
        
        valid_category_offers = [
            offer for offer in category_offers 
            if offer.category == product.catogery
        ]
        
        if valid_category_offers:
            category_offer_discount = max(
                offer.discount_percentage for offer in valid_category_offers
            )
        
        
        product.final_discount = max(
            product.discount_percentage or 0, 
            product_offer_discount,
            category_offer_discount
        )

        product.final_price = product.base_price - (product.base_price * product.final_discount / 100)




    
    paginate = products.count() > 16
    if paginate:
        paginator = Paginator(products, 16)  
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
        'total_products': products.count() if paginate else products.count(),
        'cart_count': cart_count
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

    cart_count = 0
    if request.user.is_authenticated:
        cart_count = Cart.objects.filter(user=request.user).count()


    product = get_object_or_404(
        Product.objects.prefetch_related(
            'images',
            Prefetch('offers', queryset=Offer.objects.filter(is_active=True), to_attr='active_product_offer')
        ),
        id=product_id,
        is_delete=False
    )

    active_category_offers = Offer.objects.filter(
        is_active=True,
        offer_type='CATEGORY'
    )

    product_offer_discount = 0
    category_offer_discount = 0

    if hasattr(product, 'active_product_offer') and product.active_product_offer:
        product_offer_discount = product.active_product_offer[0].discount_percentage

    category_offers = active_category_offers.filter(category=product.catogery)
    
    valid_category_offers = [
        offer for offer in category_offers 
        if offer.category == product.catogery
    ]

    if valid_category_offers:
        category_offer_discount = max(
            offer.discount_percentage for offer in valid_category_offers
        )

    product.final_discount = max(
        product.discount_percentage or 0,
        product_offer_discount,
        category_offer_discount
    )

    product.final_price = product.base_price - (product.base_price * product.final_discount / 100)

    category_name = product.catogery.name.lower()
    if category_name in ['vegetables', 'fruits', 'dried']:
        size_options = ['0.1kg', '0.5kg', '1kg', '1.5kg', '2kg']
    elif category_name == 'juice':
        size_options = ['0.5 liter', '1 liter']
    else:
        size_options = ['Small', 'Medium', 'Large', 'Extra Large']

    main_image = product.images.filter(is_primary=True).first() or product.images.first()

    related_products = Product.objects.filter(
        catogery=product.catogery,
        is_delete=False
    ).exclude(id=product_id).prefetch_related('images')[:4]

    variants = product.variants.all()

    selected_variant = variants.first() if variants.exists() else None

    return render(request, 'singleproduct.html', {
        'product': product,
        'related_products': related_products,
        'main_image': main_image,
        'size_options': size_options,
        'variants': variants,
        'selected_variant': selected_variant,
        'cart_count': cart_count
    })





from django.contrib import messages
from django.utils.timezone import now

import random

def send_otp_via_email(email, otp):
    print(f"OTP sent to {email}: {otp}")  


# -----------------------------------------------------------------



def forgotpassword(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = CustomUser.objects.filter(email=email).first()
        if user:
            otp = random.randint(1000, 9999)
            
            request.session['reset_otp'] = otp
            request.session['reset_otp_expiration'] = (now() + timedelta(seconds=20)).isoformat()
            request.session['reset_email'] = email
            
            send_otp_via_email(email, otp)
            messages.success(request, "OTP sent successfully!")
            return redirect("validate_email", email=email)
        else:
            messages.error(request, "Email not registered!")

    return render(request, "forgotpassword.html")

def validate_email(request, email):
    session_email = request.session.get('reset_email')
    session_otp = request.session.get('reset_otp')
    session_otp_expiration = request.session.get('reset_otp_expiration')
    
    if not session_email or session_email != email:
        messages.error(request, "Invalid email!")
        return redirect('forgotpassword')
    
    if request.method == "POST":
        entered_otp = request.POST.get('otp')
        
        if session_otp == int(entered_otp):
            otp_expiration = datetime.fromisoformat(session_otp_expiration)
            if otp_expiration > now():
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

        user.password = make_password(new_password)
        user.save()

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
        user = request.user  

        first_name = request.POST.get('firstName', '').strip()
        last_name = request.POST.get('lastName', '').strip()
        username = request.POST.get('UserName', '').strip()
        email = request.POST.get('email', '').strip()
        phone_number = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirmPassword', '').strip()

        changes_made = False

        if password:
            if password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return redirect('profile')
            
            user.set_password(password)
            changes_made = True

        if first_name and first_name != user.first_name:
            user.first_name = first_name
            changes_made = True
        
        if last_name and last_name != user.last_name:
            user.last_name = last_name
            changes_made = True
        
        if username and username != user.username:
            if User.objects.exclude(pk=user.pk).filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect('profile')
            user.username = username
            changes_made = True
        
        if email and email != user.email:
            if User.objects.exclude(pk=user.pk).filter(email=email).exists():
                messages.error(request, "Email already in use.")
                return redirect('profile')
            user.email = email
            changes_made = True
        
        if phone_number and phone_number != getattr(user, 'phone_number', ''):
            user.phone_number = phone_number
            changes_made = True

        if changes_made:
            user.save()

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
    
    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    
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

# -----------------------------------------------------------------------------------------
import logging
import traceback
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods




def calculate_best_discount(product, variant_price):
    """Calculate the best applicable discount for a product."""
    today = timezone.now().date()


    logger.debug(f"""
    Calculating discount for:
    Product ID: {product.id}
    Product Name: {product.name}
    Base Price: {variant_price}
    Current Date: {today}
    """)
    
    variant_price = Decimal(str(variant_price))
    
    base_discount = Decimal(str(product.discount_percentage or '0'))
    
    product_offer_discount = Decimal('0')
    product_offers = Offer.objects.filter(
        product=product,
        offer_type='PRODUCT',
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )

    logger.debug(f"""
    Found Product Offers:
    Count: {product_offers.count()}
    Offers: {[(offer.id, offer.discount_percentage, offer.start_date, offer.end_date) for offer in product_offers]}
    """)

    if product_offers.exists():
        product_offer_discount = Decimal(str(max(offer.discount_percentage for offer in product_offers)))
    
    category_offer_discount = Decimal('0')
    category_offers = Offer.objects.filter(
        category=product.catogery,
        offer_type='CATEGORY',
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    )
    if category_offers.exists():
        category_offer_discount = Decimal(str(max(offer.discount_percentage for offer in category_offers)))
    
    best_discount_percentage = max(base_discount, product_offer_discount, category_offer_discount)
    
    if best_discount_percentage > 0:
        discount_amount = (variant_price * best_discount_percentage) / Decimal('100')
        
        if best_discount_percentage == base_discount:
            discount_type = 'Product Discount'
        elif best_discount_percentage == product_offer_discount:
            discount_type = 'Product Offer'
        else:
            discount_type = 'Category Offer'
            
        return {
            'type': discount_type,
            'percentage': float(best_discount_percentage),  
            'amount': float(discount_amount)  
        }
    
    return None




# -------------------new cart view-- coupon prob solved ---------------------


@user_required
@require_http_methods(["GET", "POST"])
def cart(request):
    logger.debug("Starting cart view")
    try:
        if request.method == 'POST':
            coupon_code = request.POST.get('coupon_code')
            
            if coupon_code:
                try:
                    coupon = CouponTable.objects.get(code=coupon_code, is_active=True)
                    cart_items = Cart.objects.select_related(
                        'product', 
                        'variant', 
                        'product__catogery'
                    ).filter(user=request.user)
                    
                    temp_subtotal = Decimal('0')
                    
                    logger.debug("Initial cart state:")
                    for item in cart_items:
                        base_price = item.variant.variant_price if item.variant else item.product.base_price
                        best_discount = calculate_best_discount(item.product, base_price)
                        item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
                        
                        actual_price = base_price - item_discount
                        item_total = actual_price * item.quantity
                        temp_subtotal += item_total
                        
                        logger.debug(f"""
                        Item: {item.product.name}
                        Base price: {base_price}
                        Existing discount: {item_discount}
                        Price after discount: {actual_price}
                        Quantity: {item.quantity}
                        Item total: {item_total}
                        Running subtotal: {temp_subtotal}
                        """)
                    
                    if coupon.max_uses is None or coupon.max_uses > 0:
                        if temp_subtotal >= coupon.min_purchase_amount:
                            if coupon.coupon_type == 'percentage':
                                discount_amount = round(temp_subtotal * (Decimal(str(coupon.discount_value)) / Decimal('100')), 2)
                            else:
                                discount_amount = round(min(Decimal(str(coupon.discount_value)), temp_subtotal), 2)
                            
                            logger.debug(f"Calculated coupon discount: {discount_amount}")
                            
                            if cart_items.exists():
                                discount_per_item = round(discount_amount / len(cart_items), 2)
                                for item in cart_items:
                                    item.applied_coupon = coupon
                                    item.discount_amount = discount_per_item
                                    item.save()
                                    logger.debug(f"Applied discount per item: {discount_per_item} to {item.product.name}")

                            CouponUsage.objects.create(
                                user=request.user,
                                coupon=coupon,
                                discount_value=discount_amount
                            )

                            if coupon.max_uses is not None:
                                coupon.max_uses -= 1
                                coupon.save()

                            delivery_charge = Decimal('10')
                            final_subtotal = temp_subtotal - discount_amount
                            final_total = final_subtotal + delivery_charge

                            logger.debug(f"""
                            Final calculation breakdown:
                            Original subtotal: {temp_subtotal}
                            Coupon discount: {discount_amount}
                            After discount: {final_subtotal}
                            Delivery charge: {delivery_charge}
                            Final total: {final_total}
                            """)

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

        Cart.objects.filter(user=request.user).update(applied_coupon=None, discount_amount=0)

        cart_items = Cart.objects.select_related(
            'product', 
            'variant', 
            'product__catogery'
        ).filter(user=request.user)
        
        formatted_cart_items = []
        cart_subtotal = Decimal('0')
        total_discount = Decimal('0')
        coupon_discount = Decimal('0')
        
        logger.debug("Processing GET request - calculating cart totals")
        
        for item in cart_items:
            item_price = item.variant.variant_price if item.variant else item.product.base_price
            
            best_discount = calculate_best_discount(item.product, item_price)
            item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
            
            coupon_discount_per_item = Decimal(str(item.discount_amount)) if item.applied_coupon else Decimal('0')
            
            discounted_price = item_price - item_discount - coupon_discount_per_item
            item_total = discounted_price * item.quantity

            logger.debug(f"""
            Cart item calculation:
            Item: {item.product.name}
            Base price: {item_price}
            Product discount: {item_discount}
            Coupon discount: {coupon_discount_per_item}
            Final price: {discounted_price}
            Quantity: {item.quantity}
            Item total: {item_total}
            """)
            
            variant_display = ''
            if item.variant:
                if item.product.category.name.lower() in ['vegetables', 'fruits', 'dried']:
                    variant_display = f"{item.variant.weight} kg"
                elif item.product.category.name.lower() == 'juice':
                    variant_display = f"{item.variant.volume} liter" if item.variant.volume else ''
                else:
                    variant_display = item.variant.weight or ''
            
            cart_subtotal += item_total
            total_discount += (item_discount * item.quantity)
            coupon_discount += (coupon_discount_per_item * item.quantity)
            
            formatted_item = {
                'cart_item': item,
                'variant_display': variant_display,
                'original_price': float(item_price),
                'discount_info': best_discount,
                'coupon_discount': float(coupon_discount_per_item),
                'discounted_price': float(discounted_price),
                'item_total': float(item_total),
                'item_discount': float(item_discount)
            }
            formatted_cart_items.append(formatted_item)

        delivery_charge = Decimal('10')
        cart_total = cart_subtotal + delivery_charge
        cart_empty = not cart_items.exists()

        logger.debug(f"""
        Final cart totals:
        Subtotal: {cart_subtotal}
        Total discount: {total_discount}
        Coupon discount: {coupon_discount}
        Delivery charge: {delivery_charge}
        Final total: {cart_total}
        """)

        context = {
            'cart_items': formatted_cart_items,
            'cart_subtotal': float(cart_subtotal),
            'delivery_charge': float(delivery_charge),
            'cart_total': float(cart_total),
            'total_discount': float(total_discount),
            'coupon_discount': float(coupon_discount),
            'cart_empty': cart_empty,
        }
        
        return render(request, 'cart.html', context)

    except Exception as e:
        logger.error(f"Error in cart view: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})








# --------add to cart ajax new for varient ---------------------------------------------------------------------------------------






# ----------above code is working for single productpage --------------------------------------------------------------------------------------------------------
# -----------------------------recently comnted know to transaction--------------------------------------------






from django.db import transaction
from django.core.exceptions import ValidationError



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

        cart_item = Cart.objects.filter(
            user=request.user,
            product=product,
            variant=variant
        ).first()

        try:
            if cart_item:
                cart_item.quantity += quantity
                cart_item.save()
            else:
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






@login_required
@transaction.atomic
def update_cart_quantity_ajax(request, cart_id):
    try:
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        
        if quantity < 1:
            return JsonResponse({
                'success': False,
                'message': 'Quantity must be at least 1'
            }, status=400)

        cart_item = get_object_or_404(Cart, id=cart_id, user=request.user)
        
        cart_item.quantity = quantity
        cart_item.save()

        item_price = cart_item.variant.variant_price if cart_item.variant else cart_item.product.base_price
        
        best_discount = calculate_best_discount(cart_item.product, item_price)
        item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
        
        coupon_discount = Decimal(str(cart_item.discount_amount)) if cart_item.applied_coupon else Decimal('0')
        
        discounted_price = item_price - item_discount - coupon_discount
        item_total = discounted_price * quantity

        cart_items = Cart.objects.filter(user=request.user)
        cart_subtotal = sum(
            (item.variant.variant_price if item.variant else item.product.base_price) * item.quantity
            for item in cart_items
        )
        total_discount = Decimal('0')
        coupon_discount = Decimal('0')
        
        for item in cart_items:
            item_price = item.variant.variant_price if item.variant else item.product.base_price
            best_disc = calculate_best_discount(item.product, item_price)
            if best_disc:
                total_discount += Decimal(str(best_disc['amount'])) * item.quantity
            if item.applied_coupon:
                coupon_discount += item.discount_amount * item.quantity

        delivery_charge = Decimal('10')
        cart_total = cart_subtotal - total_discount - coupon_discount + delivery_charge

        return JsonResponse({
            'success': True,
            'item_total': float(item_total),
            'original_price': float(item_price),
            'discounted_price': float(discounted_price),
            'cart_subtotal': float(cart_subtotal),
            'cart_total': float(cart_total),
            'total_discount': float(total_discount),
            'coupon_discount': float(coupon_discount),
            'message': 'Cart updated successfully'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating the cart'
        }, status=400)

# ------------------------------------------------------------------------------------------------------------

# ----CART DELETION -----------------------------------------------------------------------------------------------------


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






# --------------new checkout page view ---------------




@user_required
def checkout(request):
    try:
        if not request.user.is_authenticated:
            return redirect('login')
            
        cart_items = Cart.objects.select_related(
            'product', 
            'variant', 
            'product__catogery',
            'applied_coupon'
        ).filter(user=request.user)
        
        temp_subtotal = Decimal('0')
        total_product_discount = Decimal('0')
        
        logger.debug("Starting checkout calculations")
        
        formatted_cart_items = []
        for item in cart_items:
            item_price = item.variant.variant_price if item.variant else item.product.base_price
            
            best_discount = calculate_best_discount(item.product, item_price)
            item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
            
            price_after_product_discount = item_price - item_discount
            item_subtotal = price_after_product_discount * item.quantity
            
            temp_subtotal += item_subtotal
            total_product_discount += (item_discount * item.quantity)
            
            logger.debug(f"""
            Initial item calculation:
            Item: {item.product.name}
            Base price: {item_price}
            Product discount: {item_discount}
            Price after product discount: {price_after_product_discount}
            Item subtotal: {item_subtotal}
            Running subtotal: {temp_subtotal}
            """)
        
        coupon_discount = Decimal('0')
        if any(item.applied_coupon for item in cart_items):
            coupon = cart_items.first().applied_coupon
            if coupon.coupon_type == 'percentage':
                coupon_discount = round(temp_subtotal * (Decimal(str(coupon.discount_value)) / Decimal('100')), 2)
            else:
                coupon_discount = round(min(Decimal(str(coupon.discount_value)), temp_subtotal), 2)
            
            logger.debug(f"Calculated coupon discount: {coupon_discount}")
        
        delivery_charge = Decimal('10')
        cart_subtotal = temp_subtotal - coupon_discount
        final_total = cart_subtotal + delivery_charge
        
        logger.debug(f"""
        Final checkout calculations:
        Initial subtotal: {temp_subtotal}
        Total product discounts: {total_product_discount}
        Coupon discount: {coupon_discount}
        Final subtotal: {cart_subtotal}
        Delivery charge: {delivery_charge}
        Final total: {final_total}
        """)
        
        formatted_cart_items = []
        coupon_discount_per_item = Decimal('0')
        if cart_items.exists() and coupon_discount > 0:
            coupon_discount_per_item = round(coupon_discount / len(cart_items), 2)
        
        for item in cart_items:
            item_price = item.variant.variant_price if item.variant else item.product.base_price
            best_discount = calculate_best_discount(item.product, item_price)
            item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
            
            discounted_price = item_price - item_discount - coupon_discount_per_item
            item_total = discounted_price * item.quantity
            
            formatted_cart_items.append({
                'cart_item': item,
                'original_price': float(item_price),
                'discount_info': best_discount,
                'coupon_discount': float(coupon_discount_per_item),
                'discounted_price': float(discounted_price),
                'item_total': float(item_total)
            })
        
        addresses = Address.objects.filter(user=request.user)
        
        context = {
            'addresses': addresses,
            'cart_items': formatted_cart_items,
            'cart_subtotal': float(cart_subtotal),
            'total_discount': float(total_product_discount),
            'coupon_discount': float(coupon_discount),
            'delivery_charge': float(delivery_charge),
            'final_total': float(final_total)
        }
        
        return render(request, 'checkout.html', context)
        
    except Exception as e:
        logger.error(f"Error in checkout view: {traceback.format_exc()}")
        messages.error(request, f"An error occurred during checkout: {str(e)}")
        return redirect('cart')


#------------ order placing    normal working without razorpay ---------------------------------------------------------------
# ----------adding wallet payment ---------------------------------------------------------------------------------------------

from django.views.decorators.csrf import ensure_csrf_cookie


import logging
logger = logging.getLogger(__name__)
@ensure_csrf_cookie






# ---------new place order-----------------


@user_required
def place_order(request):
    if request.method == "POST":
        try:
            user = request.user
            cart_items = Cart.objects.select_related(
                'product', 
                'variant', 
                'product__catogery',
                'applied_coupon'
            ).filter(user=user)
            default_address = Address.objects.filter(user=user, is_default=True).first()

            if not cart_items.exists():
                return JsonResponse({'success': False, 'message': 'Your cart is empty.'})

            if not default_address:
                return JsonResponse({'success': False, 'message': 'Please select a shipping address.'})

            payment_method = request.POST.get("payment_method")
            if not payment_method:
                return JsonResponse({'success': False, 'message': 'Please select a payment method.'})

            temp_subtotal = Decimal('0')
            total_product_discount = Decimal('0')
            
            order_items_data = []
            for item in cart_items:
                item_price = item.variant.variant_price if item.variant else item.product.base_price
                
                best_discount = calculate_best_discount(item.product, item_price)
                item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
                
                price_after_product_discount = item_price - item_discount
                item_subtotal = price_after_product_discount * item.quantity
                
                temp_subtotal += item_subtotal
                total_product_discount += (item_discount * item.quantity)

            coupon_discount = Decimal('0')
            applied_coupon = None
            if any(item.applied_coupon for item in cart_items):
                applied_coupon = cart_items.first().applied_coupon
                if applied_coupon.coupon_type == 'percentage':
                    coupon_discount = round(temp_subtotal * (Decimal(str(applied_coupon.discount_value)) / Decimal('100')), 2)
                else:
                    coupon_discount = round(min(Decimal(str(applied_coupon.discount_value)), temp_subtotal), 2)

            delivery_charge = Decimal('10')
            cart_subtotal = temp_subtotal - coupon_discount
            final_total = cart_subtotal + delivery_charge

            coupon_discount_per_item = Decimal('0')
            if cart_items.exists() and coupon_discount > 0:
                coupon_discount_per_item = round(coupon_discount / len(cart_items), 2)

            order_items_data = []
            for item in cart_items:
                item_price = item.variant.variant_price if item.variant else item.product.base_price
                best_discount = calculate_best_discount(item.product, item_price)
                item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
                
                final_price_per_unit = item_price - item_discount - coupon_discount_per_item
                item_total = final_price_per_unit * item.quantity
                
                order_items_data.append({
                    'product': item.product,
                    'variant': item.variant,
                    'quantity': item.quantity,
                    'price_per_unit': float(final_price_per_unit),
                    'total_price': float(item_total)
                })

            if payment_method == 'COD' and final_total > 1000:
                return JsonResponse({
                    'success': False,
                    'message': 'Cash on Delivery is not available for orders above ₹1000. Please choose another payment method.',
                    'cod_limit_exceeded': True
                })

            if payment_method == 'Wallet':
                try:
                    wallet = Wallet.objects.get(user=user)
                    if wallet.balance < final_total:
                        return JsonResponse({
                            'success': False,
                            'message': f'Insufficient wallet balance. Available: ₹{wallet.balance}, Required: ₹{final_total}'
                        })

                    order = Order.objects.create(
                        user=user,
                        address=default_address,
                        payment_method='WALLET',
                        total_amount=final_total,
                        payment_status='success',
                        applied_coupon=applied_coupon,
                        coupon_discount=coupon_discount
                    )
                    
                    OrderAddress.create_from_address(order, default_address)

                    for item_data in order_items_data:
                        OrderItem.objects.create(
                            order=order,
                            product=item_data['product'],
                            variant=item_data['variant'],
                            quantity=item_data['quantity'],
                            price_per_unit=item_data['price_per_unit'],
                            total_price=item_data['total_price']
                        )

                    WalletTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='DEBIT',
                        amount=final_total,
                        payment_method='INTERNAL'
                    )

                    wallet.balance -= final_total
                    wallet.save()

                    cart_items.delete()

                    return JsonResponse({
                        'success': True,
                        'message': 'Order placed successfully using wallet balance!',
                        'new_balance': float(wallet.balance)
                    })

                except Wallet.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': 'Wallet not found for this user.'
                    })

            elif payment_method == 'COD':
                order = Order.objects.create(
                    user=user,
                    address=default_address,
                    payment_method='COD',
                    total_amount=final_total,
                    payment_status='success',
                    applied_coupon=applied_coupon,
                    coupon_discount=coupon_discount
                )

                OrderAddress.create_from_address(order, default_address)

                for item_data in order_items_data:
                    OrderItem.objects.create(
                        order=order,
                        product=item_data['product'],
                        variant=item_data['variant'],
                        quantity=item_data['quantity'],
                        price_per_unit=item_data['price_per_unit'],
                        total_price=item_data['total_price']
                    )

                cart_items.delete()

                return JsonResponse({
                    'success': True,
                    'message': 'Order placed successfully!',
                    'is_cod': True
                })

            elif payment_method == 'Online':
                env = environ.Env()
                client = razorpay.Client(
                    auth=(env('RAZORPAY_KEY_ID'), env('RAZORPAY_KEY_SECRET'))
                )
                
                order = Order.objects.create(
                    user=user,
                    address=default_address,
                    payment_method='ONLINE',
                    total_amount=final_total,
                    payment_status='pending',
                    applied_coupon=applied_coupon,
                    coupon_discount=coupon_discount
                )

                OrderAddress.create_from_address(order, default_address)

                razorpay_order = client.order.create({
                    'amount': int(final_total * 100),
                    'currency': 'INR',
                    'receipt': str(order.id),
                    'payment_capture': 1
                })

                order.razorpay_order_id = razorpay_order['id']
                order.save()

                for item_data in order_items_data:
                    OrderItem.objects.create(
                        order=order,
                        product=item_data['product'],
                        variant=item_data['variant'],
                        quantity=item_data['quantity'],
                        price_per_unit=item_data['price_per_unit'],
                        total_price=item_data['total_price']
                    )

                return JsonResponse({
                    'success': True,
                    'is_cod': False,
                    'razorpay_key': env('RAZORPAY_KEY_ID'),
                    'razorpay_order_id': razorpay_order['id'],
                    'amount': int(final_total * 100),
                    'name': user.username,
                    'email': user.email,
                    'contact': user.phone_number
                })

        except Exception as e:
            logger.error(f"Error in place_order: {traceback.format_exc()}")
            return JsonResponse({
                'success': False,
                'message': f'An error occurred while processing your order: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def verify_payment(request):
    if request.method == "POST":
        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            env = environ.Env()
            client = razorpay.Client(
                auth=(env('RAZORPAY_KEY_ID'), env('RAZORPAY_KEY_SECRET'))
            )

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            try:
                client.utility.verify_payment_signature(params_dict)
                
                order = Order.objects.get(razorpay_order_id=razorpay_order_id)
                
                order.payment_status = 'success'
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.save()

                Cart.objects.filter(user=request.user).delete()

                return JsonResponse({
                    'success': True,
                    'message': 'Payment successful'
                })

            except Exception as e:
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



@user_required 
def order_details(request):
    user_orders = Order.objects.filter(
        user=request.user
    ).order_by('-order_date')
    
    for order in user_orders:
        if not order.payment_retry_window:
            order.payment_retry_window = order.order_date + timedelta(minutes=10)
            order.save()
    
    return render(request, 'user_order_details.html', {'orders': user_orders})



    



def retry_payment(request, order_id):
    """
    View to handle both payment initialization and verification
    """
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == "GET":
        if order.payment_status == 'success':
            return JsonResponse({
                'status': 'error',
                'message': 'Order is already paid'
            }, status=400)

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            payment_data = {
                'amount': int(order.total_amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': f'order_{order.id}',
                'notes': {
                    'order_id': order.id
                }
            }
            
            razorpay_order = client.order.create(data=payment_data)

            order.razorpay_order_id = razorpay_order['id']
            order.save()

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
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            params_dict = {
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_order_id': razorpay_order_id,
                'razorpay_signature': razorpay_signature
            }
            
            client.utility.verify_payment_signature(params_dict)
            
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




def single_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.order_items.select_related('product').prefetch_related('product__images')

    for item in order_items:
        primary_image = item.product.images.filter(is_primary=True).first()
        item.primary_image = primary_image  

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
        order_item = OrderItem.objects.select_related(
            'order', 
            'product', 
            'variant',
            'order__user'
        ).get(
            id=order_item_id, 
            order__user=request.user
        )
        
       
        if order_item.order.order_status in ['delivered', 'shipped']:
            return JsonResponse({
                'success': False, 
                'message': 'Cannot cancel items in delivered or shipped orders'
            }, status=400)
            
       
        if order_item.is_cancelled:
            return JsonResponse({
                'success': False, 
                'message': 'This item is already cancelled'
            }, status=400)

        
        with transaction.atomic():
            
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            
            refund_amount = order_item.total_price + 10
            
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='REFUND',
                amount=refund_amount,
                payment_method='INTERNAL'
            )
            
            wallet.balance += refund_amount
            wallet.save()
            
            order_item.is_cancelled = True
            order_item.save()
            
            order = order_item.order
            order.calculate_total()
            
            if not order.order_items.filter(is_cancelled=False).exists():
                order.order_status = 'cancelled'
                order.is_canceled = True
                order.cancel_date = timezone.now()
                order.save()
            
            order_item.product.stock_quantity += order_item.quantity
            order_item.product.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Product cancelled successfully and amount refunded to wallet',
            'refund_amount': float(refund_amount),
            'new_wallet_balance': float(wallet.balance)
        })
    
    except OrderItem.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Order item not found'
        }, status=404)
        
    except Exception as e:
        logger.error(f"Error in cancel_order_item: {traceback.format_exc()}")
        return JsonResponse({
            'success': False, 
            'message': f'An error occurred while cancelling the order item: {str(e)}'
        }, status=500)

# ---------------------------------------------------------------------------------------------------
@login_required
def wishlist(request):
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
        context = {
            "wishlist_items": wishlist_items,
            "rating_range": range(5),
        }
        return render(request, "User_wishlist.html", context)
    else:
        return redirect("login")

# ------------------------------------------------------------------------------------------

def add_to_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        user = request.user

        if not user.is_authenticated:
            return JsonResponse({"status": "error", "message": "User not authenticated"}, status=401)

        product = get_object_or_404(Product, id=product_id)

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

import razorpay
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@user_required
def wallet(request):
    user_wallet = Wallet.objects.get_or_create(user=request.user)[0]

    wallet_balance = user_wallet.update_balance()
    
    wallet_balance = user_wallet.balance
    total_refunds = user_wallet.get_total_refunds()
    total_added_funds = user_wallet.get_total_added_funds()


    withdrawal_history = WalletWithdrawal.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10] 

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    razorpay_order = client.order.create({
        'amount': int(1000),  
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
            
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                payment_id = data.get('razorpay_payment_id')
                order_id = data.get('razorpay_order_id')
                signature = data.get('razorpay_signature')
                amount = data.get('amount')
            else:
                payment_id = request.POST.get('razorpay_payment_id')
                order_id = request.POST.get('razorpay_order_id')
                signature = request.POST.get('razorpay_signature')
                amount = request.POST.get('amount')

            if not all([payment_id, order_id, signature, amount]):
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Missing required payment parameters'
                }, status=400)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            try:
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

            payment_details = client.payment.fetch(payment_id)
            
            if payment_details['status'] != 'captured':
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Payment not captured'
                }, status=400)

            user_wallet = Wallet.objects.get(user=request.user)
            
            amount_in_rupees = Decimal(amount) / 100

            if WalletTransaction.objects.filter(
                razorpay_payment_id=payment_id,
                transaction_type='FUND_ADDED'
            ).exists():
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Payment already processed'
                }, status=400)

            wallet_transaction = WalletTransaction.create_razorpay_fund_transaction(
                wallet=user_wallet, 
                amount=amount_in_rupees,
                razorpay_payment_id=payment_id
            )

           

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
            import traceback
            traceback.print_exc()
            
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=400)



def generate_razorpay_order(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = int(data.get('amount')) 
        
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
        order_item_id = request.POST.get('order_item_id')
        return_reason = request.POST.get('return_reason')  
        return_explanation = request.POST.get('explanation')  
        return_proof = request.FILES.get('proof_image') 

        if not order_item_id or not return_reason:
            return JsonResponse({
                'status': 'error', 
                'message': 'Missing required information'
            }, status=400)

        order_item = OrderItem.objects.get(
            id=order_item_id, 
            order__user=request.user
        )

        return_request = OrderReturn.objects.create(
            order_item=order_item,
            return_reason=return_reason,  
            return_explanation=return_explanation,  
            return_proof=return_proof,  
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












@user_required
def generate_invoice(request, order_id):
    try:
        order = Order.objects.select_related('user', 'shipping_address').get(id=order_id)
        order_items = order.order_items.select_related('product', 'variant', 'product__catogery').all()

        cart_subtotal = Decimal('0')
        total_discount = Decimal('0')
        
        item_details = []
        for item in order_items:
            item_price = item.variant.variant_price if item.variant else item.product.base_price
            
            best_discount = calculate_best_discount(item.product, item_price)
            item_discount = Decimal(str(best_discount['amount'])) if best_discount else Decimal('0')
            
            discounted_price = item_price - item_discount
            item_total = discounted_price * item.quantity
            
            cart_subtotal += item_total
            total_discount += (item_discount * item.quantity)
            
            item_details.append({
                'item': item,
                'original_price': item_price,
                'discounted_price': discounted_price,
                'total': item_total,
                'discount': item_discount * item.quantity
            })

        delivery_charge = Decimal('10')
        final_total = cart_subtotal + delivery_charge

        refunded_amount = sum(
            detail['total'] for detail in item_details 
            if detail['item'].is_cancelled
        )
        remaining_amount = final_total - refunded_amount

        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter

        p.setFont("Helvetica-Bold", 24)
        p.drawCentredString(width / 2, height - 30, "VEGEFOODS")
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(width / 2, height - 60, f"Invoice for Order-{order_id}")

        p.setFont("Helvetica", 12)
        shipping_address = order.shipping_address
        
        p.drawCentredString(width / 2, height - 80, 
            f"Customer: {shipping_address.full_name} ({shipping_address.phone_number})")

        line1_parts = [
            shipping_address.street_address,
            shipping_address.apartment_suite,
            shipping_address.landmark
        ]
        line1 = ', '.join(filter(None, line1_parts))

        line2_parts = [
            shipping_address.city,
            shipping_address.state,
            shipping_address.postal_code
        ]
        line2 = ', '.join(filter(None, line2_parts))

        p.drawCentredString(width / 2, height - 100, f"Shipping Address:")
        p.drawCentredString(width / 2, height - 120, line1)
        p.drawCentredString(width / 2, height - 140, line2)

        p.line(50, height - 160, width - 50, height - 160)

        y = height - 190
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Product")
        p.drawString(200, y, "Variant")
        p.drawString(300, y, "Qty")
        p.drawString(350, y, "Price")
        p.drawString(420, y, "Discount")
        p.drawString(500, y, "Total")
        y -= 20

        p.setFont("Helvetica", 10)
        for detail in item_details:
            item = detail['item']
            product_name = item.product.name
            
            if item.variant:
                variant_info = item.variant.display_name
            else:
                default_variant = item.product.get_default_variant()
                variant_info = default_variant.display_name if default_variant else "Standard"
            
            p.drawString(50, y, f"{product_name}")
            p.drawString(200, y, variant_info)
            p.drawString(300, y, f"{item.quantity}")
            p.drawString(350, y, f"₹{detail['original_price']:.2f}")
            p.drawString(420, y, f"₹{detail['discount']:.2f}")
            p.drawString(500, y, f"₹{detail['total']:.2f}")
            y -= 20

        p.line(50, y, width - 50, y)
        y -= 20

        p.setFont("Helvetica-Bold", 12)
        p.drawString(300, y, "Order Summary")
        y -= 20

        p.setFont("Helvetica", 12)
        p.drawString(300, y, "Subtotal:")
        p.drawString(500, y, f"₹{cart_subtotal:.2f}")
        y -= 20

        if total_discount > 0:
            p.drawString(300, y, "Total Discount:")
            p.drawString(500, y, f"₹{total_discount:.2f}")
            y -= 20

        p.drawString(300, y, "Delivery Charge:")
        p.drawString(500, y, f"₹{delivery_charge:.2f}")
        y -= 20

        p.setFont("Helvetica-Bold", 12)
        p.drawString(300, y, "Total Amount:")
        p.drawString(500, y, f"₹{final_total:.2f}")
        y -= 20

        if refunded_amount > 0:
            p.setFont("Helvetica", 12)
            p.drawString(300, y, "Refunded Amount:")
            p.drawString(500, y, f"₹{refunded_amount:.2f}")
            y -= 20

            p.setFont("Helvetica-Bold", 12)
            p.drawString(300, y, "Final Amount:")
            p.drawString(500, y, f"₹{remaining_amount:.2f}")
            y -= 20

        y -= 20
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Payment Details")
        y -= 20
        
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"Payment Method: {order.get_payment_method_display()}")
        y -= 20
        p.drawString(50, y, f"Payment Status: {order.get_payment_status_display()}")
        y -= 20
        p.drawString(50, y, f"Order Status: {order.get_order_status_display()}")

        if order.is_canceled:
            y -= 20
            p.drawString(50, y, f"Canceled on: {order.cancel_date}")
            y -= 20
            p.drawString(50, y, f"Reason: {order.cancel_description}")

        
        p.setFont("Helvetica", 10)
        p.drawCentredString(width / 2, 30, "Thank you for shopping with us!")

        p.save()
        buffer.seek(0)

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{order_id}.pdf"'
        response.write(buffer.getvalue())
        buffer.close()

        return response

    except Order.DoesNotExist:
        return HttpResponse('Order not found.', status=404)
    except Exception as e:
        logger.error(f"Error generating invoice: {traceback.format_exc()}")
        return HttpResponse(f'Error generating invoice: {str(e)}', status=500)

# ------ withdrawal ------------------------------------------------------------------








def request_withdrawal(request):
    return render(request, 'withdraw.html')







@user_required
def process_withdrawal(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            account_holder = request.POST.get('account_holder_name')
            account_number = request.POST.get('bank_account_number')
            ifsc_code = request.POST.get('bank_ifsc_code')
            remarks = request.POST.get('remarks', '')

            wallet = request.user.wallet
            if amount <= 0:
                return JsonResponse({'status': 'error', 'message': 'Invalid withdrawal amount'})
            if amount > wallet.balance:
                return JsonResponse({'status': 'error', 'message': 'Insufficient wallet balance'})

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

            WalletTransaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type='DEBIT',
                payment_method='BANK_TRANSFER'
            )

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

















