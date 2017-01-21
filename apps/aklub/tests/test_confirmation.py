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

import io

from PyPDF2 import PdfFileReader

from django.test import TestCase

from ..confirmation import makepdf


class ConfirmationTest(TestCase):
    def test_makepdf(self):
        output = io.BytesIO()
        makepdf(output, 'Test name', 'male', 'Test street', 'Test city', 2099, 999)
        pdf = PdfFileReader(output)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue('Test name' in pdf_string)
        self.assertTrue('Test street' in pdf_string)
        self.assertTrue('Test city' in pdf_string)
        self.assertTrue('2099' in pdf_string)
        self.assertTrue('999' in pdf_string)

    def test_makepdf_female(self):
        output = io.BytesIO()
        makepdf(output, 'Test name', 'female', 'Test street', 'Test city', 2099, 999)
        pdf = PdfFileReader(output)
        pdf_string = pdf.pages[0].extractText()
        self.assertTrue('Test name' in pdf_string)
        self.assertTrue('Test street' in pdf_string)
        self.assertTrue('Test city' in pdf_string)
        self.assertTrue('2099' in pdf_string)
        self.assertTrue('999' in pdf_string)
