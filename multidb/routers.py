class MultiDBRouter:
    app_label = 'multidb'
    model_to_db = {
        'appuser': 'users',
        'product': 'products',
        'order': 'orders',
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return self.model_to_db.get(model._meta.model_name)
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return self.model_to_db.get(model._meta.model_name)
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label != self.app_label:
            return None
        return db == self.model_to_db.get(model_name)
