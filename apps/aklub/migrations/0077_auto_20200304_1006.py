# Generated by Django 2.2.10 on 2020-03-04 09:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('smmapdfs_edit', '0004_auto_20200304_0947'),
        ('aklub', '0076_auto_20200303_1502'),
    ]
    def mass_communication_tax_detail_info(apps, schema_editor):
        db_alias = schema_editor.connection.alias
        AdministrativeUnit = apps.get_model("aklub", "AdministrativeUnit")
        PdfSandwichType = apps.get_model('smmapdfs','PdfSandwichType')
        MassCommunication = apps.get_model("aklub", "MassCommunication")
        mass_coms = MassCommunication.objects.filter(attach_tax_confirmation=True)
        for mass in mass_coms:
            #  before this change tax_confirmation was auto_send always over last year
            mass.attached_tax_confirmation_year = mass.date.year-1
            # before this change there was only one PdfSandwichType for every administrative_unit
            pdf_type = PdfSandwichType.objects.get(pdfsandwichtypeconnector__administrative_unit=mass.administrative_unit)
            mass.attached_tax_confirmation_type = pdf_type
            mass.save()



    def taxconfirmation_type(apps, schema_editor):
        db_alias = schema_editor.connection.alias
        AdministrativeUnit = apps.get_model("aklub", "AdministrativeUnit")
        TaxConfirmation = apps.get_model("aklub", "TaxConfirmation")
        PdfSandwichType = apps.get_model('smmapdfs','PdfSandwichType')
        for unit in AdministrativeUnit.objects.using(db_alias).all():
            try:
                pdf_type = PdfSandwichType.objects.using(db_alias).get(pdfsandwichtypeconnector__administrative_unit=unit)
            except PdfSandwichType.DoesNotExist:
                continue
            taxs = TaxConfirmation.objects.using(db_alias).filter(administrative_unit=unit)
            taxs.update(pdf_type=pdf_type)




    operations = [
            migrations.RunPython(mass_communication_tax_detail_info, reverse_code=migrations.RunPython.noop),
            migrations.RunPython(taxconfirmation_type, reverse_code=migrations.RunPython.noop),
    ]
