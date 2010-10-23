#!/usr/bin/env python

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
        if obj == 'u':
            return getattr(user, attr)
        if obj == 'datetime':
            return datetime.datetime.strptime(attr, '%Y-%m-%d %H:%M')
    else:
        return spec

def is_true(condition, user):
    # Composed conditions
    if condition.operation == 'and':
        return is_true(condition.cond1, user) and is_true(condition.cond2, user)
    if condition.operation == 'or':
        return is_true(condition.cond1, user) or is_true(condition.cond2, user)

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
                                      handled_by="Auto*Mat", dispatched=False)
                    auto_comm.sent_to_users.add(user)
                    c.save()
                    if auto_comm.dispatch_auto:
                        c.dispatch()

