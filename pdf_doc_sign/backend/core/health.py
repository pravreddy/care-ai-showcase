"""
Health check for Uptime Kuma / load balancers.

Returns 200 only if Django is up AND the database answers a trivial query.
This is deliberately tiny and unauthenticated. It exists so an external
monitor can tell "the API is actually serving" apart from "the container is
running" — a container can be up while the DB is unreachable.
"""
from django.db import connection
from django.http import JsonResponse


def health(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except Exception:
        return JsonResponse({"status": "db_error"}, status=503)
    return JsonResponse({"status": "ok"})
