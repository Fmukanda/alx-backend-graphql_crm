import graphene

class Query(graphene.ObjectType):
    """Root GraphQL query class"""
    
    hello = graphene.String(
        description="A simple hello world GraphQL field"
    )
    
    def resolve_hello(root, info):
        """Resolver for the hello field"""
        return "Hello, GraphQL!"

# Create schema instance
schema = graphene.Schema(query=Query)