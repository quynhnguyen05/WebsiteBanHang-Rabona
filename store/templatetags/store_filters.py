from django import template

register = template.Library()


@register.filter
def vnd(value):
    """Format số thành giá VND với dấu chấm phân cách hàng nghìn.
    Ví dụ: 55000 → 55.000đ
    """
    try:
        num = int(float(str(value).replace(',', '').replace('.', '')))
        return f"{num:,}".replace(',', '.') + 'đ'
    except (ValueError, TypeError):
        return str(value)
