"""
URL configuration for alx-backend-graphql_crm project.
"""
from django.contrib import admin
from django.urls import path
# Import the necessary GraphQL components
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # 1. Define the GraphQL endpoint
    # We use csrf_exempt to allow POST requests (queries/mutations) 
    # from external clients, and set graphiql=True to enable the 
    # interactive testing environment.
    path("graphql", csrf_exempt(GraphQLView.as_view(graphiql=True))),
]