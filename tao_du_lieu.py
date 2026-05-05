"""
Script tạo dữ liệu mẫu nâng cao cho rabonastore (Bản full sản phẩm & tên khách hàng).
Chạy: python tao_du_lieu.py
"""
import os
import django
import random
import unicodedata
import re
import time

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
    ho = ['Nguyễn','Trần','Lê','Phạm','Hoàng','Phan','Vũ','Đặng','Bùi','Hồ', 'Trịnh', 'Đinh']
    dem_nam = ['Văn','Hữu','Đức','Công','Quang','Minh','Đình','Xuân', 'Gia', 'Hoàng']
    dem_nu  = ['Thị','Thu','Ngọc','Phương','Bích','Diễm','Hồng','Mai', 'Quỳnh', 'Thanh']
    ten_nam = ['Hải','Bảo','Tùng','Sơn','Tuấn','Khang','Phong','Thắng','Cường','Long', 'Phát', 'Hưng']
    ten_nu  = ['Hà','Lan','Trang','Nhung','Linh','Anh','Quyên','Thảo','Vy','Trâm', 'Như', 'Yến']
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
    tp = random.choice(['Đà Nẵng','Hồ Chí Minh','Hà Nội','Huế','Cần Thơ', 'Hải Phòng', 'Nha Trang'])
    duong = random.choice(['Lê Lợi','Nguyễn Trãi','Trần Phú','Lê Duẩn','Nguyễn Văn Linh', 'Hoàng Diệu', 'Điện Biên Phủ', 'Hùng Vương', 'Lý Thái Tổ'])
    return f"Số {random.randint(1,500)}, đường {duong}", tp

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
    danh_muc = [
        ('Giày bóng đá', 'giay-bong-da'),
        ('Áo đấu',       'ao-dau'),
        ('Phụ kiện',     'phu-kien'),
        ('Bóng thi đấu', 'bong-thi-dau'),
    ]
    for name, slug in danh_muc:
        cats[name] = Category.objects.create(name=name, slug=slug)

    # ── Sản phẩm (Mở rộng thành 30 sản phẩm) ──
    print("3. Tạo sản phẩm...")
    san_pham_data = [
        # --- GIÀY BÓNG ĐÁ ---
        {'name':'Giày bóng đá Nike Mercurial Vapor 13 Pro','cat':'Giày bóng đá','price':799000,'sizes':['39','40','41','42'],'colors':[('Vàng','#FFD700'),('Trắng','#F2F2F2')]},
        {'name':'Giày bóng đá Adidas F5E Elite Lawn','cat':'Giày bóng đá','price':270000,'sizes':['38','39','40','41'],'colors':[('Đỏ','#FF0000'),('Trắng','#F2F2F2')]},
        {'name':'Giày bóng đá Nike Mercurial Vapor 16 Elite','cat':'Giày bóng đá','price':750000,'sizes':['39','40','41','42'],'colors':[('Xanh','#0000FF'),('Đen','#000000')]},
        {'name':'Giày bóng đá Mizuno Neo 4','cat':'Giày bóng đá','price':365000,'sizes':['39','40','41'],'colors':[('Đen','#000000'),('Trắng','#F2F2F2')]},
        {'name':'Giày bóng đá Puma Future Ultimate','cat':'Giày bóng đá','price':650000,'sizes':['40','41','42'],'colors':[('Cam','#FF8C00'),('Đen','#000000')]},
        {'name':'Giày bóng đá Adidas X Crazyfast.1','cat':'Giày bóng đá','price':850000,'sizes':['39','40','41','42'],'colors':[('Trắng Xanh','#00FFFF'),('Đen','#000000')]},
        {'name':'Giày bóng đá Nike Tiempo Legend 10','cat':'Giày bóng đá','price':920000,'sizes':['40','41','42','43'],'colors':[('Trắng Đỏ','#FFCCCC'),('Đen','#000000')]},
        {'name':'Giày bóng đá Mizuno Alpha Japan','cat':'Giày bóng đá','price':1200000,'sizes':['39','40','41'],'colors':[('Trắng','#FFFFFF'),('Đỏ','#FF0000')]},
        {'name':'Giày bóng đá Puma Ultra Ultimate','cat':'Giày bóng đá','price':780000,'sizes':['39','40','41','42'],'colors':[('Hồng','#FFC0CB'),('Xanh Đậm','#00008B')]},
        {'name':'Giày bóng đá Kamito TA11','cat':'Giày bóng đá','price':550000,'sizes':['38','39','40','41'],'colors':[('Vàng Đen','#BDB76B')]},

        # --- ÁO ĐẤU ---
        {'name':'Áo đấu Manchester United 23/24','cat':'Áo đấu','price':180000,'sizes':['S','M','L','XL'],'colors':[('Đỏ','#CC0000')]},
        {'name':'Áo đấu Real Madrid 23/24','cat':'Áo đấu','price':220000,'sizes':['S','M','L','XL'],'colors':[('Trắng','#F2F2F2')]},
        {'name':'Áo đấu Arsenal sân khách 23/24','cat':'Áo đấu','price':190000,'sizes':['M','L','XL'],'colors':[('Vàng','#FFD700')]},
        {'name':'Áo đấu Manchester City 23/24','cat':'Áo đấu','price':210000,'sizes':['S','M','L'],'colors':[('Xanh Da Trời','#87CEEB')]},
        {'name':'Áo đấu Bayern Munich 23/24','cat':'Áo đấu','price':195000,'sizes':['M','L','XL'],'colors':[('Đỏ Trắng','#B22222')]},
        {'name':'Áo đấu PSG 23/24','cat':'Áo đấu','price':250000,'sizes':['S','M','L','XL'],'colors':[('Xanh Đen','#000080')]},
        {'name':'Áo đấu Chelsea 23/24','cat':'Áo đấu','price':185000,'sizes':['M','L','XL'],'colors':[('Xanh Dương','#0000FF')]},
        {'name':'Áo đấu Đội Tuyển Việt Nam 2024','cat':'Áo đấu','price':299000,'sizes':['S','M','L','XL'],'colors':[('Đỏ','#FF0000')]},
        {'name':'Áo đấu Liverpool 23/24','cat':'Áo đấu','price':190000,'sizes':['M','L','XL'],'colors':[('Đỏ','#8B0000')]},
        {'name':'Áo đấu AC Milan 23/24','cat':'Áo đấu','price':200000,'sizes':['S','M','L'],'colors':[('Sọc Đỏ Đen','#000000')]},

        # --- PHỤ KIỆN ---
        {'name':'Tất chống trượt Fox','cat':'Phụ kiện','price':55000,'sizes':['Free'],'colors':[('Đen','#000000'),('Trắng','#F2F2F2')]},
        {'name':'Găng tay thủ môn Adidas Predator','cat':'Phụ kiện','price':450000,'sizes':['M','L'],'colors':[('Đen','#000000')]},
        {'name':'Băng gót chân thể thao','cat':'Phụ kiện','price':45000,'sizes':['Free'],'colors':[('Xanh','#0000FF'),('Đen','#000000')]},
        {'name':'Túi rút đựng giày thể thao','cat':'Phụ kiện','price':60000,'sizes':['Free'],'colors':[('Đen','#000000'),('Đỏ','#FF0000')]},
        {'name':'Băng đội trưởng (Captain)','cat':'Phụ kiện','price':30000,'sizes':['Free'],'colors':[('Cam','#FFA500'),('Vàng','#FFD700')]},
        {'name':'Còi trọng tài Fox 40','cat':'Phụ kiện','price':85000,'sizes':['Free'],'colors':[('Đen','#000000')]},
        {'name':'Ống đồng bảo vệ chân','cat':'Phụ kiện','price':95000,'sizes':['M','L'],'colors':[('Trắng','#FFFFFF')]},

        # --- BÓNG THI ĐẤU ---
        {'name':'Bóng Động Lực UHV 2.07','cat':'Bóng thi đấu','price':650000,'sizes':['Size 5'],'colors':[('Trắng Xanh','#FFFFFF')]},
        {'name':'Bóng Động Lực UHV 2.05','cat':'Bóng thi đấu','price':550000,'sizes':['Size 5'],'colors':[('Trắng Đỏ','#FFFFFF')]},
        {'name':'Bóng thi đấu Nike Flight','cat':'Bóng thi đấu','price':1150000,'sizes':['Size 5'],'colors':[('Trắng','#FFFFFF')]},
    ]

    products = []
    for i, d in enumerate(san_pham_data):
        slug = slugify_vn(d['name']) + f'-{i+1}'
        sp = Product.objects.create(
            name=d['name'], slug=slug, price=d['price'],
            category=cats[d['cat']], is_active=True,
            description=f"Sản phẩm chính hãng chất lượng cao - {d['name']}. Phù hợp cho việc thi đấu và tập luyện."
        )
        for size in d['sizes']:
            for color_name, color_hex in d['colors']:
                ProductVariant.objects.create(
                    product=sp, size=size, color_name=color_name,
                    color_hex=color_hex, stock=random.randint(10, 80)
                )
        products.append(sp)
    print(f"   → Tạo {len(products)} sản phẩm với hàng chục biến thể")

    # ── Khách hàng ──
    print("4. Tạo 50 khách hàng (Có đầy đủ Họ và Tên)...")
    users = []
    for i in range(50):
        ten_day_du = ho_ten()
        email = email_tu_ten(ten_day_du)
        username = f"khachhang_{i+1}_{random.randint(1000,9999)}"

        # Tách Họ và Tên để điền vào bảng User của Django
        parts = ten_day_du.split(' ')
        ho = parts[0]
        ten = " ".join(parts[1:])

        try:
            u = User.objects.create_user(
                username=username,
                email=email,
                password='password123',
                last_name=ho,        # Lưu HỌ
                first_name=ten       # Lưu TÊN
            )
            detail, city = dia_chi()
            Address.objects.create(
                user=u, full_name=ten_day_du, phone=sdt(),
                detail=detail, city=city, is_default=True
            )
            UserProfile.objects.get_or_create(user=u, defaults={'full_name': ten_day_du})
            users.append(u)
        except Exception as e:
            pass
    print(f"   → Tạo {len(users)} khách hàng")

    # ── Đơn hàng ──
    print("5. Tạo các đơn hàng đa dạng...")
    statuses = ['pending', 'confirmed', 'shipping', 'delivered', 'completed', 'cancelled']
    don_hoan_thanh = []
    all_variants = list(ProductVariant.objects.all())

    for u in users:
        addr = u.addresses.first()
        for _ in range(random.randint(2, 5)):
            status = random.choice(['delivered', 'completed', 'completed', 'shipping', 'pending'])
            subtotal = 0
            items_data = []
            for v in random.sample(all_variants, random.randint(1, 4)):
                qty = random.randint(1, 2)
                items_data.append((v, qty))
                subtotal += v.product.price * qty

                # Tạo mã đơn hàng duy nhất tuyệt đối bằng thời gian + số ngẫu nhiên
                unique_order_code = f"DH{int(time.time() * 1000)}{random.randint(1000, 9999)}"

                order = Order.objects.create(
                    order_code=unique_order_code,  # <-- Đã thêm dòng này để chống trùng lặp
                    user=u,
                    recipient_name=addr.full_name if addr else u.username,
                    recipient_phone=addr.phone if addr else '0901234567',
                    shipping_address=addr.detail if addr else '123 Lê Lợi',
                    shipping_city=addr.city if addr else 'Đà Nẵng',
                    payment_method=random.choice(['cod', 'cod', 'bank']),
                    subtotal=subtotal,
                    discount_amount=0,
                    shipping_fee=random.choice([0, 25000, 30000, 35000]),
                    status=status,
                )
            time.sleep(0.005)
            for v, qty in items_data:
                OrderItem.objects.create(
                    order=order, variant=v,
                    product_name=v.product.name,
                    color=v.color_name, size=v.size,
                    price=v.product.price, quantity=qty,
                )
            if status in ('delivered', 'completed'):
                don_hoan_thanh.append(order)

    print(f"   → Tạo {Order.objects.count()} đơn hàng")

    # ── Phiếu trả hàng ──
    print("6. Tạo 40 phiếu trả hàng với kịch bản thực tế...")
    mau_tra_hang = random.sample(don_hoan_thanh, min(40, len(don_hoan_thanh)))

    ret_statuses = (
        ['pending'] * 8 +
        ['rejected'] * 4 +
        ['approved'] * 5 +
        ['picking'] * 5 +
        ['returning_to_warehouse'] * 5 +
        ['received'] * 4 +
        ['processing'] * 4 +
        ['completed'] * 5
    )
    random.shuffle(ret_statuses)

    scenarios = {
        'defective': "Sản phẩm bị bung keo ở phần đế giày.",
        'wrong_item': "Mình đặt áo size M nhưng shop giao size L.",
        'damaged': "Hộp rách nát, tất bên trong bị dính bẩn.",
        'late': "Hàng giao trễ 1 tuần so với dự kiến, mình mua chỗ khác rồi.",
        'quality': "Chất liệu áo khá nóng, không giống quảng cáo.",
        'other': "Mình đi thử thấy chật quá, muốn trả lại."
    }
    shop_faults = ['defective', 'wrong_item', 'damaged', 'late']

    for i, don in enumerate(mau_tra_hang):
        reason = random.choice(list(scenarios.keys()))
        customer_note = scenarios[reason]
        ret_status = ret_statuses[i % len(ret_statuses)]

        admin_note = ""
        if reason in shop_faults:
            refund_val = don.total
        else:
            refund_val = don.subtotal - don.shipping_fee

            if ret_status in ['processing', 'completed'] and random.choice([True, False]):
                refund_val = don.total
                admin_note = "Cập nhật khi kiểm kho: Khách quen, shop hỗ trợ phí ship thu hồi."

        ngan_hang = random.choice(['Vietcombank', 'MB Bank', 'Techcombank', 'BIDV', 'Agribank'])
        so_tk = f"0{random.randint(1000000000, 9999999999)}"
        chu_tk = unicodedata.normalize('NFKD', don.recipient_name).encode('ASCII','ignore').decode().upper()

        if ret_status == 'rejected':
            admin_note = "Lý do từ chối: Sản phẩm đã bị cắt mác và qua sử dụng."
            don.status = 'delivered'
        elif ret_status == 'completed':
            don.status = 'returned'
        elif ret_status != 'pending':
            don.status = 'returning'

        don.save()

        ReturnRequest.objects.create(
            order=don,
            reason=reason,
            note=customer_note,
            status=ret_status,
            refund_amount=refund_val,
            bank_name=ngan_hang,
            bank_account_number=so_tk,
            bank_account_holder=chu_tk,
            admin_note=admin_note
        )

    print(f"   → Tạo {ReturnRequest.objects.count()} phiếu trả hàng.")

    print("\n✅ XONG! Dữ liệu mẫu đã sẵn sàng.")
    print(f"   Users: {User.objects.filter(is_staff=False).count()}")
    print(f"   Sản phẩm: {Product.objects.count()}")
    print(f"   Đơn hàng: {Order.objects.count()}")
    print(f"   Phiếu trả hàng: {ReturnRequest.objects.count()}")

if __name__ == '__main__':
    main()