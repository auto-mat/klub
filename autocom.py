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

def get_val(spec, user):
    # Symbolic names
    if spec == 'month_ago':
        return datetime.datetime.now()-datetime.timedelta(days=30)
    if spec == 'true':
        return True
    if spec == 'false':
        return False

    # DB objects
    if '.' in spec:
        obj, attr = spec.split('.')
        if obj == 'user':
            attr_val = getattr(user, attr)
            if attr[-2:] == '()':
                return attr_val()
            else:
                return attr_val
        elif obj == 'datetime':
            return datetime.datetime.strptime(attr, '%Y-%m-%d %H:%M')
        elif obj == 'timedelta':
            return datetime.timedelta(days=int(attr))
    else:
        return spec

def is_true(condition, user, simple=False):
    # Composed conditions
    if condition.operation == 'and':
        for cond in [condition.cond1] + list(condition.conds2.all()):
            if not is_true(cond, user):
                return False
        return True
    if condition.operation == 'or':
        for cond in [condition.cond1] + list(condition.conds2.all()):
            if is_true(condition.cond1, user):
                return True
        return False

    # Elementary conditions
    left = get_val(condition.variable, user)
    right = get_val(condition.value, user)
    #print "left: %s" % left
    #print "right: %s" % right

    if left == None or right == None:
        return False

    if condition.operation == '=':
        return left == right
    if condition.operation == '<':
        return left < right
    if condition.operation == '>':
        return left > right
    raise NotImplementedError("Unknown operation %s" % condition.operation)
    
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
        monthly_donation = user.monthly_payment,
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
                if is_true(auto_comm.condition, user):
                    #print "      %s" % user
                    c = Communication(user=user, method=auto_comm.method, date=datetime.datetime.now(),
                                      subject=auto_comm.subject, summary=process_template(auto_comm.template, user),
                                      note="Prepared by auto*mated mailer at %s" % datetime.datetime.now(),
                                      dispatched=False)
                    auto_comm.sent_to_users.add(user)
                    c.save()
                    if auto_comm.dispatch_auto:
                        c.dispatch()

