class ReadOnlyDbRouter(object):
    """
    A router for readonly
    """

    def db_for_read(self, model, **hints):
        """
        Point all operations on myapp2 models to 'tcexam'
        """
        if model._meta.app_label == 'csa':
            return 'csa'
 
    # def db_for_write(self, model, **hints):
        # """
        # Point all operations on myapp models to 'other'
        # """
        # disabled
        # if model._meta.app_label == 'csa':
            # return 'csa'
        # return None
 
    # def allow_syncdb(self, db, model):
        # """
        # Make sure the 'myapp2' app only appears on the 'other' db
        # """
        # disabled too
        # if db == 'csa':
            # return model._meta.app_label == 'csa'
        # elif model._meta.app_label == 'csa':
            # return False
        # return None

    # def allow_relation(self, obj1, obj2, **hints):
        # """Determine if relationship is allowed between two objects."""

        # Allow any relation between two models that are both in the Example app.
        # if obj1._meta.app_label == 'csa' and obj2._meta.app_label == 'csa':
            # return True
        # No opinion if neither object is in the Example app (defer to default or other routers).
        # elif 'csa' not in [obj1._meta.app_label, obj2._meta.app_label]:
            # return None

        # Block relationship if one object is in the Example app and the other isn't.
        # return False

    # def allow_migrate(self, db, app_label, model_name=None, **hints):
        # """Ensure that the Example app's models get created on the right database."""
        # if app_label == 'csa':
            # The Example app should be migrated only on the example_db database.
            # return db == 'csa'
        # elif db == 'csa':
            # Ensure that all other apps don't get migrated on the example_db database.
            # return False

        # No opinion for all other scenarios
        # return None
