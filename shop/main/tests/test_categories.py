from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from main.models import Category, Headphone, ProductGroup
from main.services.categories import (
    get_category_descendant_ids,
    get_category_group_queryset,
    get_category_product_queryset,
    get_category_filter_key,
    get_category_model,
    get_product_model,
)


class CategoryModelTest(TestCase):
    def test_root_categories_are_seeded(self):
        self.assertEqual(
            set(Category.objects.filter(parent__isnull=True).values_list('slug', flat=True)),
            {'smartphones', 'headphones', 'chargers', 'cables', 'powerbanks'},
        )

    def test_root_category_requires_product_type(self):
        category = Category(name='Без типа', slug='without-type')
        with self.assertRaises(ValidationError):
            category.full_clean()

    def test_child_inherits_product_type(self):
        root = Category.objects.get(slug='headphones')
        child = Category.objects.create(name='Игровые', slug='gaming', parent=root)
        self.assertEqual(child.get_effective_product_type(), 'headphone')
        self.assertEqual(get_category_model(child), Headphone)
        self.assertEqual(get_category_filter_key(child), 'headphones')

    def test_child_with_conflicting_product_type_is_invalid(self):
        root = Category.objects.get(slug='headphones')
        child = Category(
            name='Смешанная',
            slug='mixed',
            parent=root,
            product_type='smartphone',
        )
        with self.assertRaises(ValidationError):
            child.full_clean()

    def test_root_product_type_is_unique_in_database(self):
        with self.assertRaises(IntegrityError):
            Category.objects.create(
                name='Еще смартфоны',
                slug='smartphones-2',
                product_type='smartphone',
            )

    def test_descendants_include_nested_children(self):
        root = Category.objects.get(slug='headphones')
        parent = Category.objects.create(name='Игровые', slug='gaming-root', parent=root)
        child = Category.objects.create(name='С микрофоном', slug='gaming-mic', parent=parent)

        descendant_ids = get_category_descendant_ids(parent)
        self.assertEqual(set(descendant_ids), {parent.id, child.id})


class CategoryQuerysetTest(TestCase):
    def setUp(self):
        self.brand = None
        root = Category.objects.get(slug='headphones')
        self.wireless = Category.objects.create(name='Беспроводные', slug='wireless-test', parent=root)
        self.gaming = Category.objects.create(name='Игровые', slug='gaming-test', parent=root)
        self.deeper = Category.objects.create(
            name='Игровые с микрофоном',
            slug='gaming-mic-test',
            parent=self.gaming,
        )
        self.group = ProductGroup.objects.create(name='Hator Test', slug='hator-test')
        Headphone.objects.create(
            group=self.group,
            name='Hator Test Black',
            slug='hator-test-black',
            price='100.00',
            stock=5,
            available=True,
            headphone_type='over_ear',
            connection_type='wireless',
        )
        self.group.categories.add(self.wireless, self.deeper)

    def test_product_queryset_uses_category_and_descendants(self):
        qs = get_category_product_queryset(self.gaming)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().group_id, self.group.id)

    def test_inactive_category_returns_no_products(self):
        self.wireless.is_active = False
        self.wireless.save(update_fields=['is_active'])
        qs = get_category_product_queryset(self.wireless)
        self.assertEqual(qs.count(), 0)

    def test_group_queryset_matches_category_membership(self):
        qs = get_category_group_queryset(self.wireless)
        self.assertEqual(list(qs.values_list('id', flat=True)), [self.group.id])

    def test_product_model_detection_for_concrete_instance(self):
        product = self.group.products.first()
        self.assertIs(get_product_model(product), Headphone)
