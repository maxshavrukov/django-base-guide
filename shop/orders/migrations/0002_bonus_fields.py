from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('orders', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='purchase_bonus_granted',
            field=models.BooleanField(default=False, verbose_name='Бонусы за покупку начислены'),
        ),
        migrations.AddField(
            model_name='order',
            name='purchase_bonus_amount',
            field=models.PositiveIntegerField(default=0, verbose_name='Начислено бонусов за заказ'),
        ),
        migrations.AddField(
            model_name='order',
            name='basket_discount_amount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Скидка корзины'),
        ),
        migrations.AddField(
            model_name='order',
            name='bonus_spent_amount',
            field=models.PositiveIntegerField(default=0, verbose_name='Оплачено бонусами'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='bonus_eligible',
            field=models.BooleanField(default=None, null=True, verbose_name='Учитывать в начислении бонусов'),
        ),
    ]
