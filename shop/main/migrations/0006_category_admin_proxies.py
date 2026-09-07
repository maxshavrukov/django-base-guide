from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('main', '0005_productpromotion_cartpromotion'),
    ]

    operations = [
        migrations.CreateModel(
            name='MainCategory',
            fields=[],
            options={
                'verbose_name': 'Основная категория',
                'verbose_name_plural': 'Основные категории',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.category',),
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[],
            options={
                'verbose_name': 'Подкатегория',
                'verbose_name_plural': 'Подкатегории',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('main.category',),
        ),
    ]
