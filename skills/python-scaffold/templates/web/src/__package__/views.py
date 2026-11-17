"""Views for {{PROJECT}}.

The home page is the full document; ``ping`` returns a fragment so the scaffold
proves the HTMX wiring without any JavaScript of its own.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def home(request: HttpRequest) -> HttpResponse:
    """Render the application shell."""
    return render(request, "home.html", {"title": "{{PROJECT}}"})


def ping(request: HttpRequest) -> HttpResponse:
    """Return the HTMX fragment swapped into the home page."""
    return render(request, "partials/ping.html")
