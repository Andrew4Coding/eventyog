# Generated by Django 5.1.1 on 2024-10-12 06:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_userprofile_name_userprofile_prefered_categories_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userprofile',
            old_name='prefered_categories',
            new_name='categories',
        ),
    ]
