import graphene
from graphene_django.types import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from graphql import GraphQLError
import decimal
import re

from .models import Customer, Product, Order, OrderItem

# GraphQL Types
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            'name': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
        }

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            'name': ['exact', 'icontains'],
            'price': ['exact', 'gte', 'lte'],
        }

class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem

class OrderType(DjangoObjectType):
    total_amount = graphene.Decimal()
    
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            'customer__name': ['exact', 'icontains'],
            'order_date': ['exact', 'gte', 'lte'],
        }
    
    def resolve_total_amount(self, info):
        return self.total_amount

# Input Types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class BulkCustomerInput(graphene.InputObjectType):
    customers = graphene.List(CustomerInput, required=True)

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    description = graphene.String()
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(required=True)
    product_ids = graphene.List(graphene.ID, required=True)
    order_date = graphene.DateTime()

# Response Types
class CustomerResponse(graphene.ObjectType):
    success = graphene.Boolean()
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

class BulkCustomerResponse(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

class ProductResponse(graphene.ObjectType):
    success = graphene.Boolean()
    product = graphene.Field(ProductType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

class OrderResponse(graphene.ObjectType):
    success = graphene.Boolean()
    order = graphene.Field(OrderType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

# Utility Functions
def validate_phone_format(phone):
    """Validate phone format"""
    if phone:
        phone_pattern = r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$'
        return bool(re.match(phone_pattern, phone))
    return True

def validate_email_unique(email, exclude_id=None):
    """Validate email uniqueness"""
    queryset = Customer.objects.filter(email=email)
    if exclude_id:
        queryset = queryset.exclude(id=exclude_id)
    return not queryset.exists()

# Mutations
class CreateCustomer(graphene.Mutation):
    """Mutation to create a single customer"""
    
    class Arguments:
        input = CustomerInput(required=True)

    Output = CustomerResponse

    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate phone format
            if input.phone and not validate_phone_format(input.phone):
                return CustomerResponse(
                    success=False,
                    customer=None,
                    message="Validation failed",
                    errors=["Phone number must be in format: +1234567890 or 123-456-7890"]
                )

            # Validate email uniqueness
            if not validate_email_unique(input.email):
                return CustomerResponse(
                    success=False,
                    customer=None,
                    message="Validation failed",
                    errors=["Email already exists"]
                )

            customer = Customer(
                name=input.name,
                email=input.email,
                phone=input.phone or ""
            )
            
            # Full model validation
            customer.full_clean()
            customer.save()

            return CustomerResponse(
                success=True,
                customer=customer,
                message="Customer created successfully",
                errors=None
            )

        except DjangoValidationError as e:
            errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            return CustomerResponse(
                success=False,
                customer=None,
                message="Validation failed",
                errors=errors
            )
        except Exception as e:
            return CustomerResponse(
                success=False,
                customer=None,
                message="Failed to create customer",
                errors=[str(e)]
            )

class BulkCreateCustomers(graphene.Mutation):
    """Mutation to create multiple customers with partial success support"""
    
    class Arguments:
        input = BulkCustomerInput(required=True)

    Output = BulkCustomerResponse

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        created_customers = []
        errors = []
        
        for index, customer_data in enumerate(input.customers):
            try:
                # Check for duplicate email in the same request
                existing_emails = [c.email for c in created_customers]
                if customer_data.email in existing_emails:
                    errors.append(f"Row {index + 1}: Email '{customer_data.email}' is duplicated in this request")
                    continue

                # Check for existing email in database
                if not validate_email_unique(customer_data.email):
                    errors.append(f"Row {index + 1}: Email '{customer_data.email}' already exists")
                    continue

                # Validate phone format
                if customer_data.phone and not validate_phone_format(customer_data.phone):
                    errors.append(f"Row {index + 1}: Phone number must be in format: +1234567890 or 123-456-7890")
                    continue

                customer = Customer(
                    name=customer_data.name,
                    email=customer_data.email,
                    phone=customer_data.phone or ""
                )
                
                customer.full_clean()
                customer.save()
                created_customers.append(customer)

            except DjangoValidationError as e:
                error_messages = []
                for field, field_errors in e.message_dict.items():
                    for error in field_errors:
                        error_messages.append(f"{field}: {error}")
                errors.append(f"Row {index + 1}: {', '.join(error_messages)}")
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")

        return BulkCustomerResponse(
            customers=created_customers,
            errors=errors
        )

class CreateProduct(graphene.Mutation):
    """Mutation to create a product"""
    
    class Arguments:
        input = ProductInput(required=True)

    Output = ProductResponse

    @staticmethod
    def mutate(root, info, input):
        try:
            # Validate price is positive
            if input.price <= 0:
                return ProductResponse(
                    success=False,
                    product=None,
                    message="Validation failed",
                    errors=["Price must be greater than 0"]
                )

            # Validate stock is non-negative
            stock = input.stock if input.stock is not None else 0
            if stock < 0:
                return ProductResponse(
                    success=False,
                    product=None,
                    message="Validation failed",
                    errors=["Stock cannot be negative"]
                )

            product = Product(
                name=input.name,
                description=input.description or "",
                price=input.price,
                stock=stock
            )
            
            product.full_clean()
            product.save()

            return ProductResponse(
                success=True,
                product=product,
                message="Product created successfully",
                errors=None
            )

        except DjangoValidationError as e:
            errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            return ProductResponse(
                success=False,
                product=None,
                message="Validation failed",
                errors=errors
            )
        except Exception as e:
            return ProductResponse(
                success=False,
                product=None,
                message="Failed to create product",
                errors=[str(e)]
            )

class CreateOrder(graphene.Mutation):
    """Mutation to create an order with product associations"""
    
    class Arguments:
        input = OrderInput(required=True)

    Output = OrderResponse

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        try:
            # Validate customer exists
            try:
                customer = Customer.objects.get(id=input.customer_id)
            except Customer.DoesNotExist:
                return OrderResponse(
                    success=False,
                    order=None,
                    message="Validation failed",
                    errors=[f"Customer with ID {input.customer_id} does not exist"]
                )

            # Validate at least one product
            if not input.product_ids:
                return OrderResponse(
                    success=False,
                    order=None,
                    message="Validation failed",
                    errors=["At least one product is required"]
                )

            # Validate products exist and get them
            products = []
            invalid_product_ids = []
            for product_id in input.product_ids:
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    invalid_product_ids.append(str(product_id))

            if invalid_product_ids:
                return OrderResponse(
                    success=False,
                    order=None,
                    message="Validation failed",
                    errors=[f"Invalid product IDs: {', '.join(invalid_product_ids)}"]
                )

            # Calculate total amount
            total_amount = sum(product.price for product in products)

            # Create order
            order = Order(
                customer=customer,
                total_amount=total_amount
            )
            
            if input.order_date:
                order.order_date = input.order_date
            
            order.full_clean()
            order.save()

            # Create order items
            for product in products:
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    unit_price=product.price,
                    quantity=1
                )

            # Refresh order to get related data
            order.refresh_from_db()

            return OrderResponse(
                success=True,
                order=order,
                message="Order created successfully",
                errors=None
            )

        except DjangoValidationError as e:
            errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            return OrderResponse(
                success=False,
                order=None,
                message="Validation failed",
                errors=errors
            )
        except Exception as e:
            return OrderResponse(
                success=False,
                order=None,
                message="Failed to create order",
                errors=[str(e)]
            )

# Query Class
class Query(graphene.ObjectType):
    hello = graphene.String(description="A simple hello world GraphQL field")
    
    # Customer queries
    customer = graphene.Field(CustomerType, id=graphene.ID(required=True))
    all_customers = DjangoFilterConnectionField(CustomerType)
    
    # Product queries
    product = graphene.Field(ProductType, id=graphene.ID(required=True))
    all_products = DjangoFilterConnectionField(ProductType)
    
    # Order queries
    order = graphene.Field(OrderType, id=graphene.ID(required=True))
    all_orders = DjangoFilterConnectionField(OrderType)

    def resolve_hello(self, info):
        return "Hello, GraphQL!"

    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None

    def resolve_all_customers(self, info, **kwargs):
        return Customer.objects.all()

    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None

    def resolve_all_products(self, info, **kwargs):
        return Product.objects.all()

    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None

    def resolve_all_orders(self, info, **kwargs):
        return Order.objects.all()

    # Enhanced filtered queries with custom resolvers
    filtered_customers = graphene.List(
        CustomerType,
        filter=CustomerFilterInput(required=False),
        order_by=graphene.String(required=False)
    )
    
    filtered_products = graphene.List(
        ProductType,
        filter=ProductFilterInput(required=False),
        order_by=graphene.String(required=False)
    )
    
    filtered_orders = graphene.List(
        OrderType,
        filter=OrderFilterInput(required=False),
        order_by=graphene.String(required=False)
    )

    def resolve_filtered_customers(self, info, filter=None, order_by=None):
        queryset = Customer.objects.all()
        
        if filter:
            if filter.get('name_icontains'):
                queryset = queryset.filter(name__icontains=filter['name_icontains'])
            if filter.get('email_icontains'):
                queryset = queryset.filter(email__icontains=filter['email_icontains'])
            if filter.get('created_at_gte'):
                queryset = queryset.filter(created_at__gte=filter['created_at_gte'])
            if filter.get('created_at_lte'):
                queryset = queryset.filter(created_at__lte=filter['created_at_lte'])
            if filter.get('phone_pattern'):
                queryset = queryset.filter(phone__startswith=filter['phone_pattern'])
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset

    def resolve_filtered_products(self, info, filter=None, order_by=None):
        queryset = Product.objects.all()
        
        if filter:
            if filter.get('name_icontains'):
                queryset = queryset.filter(name__icontains=filter['name_icontains'])
            if filter.get('price_gte'):
                queryset = queryset.filter(price__gte=filter['price_gte'])
            if filter.get('price_lte'):
                queryset = queryset.filter(price__lte=filter['price_lte'])
            if filter.get('stock_gte'):
                queryset = queryset.filter(stock__gte=filter['stock_gte'])
            if filter.get('stock_lte'):
                queryset = queryset.filter(stock__lte=filter['stock_lte'])
            if filter.get('low_stock') is not None:
                if filter['low_stock']:
                    queryset = queryset.filter(stock__lt=10)
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset

    def resolve_filtered_orders(self, info, filter=None, order_by=None):
        queryset = Order.objects.all()
        
        if filter:
            if filter.get('total_amount_gte'):
                queryset = queryset.filter(total_amount__gte=filter['total_amount_gte'])
            if filter.get('total_amount_lte'):
                queryset = queryset.filter(total_amount__lte=filter['total_amount_lte'])
            if filter.get('order_date_gte'):
                queryset = queryset.filter(order_date__gte=filter['order_date_gte'])
            if filter.get('order_date_lte'):
                queryset = queryset.filter(order_date__lte=filter['order_date_lte'])
            if filter.get('customer_name'):
                queryset = queryset.filter(customer__name__icontains=filter['customer_name'])
            if filter.get('product_name'):
                queryset = queryset.filter(products__name__icontains=filter['product_name'])
            if filter.get('product_id'):
                queryset = queryset.filter(products__id=filter['product_id'])
        
        if order_by:
            queryset = queryset.order_by(order_by)
        
        return queryset.distinct()

# Add to existing Response Types
class LowStockUpdateResponse(graphene.ObjectType):
    success = graphene.Boolean()
    updated_products = graphene.List(ProductType)
    message = graphene.String()
    errors = graphene.List(graphene.String)

# Add to existing Mutations
class UpdateLowStockProducts(graphene.Mutation):
    """Mutation to update low-stock products by restocking them"""
    
    class Arguments:
        restock_amount = graphene.Int(default_value=10)

    Output = LowStockUpdateResponse

    @staticmethod
    @transaction.atomic
    def mutate(root, info, restock_amount=10):
        try:
            # Validate restock amount
            if restock_amount <= 0:
                return LowStockUpdateResponse(
                    success=False,
                    updated_products=[],
                    message="Validation failed",
                    errors=["Restock amount must be greater than 0"]
                )

            # Find products with low stock (stock < 10)
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            if not low_stock_products.exists():
                return LowStockUpdateResponse(
                    success=True,
                    updated_products=[],
                    message="No low-stock products found",
                    errors=None
                )

            # Update stock for each low-stock product
            updated_products = []
            for product in low_stock_products:
                old_stock = product.stock
                product.stock += restock_amount
                product.full_clean()
                product.save()
                updated_products.append(product)

            return LowStockUpdateResponse(
                success=True,
                updated_products=updated_products,
                message=f"Successfully updated {len(updated_products)} low-stock products",
                errors=None
            )

        except DjangoValidationError as e:
            errors = []
            for field, field_errors in e.message_dict.items():
                for error in field_errors:
                    errors.append(f"{field}: {error}")
            return LowStockUpdateResponse(
                success=False,
                updated_products=[],
                message="Validation failed during update",
                errors=errors
            )
        except Exception as e:
            return LowStockUpdateResponse(
                success=False,
                updated_products=[],
                message="Failed to update low-stock products",
                errors=[str(e)]
            )

# Update the Mutation class to include the new mutation
class Mutation(graphene.ObjectType):
    # Customer mutations
    create_customer = CreateCustomer.Field()
    update_customer = UpdateCustomer.Field()
    delete_customer = DeleteCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    
    # Product mutations
    create_product = CreateProduct.Field()
    update_product = UpdateProduct.Field()
    delete_product = DeleteProduct.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()  # Add this line
    
    # Order mutations
    create_order = CreateOrder.Field()
    update_order = UpdateOrder.Field()
    delete_order = DeleteOrder.Field()
