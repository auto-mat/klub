# -*- coding: utf-8 -*-

# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2017 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import PyPDF2

from aklub.models import TaxConfirmation

from django.core.files import File
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import reverse


from freezegun import freeze_time

from model_mommy import mommy

from ..test_admin import CreateSuperUserMixin


class TestStr(TestCase):
    """ Test UserProfile.__str__() """

    def test_str(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
            first_name="Foo",
            last_name="User",
        )
        self.assertEqual(str(t), "User Foo")

        t = mommy.make(
            "aklub.CompanyProfile",
            name="Company",
        )
        self.assertEqual(str(t), "Company")

    def test_str_titles(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
            title_before="Ing.",
            first_name="Foo",
            last_name="User",
            title_after="CSc.",
        )
        self.assertEqual(str(t), "Ing. User Foo, CSc.")

        t = mommy.make(
            "aklub.CompanyProfile",
            name="Company",
        )
        self.assertEqual(str(t), "Company")

    def test_str_only_surname(self):
        """ Test, that __str__ works, when full name is set """
        t = mommy.make(
            "aklub.UserProfile",
            last_name="User",
        )
        self.assertEqual(str(t), "User")

        t = mommy.make(
            "aklub.CompanyProfile",
            name="Company",
        )
        self.assertEqual(str(t), "Company")

    def test_username(self):
        """ Test, that __str__ works, when only username is set """
        t = mommy.make(
            "aklub.UserProfile",
            username="foo_user",
        )
        self.assertEqual(str(t), "foo_user")
        t.delete()

        t = mommy.make(
            "aklub.CompanyProfile",
            username="foo_user",
        )
        self.assertEqual(str(t), "foo_user")

    def test_get_addressment(self):
        """ Test, that get_addresment function makes vokativ """
        t = mommy.make(
            "aklub.UserProfile",
            first_name="Petr",
        )
        self.assertEqual(t.get_addressment(), "Petře")

        t = mommy.make(
            "aklub.CompanyProfile",
            name="Company",
        )
        self.assertEqual(t.get_addressment(), "Company")

    def test_get_addressment_override(self):
        """ Test, that get_addresment function takes addressment override """
        t = mommy.make(
            "aklub.UserProfile",
            first_name="Petr",
            addressment="Petříčku",
        )
        self.assertEqual(t.get_addressment(), "Petříčku")

        t = mommy.make(
            "aklub.CompanyProfile",
            name="Company",
            addressment="Companies",
        )
        self.assertEqual(t.get_addressment(), "Companies")

    def test_get_addressment_default_female(self):
        """ Test, that get_addresment function returns default for female """
        t = mommy.make(
            "aklub.UserProfile",
            sex='female',
        )
        self.assertEqual(t.get_addressment(), "přítelkyně Auto*Matu")

        t = mommy.make(
            "aklub.CompanyProfile",
        )
        self.assertEqual(t.get_addressment(), "Company")

    def test_get_addressment_default(self):
        """ Test, that get_addresment function returns default """
        t = mommy.make(
            "aklub.UserProfile",
            sex='unknown',
        )
        self.assertEqual(t.get_addressment(), "příteli/kyně Auto*Matu")

    def test_email_lowercase(self):
        """ Test, that email is stored in lowercase """
        t = mommy.make(
            "aklub.UserProfile",
            email='tEsT@TeSt.cz',
        )
        self.assertEqual(t.email, "test@test.cz")

        t = mommy.make(
            "aklub.CompanyProfile",
            email='tEsT@TeSt.cz',
        )
        self.assertEqual(t.email, "test@test.cz")

    def test_get_email_str_blank(self):
        """ Test, that get_email_str works when no email is set """
        t = mommy.make(
            "aklub.UserProfile",
        )
        self.assertEqual(t.get_email_str(), "")

        t = mommy.make(
            "aklub.CompanyProfile",
        )
        self.assertEqual(t.get_email_str(), "")

    def test_get_email_str(self):
        """ Test, that get_email_str strips the email """
        t = mommy.make(
            "aklub.UserProfile",
        )
        mommy.make("ProfileEmail", user=t, email="  test@test.cz", is_primary=True)
        self.assertEqual(t.get_email_str(), "test@test.cz")

        c = mommy.make(
            "aklub.CompanyProfile",
        )
        mommy.make("ProfileEmail", user=c, email="  test@test.cz", is_primary=True)
        self.assertEqual(c.get_email_str(), "test@test.cz")

    def test_clean_email(self):
        """ Test, that clean function cleanes the email """
        t = mommy.make(
            "aklub.UserProfile",
            email='',
        )
        t.clean()
        self.assertEqual(t.email, None)

        t = mommy.make(
            "aklub.CompanyProfile",
            email='',
        )
        t.clean()
        self.assertEqual(t.email, None)


class TestTaxConfirmation(CreateSuperUserMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.factory = RequestFactory()
        self.client.force_login(self.superuser)

    def test_profile_action(self):
        """ action make tax confirmation redirect to form """

    def test_make_tax_confirmation_no_payment(self):
        """ Test, that make_tax_confirmation function without any payment """
        t = mommy.make("aklub.UserProfile")
        unit = mommy.make("aklub.AdministrativeUnit")
        pdf_type = mommy.make(
                "smmapdfs.PdfSandwichType",
                name="sandwitch_type",
                template_pdf=File(open("apps/aklub/test_data/empty_pdf.pdf", "rb")),
        )
        tax_confirmation, created = t.make_tax_confirmation(2016, unit, pdf_type)
        self.assertEqual(tax_confirmation, None)
        self.assertEqual(created, False)

        t = mommy.make("aklub.CompanyProfile")
        tax_confirmation, created = t.make_tax_confirmation(2016, unit, pdf_type)
        self.assertEqual(tax_confirmation, None)
        self.assertEqual(created, False)

    @freeze_time("2016-5-1")
    def test_make_tax_confirmation(self):
        """ Test, that make_tax_confirmation function """
        t = mommy.make("aklub.UserProfile", sex='male')
        unit = mommy.make("aklub.AdministrativeUnit", name='test1')
        bank_acc = mommy.make("aklub.BankAccount",  bank_account_number='1111', administrative_unit=unit)
        uc = mommy.make("aklub.DonorPaymentChannel", user=t, event=mommy.make("Event"), money_account=bank_acc)
        mommy.make("aklub.Payment", amount=350, date="2016-01-01", type='regular', user_donor_payment_channel=uc)
        pdf_type = mommy.make(
                "smmapdfs.PdfSandwichType",
                name="sandwitch_type",
                template_pdf=File(open("apps/aklub/test_data/empty_pdf.pdf", "rb")),
        )
        tax_confirmation, created = t.make_tax_confirmation(2016, unit, pdf_type)
        self.assertEqual(t.email, None)
        self.assertEqual(tax_confirmation.year, 2016)
        self.assertEqual(tax_confirmation.amount, 350)

        t = mommy.make("aklub.CompanyProfile")
        uc = mommy.make("aklub.DonorPaymentChannel", user=t, event=mommy.make("Event"), money_account=bank_acc)
        mommy.make("aklub.Payment", amount=350, date="2016-01-01", type='regular', user_donor_payment_channel=uc)
        tax_confirmation, created = t.make_tax_confirmation(2016, unit, pdf_type)
        self.assertEqual(t.email, None)
        self.assertEqual(tax_confirmation.year, 2016)
        self.assertEqual(tax_confirmation.amount, 350)

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
    )
    @freeze_time("2017-5-1")
    def test_generate_pdf_userprofile(self):
        """ Test, that test tax_configurate task which create TaxConfiguration and generate pdf"""
        unit = mommy.make("aklub.AdministrativeUnit", name='unit_test1')
        t = mommy.make(
                "aklub.UserProfile",
                id=1111,
                sex='male',
                first_name='first_test_user_name',
                last_name='last_name',
                street='street_address',
                city='city_name',
                zip_code='192 00',
                country="Test_country",
                administrative_units=[unit],
        )

        bank_acc = mommy.make(
            "aklub.BankAccount",
            bank_account_number='1111',
            administrative_unit=unit,
        )

        uc = mommy.make(
            "aklub.DonorPaymentChannel",
            user=t,
            event=mommy.make("Event"),
            money_account=bank_acc,
        )
        mommy.make("aklub.Payment", amount=350, date="2016-01-01", type='regular', user_donor_payment_channel=uc)

        font = mommy.make(
                "smmapdfs.PdfSandwichFont",
                name="test_font",
                ttf=File(open("apps/aklub/test_data/TestFont.ttf", "rb")),
        )
        pdf_type = mommy.make(
                "smmapdfs.PdfSandwichType",
                id='22',
                name="sandwitch_type",
                template_pdf=File(open("apps/aklub/test_data/empty_pdf.pdf", "rb")),
        )
        mommy.make(
            "smmapdfs_edit.PdfSandwichTypeConnector",
            pdfsandwichtype=pdf_type,
            profile_type='user_profile',
            administrative_unit=unit,
        )
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="year", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="amount", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="name", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="street", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="addr_city", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="zip_code", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="country", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="date", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="administrative_unit", font=font)

        # test action
        data = {
            'action': 'make_tax_confirmation',
            '_selected_action': [1111, ],
            }
        change_url = reverse('admin:aklub_userprofile_changelist')
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 200)

        form_data = response.context['form']
        self.assertEqual(form_data['year'].initial, 2016)
        self.assertEqual(form_data['profile'].initial.first().id, 1111)
        self.assertEqual(form_data['pdf_type'].form.fields['pdf_type']._queryset.first().id, 22)

        # generate data by form
        form_url = reverse('admin:aklub_profile_taxform')
        form_data = {
            'year': '2016',
            'profile': ['1111', ],
            'pdf_type': pdf_type.id,
            }
        response = self.client.post(form_url, form_data)
        self.assertEqual(response.status_code, 302,)

        tax_confirmation = TaxConfirmation.objects.get(year=2016)
        self.assertEqual(t.email, None)
        self.assertEqual(tax_confirmation.year, 2016)
        self.assertEqual(tax_confirmation.amount, 350)

        pdf = tax_confirmation.taxconfirmationpdf_set.get().pdf
        read_pdf = PyPDF2.PdfFileReader(pdf)
        page = read_pdf.getPage(0)
        page_content = page.extractText()
        self.assertTrue("2016" in page_content)
        self.assertTrue("350 K" in page_content)
        self.assertTrue("first_test_user_name last_name" in page_content)
        self.assertTrue("street_address" in page_content)
        self.assertTrue("city_name" in page_content)
        self.assertTrue("192 00" in page_content)
        self.assertTrue("Test_country" in page_content)
        self.assertTrue("01.05.2017" in page_content)
        self.assertTrue("unit_test1" in page_content)

    @freeze_time("2017-5-1")
    def test_generate_pdf_companyprofile(self):
        """ Test, that test tax_configurate task which create TaxConfiguration and generate pdf"""
        unit = mommy.make("aklub.AdministrativeUnit", name='unit_test1')
        company = mommy.make(
                "aklub.CompanyProfile",
                id=2222,
                name='company_name',
                contact_first_name='contact_first',
                contact_last_name='contact_last',
                street='street_address',
                city='city_name_com',
                zip_code='111 00',
                country="Test_country_xx",
                crn='22670319',
                tin='CZ22670319',
                administrative_units=[unit],
        )

        bank_acc = mommy.make(
            "aklub.BankAccount",
            bank_account_number='1111',
            administrative_unit=unit,
        )

        uc = mommy.make(
            "aklub.DonorPaymentChannel",
            user=company,
            event=mommy.make("Event"),
            money_account=bank_acc,
        )
        mommy.make("aklub.Payment", amount=350, date="2016-01-01", type='regular', user_donor_payment_channel=uc)

        font = mommy.make(
                "smmapdfs.PdfSandwichFont",
                name="test_font",
                ttf=File(open("apps/aklub/test_data/TestFont.ttf", "rb")),
        )
        pdf_type = mommy.make(
                "smmapdfs.PdfSandwichType",
                id='22',
                name="sandwitch_type",
                template_pdf=File(open("apps/aklub/test_data/empty_pdf.pdf", "rb")),
        )
        mommy.make(
            "smmapdfs_edit.PdfSandwichTypeConnector",
            pdfsandwichtype=pdf_type,
            profile_type='company_profile',
            administrative_unit=unit,
        )
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="year", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="amount", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="company_name", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="street", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="addr_city", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="zip_code", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="country", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="date", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="administrative_unit", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="contact_name", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="crn", font=font)
        mommy.make("aklub.TaxConfirmationField", pdfsandwich_type=pdf_type, field="tin", font=font)

        # test action
        data = {
            'action': 'make_tax_confirmation',
            '_selected_action': [2222, ],
            }
        change_url = reverse('admin:aklub_companyprofile_changelist')
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 200)

        form_data = response.context['form']
        self.assertEqual(form_data['year'].initial, 2016)
        self.assertEqual(form_data['profile'].initial.first().id, 2222)
        self.assertEqual(form_data['pdf_type'].form.fields['pdf_type']._queryset.first().id, 22)
        # generate data by form
        form_url = reverse('admin:aklub_profile_taxform')
        form_data = {
            'year': '2016',
            'profile': ['2222', ],
            'pdf_type': pdf_type.id,
            }
        response = self.client.post(form_url, form_data)
        self.assertEqual(response.status_code, 302,)

        tax_confirmation = TaxConfirmation.objects.get(year=2016)
        self.assertEqual(company.email, None)
        self.assertEqual(tax_confirmation.year, 2016)
        self.assertEqual(tax_confirmation.amount, 350)

        pdf = tax_confirmation.taxconfirmationpdf_set.get().pdf
        read_pdf = PyPDF2.PdfFileReader(pdf)
        page = read_pdf.getPage(0)
        page_content = page.extractText()
        self.assertTrue("2016" in page_content)
        self.assertTrue("350 K" in page_content)
        self.assertTrue("street_address" in page_content)
        self.assertTrue("city_name" in page_content)
        self.assertTrue("111 00" in page_content)
        self.assertTrue("Test_country_xx" in page_content)
        self.assertTrue("01.05.2017" in page_content)
        self.assertTrue("company_name" in page_content)
        self.assertTrue("contact_first contact_last" in page_content)
        self.assertTrue("22670319" in page_content)
        self.assertTrue("CZ22670319" in page_content)
        self.assertTrue("unit_test1" in page_content)
