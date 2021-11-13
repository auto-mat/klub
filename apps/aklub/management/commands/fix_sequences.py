from django.db import connection
from django.core.management.base import BaseCommand


def pkeyseq(model_class):
    return '{}_pkey_seq'.format()

def get_max(db_table, key):
    cursor = connection.cursor()
    cursor.execute("select MAX({}) + 1 FROM {}".format(key, db_table))
    row = cursor.fetchone()
    cursor.close()
    return row[0]

def fix_sequence(db_table, key="id"):
    cursor = connection.cursor()
    value = get_max(db_table, key)
    command = "ALTER SEQUENCE {}_id_seq RESTART WITH {};".format(db_table, value)
    print(command)
    cursor.execute(command)

class Command(BaseCommand):
    help = "Fixes all posgres sequences after broken migrate or backup restore"

    def handle(self, *args, **options):
        from django.contrib.contenttypes.models import ContentType
        import django.db.utils
        for ct in ContentType.objects.all():
            try:
                print("Reseting sequence for ", ct)
                fix_sequence(ct.model_class()._meta.db_table, "id")
            except django.db.utils.ProgrammingError:
                try:
                    fix_sequence(ct.model_class()._meta.db_table, "pkey")
                except django.db.utils.ProgrammingError:
                    print("Skipping ", ct, " sequence does not exist.")
        from aklub import models
        fix_sequence(models.Profile._meta.db_table, "id")
        fix_sequence(models.MoneyAccount._meta.db_table, "id")
        #import pdb;pdb.set_trace()

