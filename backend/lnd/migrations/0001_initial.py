# Generated by Django 2.1.1 on 2018-09-16 18:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LNDWallet',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('public_alias', models.CharField(max_length=128)),
                ('name', models.CharField(max_length=100)),
                ('testnet', models.BooleanField(default=False)),
                ('initialized', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]