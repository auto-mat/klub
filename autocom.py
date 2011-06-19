# 
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
    template = string.Template(template_string)

    # Make variable substitutions
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

    # Modify text according to gender
    # Example: Vazeny{y|a} {pane|pani} -> [male] -> Vazeny pane
    gender_text = ""
    o = 0
    i = 0
    while i < len(text):
        if text[i] == '{':
            gender_text += text[o:i]
            sep_pos = text.find('|', i)
            end_pos = text.find('}', i)
            assert sep_pos > i
            assert end_pos > sep_pos, "Wrong format of template, no separator | or after end mark }"
            male_variant = text[i+1:sep_pos]
            female_variant = text[sep_pos+1:end_pos]
            if user.sex == 'male':
                gender_text += male_variant;
            elif user.sex == 'female':
                gender_text += female_variant;
            else:
                gender_text += male_variant+"/"+female_variant;
            o = end_pos+1
            i = end_pos
        i+=1
    if o == 0:
        gender_text = text

    return gender_text

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

