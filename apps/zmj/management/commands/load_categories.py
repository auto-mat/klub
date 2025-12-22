from django.core.management.base import BaseCommand

from events.models import Category


class Command(BaseCommand):
    help = "Load categories into the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--categories",
            nargs="+",
            help="List of categories to create (format: 'name:description')",
            default=[
              "Workshop:Educational workshop or training session",
              "Theater:Theater performance",
              "Games:Game performance",
              "Sale:Sale of products or services",
              "For children:Events for children",
              "Food:Food or drink",
              "Concert:Music or cultural performance",
              "Dance:Dance performance",
              "Movie:Movie projection",
              "Music:Music-related events",
              "Sports:Sport event",
              "Other:Other event",
            ],
        )

    def handle(self, *args, **options):
        categories_data = options["categories"]
        created_count = 0
        existing_count = 0

        for category_data in categories_data:
            # Parse name and description
            if ":" in category_data:
                name, description = category_data.split(":", 1)
                name = name.strip()
                description = description.strip()
            else:
                name = category_data.strip()
                description = ""

            # Create category
            obj, created = Category.objects.get_or_create(
                name=name,
                defaults={"description": description},
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created category: "{name}" (slug: {obj.slug})'
                    )
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⊘ Category already exists: "{name}"')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSummary: {created_count} created, {existing_count} already existed"
            )
        )

