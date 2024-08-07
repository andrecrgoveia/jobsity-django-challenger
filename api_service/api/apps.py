from django.apps import AppConfig


class ApiConfig(AppConfig):
    # Developer's note: Setting the default type for auto-created primary keys
    # to BigAutoField to accommodate large volumes of data.
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
