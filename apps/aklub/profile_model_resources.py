# -*- coding: utf-8 -*-

from django.apps import apps

from import_export import fields
from import_export.resources import ModelResource

from aklub.models import Profile
from .profile_model_resources_mixin import (
    get_profile_model_resource_mixin_class_body,
)


def dehydrate_base(self, profile):
    pass


def get_polymorphic_parent_child_fields(parent_model):
    exclude_fields = {"profile_ptr"}
    parent_model_fields = [f.name for f in parent_model._meta.fields]
    result = {}
    for child_model in parent_model.__subclasses__():
        child_model_fields = [f.name for f in child_model._meta.fields]
        child_model_fields_only = set(parent_model_fields).symmetric_difference(
            set(child_model_fields)
        )
        child_model_fields_only = child_model_fields_only - exclude_fields
        result[child_model._meta.model_name] = child_model_fields_only
    return result


def dehydrate_decorator(field):
    def wrap(f):
        def wrapped_f(self, profile):
            if profile.pk and field in (f.name for f in profile._meta.fields):
                return getattr(profile, field)
            else:
                return None

        return wrapped_f

    return wrap


def get_parent_child_instance(self, row):
    return apps.get_model("aklub", row["profile_type"])()


def init_instance(self, row=None):
    return self.get_polymorphic_child_instance(row=row)


def get_profile_model_resource_class_body(parent_model):
    body = {}
    all_child_models_fields = get_polymorphic_parent_child_fields(
        parent_model=parent_model
    )
    for model, model_fields in all_child_models_fields.items():
        for field in model_fields:
            # Additional child field
            body[field] = fields.Field()
            # Additional child field dehydrate method
            dehydrate_func = (dehydrate_decorator(field=field))(dehydrate_base)
            body["dehydrate_{}".format(field)] = dehydrate_func

    body["get_polymorphic_child_instance"] = get_parent_child_instance
    body["init_instance"] = init_instance

    # Get profile model resource mixin class body
    body.update(get_profile_model_resource_mixin_class_body())

    return body


ProfileModelResource = type(
    "ProfileModelResource",
    (ModelResource,),
    get_profile_model_resource_class_body(parent_model=Profile),
)
