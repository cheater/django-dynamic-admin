from django.contrib import admin

def get_admin_class(model_class):
    """ Gets the admin class registered for the passed model
        class. If the model class has not been registered, the
        function returns admin.ModelAdmin."""
    try:
        admin_class = admin.site._registry[model_class].__class__
    except KeyError:
        admin_class = admin.ModelAdmin
    return admin_class

def attach_inline_to_admin(model_class, model_enhancement,
    inline_class=admin.StackedInline):
    """ This function enhances a model's admin page by inlining
        a model that inherits from it (in Django parlance).

        You feed it a model and the model's "sub class".

        So for example you have model MyModel which you don't want to
        modify (e.g. it's a core part of Django or just a separate
        model), and you want some extra information to be editable on
        the admin page of that model. You create a new class:

        class MyModelEnhanced(models.Model):
            my_model = models.OneToOneField(MyModel, primary_key=True)
            some_extra_field = models.TextField()

        The crucial parts are:
        - do *not* inherit from MyModel, instead inherit your Python
        class from models.Model. Otherwise your inline will contain
        a copy of each field that's in the admin already, which is
        bad, and can probably break your database very easily
        - give the class a single primary key, and make it a
        OneToOneField to the model you are enhancing (MyModel), just
        like in the example above.

        Then, you just do attach_inline_to_admin(MyModel, MyModelEnhanced).
        """

    admin_class = get_admin_class(model_class)
    admin.site.unregister(model_class)
    Inline = type("Inline", (inline_class,), {
        'model': model_enhancement,
        })
    NewModelAdmin = type("NewModelAdmin", (admin_class,), {
        'inlines': getattr(admin_class, 'inlines', []) + [Inline]
        })
    admin.site.register(model_class, NewModelAdmin)

def add_column_to_changelist(model_class, column, link=False, prepend=False):
    """ This function lets you add columns to the changelist of a model.
        You can use a string or a callable, just like in list_display.
        """
    admin_class = get_admin_class(model_class)
    admin.site.unregister(model_class)
    new_list_display = getattr(
        admin_class,
        'list_display',
        ['pk']
        )
    new_list_display = list(new_list_display)
    new_list_display_links = getattr(
        admin_class,
        'list_display_links',
        []
        )
    if new_list_display and not new_list_display_links:
        new_list_display_links = [new_list_display[0]]

    new_list_display_links = list(new_list_display_links)

    if prepend:
        new_list_display = [column] + new_list_display
    else:
        new_list_display.append(column)

    if link and isinstance(column, basestring):
        new_list_display_links.append(column)

    NewModelAdmin = type("NewModelAdmin", (admin_class,), {
        'list_display': new_list_display,
        'list_display_links': new_list_display_links,
        })
    admin.site.register(model_class, NewModelAdmin)

def override_admin(model_class, admin_enhancement, prefer_new=False):
    """ This function overrides the current admin page for the
        passed model by a new one which inherits from the current
        one as well as the (new) admin enhancing class. This new
        admin class is registered for the given model class.

        For example you could use it to add some more properties
        to the admin class.

        parameter prefer_new:
        By default, when the argument prefer_new is False, the old
        class is inherited from first, the new class is inherited
        from second. If you set the argument to be True then the
        new class is inherited from first and the old class is
        inherited from second. You can use that to mask behaviours
        of the old class. You can use this creatively together
        with get_admin_class()."""

    admin_class = get_admin_class(model_class)

    x, y = admin_class, admin_enhancement
    if prefer_new:
        y, x = x, y
    NewModelAdmin = type("NewModelAdmin", (x, y), {})
    admin.site.register(model_class, NewModelAdmin)
