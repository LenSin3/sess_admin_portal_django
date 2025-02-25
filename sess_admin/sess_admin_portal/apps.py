from django.apps import AppConfig


class SessAdminPortalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sess_admin_portal"
    
    def ready(self):
        import sess_admin_portal.signals
