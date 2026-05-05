import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rabonastore.settings')
django.setup()
from store.models import Category, Product

# Fix slug sai về đúng
fixes = [
    ('giay-bong-a-3927', 'giay-bong-da'),
    ('ao-au-3927', 'ao-dau'),
    ('phu-kien-3927', 'phu-kien'),
    ('bong-thi-au-3927', 'bong-thi-dau'),
]
for old, new in fixes:
    n = Category.objects.filter(slug=old).update(slug=new)
    if n:
        print(f'Fixed: {old} -> {new}')

# Hiện tất cả category hiện tại
print('\nAll categories:')
for c in Category.objects.all():
    print(f'  id={c.id} slug={c.slug} name={c.name}')

print(f'\nTotal products: {Product.objects.count()}')
