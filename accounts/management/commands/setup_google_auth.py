"""
Management command: setup_google_auth
Syncs Google OAuth app credentials from env vars to the database.

Run once after deploy:
    python manage.py setup_google_auth

This is also called automatically by entrypoint.sh.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Create/Update Google SocialApp credentials from environment variables'

    def handle(self, *args, **options):
        from decouple import config

        client_id = config('GOOGLE_CLIENT_ID', default='')
        client_secret = config('GOOGLE_CLIENT_SECRET', default='')
        site_domain = config('SITE_DOMAIN', default='localhost:8000')

        if not client_id or not client_secret:
            self.stdout.write(self.style.WARNING(
                'GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in environment. '
                'Google login will not work.'
            ))
            return

        # Ensure Site record exists and matches domain
        site, _ = Site.objects.update_or_create(
            id=1,
            defaults={'domain': site_domain, 'name': site_domain}
        )
        self.stdout.write(f'Site set to: {site_domain}')

        # Import allauth models only after Django setup
        try:
            from allauth.socialaccount.models import SocialApp

            # ✅ AGGRESSIVE CLEANUP: Wipe ALL Google entries to guarantee NO duplicates!
            deleted_count, _ = SocialApp.objects.filter(provider='google').delete()
            if deleted_count > 0:
                self.stdout.write(self.style.WARNING(f'Wiped {deleted_count} existing Google SocialApp(s) to fix duplicates.'))

            # ✅ Create exactly 1 brand new entry
            app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=client_id,
                secret=client_secret,
                key='',
            )

            # Assign site freshly
            app.sites.add(site)

            self.stdout.write(self.style.SUCCESS(
                f'Successfully recreated Google SocialApp with client_id: {client_id[:12]}...'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error setting up Google Auth: {e}'))
