from django.apps import AppConfig


class ComplianceBacenConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compliance_bacen'
    verbose_name = 'Compliance BACEN'
    
    def ready(self):
        import compliance_bacen.signals
