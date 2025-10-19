import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    """Root query that combines all app queries"""
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    """Root mutation that combines all app mutations"""
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)