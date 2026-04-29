"""
Script tạo sản phẩm mẫu cho rabonastore.
Chạy: python tao_san_pham.py
"""
import os
import django
import random
import itertools
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rabonastore.settings')
django.setup()

from store.models import Category, Product, ProductVariant
from django.db import connection
from django.utils.text import slugify


def tao_kho_hang_the_thao():
    print("🧹 1. Đang dọn dẹp kho hàng cũ...")
    Product.objects.all().delete()
    Category.objects.all().delete()

    # Reset ID về 1
    try:
        with connection.cursor() as cursor:
            for table in ['store_product', 'store_productvariant', 'store_category']:
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
    except:
        pass

    print("📦 2. Đang nhập hàng mới về kho Rabona Sport...")

    danh_muc_san_pham = [
        # ── GIÀY BÓNG ĐÁ ──────────────────────────────────────────
        {"danh_muc": "Giày bóng đá", "ten": "Giày đá bóng Nike Mercurial Vapor 15 Club TF",
         "mo_ta": "Giày sân cỏ nhân tạo siêu nhẹ, hỗ trợ bứt tốc cực tốt. Form ôm chân.",
         "gia_goc": 1250000},
        {"danh_muc": "Giày bóng đá", "ten": "Giày đá bóng Adidas X Crazyfast.3 TF",
         "mo_ta": "Công nghệ đế EVA êm ái, đinh dăm bám sân kể cả khi trời mưa.",
         "gia_goc": 1450000},
        {"danh_muc": "Giày bóng đá", "ten": "Giày Mizuno Monarcida Neo 2 Select AS",
         "mo_ta": "Thương hiệu Nhật Bản, khâu full đế mũi siêu bền bỉ, hợp form chân bè.",
         "gia_goc": 1150000},
        {"danh_muc": "Giày bóng đá", "ten": "Giày đá bóng Kamito TA11 (Bản Tuấn Anh)",
         "mo_ta": "Giày thương hiệu Việt, da cực mềm, đinh dăm bám sân tốt.",
         "gia_goc": 650000},

        # ── ÁO QUẦN ───────────────────────────────────────────────
        {"danh_muc": "Áo đấu", "ten": "Áo đấu Manchester United Sân Nhà 23/24",
         "mo_ta": "Chất thun lạnh Thái Lan cao cấp, logo thêu sắc nét, thấm hút mồ hôi tốt.",
         "gia_goc": 180000},
        {"danh_muc": "Áo đấu", "ten": "Áo đấu Real Madrid Sân Khách 23/24",
         "mo_ta": "Bản Player Issue ôm body, vải dập vân chìm cực đẹp.",
         "gia_goc": 220000},
        {"danh_muc": "Áo đấu", "ten": "Áo đấu Arsenal Sân Nhà 23/24",
         "mo_ta": "Thiết kế cổ điển kết hợp hiện đại, màu đỏ truyền thống.",
         "gia_goc": 180000},
        {"danh_muc": "Áo đấu", "ten": "Bộ quần áo Đội tuyển Việt Nam 2024",
         "mo_ta": "Cờ in chuyển nhiệt không bong tróc, tự hào tinh thần Việt Nam.",
         "gia_goc": 150000},

        # ── PHỤ KIỆN ──────────────────────────────────────────────
        {"danh_muc": "Phụ kiện", "ten": "Quả bóng đá Động Lực UHV 2.07",
         "mo_ta": "Bóng thi đấu chính thức V-League, độ nảy chuẩn, giữ hơi lâu.",
         "gia_goc": 850000},
        {"danh_muc": "Phụ kiện", "ten": "Tất dệt kim chống trượt Fox",
         "mo_ta": "Có đệm silicon dưới lòng bàn chân, chống trượt xước gót.",
         "gia_goc": 45000},
        {"danh_muc": "Phụ kiện", "ten": "Băng keo thể thao quấn cơ (Cuộn 5cm)",
         "mo_ta": "Băng keo y tế dán cơ, bảo vệ cổ chân, gối khi thi đấu cường độ cao.",
         "gia_goc": 25000},
        {"danh_muc": "Phụ kiện", "ten": "Găng tay thủ môn Adidas Predator Pro",
         "mo_ta": "Mút URG 2.0 siêu dính, có xương bảo vệ tháo lắp linh hoạt.",
         "gia_goc": 650000},
    ]

    # Màu sắc theo danh mục
    COLORS = {
        "Giày bóng đá": [
            ("Đen", "#111111"), ("Trắng", "#F5F5F5"), ("Xanh chuối", "#C8F000"),
            ("Đỏ", "#E63946"), ("Cam", "#FF6B35"),
        ],
        "Áo đấu": [
            ("Đỏ", "#E63946"), ("Trắng", "#F5F5F5"), ("Xanh navy", "#1D3557"),
            ("Vàng", "#FFD60A"),
        ],
        "Phụ kiện": [
            ("Tiêu chuẩn", "#888888"),
        ],
    }

    SIZES = {
        "Giày bóng đá": ["39", "40", "41", "42", "43"],
        "Áo đấu":       ["S", "M", "L", "XL"],
        "Phụ kiện":     ["Freesize"],
    }

    dem = 0
    for item in danh_muc_san_pham:
        ten_dm = item["danh_muc"]

        # Tạo hoặc lấy danh mục
        slug_dm = slugify(ten_dm) + "-2727"
        cat, _ = Category.objects.get_or_create(
            slug=slug_dm,
            defaults={"name": ten_dm}
        )

        # Tạo sản phẩm
        slug_sp = slugify(item["ten"]) + f"-{int(time.time())}-{dem}"
        sp = Product.objects.create(
            name=item["ten"],
            slug=slug_sp,
            description=item["mo_ta"],
            price=item["gia_goc"],
            category=cat,
            is_active=True,
        )

        # Tạo biến thể
        sizes  = SIZES.get(ten_dm, ["Freesize"])
        colors = COLORS.get(ten_dm, [("Mặc định", "#888888")])
        selected_colors = random.sample(colors, random.randint(1, min(3, len(colors))))

        for size, (color_name, color_hex) in itertools.product(sizes, selected_colors):
            ton_kho = 0 if random.random() < 0.1 else random.randint(5, 150)
            ProductVariant.objects.get_or_create(
                product=sp,
                size=size,
                color_name=color_name,
                defaults={
                    "color_hex": color_hex,
                    "stock": ton_kho,
                }
            )

        dem += 1
        print(f"  ✅ [{dem:02d}] {item['ten']}")

    print(f"\n🎉 HOÀN TẤT! Đã nhập {dem} sản phẩm với hàng trăm biến thể vào kho.")


if __name__ == '__main__':
    tao_kho_hang_the_thao()
