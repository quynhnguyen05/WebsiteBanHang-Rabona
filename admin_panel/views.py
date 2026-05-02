from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, Avg, Q, Prefetch
from django.db.models.functions import TruncDate
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

        # Cập nhật email trên User
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
        total=Sum('total'))['total'] or 0
    dang_giao = Order.objects.filter(status='shipping').count()
    don_moi = Order.objects.order_by('-created_at')[:10]
    tong_sp = Product.objects.count()
    tong_kh = User.objects.filter(is_staff=False).count()

    context = {
        'tong_don_hang': tong_don,
        'doanh_thu': doanh_thu,
        'don_dang_giao': dang_giao,
        'don_hang_moi': don_moi,
        'tong_sp': tong_sp,
        'tong_kh': tong_kh,
    }
    return render(request, 'admin_panel/dashboard.html', context)


# ─── QUẢN LÝ ĐƠN HÀNG ───────────────────────────────────────
@admin_required
def quan_ly_don_hang(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order = Order.objects.get(order_code=data['order_code'])
            
            # Kiểm tra trạng thái hiện tại của đơn hàng
            if order.status in ['delivered', 'completed']:
                return JsonResponse({'status': 'error', 'message': 'Không thể thay đổi trạng thái đơn hàng đã giao hoặc đã hoàn thành.'})

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
        # Map tên hiển thị → status code
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

    paginator = Paginator(orders_qs, 15)
    danh_sach_don = paginator.get_page(request.GET.get('page'))

    # Thêm thuộc tính hiển thị cho mỗi đơn
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

    return render(request, 'admin_panel/quan_ly_don_hang.html', {
        'danh_sach_don': danh_sach_don,
        'trang_thai_hien_tai': trang_thai,
        'search': search,
        'tong_don_hang': Order.objects.count(),
        'doanh_thu': Order.objects.filter(status__in=['delivered','completed']).aggregate(total=Sum('total'))['total'] or 0,
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


# ─── XỬ LÝ TRẢ HÀNG ─────────────────────────────────────────
@admin_required
def xu_ly_tra_hang(request):
    if request.method == 'POST':
        try:
            # Hỗ trợ cả FormData (để upload file) và JSON
            if request.content_type and 'multipart/form-data' in request.content_type:
                rr_id = request.POST.get('id')
                new_status = request.POST.get('status')
            else:
                data = json.loads(request.body)
                rr_id = data.get('id')
                new_status = data.get('status')

            rr = ReturnRequest.objects.select_related('order').get(id=rr_id)
            
            # Nếu đang ở trạng thái hoàn tiền rồi thì không cho đổi
            if rr.status == 'completed' and new_status != 'completed':
                return JsonResponse({'status': 'error', 'message': 'Yêu cầu đã hoàn tiền, không thể chuyển trạng thái khác.'})
            
            # Nếu chuyển sang hoàn tiền, xử lý file ảnh
            if new_status == 'completed':
                if 'refund_proof' in request.FILES:
                    rr.refund_proof = request.FILES['refund_proof']
                elif not rr.refund_proof:
                    return JsonResponse({'status': 'error', 'message': 'Vui lòng cung cấp ảnh biên lai hoàn tiền.'})

            rr.status = new_status
            rr.save()

            # Đồng bộ Order.status
            order = rr.order
            if new_status == 'approved':
                order.status = 'returning'
            elif new_status == 'completed':
                order.status = 'returned'
            elif new_status == 'rejected':
                order.status = 'delivered'
            elif new_status in ['picking', 'returning_to_warehouse', 'received', 'processing']:
                order.status = 'returning'
            order.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    status_filter = request.GET.get('status', '')
    qs = ReturnRequest.objects.select_related('order').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)

    paginator = Paginator(qs, 15)
    phieu_list = paginator.get_page(request.GET.get('page'))

    stats = {
        'tong': ReturnRequest.objects.count(),
        'cho_duyet': ReturnRequest.objects.filter(status='pending').count(),
        'da_duyet': ReturnRequest.objects.filter(status='approved').count(),
    }
    return render(request, 'admin_panel/xu_ly_tra_hang.html', {
        'phieu_list': phieu_list,
        'stats': stats,
        'current_status': status_filter,
    })


# ─── QUẢN LÝ SẢN PHẨM ───────────────────────────────────────
@admin_required
def quan_ly_san_pham(request):
    qs = Product.objects.prefetch_related('variants').order_by('-id')
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')

    if search:
        qs = qs.filter(name__icontains=search)

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

            # Lưu ảnh nếu có upload
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
            
            # Cập nhật ảnh nếu có
            if 'image' in request.FILES:
                sp.image = request.FILES['image']
            sp.save()

            # 1. Xử lý Cập nhật và Xóa các biến thể hiện có
            list_variant_ids = request.POST.getlist('variant_id[]')
            # Lấy các biến thể hiện tại của SP
            existing_variants = sp.variants.all()
            
            # Xóa các biến thể không còn nằm trong danh sách gửi lên (bị bấm X)
            for ev in existing_variants:
                if str(ev.id) not in list_variant_ids:
                    ev.delete()
                else:
                    # Cập nhật thông tin biến thể cũ
                    ev.size = request.POST.get(f'kichCo_{ev.id}', ev.size)
                    ev.color_name = request.POST.get(f'mauSac_{ev.id}', ev.color_name)
                    stock_val = request.POST.get(f'soLuongTon_{ev.id}')
                    ev.stock = int(stock_val) if stock_val else 0
                    ev.save()

            # 2. Xử lý Thêm biến thể mới (nếu có)
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
    
    # Prefetch addresses để tránh N+1 query khi lấy địa chỉ hiển thị
    qs = User.objects.filter(is_staff=False).prefetch_related(
        Prefetch('addresses', queryset=Address.objects.all(), to_attr='user_addresses')
    ).order_by('-date_joined')
    
    if search:
        qs = qs.filter(Q(username__icontains=search) | Q(email__icontains=search))

    paginator = Paginator(qs, 15)
    users_page = paginator.get_page(request.GET.get('page'))
    
    # Gán địa chỉ hiển thị cho từng user trong trang hiện tại
    for user in users_page:
        default_addr = next((addr for addr in user.user_addresses if addr.is_default), None)
        if not default_addr and user.user_addresses:
            default_addr = user.user_addresses[0]
        
        if default_addr:
            user.display_address = f"{default_addr.detail}, {default_addr.city}"
        else:
            user.display_address = "(Chưa cập nhật)"

    return render(request, 'admin_panel/ds_khach_hang.html', {
        'users': users_page,
        'search': search,
        'tong_kh': User.objects.filter(is_staff=False).count(),
    })


# ─── BÁO CÁO DOANH THU ───────────────────────────────────────
@admin_required
def bao_cao_doanh_thu(request):
    orders = Order.objects.filter(status__in=['delivered', 'completed'])
    stats = orders.aggregate(
        total_revenue=Sum('total'),
        order_count=Count('id'),
        avg_value=Avg('total'),
    )
    daily = (orders.annotate(date=TruncDate('created_at'))
             .values('date')
             .annotate(daily_total=Sum('total'))
             .order_by('date'))

    return render(request, 'admin_panel/bao_cao_doanh_thu.html', {
        'stats': stats,
        'daily_revenue': list(daily),
        'recent_orders': orders.order_by('-created_at')[:10],
    })


# ─── QUẢN LÝ PHÍ VẬN CHUYỂN ─────────────────────────────────
@admin_required
def quan_ly_phi_ship(request):
    ds_phi = PhiVanChuyen.objects.all().order_by('tenKhuVuc')
    phi_trung_binh = ds_phi.aggregate(avg=Avg('phiShip'))['avg'] or 0
    return render(request, 'admin_panel/quan_ly_phi_ship.html', {
        'ds_phi': ds_phi,
        'phi_trung_binh': phi_trung_binh,
    })


@admin_required
def ajax_luu_phi_ship(request):
    if request.method == 'POST':
        try:
            ten = request.POST.get('tenKhuVuc', '').strip()
            phi = request.POST.get('phiShip', '0')
            tg  = request.POST.get('thoiGianGiao', '').strip() or None
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
