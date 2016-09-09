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

from admin_tools_stats.modules import DashboardChart, DashboardCharts

from django.utils.translation import ugettext_lazy as _


class YearDashboardChart(DashboardChart):
    def get_day_intervals(self):
        values = 30
        return {
            'days': values,
            'weeks': values * 7,
            'months': values * 30,
            'years': values * 365,
        }[self.interval]


class YearDashboardCharts(DashboardCharts):
    def get_registration_charts(self, **kwargs):
        return [
            YearDashboardChart(_('By Day'), interval='days', **kwargs),
            YearDashboardChart(_('By Week'), interval='weeks', **kwargs),
            YearDashboardChart(_('By Month'), interval='months', **kwargs),
            YearDashboardChart(_('By Year'), interval='years', **kwargs),
        ]
