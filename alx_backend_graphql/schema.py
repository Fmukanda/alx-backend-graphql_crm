import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(graphene.ObjectType):
    """Root GraphQL query class"""
    
    hello = graphene.String(
        description="A simple hello world GraphQL field"
    )
    
    def resolve_hello(root, info):
        """Resolver for the hello field"""
        return "Hello, GraphQL!"

class Query(CRMQuery, graphene.ObjectType):
    """Root query that combines all app queries"""
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    """Root mutation that combines all app mutations"""
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
