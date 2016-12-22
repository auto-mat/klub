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

"""
This file was generated with the customdashboard management command, it
contains the two classes for the main dashboard and app index dashboard.
You can customize these classes as you want.

To activate your index dashboard add the following to your settings.py::
    ADMIN_TOOLS_INDEX_DASHBOARD = 'aklub.dashboard.AklubIndexDashboard'

And to activate the app index dashboard::
    ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'aklub.dashboard.AklubAppIndexDashboard'
"""
import datetime

from admin_tools.dashboard import AppIndexDashboard, Dashboard, modules
from admin_tools.utils import get_admin_site_name

from admin_tools_stats.modules import get_active_graph

from django.core.cache import caches
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from . import models
from .dashboard_charts import YearDashboardCharts
from .models import AccountStatements, Condition, MassCommunication, UserInCampaign

cache = caches['default']


def get_users_by_condition_cached(cond):
    items = cache.get('condition_filter_%i' % cond.pk, None)
    if not items:
        items = models.filter_by_condition(UserInCampaign.objects, cond)
        now = datetime.datetime.now()
        td = now.replace(hour=23, minute=59, second=59, microsecond=999) - now
        seconds_till_midnight = td.seconds + (td.days * 24 * 3600)
        cache.set('condition_filter_%i' % cond.pk, items, seconds_till_midnight)
    return items


class AklubIndexDashboard(Dashboard):
    """
    Aklub index dashboard for aklub.
    """
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        # append a link list module for "quick links"
        self.children.append(
            modules.LinkList(
                _('Quick links'),
                layout='inline',
                draggable=False,
                deletable=False,
                collapsible=False,
                children=[
                    [_('Return to site'), '/'],
                    [
                        _('Change password'),
                        reverse('%s:password_change' % site_name),
                    ],
                    [_('Log out'), reverse('%s:logout' % site_name)],
                ],
            ),
        )

        # append an app list module for "Applications"
        self.children.append(
            modules.AppList(
                _('Applications'),
                exclude=('django.contrib.*',),
            ),
        )

        # append an app list module for "Administration"
        self.children.append(
            modules.AppList(
                _('Administration'),
                models=('django.contrib.*',),
            ),
        )

        # append a recent actions module
        self.children.append(modules.RecentActions(_('Recent Actions'), 5))

        self.children.append(
            modules.LinkList(
                _('Statistics'),
                children=[
                    {
                        'title': _('Members'),
                        'url': '/admin/aklub/stat-members',
                        'external': False,
                    },
                    {
                        'title': _('Payments'),
                        'url': '/admin/aklub/stat-payments',
                        'external': False,
                    },
                ],
            ),
        )

        # Modules for conditions:
        children = []
        if AccountStatements.objects.exists():
            children.append(
                {
                    'title': _(u"Days from last bill upload: %(days)s days") % {"days": (datetime.datetime.now() - AccountStatements.objects.first().import_date).days},
                    'url': "aklub/accountstatements/",
                    'external': False,
                }
            )
        if MassCommunication.objects.exists():
            children.append(
                {
                    'title': _(
                        u"Days from last mass communication: %(days)s days"
                    ) % {"days": (datetime.date.today() - MassCommunication.objects.order_by("-date").first().date).days},
                    'url': "aklub/masscommunication/",
                    'external': False,
                }
            )
        for cond in Condition.objects.filter(on_dashboard=True):
            children.append(
                {
                    'title': _(u"%(name)s: %(items)s items") % {"name": str(cond.name), "items": get_users_by_condition_cached(cond).count()},
                    'url': "aklub/user/?user_condition=%i" % cond.id,
                    'external': False,
                }
            )
        self.children.append(
            modules.LinkList(
                _('Conditions'),
                children=children,
            ),
        )

        for cond in Condition.objects.filter(on_dashboard=True):
            children = []
            members = get_users_by_condition_cached(cond)
            for member in members[:10]:
                children.append(
                    {
                        'title': member.person_name(),
                        'url': reverse('admin:aklub_userincampaign_change', args=[member.id]),
                        'external': False,
                    }
                )
            self.children.append(
                modules.LinkList(
                    title=cond.name,
                    title_url="aklub/user/?user_condition=%i" % cond.id,
                    children=children,
                    pre_content=_(u"Total number of items: %i") % members.count(),
                ),
            )

        # append an app list module
        self.children.append(
            modules.AppList(
                _('Dashboard Stats Settings'),
                models=('admin_tools_stats.*', ),
            ),
        )

        # Copy following code into your custom dashboard
        # append following code after recent actions module or
        # a link list module for "quick links"
        graph_list = get_active_graph()
        for i in graph_list:
            kwargs = {}
            kwargs['require_chart_jscss'] = True
            kwargs['graph_key'] = i.graph_key

            for key in context['request'].POST:
                if key.startswith('select_box_'):
                    kwargs[key] = context['request'].POST[key]

            self.children.append(YearDashboardCharts(**kwargs))


class AklubAppIndexDashboard(AppIndexDashboard):
    """
    Aklub app index dashboard for aklub.
    """

    # we disable title because its redundant with the model list module
    title = ''

    def __init__(self, *args, **kwargs):
        AppIndexDashboard.__init__(self, *args, **kwargs)

        # append a model list module and a recent actions module
        self.children += [
            modules.ModelList(self.app_title, self.models),
            modules.RecentActions(
                _('Recent Actions'),
                include_list=self.get_app_content_types(),
                limit=5,
            ),
        ]

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        return super(AklubAppIndexDashboard, self).init_with_context(context)
