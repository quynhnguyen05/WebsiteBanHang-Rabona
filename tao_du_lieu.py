"""
Script tạo dữ liệu mẫu cho rabonastore.
Chạy: python tao_du_lieu.py
"""
import os
import django
import random
import unicodedata
import re
import time
import uuid

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rabonastore.settings')
django.setup()

from django.contrib.auth.models import User
from store.models import (
    Category, Product, ProductVariant,
    Order, OrderItem, ReturnRequest,
    Address, UserProfile
)

# ── Tiện ích ──────────────────────────────────────────────────
def ho_ten():
    ho = ['Nguyễn','Trần','Lê','Phạm','Hoàng','Phan','Vũ','Đặng','Bùi','Hồ']
    dem_nam = ['Văn','Hữu','Đức','Công','Quang','Minh','Đình','Xuân']
    dem_nu  = ['Thị','Thu','Ngọc','Phương','Bích','Diễm','Hồng','Mai']
    ten_nam = ['Hải','Bảo','Tùng','Sơn','Tuấn','Khang','Phong','Thắng','Cường','Long']
    ten_nu  = ['Hà','Lan','Trang','Nhung','Linh','Anh','Quyên','Thảo','Vy','Trâm']
    if random.choice([0,1]):
        return f"{random.choice(ho)} {random.choice(dem_nam)} {random.choice(ten_nam)}"
    return f"{random.choice(ho)} {random.choice(dem_nu)} {random.choice(ten_nu)}"

def sdt():
    dau = ['032','033','034','035','036','037','038','039','070','079','089','090','093']
    return random.choice(dau) + str(random.randint(1000000,9999999))

def email_tu_ten(ten):
    s = unicodedata.normalize('NFKD', ten).encode('ASCII','ignore').decode().lower()
    s = re.sub(r'[^a-z]','',s)
    return f"{s}{random.randint(80,2005)}@gmail.com"

def dia_chi():
    tp = random.choice(['Đà Nẵng','Hồ Chí Minh','Hà Nội','Huế','Cần Thơ'])
    duong = random.choice(['Lê Lợi','Nguyễn Trãi','Trần Phú','Lê Duẩn','Nguyễn Văn Linh'])
    return f"Số {random.randint(1,300)}, đường {duong}", tp

def slugify_vn(text):
    s = unicodedata.normalize('NFKD', text).encode('ASCII','ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+','-',s).strip('-')
    return s

# ── Chạy ──────────────────────────────────────────────────────
def main():
    print("1. Xóa dữ liệu cũ (giữ superuser)...")
    ReturnRequest.objects.all().delete()
    OrderItem.objects.all().delete()
    Order.objects.all().delete()
    ProductVariant.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Address.objects.all().delete()
    User.objects.filter(is_superuser=False, is_staff=False).delete()

    # ── Danh mục ──
    print("2. Tạo danh mục...")
    cats = {}
    for name in ['Giày bóng đá','Áo đấu','Phụ kiện']:
        slug = slugify_vn(name) + f'-{int(time.time()) % 10000}'
        cats[name] = Category.objects.create(name=name, slug=slug)

    # ── Sản phẩm ──
    print("3. Tạo sản phẩm...")
    san_pham_data = [
        {'name':'Giày bóng đá Nike Mercurial Vapor 13 Pro','cat':'Giày bóng đá','price':799000,
         'sizes':['39','40','41','42'],'colors':[('Vàng','#FFD700'),('Trắng','#F2F2F2')]},
        {'name':'Giày bóng đá Adidas F5E Elite Lawn','cat':'Giày bóng đá','price':270000,
         'sizes':['38','39','40','41'],'colors':[('Đỏ','#FF0000'),('Trắng','#F2F2F2')]},
        {'name':'Giày bóng đá Nike Mercurial Vapor 16 Elite','cat':'Giày bóng đá','price':750000,
         'sizes':['39','40','41','42'],'colors':[('Xanh','#0000FF'),('Đen','#000000')]},
        {'name':'Giày bóng đá Mizuno Neo 4','cat':'Giày bóng đá','price':365000,
         'sizes':['39','40','41'],'colors':[('Đen','#000000'),('Trắng','#F2F2F2')]},
        {'name':'Giày bóng đá Lingy UST083','cat':'Giày bóng đá','price':1120000,
         'sizes':['40','41','42'],'colors':[('Cam','#FF8C00'),('Đen','#000000')]},
        {'name':'Áo đấu Manchester United 23/24','cat':'Áo đấu','price':180000,
         'sizes':['S','M','L','XL'],'colors':[('Đỏ','#CC0000')]},
        {'name':'Áo đấu Real Madrid 23/24','cat':'Áo đấu','price':220000,
         'sizes':['S','M','L','XL'],'colors':[('Trắng','#F2F2F2')]},
        {'name':'Tất chống trượt Fox','cat':'Phụ kiện','price':55000,
         'sizes':['Free'],'colors':[('Đen','#000000'),('Trắng','#F2F2F2')]},
        {'name':'Găng tay thủ môn Adidas Predator','cat':'Phụ kiện','price':450000,
         'sizes':['M','L'],'colors':[('Đen','#000000')]},
    ]

    products = []
    for i, d in enumerate(san_pham_data):
        slug = slugify_vn(d['name']) + f'-{i+1}'
        sp = Product.objects.create(
            name=d['name'], slug=slug, price=d['price'],
            category=cats[d['cat']], is_active=True,
            description=f"Sản phẩm chất lượng cao - {d['name']}"
        )
        for size in d['sizes']:
            for color_name, color_hex in d['colors']:
                ProductVariant.objects.create(
                    product=sp, size=size, color_name=color_name,
                    color_hex=color_hex, stock=random.randint(20,150)
                )
        products.append(sp)
    print(f"   → Tạo {len(products)} sản phẩm")

    # ── Khách hàng ──
    print("4. Tạo 20 khách hàng...")
    users = []
    for i in range(20):
        ten = ho_ten()
        email = email_tu_ten(ten)
        username = f"kh{i+1}_{random.randint(100,999)}"
        try:
            u = User.objects.create_user(username=username, email=email, password='password123')
            detail, city = dia_chi()
            Address.objects.create(
                user=u, full_name=ten, phone=sdt(),
                detail=detail, city=city, is_default=True
            )
            UserProfile.objects.get_or_create(user=u, defaults={'full_name': ten})
            users.append(u)
        except Exception as e:
            print(f"   Bỏ qua user {username}: {e}")
    print(f"   → Tạo {len(users)} khách hàng")

    # ── Đơn hàng ──
    print("5. Tạo đơn hàng...")
    statuses = ['pending','confirmed','shipping','delivered','completed','cancelled']
    don_hoan_thanh = []
    all_variants = list(ProductVariant.objects.all())

    for u in users:
        addr = u.addresses.first()
        for _ in range(random.randint(1,3)):
            status = random.choice(statuses)
            subtotal = 0
            items_data = []
            for v in random.sample(all_variants, random.randint(1,3)):
                qty = random.randint(1,2)
                items_data.append((v, qty))
                subtotal += v.product.price * qty

            order = Order.objects.create(
                user=u,
                order_code='DH' + uuid.uuid4().hex[:10].upper(),
                recipient_name=addr.full_name if addr else u.username,
                recipient_phone=addr.phone if addr else '0901234567',
                shipping_address=addr.detail if addr else '123 Lê Lợi',
                shipping_city=addr.city if addr else 'Đà Nẵng',
                payment_method=random.choice(['cod','bank']),
                subtotal=subtotal,
                discount_amount=0,
                shipping_fee=random.choice([0,20000,30000]),
                status=status,
            )
            time.sleep(0.01)  # tránh trùng order_code
            for v, qty in items_data:
                OrderItem.objects.create(
                    order=order, variant=v,
                    product_name=v.product.name,
                    color=v.color_name, size=v.size,
                    price=v.product.price, quantity=qty,
                )
            if status in ('delivered','completed'):
                don_hoan_thanh.append(order)

    print(f"   → Tạo {Order.objects.count()} đơn hàng")

    # ── Phiếu trả hàng ──
    print("6. Tạo phiếu trả hàng...")
    mau = random.sample(don_hoan_thanh, min(8, len(don_hoan_thanh)))
    for don in mau:
        don.status = 'returning'
        don.save()
        ReturnRequest.objects.create(
            order=don,
            reason=random.choice(['defective','wrong_item','quality','other']),
            note='Hàng bị lỗi, vui lòng xử lý.',
            status=random.choice(['pending','approved','completed']),
        )
    print(f"   → Tạo {ReturnRequest.objects.count()} phiếu trả hàng")

    print("\n✅ XONG! Dữ liệu mẫu đã sẵn sàng.")
    print(f"   Users: {User.objects.filter(is_staff=False).count()}")
    print(f"   Sản phẩm: {Product.objects.count()}")
    print(f"   Đơn hàng: {Order.objects.count()}")

if __name__ == '__main__':
    main()
