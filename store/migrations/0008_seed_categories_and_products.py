from django.db import migrations


def seed_data(apps, schema_editor):
    Category = apps.get_model('store', 'Category')
    Product = apps.get_model('store', 'Product')
    ProductVariant = apps.get_model('store', 'ProductVariant')

    # ── Danh mục ──────────────────────────────────────────────────────────────
    cat_giay, _ = Category.objects.get_or_create(
        slug='giay-bong-a-3927',
        defaults={'name': 'Giày bóng đá'},
    )
    Category.objects.get_or_create(
        slug='ao-au-3927',
        defaults={'name': 'Quần áo'},
    )
    Category.objects.get_or_create(
        slug='phu-kien-3927',
        defaults={'name': 'Phụ kiện'},
    )

    # ── Sản phẩm (chỉ tạo nếu chưa tồn tại) ──────────────────────────────────
    products_data = [
        {
            'slug': 'giay-bong-da-lingy-ust083',
            'name': 'Giày bóng đá Lingy UST083',
            'description': 'Giày đá bóng Lingy UST083 được thiết kế với đế cao su giảm chấn, mang lại cảm giác thoải mái khi di chuyển.',
            'price': 1120000,
            'sold': 2000,
            'origin': 'Việt Nam',
            'gender': 'unisex',
            'variants': [
                {'color_name': 'Cam',   'color_hex': '#F04B3A', 'size': '40', 'stock': 10},
                {'color_name': 'Trắng', 'color_hex': '#F2F2F2', 'size': '40', 'stock': 8},
                {'color_name': 'Vàng',  'color_hex': '#FFE27A', 'size': '41', 'stock': 5},
            ],
        },
        {
            'slug': 'nike-mercurial-vapor-13-pro',
            'name': 'Giày bóng đá Nike Mercurial Vapor 13 Pro',
            'description': 'Nike Mercurial Vapor 13 Pro Hard Ground - tốc độ và kiểm soát tuyệt vời.',
            'price': 799000,
            'sold': 1500,
            'origin': 'Việt Nam',
            'gender': 'unisex',
            'variants': [
                {'color_name': 'Vàng',  'color_hex': '#F5E65E', 'size': '40', 'stock': 7},
                {'color_name': 'Trắng', 'color_hex': '#EFEFEF', 'size': '40', 'stock': 6},
                {'color_name': 'Hồng',  'color_hex': '#FF5A86', 'size': '39', 'stock': 4},
            ],
        },
        {
            'slug': 'adidas-f5e-elite-lawn',
            'name': 'Giày bóng đá Adidas F5E Elite Lawn',
            'description': 'Adidas F5E Elite Lawn - thiết kế nhẹ, phù hợp sân cỏ nhân tạo.',
            'price': 270000,
            'sold': 800,
            'origin': 'Việt Nam',
            'gender': 'unisex',
            'variants': [
                {'color_name': 'Đỏ',    'color_hex': '#D14B63', 'size': '38', 'stock': 12},
                {'color_name': 'Trắng', 'color_hex': '#F6F6F6', 'size': '39', 'stock': 9},
            ],
        },
        {
            'slug': 'nike-mercurial-vapor-16-elite',
            'name': 'Giày bóng đá Nike Mercurial Vapor 16 Elite',
            'description': 'Nike Mercurial Vapor 16 Elite - công nghệ mới nhất từ Nike.',
            'price': 750000,
            'sold': 600,
            'origin': 'Việt Nam',
            'gender': 'unisex',
            'variants': [
                {'color_name': 'Xanh', 'color_hex': '#2C6CF6', 'size': '40', 'stock': 5},
                {'color_name': 'Cam',  'color_hex': '#FF7A18', 'size': '41', 'stock': 3},
            ],
        },
        {
            'slug': 'mizuno-neo-4',
            'name': 'Giày bóng đá Mizuno Neo 4',
            'description': 'Mizuno Neo 4 - chất lượng Nhật Bản, bền bỉ và thoải mái.',
            'price': 365000,
            'sold': 400,
            'origin': 'Việt Nam',
            'gender': 'unisex',
            'variants': [
                {'color_name': 'Đen', 'color_hex': '#111111', 'size': '40', 'stock': 8},
                {'color_name': 'Đỏ',  'color_hex': '#FF4D4D', 'size': '42', 'stock': 6},
            ],
        },
    ]

    for data in products_data:
        variants = data.pop('variants')
        product, created = Product.objects.get_or_create(
            slug=data['slug'],
            defaults={**data, 'category': cat_giay, 'is_active': True},
        )
        if created:
            for v in variants:
                ProductVariant.objects.get_or_create(
                    product=product,
                    color_name=v['color_name'],
                    size=v['size'],
                    defaults={'color_hex': v['color_hex'], 'stock': v['stock']},
                )


def unseed_data(apps, schema_editor):
    """Reverse: xóa dữ liệu seed (chỉ xóa nếu không có đơn hàng liên quan)."""
    Category = apps.get_model('store', 'Category')
    Category.objects.filter(
        slug__in=['giay-bong-a-3927', 'ao-au-3927', 'phu-kien-3927']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0007_returnrequest_refund_amount'),
    ]

    operations = [
        migrations.RunPython(seed_data, reverse_code=unseed_data),
    ]
