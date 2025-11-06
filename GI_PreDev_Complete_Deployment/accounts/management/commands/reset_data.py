from django.core.management.base import BaseCommand
from django.db import transaction
from implement.models import Action, ActionHistory, Issue, NumbersTracking, ProjectStatus
from plans.models import (
    AnnualPlan, QuarterlyPlan, FPIParameter, GPIParameter,
    PPIProject, PPITask, GPIMilestone, FPIMilestone,
    AnnualFPIParameter, AnnualGPIParameter, AnnualPPIProject
)
from improve.models import ImprovementUpload, ImprovementProject, ImprovementTask, ImprovementProjectStatus
from reviews.models import ReviewMeeting, ReviewNote, ReviewDecision, ReviewActionItem


class Command(BaseCommand):
    help = 'Deletes all data except users, teams, financial years and quarters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion of data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    '\nWARNING: This will delete ALL data except:\n'
                    '- Users and credentials\n'
                    '- Teams\n'
                    '- Financial Years\n'
                    '- Quarters\n\n'
                    'To proceed, run with --confirm flag:\n'
                    'py manage.py reset_data --confirm\n'
                )
            )
            return

        self.stdout.write(self.style.WARNING('\nStarting data deletion...'))

        with transaction.atomic():
            # Delete Review data
            self.stdout.write('Deleting Review data...')
            ReviewActionItem.objects.all().delete()
            ReviewDecision.objects.all().delete()
            ReviewNote.objects.all().delete()
            ReviewMeeting.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Review data deleted'))

            # Delete Implement data
            self.stdout.write('Deleting Implement data...')
            ActionHistory.objects.all().delete()
            Action.objects.all().delete()
            Issue.objects.all().delete()
            ProjectStatus.objects.all().delete()
            NumbersTracking.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Implement data deleted'))

            # Delete Improve data
            self.stdout.write('Deleting Improve data...')
            ImprovementProjectStatus.objects.all().delete()
            ImprovementTask.objects.all().delete()
            ImprovementProject.objects.all().delete()
            ImprovementUpload.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Improve data deleted'))

            # Delete Plans data
            self.stdout.write('Deleting Plans data...')
            PPITask.objects.all().delete()
            PPIProject.objects.all().delete()
            GPIMilestone.objects.all().delete()
            FPIMilestone.objects.all().delete()
            GPIParameter.objects.all().delete()
            FPIParameter.objects.all().delete()
            AnnualPPIProject.objects.all().delete()
            AnnualGPIParameter.objects.all().delete()
            AnnualFPIParameter.objects.all().delete()
            QuarterlyPlan.objects.all().delete()
            AnnualPlan.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Plans data deleted'))

        self.stdout.write(
            self.style.SUCCESS(
                '\nData reset complete!\n\n'
                'Preserved:\n'
                '- Users and credentials\n'
                '- Teams\n'
                '- Financial Years\n'
                '- Quarters\n'
            )
        )
