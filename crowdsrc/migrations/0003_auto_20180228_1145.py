# Generated by Django 2.0.2 on 2018-02-28 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crowdsrc', '0002_auto_20180228_0952'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='category',
            options={'ordering': ('name',)},
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='skill',
            name='name',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]