# Generated by Django 2.2.24 on 2021-09-02 17:09

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0016_event_additional_question_4'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='basic_purpose',
            field=models.CharField(choices=[('action', 'Action'), ('action-with-attendee-list', 'Action with attendee list'), ('petition', 'Petition'), ('camp', 'Camp'), ('opportunity', 'Opportunity')], default='action', max_length=128, verbose_name='Basic Purpose'),
        ),
        migrations.AlterField(
            model_name='event',
            name='diet',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, choices=[('vegetarian', 'Vegetarian'), ('non_vegetarian', 'Non-vegetarian'), ('vegan', 'Vegan'), ('kosher', 'Kosher'), ('halal', 'Halal'), ('gluten_free', 'Gluten free')], max_length=56, verbose_name='Diet'),
        ),
    ]
