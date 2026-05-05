import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rabonastore.settings')
django.setup()
from django.contrib.auth.models import User
if User.objects.filter(username='admin').exists():
    u = User.objects.get(username='admin')
    u.set_password('admin123')
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Da cap nhat tai khoan admin')
else:
    User.objects.create_superuser('admin', 'admin@admin.com', 'admin123')
    print('Da tao tai khoan admin moi')
print('Username: admin')
print('Password: admin123')
