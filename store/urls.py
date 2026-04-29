from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    # Trang chủ
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),

    # Sản phẩm
    path('products/', views.product_list, name='product_list'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),

    # Giỏ hàng
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/json/', views.cart_json, name='cart_json'),
    path('cart/add/<int:variant_id>/', views.cart_add, name='cart_add'),
    path('cart/update/<int:item_id>/', views.cart_update, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove, name='cart_remove'),

    # Thanh toán
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/set-items/', views.set_checkout_items, name='set_checkout_items'),
    path('checkout/place/', views.place_order, name='place_order'),
    path('orders/<str:order_code>/cancel/', views.cancel_order, name='cancel_order'),

    # Đơn hàng
    path('orders/', views.order_list, name='order_list'),
    path('orders/<str:order_code>/', views.order_detail, name='order_detail'),
    path('orders/<str:order_code>/return/', views.return_request, name='return_request'),

    # Hồ sơ
    path('profile/', views.profile, name='profile'),
    path('profile/address/', views.address_manage, name='address_manage'),
]
