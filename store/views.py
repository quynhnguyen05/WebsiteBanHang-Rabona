from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import (
    Product, ProductVariant, Category,
    Cart, CartItem, Address,
    Order, OrderItem, ReturnRequest, UserProfile
)


# ─────────────────────────────────────────
#  TRANG CHỦ
# ─────────────────────────────────────────

def home(request):
    products = Product.objects.filter(is_active=True).prefetch_related('variants', 'images')
    return render(request, 'store/home.html', {'products': products})


def custom_login(request):
    """Custom login view: phân luồng admin → dashboard, khách → trang chủ."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_panel:dashboard')
        return redirect('store:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Phân luồng
            if user.is_staff or user.is_superuser:
                return JsonResponse({'success': True, 'redirect': '/admin-panel/'})
            if next_url and next_url.startswith('/'):
                return JsonResponse({'success': True, 'redirect': next_url})
            return JsonResponse({'success': True, 'redirect': '/'})
        else:
            return JsonResponse({'success': False, 'error': 'Tên đăng nhập hoặc mật khẩu không đúng.'})

    # GET — hiển thị trang login
    next_url = request.GET.get('next', '')
    return render(request, 'registration/login.html', {'next': next_url})


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not username or not password1:
            return JsonResponse({'success': False, 'error': 'Vui lòng điền đầy đủ thông tin.'})
        if password1 != password2:
            return JsonResponse({'success': False, 'error': 'Mật khẩu không khớp.'})

        from django.contrib.auth.models import User
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'error': 'Tên đăng nhập đã tồn tại.'})

        user = User.objects.create_user(username=username, password=password1)
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)


# ─────────────────────────────────────────
#  SẢN PHẨM
# ─────────────────────────────────────────

def product_list(request):
    from django.db.models import Q

    category_slug = request.GET.get('category')
    query = request.GET.get('q', '').strip()
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    active_category = None

    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)

    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        ).distinct()

    return render(request, 'store/product_list.html', {
        'products': products,
        'categories': categories,
        'active_category': active_category,
        'query': query,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    variants = product.variants.all()
    images = product.images.all()

    # Nhóm màu sắc
    colors = variants.values('color_name', 'color_hex').distinct()
    sizes  = variants.values_list('size', flat=True).distinct()

    return render(request, 'store/product_detail.html', {
        'product': product,
        'variants': variants,
        'images': images,
        'colors': colors,
        'sizes': sizes,
    })


# ─────────────────────────────────────────
#  GIỎ HÀNG
# ─────────────────────────────────────────

@login_required
def cart_detail(request):
    # Trang /cart/ không dùng nữa, redirect về trang chủ
    return redirect('store:home')


@login_required
def cart_json(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    items = []
    for item in cart.items.select_related('variant__product'):
        items.append({
            'id': item.id,
            'variant_id': item.variant.id,
            'name': item.variant.product.name,
            'color': item.variant.color_name,
            'size': item.variant.size,
            'price': str(item.variant.product.price),
            'qty': item.quantity,
            'subtotal': str(item.subtotal),
            'img': item.variant.product.display_image,
        })
    return JsonResponse({
        'items': items,
        'total': str(cart.total_price),
        'count': cart.total_items,
    })


@login_required
@require_POST
def cart_add(request, variant_id):
    variant = get_object_or_404(ProductVariant, id=variant_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    qty = int(request.POST.get('quantity', 1))

    item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
    if not created:
        item.quantity += qty
    else:
        item.quantity = qty
    item.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'cart_count': cart.total_items})
    messages.success(request, f'Đã thêm "{variant.product.name}" vào giỏ hàng.')
    return redirect('store:cart_detail')


@require_POST
def cart_update(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'login_required'}, status=401)
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    qty = int(request.POST.get('quantity', 1))
    cart = item.cart
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return JsonResponse({'success': True, 'cart_count': cart.total_items})


@require_POST
def cart_remove(request, item_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'login_required'}, status=401)
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart = item.cart
    item.delete()
    return JsonResponse({'success': True, 'cart_count': cart.total_items})


# ─────────────────────────────────────────
#  THANH TOÁN
# ─────────────────────────────────────────

@login_required
@require_POST
def set_checkout_items(request):
    """Lưu danh sách item ID đã chọn vào session qua AJAX."""
    import json
    try:
        data = json.loads(request.body)
        ids = [int(i) for i in data.get('ids', [])]
    except (ValueError, KeyError):
        ids = []
    request.session['checkout_selected_ids'] = ids
    return JsonResponse({'success': True})


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        messages.warning(request, 'Giỏ hàng trống.')
        return redirect('store:product_list')

    # Lấy danh sách item ID đã chọn từ session
    selected_ids = request.session.get('checkout_selected_ids', [])

    all_items = cart.items.select_related('variant__product')
    if selected_ids:
        checkout_items = all_items.filter(id__in=selected_ids)
    else:
        checkout_items = all_items

    if not checkout_items.exists():
        messages.warning(request, 'Không có sản phẩm nào được chọn.')
        return redirect('store:product_list')

    selected_total = sum(item.subtotal for item in checkout_items)
    total_quantity = sum(item.quantity for item in checkout_items)

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first() or addresses.exclude(full_name='').first()

    # Tính phí vận chuyển
    FREE_SHIP_THRESHOLD = 500000
    if selected_total >= FREE_SHIP_THRESHOLD:
        shipping_fee = 0
        is_free_ship = True
        ship_note = 'Miễn phí vận chuyển cho đơn hàng từ 500.000đ'
    else:
        from .models import PhiVanChuyen
        phi_ship = None
        if default_address:
            phi_ship = PhiVanChuyen.objects.filter(
                tenKhuVuc__icontains=default_address.city
            ).first()
        if not phi_ship:
            phi_ship = PhiVanChuyen.objects.first()
        shipping_fee = int(phi_ship.phiShip) if phi_ship else 30000
        is_free_ship = False
        ship_note = f'Phí vận chuyển đến {default_address.city if default_address else "khu vực của bạn"}'

    total_payment = int(selected_total) + shipping_fee

    return render(request, 'store/checkout.html', {
        'cart': cart,
        'checkout_items': checkout_items,
        'selected_total': selected_total,
        'total_quantity': total_quantity,
        'shipping_fee': shipping_fee,
        'is_free_ship': is_free_ship,
        'ship_note': ship_note,
        'total_payment': total_payment,
        'addresses': addresses,
        'default_address': default_address,
    })


@login_required
@require_POST
def place_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    if not cart.items.exists():
        return redirect('store:cart_detail')

    # Lấy danh sách item đã chọn từ session
    selected_ids = request.session.get('checkout_selected_ids', [])
    all_items = cart.items.select_related('variant__product')
    if selected_ids:
        order_items_qs = all_items.filter(id__in=selected_ids)
    else:
        order_items_qs = all_items

    if not order_items_qs.exists():
        return redirect('store:cart_detail')

    # Lấy địa chỉ
    address_id = request.POST.get('address_id')
    if address_id:
        address = get_object_or_404(Address, id=address_id, user=request.user)
    else:
        # Tạo địa chỉ mới từ form
        address = Address.objects.create(
            user=request.user,
            full_name=request.POST.get('full_name', ''),
            phone=request.POST.get('phone', ''),
            detail=request.POST.get('detail', ''),
            city=request.POST.get('city', ''),
        )

    from decimal import Decimal
    subtotal = sum(item.subtotal for item in order_items_qs)
    discount = 0

    # Nhận phí ship từ form (đã tính sẵn ở checkout view)
    try:
        shipping_fee = int(request.POST.get('shipping_fee_amount', 0))
    except (ValueError, TypeError):
        # Fallback: tính lại
        FREE_SHIP_THRESHOLD = 500000
        if subtotal >= FREE_SHIP_THRESHOLD:
            shipping_fee = 0
        else:
            from .models import PhiVanChuyen
            phi_ship = PhiVanChuyen.objects.filter(
                tenKhuVuc__icontains=address.city
            ).first() or PhiVanChuyen.objects.first()
            shipping_fee = int(phi_ship.phiShip) if phi_ship else 30000

    order = Order.objects.create(
        user=request.user,
        recipient_name=address.full_name,
        recipient_phone=address.phone,
        shipping_address=address.detail,
        shipping_city=address.city,
        shipping_method=request.POST.get('shipping_method', 'standard'),
        payment_method=request.POST.get('payment_method', 'cod'),
        subtotal=subtotal,
        discount_amount=discount,
        shipping_fee=shipping_fee,
        note=request.POST.get('note', ''),
    )

    # Tạo OrderItem chỉ từ các CartItem đã chọn
    for item in order_items_qs:
        OrderItem.objects.create(
            order=order,
            variant=item.variant,
            product_name=item.variant.product.name,
            color=item.variant.color_name,
            size=item.variant.size,
            price=item.variant.product.price,
            quantity=item.quantity,
        )
        # Trừ tồn kho
        item.variant.stock = max(0, item.variant.stock - item.quantity)
        item.variant.save()
        item.variant.product.sold += item.quantity
        item.variant.product.save()

    # Xử lý biên lai chuyển khoản
    if 'payment_proof' in request.FILES:
        order.payment_proof = request.FILES['payment_proof']
        order.save()

    # Xóa chỉ các item đã đặt khỏi giỏ hàng
    order_items_qs.delete()

    # Xóa session
    if 'checkout_selected_ids' in request.session:
        del request.session['checkout_selected_ids']

    # Trả về JSON nếu AJAX, redirect nếu thường
    first_item = order.items.first()
    img_url = ''
    if first_item and first_item.variant:
        img_url = first_item.variant.product.display_image

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'order_code': order.order_code,
            'img_url': img_url,
        })

    return redirect('store:order_list')


@login_required
@require_POST
def cancel_order(request, order_code):
    order = get_object_or_404(Order, order_code=order_code, user=request.user)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if order.status != 'pending':
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Chỉ có thể hủy đơn hàng đang chờ xác nhận.'})
        messages.error(request, 'Chỉ có thể hủy đơn hàng đang chờ xác nhận.')
        return redirect('store:order_list')

    # Hoàn lại tồn kho
    for item in order.items.select_related('variant'):
        if item.variant:
            item.variant.stock += item.quantity
            item.variant.save()
            item.variant.product.sold = max(0, item.variant.product.sold - item.quantity)
            item.variant.product.save()

    order.status = 'cancelled'
    order.save()

    if is_ajax:
        return JsonResponse({'success': True})
    messages.success(request, f'Đã hủy đơn hàng #{order_code}.')
    return redirect('store:order_list')


# ─────────────────────────────────────────
#  ĐƠN HÀNG
# ─────────────────────────────────────────

@login_required
def order_list(request):
    status = request.GET.get('status', '')
    orders = Order.objects.filter(user=request.user)
    if status:
        orders = orders.filter(status=status)
    return render(request, 'store/order_list.html', {
        'orders': orders,
        'active_status': status,
    })


@login_required
def order_detail(request, order_code):
    order = get_object_or_404(Order, order_code=order_code, user=request.user)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        items_data = []
        for item in order.items.all():
            items_data.append({
                'product_name': item.product_name,
                'color': item.color,
                'size': item.size,
                'price': str(item.price),
                'quantity': item.quantity,
                'subtotal': str(item.subtotal),
                'img': item.variant.product.display_image if item.variant else '',
            })
        return JsonResponse({
            'order_code': order.order_code,
            'status': order.status,
            'status_display': order.get_status_display(),
            'created_at': order.created_at.strftime('%d/%m/%Y %H:%M'),
            'payment_method': order.get_payment_method_display(),
            'recipient_name': order.recipient_name,
            'recipient_phone': order.recipient_phone,
            'shipping_address': order.shipping_address,
            'shipping_city': order.shipping_city,
            'subtotal': str(order.subtotal),
            'shipping_fee': str(order.shipping_fee),
            'discount_amount': str(order.discount_amount),
            'total': str(order.total),
            'note': order.note or '',
            'has_return_request': hasattr(order, 'return_request'),
            'items': items_data,
        })
    return render(request, 'store/order_detail.html', {'order': order})


@login_required
@require_POST
def upload_payment_proof(request, order_code):
    order = get_object_or_404(Order, order_code=order_code, user=request.user)

    if order.payment_method != 'bank':
        messages.error(request, 'Chỉ có thể tải biên lai cho đơn hàng thanh toán bằng chuyển khoản.')
        return redirect('store:order_detail', order_code=order_code)

    if order.payment_proof:
        messages.warning(request, 'Biên lai đã được tải lên trước đó.')
        return redirect('store:order_detail', order_code=order_code)

    if request.method == 'POST' and 'payment_proof' in request.FILES:
        order.payment_proof = request.FILES['payment_proof']
        order.save()
        messages.success(request, 'Biên lai chuyển khoản đã được tải lên thành công!')
    else:
        messages.error(request, 'Vui lòng chọn một file biên lai để tải lên.')
    
    return redirect('store:order_detail', order_code=order_code)


@login_required
@require_POST
def return_request(request, order_code):
    order = get_object_or_404(Order, order_code=order_code, user=request.user)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if hasattr(order, 'return_request'):
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'Đơn hàng này đã có yêu cầu trả hàng.'})
        messages.warning(request, 'Đơn hàng này đã có yêu cầu trả hàng.')
        return redirect('store:order_detail', order_code=order_code)

    ReturnRequest.objects.create(
        order=order,
        reason=request.POST.get('reason', 'other'),
        bank_name=request.POST.get('bank_name', ''),
        bank_account_number=request.POST.get('bank_account_number', ''),
        bank_account_holder=request.POST.get('bank_account_holder', ''),
        note=request.POST.get('note', ''),
    )
    order.status = 'returning'
    order.save()

    if is_ajax:
        return JsonResponse({'success': True})
    messages.success(request, 'Gửi yêu cầu trả hàng thành công!')
    return redirect('store:order_list')


# ─────────────────────────────────────────
#  HỒ SƠ
# ─────────────────────────────────────────

@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile_obj.full_name = request.POST.get('full_name', '')
        profile_obj.phone     = request.POST.get('phone', '')
        profile_obj.dob       = request.POST.get('dob') or None
        profile_obj.gender    = request.POST.get('gender', '')
        if 'avatar' in request.FILES:
            profile_obj.avatar = request.FILES['avatar']
        profile_obj.save()
        messages.success(request, 'Cập nhật hồ sơ thành công!')
        return redirect('store:profile')
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'store/profile.html', {
        'profile': profile_obj,
        'addresses': addresses,
    })


@login_required
def address_manage(request):
    addresses = Address.objects.filter(user=request.user)
    if request.method == 'GET':
        return redirect('store:profile')
    if request.method == 'POST':
        # Xóa địa chỉ
        delete_id = request.POST.get('delete_id')
        if delete_id:
            Address.objects.filter(id=delete_id, user=request.user).delete()
            messages.success(request, 'Đã xóa địa chỉ.')
            return redirect('store:profile')

        # Đặt mặc định
        set_default = request.POST.get('set_default')
        if set_default:
            Address.objects.filter(user=request.user).update(is_default=False)
            Address.objects.filter(id=set_default, user=request.user).update(is_default=True)
            messages.success(request, 'Đã đặt địa chỉ mặc định.')
            return redirect('store:profile')

        # Thêm mới
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        detail = request.POST.get('detail', '').strip()
        city = request.POST.get('city', '').strip()
        
        if not full_name or not phone or not detail or not city:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin địa chỉ.')
            return redirect('store:profile')
        
        is_default = request.POST.get('is_default') == 'on'
        if is_default:
            Address.objects.filter(user=request.user).update(is_default=False)
        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            detail=detail,
            city=city,
            is_default=is_default,
        )
        messages.success(request, 'Thêm địa chỉ thành công!')
        return redirect('store:profile')
    return render(request, 'store/address.html', {'addresses': addresses})
