from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
import re

class Customer(models.Model):
    """Customer model for CRM"""
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        """Validate phone format"""
        if self.phone and not self.validate_phone_format():
            raise ValidationError({'phone': 'Phone number must be in format: +1234567890 or 123-456-7890'})
    
    def validate_phone_format(self):
        """Validate phone format using regex"""
        phone_pattern = r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$'
        return bool(re.match(phone_pattern, self.phone))

class Product(models.Model):
    """Product model for CRM"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    stock = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - ${self.price}"

class Order(models.Model):
    """Order model for CRM"""
    customer = models.ForeignKey(
        Customer, 
        on_delete=models.CASCADE, 
        related_name='orders'
    )
    products = models.ManyToManyField(
        Product, 
        through='OrderItem',
        related_name='orders'
    )
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    order_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-order_date']
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.name}"

class OrderItem(models.Model):
    """Through model for Order-Product relationship"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ['order', 'product']
    
    def save(self, *args, **kwargs):
        """Calculate unit price from product price"""
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} in Order #{self.order.id}"