from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import time
import uuid

# ─────────────────────────────────────────
#  SẢN PHẨM
# ─────────────────────────────────────────

class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Tên danh mục')
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Danh mục'
        verbose_name_plural = 'Danh mục'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='products', verbose_name='Danh mục'
    )
    name        = models.CharField(max_length=255, verbose_name='Tên sản phẩm')
    slug        = models.SlugField(unique=True)
    description = models.TextField(blank=True, verbose_name='Mô tả')
    price       = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Giá (đ)')
    sold        = models.PositiveIntegerField(default=0, verbose_name='Đã bán')
    image       = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Ảnh chính')
    origin      = models.CharField(max_length=100, blank=True, verbose_name='Xuất xứ')
    gender      = models.CharField(
        max_length=20,
        choices=[('unisex', 'Unisex'), ('male', 'Nam'), ('female', 'Nữ')],
        default='unisex', verbose_name='Giới tính'
    )
    is_active   = models.BooleanField(default=True, verbose_name='Hiển thị')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sản phẩm'
        verbose_name_plural = 'Sản phẩm'
        ordering = ['-created_at']

    @property
    def display_image(self):
        """Trả về URL ảnh: ưu tiên image upload, fallback về static mẫu."""
        if self.image:
            return self.image.url
        from django.templatetags.static import static
        idx = ((self.pk - 1) % 5) + 1
        return static(f'images/giay{idx}.png')

    @property
    def total_stock(self):
        """Tính tổng tồn kho từ tất cả biến thể."""
        return sum(v.stock for v in self.variants.all())

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image   = models.ImageField(upload_to='products/')
    order   = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.product.name} - ảnh {self.order}'


class ProductVariant(models.Model):
    """Biến thể: màu sắc + size"""
    product     = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color_name  = models.CharField(max_length=50, verbose_name='Màu sắc')
    color_hex   = models.CharField(max_length=7, default='#000000', verbose_name='Mã màu')
    size        = models.CharField(max_length=10, verbose_name='Size')
    stock       = models.PositiveIntegerField(default=0, verbose_name='Tồn kho')

    class Meta:
        verbose_name = 'Biến thể sản phẩm'
        verbose_name_plural = 'Biến thể sản phẩm'
        unique_together = ('product', 'color_name', 'size')

    def __str__(self):
        return f'{self.product.name} | {self.color_name} | {self.size}'


# ─────────────────────────────────────────
#  GIỎ HÀNG
# ─────────────────────────────────────────

class Cart(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Giỏ hàng'
        verbose_name_plural = 'Giỏ hàng'

    def __str__(self):
        return f'Giỏ hàng của {self.user.username}'

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())


class CartItem(models.Model):
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant  = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Sản phẩm trong giỏ'
        verbose_name_plural = 'Sản phẩm trong giỏ'
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f'{self.variant} x{self.quantity}'

    @property
    def subtotal(self):
        return self.variant.product.price * self.quantity


# ─────────────────────────────────────────
#  ĐỊA CHỈ GIAO HÀNG
# ─────────────────────────────────────────

class Address(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name   = models.CharField(max_length=150, verbose_name='Họ và tên')
    phone       = models.CharField(max_length=15, verbose_name='Số điện thoại')
    detail      = models.CharField(max_length=255, verbose_name='Địa chỉ chi tiết')
    city        = models.CharField(max_length=100, verbose_name='Tỉnh / Thành phố')
    is_default  = models.BooleanField(default=False, verbose_name='Địa chỉ mặc định')

    class Meta:
        verbose_name = 'Địa chỉ'
        verbose_name_plural = 'Địa chỉ'

    def __str__(self):
        return f'{self.full_name} - {self.detail}, {self.city}'


# ─────────────────────────────────────────
#  ĐƠN HÀNG
# ─────────────────────────────────────────

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending',    'Chờ xác nhận'),
        ('confirmed',  'Đã xác nhận'),
        ('shipping',   'Đang vận chuyển'),
        ('delivered',  'Đã giao hàng'),
        ('completed',  'Hoàn thành'),
        ('cancelled',  'Đã hủy'),
        ('returning',  'Yêu cầu trả hàng'),
        ('returned',   'Đã trả hàng'),
    ]

    PAYMENT_CHOICES = [
        ('cod',  'Thanh toán khi nhận hàng (COD)'),
        ('bank', 'Chuyển khoản ngân hàng'),
    ]

    SHIPPING_CHOICES = [
        ('standard', 'Tiêu chuẩn 2-5 ngày'),
        ('express',  'Nhanh 1-2 ngày'),
    ]

    user             = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    order_code       = models.CharField(max_length=20, unique=True, verbose_name='Mã đơn hàng')
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')

    # Địa chỉ snapshot (lưu lại tại thời điểm đặt)
    recipient_name   = models.CharField(max_length=150, verbose_name='Người nhận')
    recipient_phone  = models.CharField(max_length=15, verbose_name='SĐT người nhận')
    shipping_address = models.CharField(max_length=255, verbose_name='Địa chỉ giao hàng')
    shipping_city    = models.CharField(max_length=100, verbose_name='Tỉnh / Thành phố')

    shipping_method  = models.CharField(max_length=20, choices=SHIPPING_CHOICES, default='standard', verbose_name='Phương thức vận chuyển')
    payment_method   = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cod', verbose_name='Phương thức thanh toán')
    payment_proof    = models.ImageField(upload_to='payment_proofs/', blank=True, null=True, verbose_name='Biên lai chuyển khoản')

    subtotal         = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Tổng tiền hàng')
    discount_amount  = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Giảm giá')
    shipping_fee     = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Phí vận chuyển')
    total            = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name='Tổng thanh toán')

    note             = models.TextField(blank=True, verbose_name='Ghi chú')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Đơn hàng'
        verbose_name_plural = 'Đơn hàng'
        ordering = ['-created_at']

    def __str__(self):
        return f'#{self.order_code} - {self.user}'

    def save(self, *args, **kwargs):
        if not self.order_code:
            # DH + Timestamp + 4 ký tự ngẫu nhiên
            random_str = uuid.uuid4().hex[:4].upper()
            self.order_code = f"DH{int(time.time())}{random_str}"

        self.total = self.subtotal - self.discount_amount + self.shipping_fee
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    variant    = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    # Snapshot tại thời điểm đặt
    product_name = models.CharField(max_length=255)
    color        = models.CharField(max_length=50)
    size         = models.CharField(max_length=10)
    price        = models.DecimalField(max_digits=12, decimal_places=0)
    quantity     = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = 'Sản phẩm trong đơn'
        verbose_name_plural = 'Sản phẩm trong đơn'

    def __str__(self):
        return f'{self.product_name} ({self.color}/{self.size}) x{self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity


# ─────────────────────────────────────────
#  YÊU CẦU TRẢ HÀNG
# ─────────────────────────────────────────

class ReturnRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Chờ xử lý'),
        ('approved',  'Đã duyệt'),
        ('picking',   'Chờ lấy hàng'),
        ('returning_to_warehouse', 'Đang chuyển về kho'),
        ('received',  'Đã nhận hàng'),
        ('processing', 'Đang xử lý'),
        ('completed', 'Đã hoàn tiền'),
        ('rejected',  'Từ chối'),
    ]

    REASON_CHOICES = [
        ('defective',  'Sản phẩm bị lỗi / hư hỏng'),
        ('wrong_item', 'Nhận sai sản phẩm'),
        ('damaged',    'Sản phẩm bị vỡ do vận chuyển'),
        ('quality',    'Chất lượng không đúng kỳ vọng'),
        ('late',       'Giao hàng quá lâu'),
        ('other',      'Khác'),
    ]

    order      = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='return_request')
    reason     = models.CharField(max_length=20, choices=REASON_CHOICES, verbose_name='Lý do')
    note       = models.TextField(blank=True, verbose_name='Ghi chú')
    status     = models.CharField(max_length=22, choices=STATUS_CHOICES, default='pending', verbose_name='Trạng thái')
    created_at = models.DateTimeField(auto_now_add=True)
    admin_note = models.TextField(blank=True, null=True, verbose_name='Ghi chú của Admin (Lý do từ chối)')
    # Lưu số tiền cuối cùng sau khi đã trừ các loại phí
    refund_amount = models.DecimalField(max_digits=12, decimal_places=0, blank=True, null=True, verbose_name='Số tiền thực hoàn')
    # Thêm các trường thông tin chuyển khoản
    bank_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Tên ngân hàng')
    bank_account_number = models.CharField(max_length=50, blank=True, null=True, verbose_name='Số tài khoản')
    bank_account_holder = models.CharField(max_length=150, blank=True, null=True, verbose_name='Tên chủ tài khoản')
    
    # Trường ảnh biên lai hoàn tiền
    refund_proof = models.ImageField(upload_to='refund_proofs/', blank=True, null=True, verbose_name='Biên lai hoàn tiền')


    class Meta:
        verbose_name = 'Yêu cầu trả hàng'
        verbose_name_plural = 'Yêu cầu trả hàng'

    def __str__(self):
        return f'Trả hàng đơn #{self.order.order_code}'


# ─────────────────────────────────────────
#  PHÍ VẬN CHUYỂN
# ─────────────────────────────────────────

class PhiVanChuyen(models.Model):
    tenKhuVuc   = models.CharField(max_length=100, unique=True, verbose_name='Khu vực')
    phiShip     = models.DecimalField(max_digits=12, decimal_places=0, verbose_name='Phí vận chuyển (đ)')
    thoiGianGiao = models.CharField(max_length=100, blank=True, null=True, verbose_name='Thời gian giao dự kiến')

    class Meta:
        verbose_name = 'Phí vận chuyển'
        verbose_name_plural = 'Phí vận chuyển'

    def __str__(self):
        return f'{self.tenKhuVuc} - {self.phiShip}đ'


# ─────────────────────────────────────────
#  HỒ SƠ NGƯỜI DÙNG
# ─────────────────────────────────────────

class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name  = models.CharField(max_length=150, blank=True, verbose_name='Họ và tên')
    phone      = models.CharField(max_length=15, blank=True, verbose_name='Số điện thoại')
    dob        = models.DateField(null=True, blank=True, verbose_name='Ngày sinh')
    gender     = models.CharField(
        max_length=10,
        choices=[('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')],
        blank=True, verbose_name='Giới tính'
    )
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Ảnh đại diện')

    class Meta:
        verbose_name = 'Hồ sơ người dùng'
        verbose_name_plural = 'Hồ sơ người dùng'

    def __str__(self):
        return f'Hồ sơ của {self.user.username}'
