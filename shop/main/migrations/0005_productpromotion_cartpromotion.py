from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('main', '0004_seed_root_categories')]
    operations = [
        migrations.CreateModel(
            name='CartPromotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название акции')),
                ('rule_type', models.CharField(choices=[('cart', 'На всю корзину'), ('cheapest', 'На самый дешёвый товар'), ('most_expensive', 'На самый дорогой товар'), ('nth', 'На N-й товар')], default='cart', max_length=20, verbose_name='Правило')),
                ('discount_percent', models.PositiveSmallIntegerField(default=0, verbose_name='Скидка (%)')),
                ('min_quantity', models.PositiveIntegerField(default=1, verbose_name='Минимальное количество товаров')),
                ('nth_position', models.PositiveIntegerField(blank=True, null=True, verbose_name='Позиция N-го товара')),
                ('registered_only', models.BooleanField(default=False, verbose_name='Только для авторизованных')),
                ('starts_at', models.DateTimeField(blank=True, null=True, verbose_name='Начало действия')),
                ('ends_at', models.DateTimeField(blank=True, null=True, verbose_name='Окончание действия')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'Акция корзины', 'verbose_name_plural': 'Акции корзины', 'ordering': ('-created_at',)},
        ),
        migrations.CreateModel(
            name='ProductPromotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название акции')),
                ('target_type', models.CharField(choices=[('brand', 'Бренд'), ('category', 'Категория'), ('group', 'Группа товаров'), ('product', 'Конкретный товар')], max_length=20, verbose_name='Тип цели')),
                ('discount_percent', models.PositiveSmallIntegerField(default=0, verbose_name='Скидка (%)')),
                ('starts_at', models.DateTimeField(blank=True, null=True, verbose_name='Начало действия')),
                ('ends_at', models.DateTimeField(blank=True, null=True, verbose_name='Окончание действия')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('brand', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_promotions', to='main.brand', verbose_name='Бренд')),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_promotions', to='main.category', verbose_name='Категория')),
                ('group', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_promotions', to='main.productgroup', verbose_name='Группа товаров')),
                ('product', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_promotions', to='main.product', verbose_name='Товар')),
            ],
            options={'verbose_name': 'Акция на товары', 'verbose_name_plural': 'Акции на товары', 'ordering': ('-created_at',)},
        ),
    ]
