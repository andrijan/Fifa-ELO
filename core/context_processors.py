from django.conf import settings

"""
A generic function for generating context processors, and a processor
which adds media-specific settings to each ``RequestContext``.

"""

def settings_processor(*settings_list):
    """
    Generates and returns a context processor function which will read
    the values of all the settings passed in and return them in each
    ``RequestContext`` in which it is applied.
    
    For example::
    
        my_settings_processor = settings_processor('INTERNAL_IPS', 'SITE_ID')
    
    ``my_settings_processor`` would then be a valid context processor
    which would return the values of the settings ``INTERNAL_IPS`` and
    ``SITE_ID`` in each ``RequestContext`` in which it was applied.
    
    """
    def _processor(request):
        from django.conf import settings
        settings_dict = {}
        for setting_name in settings_list:
            settings_dict[setting_name] = getattr(settings, setting_name)
        return settings_dict
    return _processor

global_settings = settings_processor(*settings.CONTEXT_SETTINGS)

###
def request_processor(*paramters_list):
    def _processor(request):
        parameters_dict = {}
        for param in paramters_list:
            parameters_dict[param.upper()] = getattr(request, param, None)
        return parameters_dict
    return _processor

request_params = request_processor(*settings.CONTEXT_REQUEST_VARS)

###
def site_url(request):
    from django.contrib.sites.models import Site
    url = u'%s://%s' % (settings.DEFAULT_HTTP_PROTOCOL, 
                        Site.objects.get_current(),)
    return { 'SITE_URL': url }
