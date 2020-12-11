# Generated by Django 2.2.16 on 2020-12-09 10:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('interactions', '0009_auto_20200219_1818'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='interaction',
            options={'verbose_name': 'Interaction', 'verbose_name_plural': 'Interactions'},
        ),
        migrations.AlterModelOptions(
            name='interactioncategory',
            options={'verbose_name': 'Interaction Category', 'verbose_name_plural': 'Interaction Categories'},
        ),
        migrations.AlterModelOptions(
            name='interactiontype',
            options={'verbose_name': 'Interaction Type', 'verbose_name_plural': 'Interaction Types'},
        ),
        migrations.AlterModelOptions(
            name='petitionsignature',
            options={'verbose_name': 'Petition signature', 'verbose_name_plural': 'Petition signatures'},
        ),
        migrations.AlterModelOptions(
            name='result',
            options={'verbose_name': 'Result', 'verbose_name_plural': 'Results'},
        ),
        migrations.AlterField(
            model_name='interaction',
            name='administrative_unit',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit', verbose_name='Administrative unit'),
        ),
        migrations.AlterField(
            model_name='interaction',
            name='type',
            field=models.ForeignKey(help_text='Type of interaction', on_delete=django.db.models.deletion.CASCADE, to='interactions.InteractionType', verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='interactioncategory',
            name='category',
            field=models.CharField(max_length=130, verbose_name='Category name'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='attachment_bool',
            field=models.BooleanField(default=False, help_text='Choose if attachment is visible in specific type of interaction.', verbose_name='Attachment'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='category',
            field=models.ForeignKey(help_text='Timeline display category', on_delete=django.db.models.deletion.CASCADE, to='interactions.InteractionCategory', verbose_name='Category'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='communication_type_bool',
            field=models.BooleanField(default=False, help_text='Choose if communication_type is visible in specific type of interaction.', verbose_name='Type of communication'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='created_bool',
            field=models.BooleanField(default=False, help_text='Choose if created is visible in specific type of interaction.', verbose_name='Date of creation'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='created_by_bool',
            field=models.BooleanField(default=False, help_text='Choose if created_by is visible in specific type of interaction.', verbose_name='Created by'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='date_to_bool',
            field=models.BooleanField(default=False, help_text='Choose if date_to is visible in specific type of interaction.', verbose_name='End of period date'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='dispatched_bool',
            field=models.BooleanField(default=False, help_text='Choose if dispatched is visible in specific type of interaction.', verbose_name='Dispatched / Done'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='event_bool',
            field=models.BooleanField(default=False, help_text='Choose if event is visible in specific type of interaction.', verbose_name='Event'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='handled_by_bool',
            field=models.BooleanField(default=False, help_text='Choose if handled_by is visible in specific type of interaction.', verbose_name='Last handled by'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='next_communication_date_bool',
            field=models.BooleanField(default=False, help_text='Choose if next_communication_date is visible in specific type of interaction.', verbose_name='Date of next communication'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='next_step_bool',
            field=models.BooleanField(default=False, help_text='Choose if next_step is visible in specific type of interaction.', verbose_name='Next steps'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='note_bool',
            field=models.BooleanField(default=False, help_text='Choose if note is visible in specific type of interaction.', verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='rating_bool',
            field=models.BooleanField(default=False, help_text='Choose if rating is visible in specific type of interaction.', verbose_name='rating communication'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='result_bool',
            field=models.BooleanField(default=False, help_text='Choose if result is visible in specific type of interaction.', verbose_name='Result of communication'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='send_email',
            field=models.BooleanField(blank=True, default=False, help_text='the email will be immediatelly sent to the user', null=True, verbose_name='Sent email'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='send_sms',
            field=models.BooleanField(blank=True, default=False, help_text='the sms will be immediatelly send to the use', null=True, verbose_name='Sent sms'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='settlement_bool',
            field=models.BooleanField(default=False, help_text='Choose if settlement is visible in specific type of interaction.', verbose_name='Settlements'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='status_bool',
            field=models.BooleanField(default=False, help_text='Choose if status is visible in specific type of interaction.', verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='summary_bool',
            field=models.BooleanField(default=False, help_text='Choose if summary is visible in specific type of interaction.', verbose_name='Text'),
        ),
        migrations.AlterField(
            model_name='interactiontype',
            name='updated_bool',
            field=models.BooleanField(default=False, help_text='Choose if updated is visible in specific type of interaction.', verbose_name='Date of last change'),
        ),
    ]