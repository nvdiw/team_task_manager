from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from tasks.models import UserProfile

class Command(BaseCommand):
    help = 'Create missing user profiles'

    def handle(self, *args, **kwargs):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(f"Created profile for {user.username}")
        
        self.stdout.write(self.style.SUCCESS(f"Done! Created {created_count} new profiles."))