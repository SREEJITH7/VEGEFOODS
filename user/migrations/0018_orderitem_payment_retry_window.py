# Generated by Django 5.1.2 on 2024-12-24 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0017_wallettransaction_payment_method_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='payment_retry_window',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]