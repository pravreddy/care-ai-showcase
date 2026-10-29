from django.apps import AppConfig


class OrganisationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'organisations'

    def ready(self):
        # Import signals to register them
        import organisations.signals  # noqa: F401
