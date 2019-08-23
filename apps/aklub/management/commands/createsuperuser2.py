# https://github.com/adamcharnock/swiftwind-heroku/blob/master/swiftwind_heroku/management/commands/create_superuser_with_password.py

import re

from aklub.models import CompanyProfile, UserProfile

from django.contrib.auth.management.commands import createsuperuser
from django.contrib.contenttypes.models import ContentType
from django.core.management import CommandError


class Command(createsuperuser.Command):
    help = 'Crate a superuser, and allow password to be provided'  # noqa

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--password', dest='password', default=None,
            help='Specifies the password for the superuser.',
        )
        parser.add_argument(
            '--profile',
            dest='polymorphic_ctype_id',
            choices=['user', 'company'],
            default='user',
            help='Choose how user profile save as, user or company profile '
            'type, default is user profile',
        )
        parser.add_argument(
            '--crn',
            dest='crn',
            type=int,
            help='If profile type is the company, you must set company '
            'registration number (crn)',
        )
        # Remove default --polymorphic_ctype_id arg (REQUIRED_FIELDS var)
        # and replace with --profile arg
        ctype_opt = '--polymorphic_ctype_id'
        for pos, opt in enumerate(parser.__dict__['_actions']):
            if opt.option_strings[0] == ctype_opt:
                parser._handle_conflict_resolve(None, [(ctype_opt, parser._actions[pos])])

    def handle(self, *args, **options):
        password = options.get('password')
        username = options.get('username')
        database = options.get('database')
        email = options.get('email')
        profile_type = options.get('polymorphic_ctype_id')
        crn = options.get('crn')

        if profile_type == 'user':
            profile_type_id = ContentType.objects.get(model=UserProfile._meta.model_name).id
        else:
            profile_type_id = ContentType.objects.get(model=CompanyProfile._meta.model_name).id
            if not crn:
                raise CommandError("--crn is required if specifying --profile company")
            elif not re.match(r"^[0-9]{8}$", str(crn)):
                raise CommandError("--crn is eight digit positive integer number")
        options['polymorphic_ctype_id'] = profile_type_id

        model = ContentType.objects.get(id=profile_type_id).model_class()
        if email and email in model.objects.all().values_list('email', flat=True):
            raise CommandError("use another email address")

        if password and not username:
            raise CommandError("--username is required if specifying --password")

        super(Command, self).handle(*args, **options)

        user = model._default_manager.db_manager(database).get(username=username)
        if password:
            user.set_password(password)
        if crn:
            user.crn = crn
        user.save()
