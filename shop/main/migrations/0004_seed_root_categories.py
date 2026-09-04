from django.db import migrations


ROOT_CATEGORIES = (
    ('smartphones', 'Смартфоны', 'smartphone', 10),
    ('headphones', 'Наушники', 'headphone', 20),
    ('chargers', 'Зарядные устройства', 'charger', 30),
    ('cables', 'Кабели', 'cable', 40),
    ('powerbanks', 'Повербанки', 'powerbank', 50),
)


def create_root_categories(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    for slug, name, product_type, sort_order in ROOT_CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'product_type': product_type,
                'parent_id': None,
                'sort_order': sort_order,
                'is_active': True,
            },
        )


def remove_root_categories(apps, schema_editor):
    Category = apps.get_model('main', 'Category')
    Category.objects.filter(slug__in=[slug for slug, *_ in ROOT_CATEGORIES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0003_category_productgroup_categories_and_more'),
    ]

    operations = [
        migrations.RunPython(create_root_categories, remove_root_categories),
    ]
