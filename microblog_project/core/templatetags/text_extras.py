from django import template
from django.utils.safestring import mark_safe
import re
from django.utils.html import escape

register = template.Library()


@register.filter(name='linkify_hashtags')
def linkify_hashtags(value):
    if not value:
        return ''

    def _repl(match):
        tag = match.group(1)
        display = f"#{escape(tag)}"
        url = f"{ '/search' }?q=%23{tag}"
        return f'<a class="hashtag-link" href="{url}">{display}</a>'

    # Operate on HTML/text input without escaping the entire value so that
    # previous filters like `urlize` don't get double-escaped.
    try:
        result = re.sub(r"(?<!\w)#(\w+)", _repl, value)
    except Exception:
        result = value
    return mark_safe(result)
