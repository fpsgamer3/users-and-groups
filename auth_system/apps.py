from django.apps import AppConfig


class AuthSystemConfig(AppConfig):
    name = 'auth_system'

    def ready(self):
        import auth_system.signals  # noqa
