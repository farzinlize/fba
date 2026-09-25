import sqlalchemy as sa

from backend.utils.dynamic_import import get_all_models


def _register_model_globals() -> None:
    """Import all models and register them in the backend module namespace"""
    for model_obj in get_all_models():
        model_name = model_obj.name if isinstance(model_obj, sa.Table) else model_obj.__name__
        if model_name not in globals():
            globals()[model_name] = model_obj


_register_model_globals()


__version__ = '1.15.1'
