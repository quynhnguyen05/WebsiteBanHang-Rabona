from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('tai-khoan/', views.cap_nhat_tai_khoan, name='cap_nhat_tai_khoan'),
    path('don-hang/', views.quan_ly_don_hang, name='don_hang'),
    path('don-hang/hoa-don/<str:order_code>/', views.xuat_hoa_don, name='xuat_hoa_don'),
    path('tra-hang/', views.tra_hang, name='tra_hang'),
    path('cap-nhat-trang-thai-tra/', views.cap_nhat_trang_thai_tra, name='cap_nhat_trang_thai_tra'),
    path('san-pham/', views.quan_ly_san_pham, name='san_pham'),
    path('san-pham/them/', views.them_san_pham, name='them_san_pham'),
    path('san-pham/sua/<int:pk>/', views.sua_san_pham, name='sua_san_pham'),
    path('san-pham/xoa/<int:pk>/', views.xoa_san_pham, name='xoa_san_pham'),
    path('khach-hang/', views.ds_khach_hang, name='khach_hang'),
    path('doanh-thu/', views.bao_cao_doanh_thu, name='doanh_thu'),
    path('phi-ship/', views.quan_ly_phi_ship, name='phi_ship'),
    path('phi-ship/luu/', views.ajax_luu_phi_ship, name='luu_phi_ship'),
    path('phi-ship/xoa/<int:pk>/', views.ajax_xoa_phi_ship, name='xoa_phi_ship'),
]
