from djangoldp.models import Model
from djangoldp.urls import get_all_non_abstract_subclasses


def get_all_model_rdf_types():
    """Returns all model RDF types configured in the application"""
    return [
        model._meta.rdf_type
        for model in get_all_non_abstract_subclasses(Model)
        if hasattr(model._meta, "rdf_type")
    ]
