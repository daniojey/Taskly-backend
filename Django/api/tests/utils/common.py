from django.conf import settings
from django.urls import reverse

def get_url(url, version=settings.DEFAULT_API_VERSION):
    expected_version = {'v1', 'v2'}
    if version not in expected_version:
        raise AssertionError(f"We have version {version} but it not expected")

    return reverse(url, kwargs={'version': version})