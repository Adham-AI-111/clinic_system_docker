from django.apps import AppConfig


class ReceptionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'reception'
    
    def ready(self):
        """Register signals when app is ready"""
        import reception.signals  # noqa
