from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0004_dailymenu'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='dailymenu',
            options={
                'verbose_name': 'Ежедневное меню',
                'verbose_name_plural': 'Ежедневные меню',
            },
        ),
    ]
