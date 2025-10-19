import django_filters
from django.db import models
from .models import Customer, Product, Order

class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name contains')
    email = django_filters.CharFilter(lookup_expr='icontains', label='Email contains')
    created_at_gte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte', label='Created after')
    created_at_lte = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte', label='Created before')
    
    # Custom filter for phone pattern
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern', label='Phone pattern')
    
    # Ordering filter
    order_by = django_filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('email', 'email'),
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
        ),
        field_labels={
            'name': 'Name',
            'email': 'Email',
            'created_at': 'Creation Date',
            'updated_at': 'Update Date',
        }
    )
    
    class Meta:
        model = Customer
        fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'created_at': ['exact', 'gte', 'lte'],
        }
    
    def filter_phone_pattern(self, queryset, name, value):
        """
        Custom filter to match phone numbers starting with a specific pattern
        Example: filter by phone numbers starting with '+1'
        """
        if value:
            return queryset.filter(phone__startswith=value)
        return queryset

class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Name contains')
    price_gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte', label='Minimum price')
    price_lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte', label='Maximum price')
    stock_gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte', label='Minimum stock')
    stock_lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte', label='Maximum stock')
    
    # Custom filter for low stock
    low_stock = django_filters.BooleanFilter(method='filter_low_stock', label='Low stock (less than 10)')
    
    # Ordering filter
    order_by = django_filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('price', 'price'),
            ('stock', 'stock'),
            ('created_at', 'created_at'),
        ),
        field_labels={
            'name': 'Name',
            'price': 'Price',
            'stock': 'Stock',
            'created_at': 'Creation Date',
        }
    )
    
    class Meta:
        model = Product
        fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }
    
    def filter_low_stock(self, queryset, name, value):
        """
        Custom filter for products with low stock (less than 10)
        """
        if value:
            return queryset.filter(stock__lt=10)
        return queryset

class OrderFilter(django_filters.FilterSet):
    total_amount_gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte', label='Minimum total amount')
    total_amount_lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte', label='Maximum total amount')
    order_date_gte = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='gte', label='Ordered after')
    order_date_lte = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='lte', label='Ordered before')
    
    # Related field filters
    customer_name = django_filters.CharFilter(field_name='customer__name', lookup_expr='icontains', label='Customer name contains')
    product_name = django_filters.CharFilter(field_name='products__name', lookup_expr='icontains', label='Product name contains')
    
    # Custom filter for specific product ID
    product_id = django_filters.ModelChoiceFilter(
        field_name='products',
        queryset=Product.objects.all(),
        label='Contains specific product'
    )
    
    # Ordering filter
    order_by = django_filters.OrderingFilter(
        fields=(
            ('total_amount', 'total_amount'),
            ('order_date', 'order_date'),
            ('customer__name', 'customer_name'),
            ('created_at', 'created_at'),
        ),
        field_labels={
            'total_amount': 'Total Amount',
            'order_date': 'Order Date',
            'customer__name': 'Customer Name',
            'created_at': 'Creation Date',
        }
    )
    
    class Meta:
        model = Order
        fields = {
            'total_amount': ['exact', 'gte', 'lte'],
            'order_date': ['exact', 'gte', 'lte'],
            'customer__name': ['exact', 'icontains'],
            'products__name': ['exact', 'icontains'],
        }