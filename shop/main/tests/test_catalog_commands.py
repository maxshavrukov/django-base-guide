import json
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from main.models import Category, Product


class CatalogCommandTests(TestCase):
    def test_load_catalog_does_not_duplicate_migration_roots(self):
        call_command('load_catalog', if_empty=True, verbosity=0)

        self.assertEqual(Product.objects.count(), 16)
        self.assertEqual(
            Category.objects.filter(parent__isnull=True).count(),
            5,
        )
        self.assertEqual(Category.objects.count(), 8)

    def test_load_catalog_maps_legacy_top_level_category_alias(self):
        call_command('load_catalog', if_empty=True, verbosity=0)
        self.assertEqual(
            Category.objects.get(slug='besprovodnye').parent.slug,
            'headphones',
        )
        self.assertFalse(Category.objects.filter(slug='naushniki').exists())

    def test_load_catalog_if_empty_skips_existing_catalog(self):
        call_command('load_catalog', if_empty=True, verbosity=0)
        call_command('load_catalog', if_empty=True, verbosity=0)
        self.assertEqual(Product.objects.count(), 16)
