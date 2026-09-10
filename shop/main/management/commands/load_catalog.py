import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from main.models import Category, Product


ROOT_SLUGS = {
    'smartphones',
    'headphones',
    'chargers',
    'cables',
    'powerbanks',
}


class Command(BaseCommand):
    help = 'Load the current catalog snapshot without duplicating root categories created by migrations.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--if-empty',
            action='store_true',
            help='Skip loading when at least one product already exists.',
        )
        parser.add_argument(
            '--fixture',
            default='catalog_dump',
            help='Fixture name/path to load (default: catalog_dump).',
        )

    def handle(self, *args, **options):
        if options['if_empty'] and Product.objects.exists():
            self.stdout.write(self.style.WARNING(
                'Catalog is not empty; loading skipped (--if-empty).'
            ))
            return

        fixture_path = self._fixture_path(options['fixture'])
        if not fixture_path.exists():
            raise CommandError(f'Catalog fixture not found: {fixture_path}')

        payload = json.loads(fixture_path.read_text(encoding='utf-8'))
        self._remap_root_parents(payload)

        temp_fixture = fixture_path.with_name(f'.{fixture_path.stem}.render.json')
        try:
            temp_fixture.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding='utf-8',
            )
            with transaction.atomic():
                call_command('loaddata', str(temp_fixture), verbosity=options.get('verbosity', 1))
        finally:
            temp_fixture.unlink(missing_ok=True)

        self.stdout.write(self.style.SUCCESS(
            f'Catalog loaded successfully: {Product.objects.count()} products.'
        ))

    @staticmethod
    def _fixture_path(fixture_name):
        path = Path(fixture_name)
        if path.suffix == '.json' and path.is_absolute():
            return path
        if path.suffix == '.json' and path.exists():
            return path
        return Path(__file__).resolve().parents[2] / 'fixtures' / f'{fixture_name}.json'

    @staticmethod
    def _remap_root_parents(payload):
        roots = {
            category.slug: category.pk
            for category in Category.objects.filter(
                parent__isnull=True,
                slug__in=ROOT_SLUGS,
            )
        }
        missing = ROOT_SLUGS - roots.keys()
        if missing:
            raise CommandError(
                'Required root categories are missing. Run "python manage.py migrate" first. '
                f'Missing: {", ".join(sorted(missing))}'
            )

        categories_by_pk = {
            item['pk']: item
            for item in payload
            if item.get('model') == 'main.category'
        }

        # The live DB gets canonical root categories from migration 0004.
        # The local snapshot can contain an older top-level category with a
        # different slug but the same unique product_type (for example,
        # `naushniki` -> `headphone`). Treat it as an alias of the canonical
        # migration root rather than inserting a duplicate.
        category_pk_aliases = {}
        for item in categories_by_pk.values():
            fields = item['fields']
            if fields.get('parent') is None and fields.get('product_type') in roots:
                category_pk_aliases[item['pk']] = roots[fields['product_type']]

        payload[:] = [
            item
            for item in payload
            if not (
                item.get('model') == 'main.category'
                and item['pk'] in category_pk_aliases
            )
        ]

        for item in payload:
            fields = item.get('fields', {})
            parent_pk = fields.get('parent')
            if parent_pk in category_pk_aliases:
                fields['parent'] = category_pk_aliases[parent_pk]
                continue
            if not parent_pk:
                continue
            parent = categories_by_pk.get(parent_pk)
            if parent is None:
                raise CommandError(f'Catalog fixture references unknown category {parent_pk}.')
            parent_slug = parent['fields']['slug']
            if parent_slug in roots:
                fields['parent'] = roots[parent_slug]
