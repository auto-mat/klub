# Generated by Django 2.2.16 on 2020-09-03 09:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pinax_teams', '0004_auto_20170511_0856'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('helpdesk', '0028_auto_20190826_2034'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='kbitem',
            options={'ordering': ('order', 'title'), 'verbose_name': 'Knowledge base item', 'verbose_name_plural': 'Knowledge base items'},
        ),
        migrations.AddField(
            model_name='kbcategory',
            name='name',
            field=models.CharField(default=1, max_length=100, verbose_name='Name of the category'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='kbcategory',
            name='public',
            field=models.BooleanField(default=True, verbose_name='Is KBCategory publicly visible?'),
        ),
        migrations.AddField(
            model_name='kbcategory',
            name='queue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='helpdesk.Queue', verbose_name='Default queue when creating a ticket after viewing this category.'),
        ),
        migrations.AddField(
            model_name='kbitem',
            name='downvoted_by',
            field=models.ManyToManyField(related_name='downvotes', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='kbitem',
            name='enabled',
            field=models.BooleanField(default=True, verbose_name='Enabled to display to users'),
        ),
        migrations.AddField(
            model_name='kbitem',
            name='order',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Order'),
        ),
        migrations.AddField(
            model_name='kbitem',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='pinax_teams.Team', verbose_name='Team'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='kbitem',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='helpdesk.KBItem', verbose_name='Knowledge base item the user was viewing when they created this ticket.'),
        ),
        migrations.AlterField(
            model_name='kbcategory',
            name='title',
            field=models.CharField(max_length=100, verbose_name='Title on knowledgebase page'),
        ),
        migrations.AlterField(
            model_name='kbitem',
            name='voted_by',
            field=models.ManyToManyField(related_name='votes', to=settings.AUTH_USER_MODEL),
        ),
    ]
