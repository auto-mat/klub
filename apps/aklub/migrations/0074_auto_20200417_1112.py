# Generated by Django 2.2.12 on 2020-04-17 09:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0073_auto_20200206_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='our_note',
            field=models.CharField(blank=True, default='', help_text='Little note to payment', max_length=100, verbose_name='Our note'),
        ),
        migrations.AlterField(
            model_name='accountstatements',
            name='administrative_unit',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='aklub.AdministrativeUnit', verbose_name='administrative unit'),
        ),
        migrations.AlterField(
            model_name='automaticcommunication',
            name='method_type',
            field=models.ForeignKey(help_text='Interaction type with allowed sending', limit_choices_to=models.Q(('send_sms', True), ('send_email', True), _connector='OR'), null=True, on_delete=django.db.models.deletion.CASCADE, to='interactions.InteractionType'),
        ),
        migrations.AlterField(
            model_name='event',
            name='administrative_units',
            field=models.ManyToManyField(to='aklub.AdministrativeUnit', verbose_name='administrative units'),
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='method_type',
            field=models.ForeignKey(help_text='Interaction type with allowed sending', limit_choices_to=models.Q(('send_sms', True), ('send_email', True), _connector='OR'), null=True, on_delete=django.db.models.deletion.CASCADE, to='interactions.InteractionType'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='type',
            field=models.CharField(blank=True, choices=[('bank-transfer', 'Bank transfer'), ('cash', 'In cash'), ('expected', 'Expected payment'), ('creadit_card', 'Credit card'), ('material_gift', 'Material gift'), ('darujme', 'Darujme.cz')], help_text='Type of payment', max_length=200, verbose_name='Type'),
        ),
    ]
