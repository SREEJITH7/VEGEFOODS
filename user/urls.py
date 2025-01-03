from django.urls import include, path ,re_path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('',views.beforelogin, name='beforelogin'),
    path('login/',views.index, name='login'),
    path('custom-logout/', views.custom_logout, name='logout'),
    path('registration/',views.registrationPage, name='signup'),
    path('verify_otp/',views.verify_otp ,name='verify_otp'),
    path('welcome/',views.welcome,name= 'welcome'),
    path('logout/',views.logout_view, name='logout'),
    path('resend_otp/',views.resend_otp, name = 'resend_otp'),
    path('shopsection/',views.shopsection, name = 'shopsection'),
    path('shopvegetables/',views.shopvegetables,name='shopvegetables'),
    path('shopfruits/',views.shopfruits,name = 'shopfruits'),
    path('shopjuice/',views.shopjuice, name= 'shopjuice'),
    path('shopdried/',views.shopdried, name= 'shopdried'),
    path('product/<int:product_id>/', views.product_details,name= 'product_details'),
    path('accounts/', include('allauth.urls')),
    path('forgotpassword/',views.forgotpassword, name= 'forgotpassword'),
    path('validate_email/<str:email>/',views.validate_email, name = 'validate_email'),
    path('enter_new_password/', views.enter_new_password, name='enter_new_password'),
    path('profile/',views.profile, name = 'profile'),
    path('update_profile/',views.update_profile, name = 'update_profile'),
    path('addressbook/',views.addressbook,name = 'addressbook'),
    path('add_address/', views.add_address, name='add_address'),
    path('set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('edit_address/<int:address_id>/', views.edit_address, name='edit_address'),
    path('cart/', views.cart, name='cart'),
    path('ajax/add-to-cart/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
    path('cart/update/<int:cart_id>/', views.update_cart_quantity_ajax, name='update_cart_quantity_ajax'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='cart_remove'),
    path('checkout',views.checkout, name = 'checkout'),
    path('place-order/', views.place_order, name='place_order'),
    path('order-details/', views.order_details, name='order_details'),

    path('order/<int:order_id>/retry-payment/', views.retry_payment, name='retry_payment'),
    # path('payment/verify/', views.verify_payment, name='verify_payment'),

    path('orders/<int:order_id>/', views.single_order_detail, name='single_order_detail'),
    path('cancel-order-item/<int:order_item_id>/', views.cancel_order_item, name='cancel_order_item'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path("add-to-wishlist/", views.add_to_wishlist, name="add_to_wishlist"),
    path("delete-wishlist-item/", views.delete_wishlist_item, name="delete_wishlist_item"),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('wallet/', views.wallet , name = 'wallet'),
    path('submit-return-request/', views.submit_return_request, name='submit_return_request'),
    path('wallet/verify-payment/', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('wallet/generate-order/', views.generate_razorpay_order, name='generate_razorpay_order'),
    


    path('generate-invoice/<int:order_id>/', views.generate_invoice, name='generate_invoice'),

    path('wallet/withdraw/', views.request_withdrawal, name='request_withdrawal'),
    path('withdraw/process/', views.process_withdrawal, name='process_withdrawal'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


