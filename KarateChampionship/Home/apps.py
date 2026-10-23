from django.apps import AppConfig


class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Home'

    def ready(self):
        from django.db.models.signals import post_delete, post_save
        from .rules import CONFIG_MODELS, clear_config_cache

        for model in CONFIG_MODELS:
            post_save.connect(clear_config_cache, sender=model, dispatch_uid=f'config-save-{model.__name__}')
            post_delete.connect(clear_config_cache, sender=model, dispatch_uid=f'config-delete-{model.__name__}')
