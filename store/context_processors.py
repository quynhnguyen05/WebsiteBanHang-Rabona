from .models import Cart


def cart_count(request):
    """Inject số lượng sản phẩm trong giỏ vào mọi template."""
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.cart.total_items
        except Cart.DoesNotExist:
            pass
    return {'cart_count': count}
