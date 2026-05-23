from django.core.management.base import BaseCommand
from tasks.models import Team

class Command(BaseCommand):
    help = 'Create default teams'

    def handle(self, *args, **kwargs):
        teams = [
            {'name': 'Engineering & Development', 'description': 'Software development, coding, and technical architecture', 'icon': 'fas fa-code'},
            {'name': 'Product Management', 'description': 'Product strategy, roadmap, and feature planning', 'icon': 'fas fa-chart-line'},
            {'name': 'Marketing & Sales', 'description': 'Market research, campaigns, and customer acquisition', 'icon': 'fas fa-bullhorn'},
            {'name': 'Human Resources', 'description': 'Recruitment, employee relations, and company culture', 'icon': 'fas fa-users'},
            {'name': 'Customer Support', 'description': 'Customer service, troubleshooting, and client relations', 'icon': 'fas fa-headset'},
        ]
        
        for team_data in teams:
            team, created = Team.objects.get_or_create(
                name=team_data['name'],
                defaults={
                    'description': team_data['description'],
                    'icon': team_data['icon']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Team created: {team.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Team already exists: {team.name}'))
        
        self.stdout.write(self.style.SUCCESS('Default teams setup complete!'))