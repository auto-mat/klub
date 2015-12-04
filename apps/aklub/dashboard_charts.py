# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
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

from django.utils.translation import ugettext_lazy as _
from django.db.models import Sum, Count
from admin_user_stats.base_modules import BaseChart, BaseCharts
from aklub.models import Payment, User


class PaymentCountChart(BaseChart):
    """
    Dashboard module with Activity charts.
    """
    title = _('Payments count')
    template = 'admin_user_stats/modules/chart.html'
    chart_size = "900x200"
    values_count = 50
    interval = 'months'
    queryset = Payment.objects
    date_field = 'date'
    aggregate = Count('pk')


class PaymentCountCharts(BaseCharts):
    """ Group module with 3 default registration charts """
    title = _('Payments count')
    chart_model = PaymentCountChart

    def get_charts(self):
        """ Returns 3 basic chart modules (per-day, per-week and per-month) """
        return [
            self.chart_model(_('By Day'), interval='days'),
            self.chart_model(_('By Week'), interval='weeks'),
            self.chart_model(_('By Month'), interval='months'),
            self.chart_model(_('By Month from regular'), interval='months', queryset=Payment.objects.filter(user__regular_payments=True)),
            self.chart_model(_('By Month from onetimers'), interval='months', queryset=Payment.objects.filter(user__regular_payments=False)),
            self.chart_model(_('By Year'), interval='years'),
        ]


class PaymentChart(BaseChart):
    """
    Dashboard module with Activity charts.
    """
    title = _('Payments')
    template = 'admin_user_stats/modules/chart.html'
    chart_size = "900x200"
    values_count = 50
    interval = 'months'
    queryset = Payment.objects
    date_field = 'date'
    aggregate = Sum('amount')


class PaymentCharts(BaseCharts):
    """ Group module with 3 default registration charts """
    title = _('Payments')
    chart_model = PaymentChart

    def get_charts(self):
        """ Returns 3 basic chart modules (per-day, per-week and per-month) """
        return [
            self.chart_model(_('By Day'), interval='days'),
            self.chart_model(_('By Week'), interval='weeks'),
            self.chart_model(_('By Month'), interval='months'),
            self.chart_model(_('By Month from regular'), interval='months', queryset=Payment.objects.filter(user__regular_payments=True)),
            self.chart_model(_('By Month from onetimers'), interval='months', queryset=Payment.objects.filter(user__regular_payments=False)),
            self.chart_model(_('By Year'), interval='years'),
        ]


class UserChart(BaseChart):
    """
    Dashboard module with Activity charts.
    """
    title = _(u'New users')
    template = 'admin_user_stats/modules/chart.html'
    chart_size = "900x200"
    values_count = 50
    interval = 'months'
    queryset = User.objects
    date_field = 'registered_support'


class UserCharts(BaseCharts):
    """ Group module with 3 default registration charts """
    title = _('New users')
    chart_model = UserChart

    def get_charts(self):
        """ Returns 3 basic chart modules (per-day, per-week and per-month) """
        return [
            self.chart_model(_('By Day'), interval='days'),
            self.chart_model(_('By Week'), interval='weeks'),
            self.chart_model(_('By Month'), interval='months'),
            self.chart_model(_('Regular By Month'), interval='months', queryset=User.objects.filter(regular_payments=True)),
            self.chart_model(_('Onetime By Month'), interval='months', queryset=User.objects.filter(regular_payments=False)),
            self.chart_model(_('By Year'), interval='years'),
        ]
