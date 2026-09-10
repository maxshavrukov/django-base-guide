import json
from pathlib import Path

from django.core.management import BaseCommand, CommandError, call_command


MODEL_ORDER = {
    'main.brand': 0,
    'main.category': 1,
    'main.productgroup': 2,
    'main.product': 3,
    'main.smartphone': 4,
    'main.headphone': 4,
    'main.charger': 4,
    'main.cable': 4,
    'main.powerbank': 4,
    'main.productimage': 5,
    'main.productpromotion': 6,
    'main.cartpromotion': 7,
    'main.banner': 8,
}

MODEL_LABELS = tuple(MODEL_ORDER)


class Command(BaseCommand):
    help = 'Export the current catalog into main/fixtures/catalog_dump.json.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            default='main/fixtures/catalog_dump.json',
            help='Output JSON path relative to the project directory.',
        )

    def handle(self, *args, **options):
        output = Path(options['output'])
        if not output.is_absolute():
            output = Path.cwd() / output
        output.parent.mkdir(parents=True, exist_ok=True)

        from io import StringIO

        stream = StringIO()
        call_command('dumpdata', *MODEL_LABELS, format='json', indent=2, stdout=stream)
        payload = json.loads(stream.getvalue())
        payload.sort(key=lambda item: (MODEL_ORDER[item['model']], item['pk']))

        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding='utf-8',
        )
        self.stdout.write(self.style.SUCCESS(
            f'Catalog exported to {output} ({len(payload)} objects).'
        ))
