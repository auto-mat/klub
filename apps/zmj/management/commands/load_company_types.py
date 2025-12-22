from django.core.management.base import BaseCommand

from aklub.models import CompanyType


class Command(BaseCommand):
    help = "Load company types into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--types",
            nargs="+",
            help="List of company types to create",
            default=[
              "Fyzická osoba",
              "Právnická osoba",
              "Nezisková organizace",
            ],
        )

    def handle(self, *args, **options):
        company_types = options["types"]
        created_count = 0
        existing_count = 0

        for type_name in company_types:
            obj, created = CompanyType.objects.get_or_create(type=type_name)
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created company type: "{type_name}"')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⊘ Company type already exists: "{type_name}"')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {created_count} created, {existing_count} already existed"
            )
        )

