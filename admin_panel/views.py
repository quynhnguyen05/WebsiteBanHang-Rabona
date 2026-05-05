from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Sum, Count, Avg, Q, Prefetch, FloatField, DecimalField
from django.db.models.functions import TruncDate, Coalesce
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json


from store.models import (
   Product, ProductVariant, Category,
   Order, OrderItem, ReturnRequest,
   Cart, CartItem, Address, UserProfile,
   PhiVanChuyen,
)




def admin_required(view_func):
    """Decorator: chỉ cho phép staff/superuser."""
    @login_required(login_url='/login/')
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('store:home')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── CẬP NHẬT TÀI KHOẢN ADMIN ───────────────────────────────

@admin_required
def cap_nhat_tai_khoan(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        profile_obj.full_name = full_name
        profile_obj.phone = phone
        if 'avatar' in request.FILES:
            profile_obj.avatar = request.FILES['avatar']
        profile_obj.save()
        request.user.email = email
        request.user.save()
        from django.contrib import messages
        messages.success(request, 'Cập nhật thông tin tài khoản thành công!')
        return redirect('admin_panel:cap_nhat_tai_khoan')
    return render(request, 'admin_panel/cap_nhat_tai_khoan.html', {
        'profile': profile_obj,
    })


# ─── DASHBOARD ───────────────────────────────────────────────

@admin_required
def dashboard(request):
    tong_don = Order.objects.count()
    doanh_thu = Order.objects.filter(status__in=['delivered', 'completed']).aggregate(
        total=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField())
    )['total']
    dang_giao = Order.objects.filter(status='shipping').count()
    don_moi = Order.objects.order_by('-created_at')[:10]
    tong_sp = Product.objects.count()
    tong_kh = User.objects.filter(is_staff=False).count()



# ─── QUẢN LÝ ĐƠN HÀNG ───────────────────────────────────────

@admin_required
def quan_ly_don_hang(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order = Order.objects.get(order_code=data['order_code'])
            if order.status in ['delivered', 'completed']:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Không thể thay đổi trạng thái đơn hàng đã giao hoặc đã hoàn thành.'
                })
            order.status = data['status']
            order.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    trang_thai = request.GET.get('trang_thai', 'Tat_ca')
    search = request.GET.get('q', '')
    orders_qs = Order.objects.order_by('-created_at')

    if search:
        orders_qs = orders_qs.filter(
            Q(order_code__icontains=search) |
            Q(recipient_name__icontains=search)
        )

    if trang_thai != 'Tat_ca' and trang_thai:
        status_map = {
            'Chờ xác nhận': 'pending',
            'Đang chuẩn bị': 'confirmed',
            'Đang giao': 'shipping',
            'Đã giao': 'delivered',
            'Trả hàng': 'returning',
            'Đã trả hàng': 'returned',
            'Đã hủy': 'cancelled',
        }
        status_code = status_map.get(trang_thai, trang_thai)
        orders_qs = orders_qs.filter(status=status_code)

    status_display = {
        'pending': 'Chờ xác nhận',
        'confirmed': 'Đang chuẩn bị',
        'shipping': 'Đang giao',
        'delivered': 'Đã giao',
        'completed': 'Hoàn thành',
        'cancelled': 'Đã hủy',
        'returning': 'Trả hàng',
        'returned': 'Đã trả hàng',
    }

    page_number = request.GET.get('page', 1)
    paginator = Paginator(orders_qs, 15)
    danh_sach_don = paginator.get_page(page_number)
    custom_page_range = paginator.get_elided_page_range(page_number, on_each_side=2, on_ends=1)

    return render(request, 'admin_panel/quan_ly_don_hang.html', {
        'danh_sach_don': danh_sach_don,
        'custom_page_range': custom_page_range,
        'trang_thai_hien_tai': trang_thai,
        'search': search,
        'tong_don_hang': Order.objects.count(),
        'doanh_thu': Order.objects.filter(
            status__in=['delivered', 'completed']
        ).aggregate(total=Sum('total'))['total'] or 0,
        'don_dang_giao': Order.objects.filter(status='shipping').count(),
        'status_display': status_display,
    })


@admin_required
def xuat_hoa_don(request, order_code):
   order = get_object_or_404(Order, order_code=order_code)
   return render(request, 'admin_panel/hoa_don.html', {
       'order': order,
       'today': timezone.now(),
   })




# ─── 1. XỬ LÝ YÊU CẦU TRẢ HÀNG (CSKH - Duyệt/Từ chối) ────────────────────────

@admin_required
def tra_hang(request):
   if request.method == 'POST':
       try:
           data = json.loads(request.body)
           rr = ReturnRequest.objects.select_related('order').get(id=data.get('id'))
           new_status = data.get('status')

            if new_status == 'approved':
                order = rr.order
                shop_faults = ['defective', 'wrong_item', 'damaged', 'late']
                refund_val = data.get('refund_amount')
                if refund_val and str(refund_val).strip() != '':
                    rr.refund_amount = float(refund_val)
                else:
                    if rr.reason in shop_faults:
                        rr.refund_amount = order.total
                    else:
                        calculated_refund = order.subtotal - order.shipping_fee
                        rr.refund_amount = max(0, calculated_refund)
                order.status = 'returning'
                order.save()
                rr.save()

            elif new_status == 'rejected':
                rr.admin_note = f"Lý do từ chối: {data.get('ly_do_tu_choi', '').strip()}"
                rr.order.status = 'delivered'
                rr.order.save()

               # Ưu tiên lấy số tiền Admin tự điều chỉnh trên giao diện
               refund_val = data.get('refund_amount')
               if refund_val and str(refund_val).strip() != '':
                   rr.refund_amount = float(refund_val)
               else:
                   # Nếu Admin không chỉnh, lấy theo logic hệ thống mặc định (2 chiều)
                   if rr.reason in shop_faults:
                       rr.refund_amount = order.total
                   else:
                       calculated_refund = order.subtotal - order.shipping_fee
                       rr.refund_amount = max(0, calculated_refund)  # Giới hạn mức thấp nhất là 0


               order.status = 'returning'
               order.save()
               rr.save()
           elif new_status == 'rejected':
               rr.admin_note = f"Lý do từ chối: {data.get('ly_do_tu_choi', '').strip()}"
               rr.order.status = 'delivered'
               rr.order.save()


           rr.status = new_status
           rr.save()
           return JsonResponse({'status': 'success'})
       except Exception as e:
           return JsonResponse({'status': 'error', 'message': str(e)})


    status_filter = request.GET.get('status', 'pending')
    search_query = request.GET.get('q', '').strip()

    qs = ReturnRequest.objects.select_related('order').filter(
        status__in=['pending', 'rejected']
    ).order_by('-created_at')

    if search_query:
        clean_query = search_query.replace('#', '')
        qs = qs.filter(
            Q(id__icontains=clean_query) |
            Q(order__order_code__icontains=clean_query) |
            Q(order__recipient_name__icontains=search_query)
        )

    cho_duyet_count = qs.filter(status='pending').count()
    tu_choi_count = qs.filter(status='rejected').count()

    if search_query:
        if status_filter == 'pending' and cho_duyet_count == 0 and tu_choi_count > 0:
            status_filter = 'rejected'
        elif status_filter == 'rejected' and tu_choi_count == 0 and cho_duyet_count > 0:
            status_filter = 'pending'

    qs = qs.filter(status=status_filter)

   # 4. Tính toán số liệu (Stats) dựa trên kết quả đã tìm kiếm
   cho_duyet_count = qs.filter(status='pending').count()
   tu_choi_count = qs.filter(status='rejected').count()


   # --- 5. LOGIC TỰ ĐỘNG CHUYỂN TAB THÔNG MINH ---
   if search_query:
       if status_filter == 'pending' and cho_duyet_count == 0 and tu_choi_count > 0:
           status_filter = 'rejected'
       elif status_filter == 'rejected' and tu_choi_count == 0 and cho_duyet_count > 0:
           status_filter = 'pending'


   # 6. Lọc lại QuerySet theo Tab cuối cùng sau khi đã kiểm tra
   qs = qs.filter(status=status_filter)


   stats = {
       'tong_yeu_cau': cho_duyet_count + tu_choi_count,
       'cho_duyet': cho_duyet_count,
       'tu_choi': tu_choi_count,
   }


   paginator = Paginator(qs, 15)
   paginator = Paginator(qs, 15)
   page_number = request.GET.get('page', 1)
   page_obj = paginator.get_page(page_number)


   # TẠO DÃY TRANG CÓ DẤU "..."
   # on_each_side: số trang hiện ra bên cạnh trang hiện tại
   # on_ends: số trang hiện ra ở 2 đầu (trang 1 và trang cuối)
   custom_page_range = paginator.get_elided_page_range(
       page_number,
       on_each_side=2,
       on_ends=1
   )


   return render(request, 'admin_panel/xu_ly_yeu_cau.html', {
       'phieu_list': page_obj,
       'custom_page_range': custom_page_range,  # Truyền dãy trang mới này vào HTML
       'current_status': status_filter,
       'stats': stats,
       'search': search_query,
   })

    paginator = Paginator(qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    custom_page_range = paginator.get_elided_page_range(page_number, on_each_side=2, on_ends=1)

    return render(request, 'admin_panel/xu_ly_yeu_cau.html', {
        'phieu_list': page_obj,
        'custom_page_range': custom_page_range,
        'current_status': status_filter,
        'stats': stats,
        'search': search_query,
    })


# ─── 2. CẬP NHẬT TRẠNG THÁI TRẢ HÀNG (KHO & KẾ TOÁN) ────────────────────────

@admin_required
def cap_nhat_trang_thai_tra(request):
    if request.method == 'POST':
        try:
            if request.content_type and 'multipart/form-data' in request.content_type:
                rr_id = request.POST.get('id')
                new_status = request.POST.get('status')
                refund_amount = request.POST.get('refund_amount')
                final_note = request.POST.get('final_note')
            else:
                data = json.loads(request.body)
                rr_id = data.get('id')
                new_status = data.get('status')
                refund_amount = data.get('refund_amount')
                final_note = data.get('final_note')

            rr = ReturnRequest.objects.select_related('order').get(id=rr_id)

            if new_status == 'completed':
                if 'refund_proof' in request.FILES:
                    rr.refund_proof = request.FILES['refund_proof']
                if refund_amount is not None and str(refund_amount).strip() != '':
                    rr.refund_amount = float(refund_amount)
                if final_note is not None and str(final_note).strip() != '':
                    rr.admin_note = str(final_note).strip()
                order = rr.order
                order.status = 'returned'
                order.save()
                for item in order.items.all():
                    if item.variant:
                        item.variant.stock += item.quantity
                        item.variant.save()

            elif new_status in ['picking', 'returning_to_warehouse', 'received', 'processing']:
                rr.order.status = 'returning'
                rr.order.save()

            rr.status = new_status
            rr.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    status_filter = request.GET.get('status', 'processing_all')
    search_query = request.GET.get('q', '').strip()
    sub_status = request.GET.get('sub_status', '').strip()

    valid_statuses = ['approved', 'picking', 'returning_to_warehouse', 'received', 'processing', 'completed']
    qs = ReturnRequest.objects.select_related('order').filter(
        status__in=valid_statuses
    ).order_by('-created_at')

    if search_query:
        clean_query = search_query.replace('#', '')
        qs = qs.filter(
            Q(id__icontains=clean_query) |
            Q(order__order_code__icontains=clean_query) |
            Q(order__recipient_name__icontains=search_query)
        )

    dang_xu_ly_count = qs.filter(
        status__in=['approved', 'picking', 'returning_to_warehouse', 'received', 'processing']
    ).count()
    da_hoan_tien_count = qs.filter(status='completed').count()

    if search_query and not sub_status:
        if status_filter == 'processing_all' and dang_xu_ly_count == 0 and da_hoan_tien_count > 0:
            status_filter = 'completed'
        elif status_filter == 'completed' and da_hoan_tien_count == 0 and dang_xu_ly_count > 0:
            status_filter = 'processing_all'

    if sub_status:
        qs = qs.filter(status=sub_status)
    else:
        if status_filter == 'completed':
            qs = qs.filter(status='completed')
        else:
            qs = qs.filter(status__in=['approved', 'picking', 'returning_to_warehouse', 'received', 'processing'])

    sub_status_choices = [
        ('approved', 'Đã duyệt'),
        ('picking', 'Chờ lấy hàng'),
        ('returning_to_warehouse', 'Đang về kho'),
        ('received', 'Đã nhận hàng'),
        ('processing', 'Đang xử lý'),
    ]

    page_number = request.GET.get('page', 1)
    paginator = Paginator(qs, 15)
    custom_page_range = paginator.get_elided_page_range(page_number, on_each_side=2, on_ends=1)

    return render(request, 'admin_panel/cap_nhat_tra_hang.html', {
        'phieu_list': paginator.get_page(page_number),
        'custom_page_range': custom_page_range,
        'current_status': status_filter,
        'current_sub_status': sub_status,
        'stats': {'dang_xu_ly': dang_xu_ly_count, 'da_hoan_tien': da_hoan_tien_count},
        'search': search_query,
        'sub_status_choices': sub_status_choices,
    })


# ─── QUẢN LÝ SẢN PHẨM ───────────────────────────────────────

@admin_required
def quan_ly_san_pham(request):
   qs = Product.objects.prefetch_related('variants').order_by('-id')
   search = request.GET.get('q', '')
   status_filter = request.GET.get('status', 'all')
   category_filter = request.GET.get('category', 'all')


    if status_filter == 'in_stock':
        qs = qs.filter(variants__stock__gt=0).distinct()
    elif status_filter == 'out_of_stock':
        from django.db.models import Sum
        qs = qs.annotate(tong_kho=Sum('variants__stock')).filter(
            Q(tong_kho=0) | Q(tong_kho__isnull=True)
        )

    if category_filter != 'all':
        qs = qs.filter(category__slug=category_filter)

   # Lọc theo trạng thái
   if status_filter == 'in_stock':
       qs = qs.filter(variants__stock__gt=0).distinct()
   elif status_filter == 'out_of_stock':
       # Sản phẩm mà tất cả biến thể đều hết hàng (hoặc không có biến thể)
       from django.db.models import Sum
       qs = qs.annotate(tong_kho=Sum('variants__stock')).filter(
           Q(tong_kho=0) | Q(tong_kho__isnull=True)
       )


   # Lọc theo danh mục
   if category_filter != 'all':
       qs = qs.filter(category__slug=category_filter)


   paginator = Paginator(qs, 15)
   products = paginator.get_page(request.GET.get('page'))


   # Đếm số lượng sản phẩm theo trạng thái tồn kho
   from django.db.models import Sum
   all_products = Product.objects.annotate(tong_kho=Sum('variants__stock'))
   stats = {
       'tong': Product.objects.count(),
       'con_hang': all_products.filter(tong_kho__gt=0).count(),
       'het_hang': all_products.filter(Q(tong_kho=0) | Q(tong_kho__isnull=True)).count(),
   }
   categories = Category.objects.all()
   return render(request, 'admin_panel/quan_ly_san_pham.html', {
       'danh_sach_san_pham': products,
       'tong_san_pham': stats['tong'],
       'dang_kinh_doanh': stats['con_hang'],
       'het_hang': stats['het_hang'],
       'categories': categories,
       'filter_status': status_filter,
       'filter_category': category_filter,
       'search': search,
   })


    from django.db.models import Sum
    all_products = Product.objects.annotate(tong_kho=Sum('variants__stock'))
    stats = {
        'tong': Product.objects.count(),
        'con_hang': all_products.filter(tong_kho__gt=0).count(),
        'het_hang': all_products.filter(Q(tong_kho=0) | Q(tong_kho__isnull=True)).count(),
    }
    categories = Category.objects.all()

    return render(request, 'admin_panel/quan_ly_san_pham.html', {
        'danh_sach_san_pham': products,
        'tong_san_pham': stats['tong'],
        'dang_kinh_doanh': stats['con_hang'],
        'het_hang': stats['het_hang'],
        'categories': categories,
        'filter_status': status_filter,
        'filter_category': category_filter,
        'search': search,
    })


@admin_required
def them_san_pham(request):
    if request.method == 'POST':
        try:
            from django.utils.text import slugify
            import time
            danh_muc = request.POST.get('danhMuc', '').strip()
            cat = None
            if danh_muc:
                slug_cat = slugify(danh_muc) or f'cat-{int(time.time())}'
                cat, _ = Category.objects.get_or_create(
                    name=danh_muc,
                    defaults={'slug': slug_cat}
                )
            ten_sp = request.POST.get('tenSP', '')
            prices = request.POST.getlist('giaBan[]')
            gia = prices[0] if prices else 0
            slug_sp = slugify(ten_sp) + f'-{int(time.time())}'
            sp = Product.objects.create(
                name=ten_sp,
                description=request.POST.get('moTa', ''),
                price=gia or 0,
                category=cat,
                is_active=True,
                slug=slug_sp,
            )
            if 'image' in request.FILES:
                sp.image = request.FILES['image']
                sp.save()
            sizes = request.POST.getlist('kichCo[]')
            colors = request.POST.getlist('mauSac[]')
            stocks = request.POST.getlist('soLuongTon[]')
            for i in range(len(sizes)):
                if sizes[i]:
                    ProductVariant.objects.create(
                        product=sp,
                        size=sizes[i],
                        color_name=colors[i] if i < len(colors) else 'Mặc định',
                        color_hex='#000000',
                        stock=int(stocks[i]) if i < len(stocks) and stocks[i] else 0,
                    )
            return JsonResponse({'status': 'success', 'id': sp.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'}, status=405)


@admin_required
def sua_san_pham(request, pk):
    sp = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            sp.name = request.POST.get('tenSP', sp.name)
            sp.description = request.POST.get('moTa', sp.description)
            price = request.POST.get('price')
            if price:
                sp.price = price
            if 'image' in request.FILES:
                sp.image = request.FILES['image']
            sp.save()

            list_variant_ids = request.POST.getlist('variant_id[]')
            existing_variants = sp.variants.all()
            for ev in existing_variants:
                if str(ev.id) not in list_variant_ids:
                    ev.delete()
                else:
                    ev.size = request.POST.get(f'kichCo_{ev.id}', ev.size)
                    ev.color_name = request.POST.get(f'mauSac_{ev.id}', ev.color_name)
                    stock_val = request.POST.get(f'soLuongTon_{ev.id}')
                    ev.stock = int(stock_val) if stock_val else 0
                    ev.save()

            new_sizes = request.POST.getlist('new_kichCo[]')
            new_colors = request.POST.getlist('new_mauSac[]')
            new_stocks = request.POST.getlist('new_soLuongTon[]')
            for i in range(len(new_sizes)):
                if new_sizes[i].strip():
                    ProductVariant.objects.create(
                        product=sp,
                        size=new_sizes[i],
                        color_name=new_colors[i] if i < len(new_colors) else 'Mặc định',
                        color_hex='#000000',
                        stock=int(new_stocks[i]) if i < len(new_stocks) and new_stocks[i] else 0,
                    )
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'}, status=405)


@admin_required
def xoa_san_pham(request, pk):
   if request.method == 'POST':
       get_object_or_404(Product, pk=pk).delete()
       return JsonResponse({'status': 'success'})
   return JsonResponse({'status': 'error'}, status=405)




# ─── DANH SÁCH KHÁCH HÀNG ────────────────────────────────────

@admin_required
def ds_khach_hang(request):
    search = request.GET.get('q', '')
    qs = User.objects.filter(is_staff=False).prefetch_related(
        Prefetch('addresses', queryset=Address.objects.all(), to_attr='user_addresses')
    ).order_by('-date_joined')

   qs = User.objects.filter(is_staff=False).prefetch_related(
       Prefetch('addresses', queryset=Address.objects.all(), to_attr='user_addresses')
   ).order_by('-date_joined')


    for user in users_page:
        default_addr = next((addr for addr in user.user_addresses if addr.is_default), None)
        if not default_addr and user.user_addresses:
            default_addr = user.user_addresses[0]
        if default_addr:
            user.display_address = f"{default_addr.detail}, {default_addr.city}"
        else:
            user.display_address = "(Chưa cập nhật)"



# ─── BÁO CÁO DOANH THU ───────────────────────────────────────

@admin_required
def bao_cao_doanh_thu(request):
    orders = Order.objects.filter(status__in=['delivered', 'completed'])
    stats = orders.aggregate(
        total_revenue=Coalesce(Sum('total'), Decimal('0'), output_field=DecimalField()),
        order_count=Count('id'),
        avg_value=Coalesce(Avg('total'), Decimal('0'), output_field=DecimalField()),
    )
    daily = (
        orders
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(daily_total=Sum('total'))
        .order_by('date')
    )
    return render(request, 'admin_panel/bao_cao_doanh_thu.html', {
        'stats': stats,
        'daily_revenue': list(daily),
        'recent_orders': orders.order_by('-created_at')[:10],
    })


# ─── QUẢN LÝ PHÍ VẬN CHUYỂN ─────────────────────────────────

@admin_required
def quan_ly_phi_ship(request):
    search_query = request.GET.get('q', '').strip()
    ds_phi_qs = PhiVanChuyen.objects.all().order_by('tenKhuVuc')

    if search_query:
        search_lower = search_query.lower()
        ds_phi_list = [p for p in ds_phi_qs if search_lower in p.tenKhuVuc.lower()]
        if ds_phi_list:
            phi_trung_binh = sum(p.phiShip for p in ds_phi_list) / len(ds_phi_list)
        else:
            phi_trung_binh = 0
        ds_phi_qs = ds_phi_list
    else:
        phi_trung_binh = ds_phi_qs.aggregate(avg=Avg('phiShip'))['avg'] or 0

    return render(request, 'admin_panel/quan_ly_phi_ship.html', {
        'ds_phi': ds_phi_qs,
        'phi_trung_binh': phi_trung_binh,
        'search_query': search_query,
    })


@admin_required
def ajax_luu_phi_ship(request):
   if request.method == 'POST':
       try:
           ten = request.POST.get('tenKhuVuc', '').strip()
           phi = request.POST.get('phiShip', '0')
           tg = request.POST.get('thoiGianGiao', '').strip() or None
           if not ten:
               return JsonResponse({'status': 'error', 'message': 'Thiếu tên khu vực'})
           obj, _ = PhiVanChuyen.objects.update_or_create(
               tenKhuVuc=ten,
               defaults={'phiShip': phi, 'thoiGianGiao': tg},
           )
           return JsonResponse({'status': 'success', 'id': obj.pk})
       except Exception as e:
           return JsonResponse({'status': 'error', 'message': str(e)})
   return JsonResponse({'status': 'error'}, status=405)




@admin_required
def ajax_xoa_phi_ship(request, pk):
    if request.method == 'POST':
        get_object_or_404(PhiVanChuyen, pk=pk).delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=405)
