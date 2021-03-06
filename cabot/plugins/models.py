from django.db import models
from django.core.urlresolvers import reverse
from django import forms
from polymorphic.models import PolymorphicModel
from picklefield.fields import PickledObjectField
from cabot.cabotapp.models import StatusCheck
from django.contrib.auth.models import User
import os


class AlertPluginUserData(models.Model):
    """A key value model for Alert Plugin user data"""
    plugin = models.ForeignKey('PluginModel')
    key = models.CharField(max_length=128)
    value = PickledObjectField()
    
    class Meta:
        unique_together = ('user', 'key', 'plugin')

    user = models.ForeignKey(User)
    def __unicode__(self):
        return '({}) {}: {}'.format(self.user.username, self.key, self.value)


class Plugin(object):
    """
    The base class for plugins. Inherit from this to create a vanilla plugin
    (without notification or checks functionality)
    """

    # Title of the plugin as seen in cabot
    name = ""
    slug = ""
    author = None
    version = ""
    font_icon = ""

    plugin_variables = []
    
    @property
    def plugin_model(self):
        """Returns the plugin model for the plugin"""
        for p in PluginModel.objects.all():
            if p.slug == self.slug:
                return p
        return None


class AlertPlugin(Plugin):
    # A Django form to handle user settings
    user_config_form = forms.Form
    # The datastore model

    @property
    def plugin_model(self):
        for p in AlertPluginModel.objects.all():
            if p.slug == self.slug:
                return p
        return None
    
    def send_alert(self, service, users, duty_officers):
        """Implement a send_alert function here that shall be called."""
        raise NotImplementedError('{} has not implemented send_alert'.format(self.plugin_model().name))

    def send_alert_update(self, service, users, duty_officers):
        """Implement a send_alert function here that shall be called."""
        raise NotImplementedError('{} has not implemented send_alert_update'.format(self.plugin_model().name))


class StatusCheckPlugin(Plugin):
    config_form = forms.Form
    
    def run(self):
        raise NotImplementedError('{} has not implemented run()'.format(self.plugin_model().name))
    @property
    def plugin_model(self):
        for p in StatusCheckPluginModel.objects.all():
            if p.slug == self.slug:
                return p
        return None

    def description(self, status_check):
        """
        A dynamic description of the check. Should hopefully be unique for every
        check.
        """
        return ""

# A catch-all plugin class to stand in for plugin models with no plugin class
# installed.
class OrphanedPlugin(object):
    name = "Orphaned Plugin"
    slug = ""
    font_icon = "fa fa-exclamation-triangle"
    version = ""
    user_config_form = forms.Form
    config_form = forms.Form
    author = ""
    plugin_variables = []

    def send_alert(self, service, users, duty_officers):
        return False
    def send_alert_update(self, service, users, duty_officers):
        return False
    def run(self, check, result):
        result.succeeded = False
        result.error = "This check has auto failed because the plugin " + \
        "implementing the check is not available. Make sure that plugin " + \
        "is in your production.env and is shown to be installed in the " + \
        "plugins page."
        return result
    def description(self, status_check):
        return "WARNING! The associated plugin is not available"


class PluginModel(PolymorphicModel):
    "Model to represent the Plugin in the database"

    class Meta:
        ordering = ['slug']

    slug = models.CharField(max_length=256, unique=True)
    timestamp_installed = models.DateTimeField(auto_now_add=True)

    # The class used by the plugins to register this model

    def form_fields_iter(self):
        return iter(self.plugin_class.user_config_form().fields)
    def config_form_fields_iter(self):
        return iter(self.plugin_class.config_form().fields)


    def __unicode__(self):
        return '{}'.format(self.slug)

    def get_absolute_url(self):
        return reverse('plugin', self)

    @property
    def plugin_class(self):
        for p in Plugin.__subclasses__():
            if p.slug == self.slug:
                return p()
        return None
    # Mirror the Plugin class variables
    @property
    def name(self):
        return self.plugin_class.name
    @property
    def version(self):
        return self.plugin_class.version
    @property
    def author(self):
        return self.plugin_class.author
    @property
    def plugin_variables(self):
        var_list = self.plugin_class.plugin_variables
        var_dict = dict()
        for var in var_list:
            var_dict[var] = os.environ.get(var, 'VARIABLE NOT SET')

        return var_dict
    @property
    def font_icon(self):
        return self.plugin_class.font_icon if self.plugin_class.font_icon else 'fa fa-cog'


class AlertPluginModel(PluginModel):
    ds_model = AlertPluginUserData

    @property
    def plugin_class(self):
        for p in AlertPlugin.__subclasses__():
            if p.slug == self.slug:
                return p()
        return OrphanedPlugin()

    @property
    def full_name(self):
        return self.name + ' Alerts'
    @property
    def usage(self):
        return self.instance_set.all().count() + \
            self.service_set.all().count()
    
    def send_alert(self, service, users, duty_officers):
        return self.plugin_class.send_alert(service, users, duty_officers)

    def send_alert_update(self, service, users, duty_officers):
        return self.plugin_class.send_alert_update(service, users, duty_officers)


class StatusCheckPluginModel(PluginModel):
    @property
    def plugin_class(self):
        for p in StatusCheckPlugin.__subclasses__():
            if p.slug == self.slug:
                return p()
        return OrphanedPlugin()

    @property
    def get_absolute_create_url(self):
        return '{}?type={}'.format(reverse('checks-create'), self.pk)

    @property
    def full_name(self):
        return self.name + ' Check'
    @property
    def config_form(self):
        return self.plugin_class.config_form
    @property
    def usage(self):
        return StatusCheck.objects.all().count()
    def description(self, check):
        return self.plugin_class.description(check)


class FailedImport(models.Model):
    plugin_name = models.CharField(max_length=256)
    error_message = models.CharField(max_length=1024, null=True)
    timestamp_installed = models.DateTimeField(auto_now_add=True)

