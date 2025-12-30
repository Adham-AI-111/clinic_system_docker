from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def active_link(context, url_name):
    """
    Returns 'is-active' if the current URL matches the given url_name.
    Usage: {% active_link 'dashboard' %}
    """
    request = context.get('request')
    if request and hasattr(request, 'resolver_match'):
        current_url_name = request.resolver_match.url_name
        return 'is-active' if current_url_name == url_name else ''
    return ''

