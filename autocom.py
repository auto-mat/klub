#!/usr/bin/env python
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
#
# Copyright (C) 2010 o.s. Auto*Mat
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

"""Automatic communications for club management"""

from models import User, Payment, Communication, AutomaticCommunication
import sys, datetime
import string

def process_template(template_string, user):
    #TODO: Substitute variables
    template = string.Template(template_string)
    text = template.substitute(
        name = user.firstname,
        surname = user.surname,
        street = user.street,
        city = user.city,
        zipcode = user.zip_code,
        email = user.email,
        telephone = user.telephone,
        regular_amount = user.regular_amount,
        regular_frequency = user.regular_frequency,
        var_symbol = user.variable_symbol,
        )
    return text

def check():
    for auto_comm in AutomaticCommunication.objects.all():
        #print "Processing"
        #print "  %s:  %s" % (auto_comm.condition, auto_comm)
        #print "    Action: %s" % auto_comm.method
        #print "    Users newly satisfying condition:"
        for user in User.objects.all():
            if user not in auto_comm.sent_to_users.all():
                if auto_comm.condition.is_true(user):
                    #print "      %s" % user
                    c = Communication(user=user, method=auto_comm.method, date=datetime.datetime.now(),
                                      subject=auto_comm.subject, summary=process_template(auto_comm.template, user),
                                      note="Prepared by auto*mated mailer at %s" % datetime.datetime.now(),
                                      dispatched=auto_comm.dispatch_auto)
                    auto_comm.sent_to_users.add(user)
                    c.save()

