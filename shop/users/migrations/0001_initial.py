from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('main', '0005_productpromotion_cartpromotion'),
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BonusAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='bonus_account', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Бонусный счёт',
                'verbose_name_plural': 'Бонусные счета',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=100, verbose_name='Имя')),
                ('last_name', models.CharField(blank=True, max_length=100, verbose_name='Фамилия')),
                ('phone', models.CharField(blank=True, max_length=32, verbose_name='Телефон')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Дата рождения')),
                ('city', models.CharField(blank=True, max_length=120, verbose_name='Город')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Адрес')),
                ('postal_code', models.CharField(blank=True, max_length=20, verbose_name='Почтовый индекс')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Профиль пользователя',
                'verbose_name_plural': 'Профили пользователей',
            },
        ),
        migrations.CreateModel(
            name='BonusTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(help_text='Положительное число — начисление, отрицательное — списание.', verbose_name='Количество бонусов')),
                ('transaction_type', models.CharField(choices=[('purchase', 'Начисление за покупку'), ('birthday', 'Подарок ко дню рождения'), ('spend', 'Списание бонусов'), ('refund', 'Возврат бонусов'), ('adjustment', 'Корректировка')], max_length=20, verbose_name='Тип операции')),
                ('description', models.CharField(blank=True, max_length=255, verbose_name='Описание')),
                ('reference_year', models.PositiveIntegerField(blank=True, help_text='Используется для защиты от повторной выдачи подарка ко дню рождения.', null=True, verbose_name='Расчётный год')),
                ('created_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Создано')),
                ('expires_at', models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Действует до')),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='users.bonusaccount', verbose_name='Бонусный счёт')),
                ('order', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bonus_transactions', to='orders.order', verbose_name='Заказ')),
            ],
            options={
                'verbose_name': 'Бонусная операция',
                'verbose_name_plural': 'Бонусные операции',
                'ordering': ('-created_at', '-id'),
            },
        ),
        migrations.CreateModel(
            name='BonusConsumption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.PositiveIntegerField(verbose_name='Использовано бонусов')),
                ('source_transaction', models.ForeignKey(limit_choices_to={'amount__gt': 0}, on_delete=django.db.models.deletion.PROTECT, related_name='consumed_amounts', to='users.bonustransaction', verbose_name='Начисление-источник')),
                ('spend_transaction', models.ForeignKey(limit_choices_to={'amount__lt': 0}, on_delete=django.db.models.deletion.CASCADE, related_name='consumptions', to='users.bonustransaction', verbose_name='Списание')),
            ],
            options={'verbose_name': 'Расход бонусов', 'verbose_name_plural': 'Расходы бонусов'},
        ),
        migrations.CreateModel(
            name='RecentlyViewedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('viewed_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='Просмотрено')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recently_viewed_by', to='main.product', verbose_name='Товар')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='recently_viewed_products', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={'verbose_name': 'Просмотренный товар', 'verbose_name_plural': 'Просмотренные товары', 'ordering': ('-viewed_at', '-id')},
        ),
        migrations.AddConstraint(
            model_name='bonustransaction',
            constraint=models.CheckConstraint(condition=~models.Q(amount=0), name='bonus_transaction_amount_nonzero'),
        ),
        migrations.AddConstraint(
            model_name='bonustransaction',
            constraint=models.UniqueConstraint(condition=models.Q(transaction_type='birthday', reference_year__isnull=False), fields=('account', 'transaction_type', 'reference_year'), name='unique_birthday_bonus_per_year'),
        ),
        migrations.AddConstraint(
            model_name='bonusconsumption',
            constraint=models.CheckConstraint(condition=models.Q(amount__gt=0), name='bonus_consumption_amount_positive'),
        ),
        migrations.AddConstraint(
            model_name='recentlyviewedproduct',
            constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_recently_viewed_user_product'),
        ),
        migrations.AddIndex(
            model_name='bonusconsumption',
            index=models.Index(fields=['source_transaction'], name='users_bonus_source_6b6d8a_idx'),
        ),
        migrations.AddIndex(
            model_name='bonusconsumption',
            index=models.Index(fields=['spend_transaction'], name='users_bonus_spend_1e91cd_idx'),
        ),
    ]
