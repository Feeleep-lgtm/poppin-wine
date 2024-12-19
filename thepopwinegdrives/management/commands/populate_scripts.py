# thepopwinegdrives/management/commands/populate_scripts.py
from django.core.management.base import BaseCommand
from thepopwinegdrives.models import Script

class Command(BaseCommand):
    help = 'Populate the Script model with initial data'

    def handle(self, *args, **kwargs):
        scripts_data = [
            {'name': 'Fetch and Update Books', 'task_name': 'thepopwinegdrives.tasks.periodic_fetch_and_update_books'},
            # Add more scripts as needed
        ]

        for script_data in scripts_data:
            script, created = Script.objects.get_or_create(
                name=script_data['name'],
                defaults={'task_name': script_data['task_name']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Successfully added script: {script.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Script already exists: {script.name}"))
