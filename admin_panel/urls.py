from django.urls import include, path ,re_path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    

    path('admin_in/',views.admin_login, name = 'admin_login'),
    path('admin1/',views.admin_dashboard, name= 'admin1'),
    path('admin_logout/',views.admin_logout,name = 'admin_logout'),
    path('base/',views.base, name = 'base'),
    path('admin_user/',views.admin_user, name = 'admin_user'),
    path('toggle-user-status/<uuid:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('admin_category/',views.admin_category, name = 'admin_category'),
    path('add_category/',views.add_category, name = 'add_category'),
    path('add_submit_category/',views.add_submit_category, name = 'add_submit_category'),
    path('toggle-category-status/<int:category_id>/',views.toggle_category_status, name='toggle_category_status'),
    path('edit-category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('admin_product/',views.admin_product,name = 'admin_product'),
    path('add_product/',views.add_product,name = 'add_product'),
    path('edit_product/<int:pk>/', views.edit_product, name='edit_product'),

    path('admin_order/', views.admin_order, name='admin_order'),
    path('admin_orderdetails/<int:order_id>/', views.admin_orderdetails, name='admin_orderdetails'),

    path('admin_edit_order/<int:order_id>/',views.admin_edit_order,name='admin_edit_order'),
    path('admin_edit_order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
  
    path('edit_order/<int:order_id>/cancel/', views.admin_cancel_order, name='admin_cancel_order'),
    path('coupon/',views.coupons, name= 'coupons'),
    path('coupons/',views.create_coupon, name='create_coupon'),
    path('update-coupon/', views.update_coupon, name='update_coupon'),
    path('edit-coupon/<int:coupon_id>/', views.edit_coupon, name='edit_coupon'),
    path('delete-coupon/', views.delete_coupon, name='delete_coupon'),
    path('return-requests/<int:order_id>/', views.admin_return_requests, name='admin_return_requests'),
    path('process-return-request/<int:return_request_id>/', views.process_return_request, name='process_return_request'),
    path('offer/', views.offer , name = 'offer'),
    # path('edit_offer/', views.edit_offer, name='edit_offer'),
    # path('delete_offer/', views.delete_offer, name='delete_offer'),
    # path('edit_offer/<int:offer_id>/', views.edit_offer, name='edit_offer'),
    path('report/', views.report, name ='report'),
    path('generate-sales-report/', views.generate_sales_report, name='generate_sales_report'),
    path('download-sales-report/', views.download_sales_report, name='download_sales_report'),



    path('add-product-offer/<int:product_id>/', views.add_product_offer, name='add_product_offer'),
    path('edit-product-offer/<int:offer_id>/', views.edit_product_offer, name='edit_product_offer'),
    path('delete-product-offer/', views.delete_product_offer, name='delete_product_offer'),
    path('category/<int:category_id>/add_offer/', views.add_offer_to_category, name='add_offer_to_category'),
    path('offer/<int:offer_id>/edit/', views.edit_offer_for_category, name='edit_offer_for_category'),
    path('offer/<int:offer_id>/delete/', views.delete_offer_for_category, name='delete_offer_for_category'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

