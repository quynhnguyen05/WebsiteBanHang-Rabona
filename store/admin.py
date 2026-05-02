from django.contrib import admin
from .models import (
    Category, Product, ProductImage, ProductVariant,
    Cart, CartItem, Address,
    Order, OrderItem, ReturnRequest, UserProfile
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'total_stock', 'sold', 'is_active']
    list_filter   = ('category', 'is_active', 'gender')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_items', 'total_price', 'updated_at')
    inlines = [CartItemInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('order_code', 'user', 'status', 'payment_method', 'total', 'created_at')
    list_filter   = ('status', 'payment_method', 'shipping_method')
    list_editable = ('status',)
    search_fields = ('order_code', 'user__username', 'recipient_name')
    readonly_fields = ('order_code', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    actions = ['mark_shipping', 'mark_completed', 'mark_delivered']

    @admin.action(description='Đánh dấu: Đang vận chuyển')
    def mark_shipping(self, request, queryset):
        queryset.update(status='shipping')

    @admin.action(description='Đánh dấu: Đã giao hàng')
    def mark_delivered(self, request, queryset):
        queryset.update(status='delivered')

    @admin.action(description='Đánh dấu: Hoàn thành')
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'reason', 'status', 'created_at')
    list_filter  = ('status', 'reason')


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'city', 'is_default')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'phone', 'gender')
