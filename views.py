# Create your views here.
import datetime, re
from django import forms, http
from django.db import models
from django.db.models import Sum
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.contrib.admin import widgets
from django.contrib.formtools.wizard.views import SessionWizardView
from django.core.mail import EmailMessage
from django.db.models import Sum, Count, Q
from django.utils import simplejson

import settings
from wp_urls import wp_reverse
from models import *

class RegularUserForm(forms.ModelForm):
        required_css_class = 'required' 

        # the fields defined here will override those defined on the model
        regular_frequency = forms.ChoiceField(label=_("Regular payments"), choices=User.REGULAR_PAYMENT_FREQUENCIES, required=True, widget=forms.RadioSelect())
        expected_date_of_first_payment = forms.DateField(label=_("Expected date of first payment"), required=True, 
							 initial=datetime.date.today(),
							 widget=forms.DateInput(format = '%d.%m.%Y'),
							 input_formats=('%d.%m.%Y',))
 
	class Meta:
		model = User
		fields = ('title_before', 'firstname', 'surname', 'title_after',
			  'street', 'city', 'country', 'zip_code',
			  'language', 'email', 'telephone',
			  'regular_frequency', 'regular_amount', 'expected_date_of_first_payment',
			  'wished_tax_confirmation',
			  'wished_welcome_letter', 'wished_information', 'public', 'note'
		)
		required = ('firstname', 'surname', 'street', 'city', 'country', 'zip_code',
			    'language', 'email', 'telephone', 'regular_frequency', 'regular_amount')
		widgets = {
			'language': forms.RadioSelect, # should be set automatically
		}

        def __init__(self, *args, **kwargs):
		super(RegularUserForm, self).__init__(*args, **kwargs)
		for field in self.Meta.required:
			f = self.fields[field].required = True

class RegularUserFormWithProfile(RegularUserForm):
	class Meta (RegularUserForm.Meta):
		fields = ('title_before', 'firstname', 'surname', 'title_after',
			  'street', 'city', 'country', 'zip_code',
			  'language', 'email', 'telephone',
			  'regular_frequency', 'regular_amount', 'expected_date_of_first_payment',
			  'wished_tax_confirmation',
			  'wished_welcome_letter', 'wished_information', 'public',
			  'profile_text', 'profile_picture',
		)

def new_user(form, regular):
	# Check number of registrations so far today
	# TODO: Lock DB access here (to ensure uniqueness of VS)
	now = datetime.datetime.now()
	reg_n_today = len(User.objects.filter(
			registered_support__gt = (
				now-datetime.timedelta(days=1))))
	for i in range(reg_n_today+1, 299):
                variable_symbol = '%s%02d%02d%03d' % (
			str(now.year)[-2:], now.month, now.day, i)
		if len(User.objects.filter(variable_symbol=variable_symbol)) == 0:
			break
	else:
		assert 0, "Out of free variable symbols, date %s, reg_n_today=%d" % (now, reg_n_today)
	# variable_symbol is now unique in database
	# Create new user instance and fill in additional data
	new_user = form.save(commit=False)
	new_user.regular_payments = regular
	new_user.variable_symbol = variable_symbol
	new_user.source = 'web'
	# Save new user instance
	new_user.save()
	# TODO: Unlock DB access here
	return new_user.id

def regular(request):
    form_class = RegularUserForm
    if request.method == 'POST': # If the form has been submitted...
        form = form_class(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
	    new_user(form, regular=True)
            return http.HttpResponseRedirect('/thanks/') # Redirect after POST
    else:
        form = form_class() # An unbound form

    return render_to_response('regular.html', {
        'form': form,
    })

def thanks(request):
	return render_to_response('thanks.html') 

def regular_wp(request):
    form_class = RegularUserFormWithProfile
    if request.method == 'POST': # If the form has been submitted...
        form = form_class(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            new_user(form, regular=True)
            return http.HttpResponseRedirect(wp_reverse('thanks_wp')) # Redirect after POST
    else:
        form = form_class() # An unbound form

    return render_to_response('regular-wp.html', {
        'form': form,
    })

def donators(request):
        payed = Payment.objects.exclude(type='expected').values_list('user_id', flat=True)
	donators = User.objects.filter(public=True, id__in=payed).order_by('surname')
	n_donators = len(donators)
	n_regular = len(donators.filter(active=True, regular_payments=True))
	return render_to_response('donators.html', {
			'n_donators': n_donators,
			'n_regular': n_regular,
			'donators': donators})

class OneTimePaymentWizardFormBase(forms.Form):
        required_css_class = 'required' 
	firstname = forms.CharField(label=_("First name"), max_length=40, required=True)
	surname = forms.CharField(label=_("Surname"), max_length=40, required=True)
	email = forms.CharField(label=_("Email"), max_length=40, required=True)
	amount = forms.IntegerField(label=_("Amount"), required=True)

class OneTimePaymentWizardFormWhoIs(forms.Form):
        required_css_class = 'required' 
	uid = forms.CharField(label=_("Account"))

class OneTimePaymentWizardFormConfirm(forms.Form):
        required_css_class = 'required' 
	# Type in variable symbol for verification (sent by mail)
	vs_check = forms.CharField(
		label=_("Variable symbol"),
		max_length=40, required=False)

class OneTimePaymentWizardFormKnown(forms.Form):
        required_css_class = 'required' 
	note = forms.CharField(max_length=40)

class OneTimePaymentWizardFormUnknown(forms.ModelForm):
        required_css_class = 'required' 

	class Meta:
		model = User
		fields = ('title_before', 'firstname', 'surname', 'title_after',
			  'street', 'city', 'country', 'zip_code',
			  'language', 'email', 'telephone',
			  'wished_tax_confirmation', 'wished_information',
			  'public', 'note'
		)
		required = ('firstname', 'surname', 'street', 'city', 'country', 'zip_code',
			    'language', 'email', 'telephone')
		widgets = {
			'language': forms.RadioSelect, # should be set automatically
		}

        def __init__(self, *args, **kwargs):
		super(OneTimePaymentWizardFormUnknown, self).__init__(*args, **kwargs)
		for field in self.Meta.required:
			f = self.fields[field].required = True


class OneTimePaymentWizard(SessionWizardView):

    def is_possibly_known(self):
        f = self._step_data(OneTimePaymentWizardFormBase)
        if f:
            return len(self._find_matching_users(f['email'], f['firstname'], f['surname'])) > 0
	return True

    def is_unknown(self):
	    return not self.is_possibly_known()

    def is_unknown_after_whois(self):
	u = self._step_data(OneTimePaymentWizardFormUnknown)
	f = self._step_data(OneTimePaymentWizardFormWhoIs)
	if u:
		return False
	elif f:
		return f['uid'] == 'None'
	else:
		return True

    def is_unknown_after_confirm(self):
        u = self._step_data(OneTimePaymentWizardFormUnknown)
	w = self._step_data(OneTimePaymentWizardFormWhoIs)
        c = self._step_data(OneTimePaymentWizardFormConfirm)
	if u:
		return False
	elif w and c:
		return c['vs_check'] != User.objects.filter(id=w['uid'])[0].variable_symbol
	else:
		return True

    FORMS = [['0', OneTimePaymentWizardFormBase, True, 'onetime_base.html'],
	     ['1', OneTimePaymentWizardFormUnknown, is_unknown, 'onetime_unknown.html'],
	     ['2', OneTimePaymentWizardFormWhoIs, is_possibly_known, 'onetime_whois.html'],
	     ['3', OneTimePaymentWizardFormUnknown, is_unknown_after_whois, 'onetime_unknown.html'],
	     ['4', OneTimePaymentWizardFormConfirm, is_possibly_known, 'onetime_confirm.html'],
	     ['5', OneTimePaymentWizardFormUnknown, is_unknown_after_confirm, 'onetime_unknown.html']]

    def _step_number(self, form):
	for e in self.FORMS:
		if e[1] == form or isinstance(form, e[1]):
			return e[0]
	else:
		raise ValueError(("No such form as requested", form))

    def _step_data(self, form):
	stepn = self._step_number(form)
	try:
		return self.get_cleaned_data_for_step(stepn)
	except TypeError:
		return None

    def get_template_names(self):
        return self.FORMS[int(self.steps.current)][3]


    def done(self, form_list, **kwargs):
	    for form in form_list:
		    if isinstance(form, OneTimePaymentWizardFormUnknown):
			    uid = new_user(form, False)
		    elif isinstance(form, OneTimePaymentWizardFormWhoIs):
			    uid = form.cleaned_data['uid']
	    user = User.objects.filter(id=uid)[0]
	    payment = Payment(date=datetime.datetime.now(),
			      amount=form_list[0].cleaned_data['amount'],
			      VS=user.variable_symbol,
			      type='expected',
			      user=user)
	    payment.save()
	    return http.HttpResponseRedirect('/thanks/')

    def send_vs_reminder(self, id):
	    user = User.objects.filter(id=id)[0]
	    mail_subject = _(
		    "Auto*Mat: Reminder of variable symbol")
	    mail_body = _(
		    "Dear friend,\n\n"
		    "if it is you who was just trying to let us know about his\n"
		    "planned donation to us, thank you very much and for your\n"
		    "convenience, here is your variable symbol:\n\n"
		    "                %s\n\n"
		    "If you do not know what this mean, it is possible that\n"
		    "sombody else has entered your name into our system. In such\n"
		    "a case, you can safely ignore this email, nothing will happen\n"
		    "without your authorization, or if you receive it repeatedly,\n"
		    "you can contact us on kp@auto-mat.cz.\n\n"
		    "Best Regards,\n"
		    "Auto*Mat\n" % user.variable_symbol)
	    EmailMessage(subject=mail_subject, body=mail_body,
			 from_email = 'kp@auto-mat.cz', to = [user.email]).send()

    def _find_matching_users(self, email, firstname, surname):
	    users = (set(User.objects.filter(email=email, active=True).all()) |
		     set(User.objects.filter(firstname=firstname, surname=surname, active=True)))
	    return list(users)

    def get_form(self, step=None, data=None, files=None):
	    form = super(OneTimePaymentWizard, self).get_form(step, data, files)
	    if step == self._step_number(OneTimePaymentWizardFormUnknown):
		    cd0 = self._step_data(OneTimePaymentWizardFormBase)
		    if cd0:
			    for f in ['firstname', 'surname', 'email']:
				    form.fields[f].initial = cd0[f]
	    elif step == self._step_number(OneTimePaymentWizardFormWhoIs):
		    def obfuscate(email):
			    m = re.match('(?P<b1>.).*(?P<b2>.)@(?P<a>.).*\.(?P<d>.+)', email)
			    return m and ("%s***%s@%s***.%s" % m.groups()) or ""
		    cd0 = self._step_data(OneTimePaymentWizardFormBase)
		    if cd0:
			    users = self._find_matching_users(*[cd0[key] for key in [
						    'email', 'firstname', 'surname']])
			    candidates = ([(u.id, "%s %s <%s>" % (u.firstname, u.surname, obfuscate(u.email))) for u in users]
					  + [('None', _("None of these accounts"))])
			    form.fields['uid'] = forms.ChoiceField(choices=candidates)
	    elif step == self._step_number(OneTimePaymentWizardFormConfirm):
		    d2 = self._step_data(OneTimePaymentWizardFormWhoIs)
		    if d2['uid'] != 'None':
			    self.send_vs_reminder(d2['uid'])
	    return form

def onetime (request):
	forms = OneTimePaymentWizard.FORMS
	cw = OneTimePaymentWizard.as_view(
		[form[1] for form in forms],
		condition_dict = dict([(form[0], form[2]) for form in forms]))
	return cw(request)

def stat_members(request):
	return render_to_response('stat-members.html',
				  {'members_by_months': StatMemberCountsByMonths.objects.all(),
				   'total_members': User.objects.all().filter(active=True).aggregate(Count('id'))['id__count']
				   })

def stat_payments(request):
	return render_to_response('stat-payments.html',
				  {'payments_by_months': StatPaymentsByMonths.objects.all(),
				   'total_amount': Payment.objects.all().filter(~Q(type='expected')).aggregate(Sum('amount'))['amount__sum']
				   })

	return render_to_response('stat-finance.html',
			      RequestContext(request, {}),)

def profiles(request):
	from_date = request.GET.get('from') or '1970-1-1'
	paying = request.GET.get('paying')
	result = [{'firstname': u.public and u.firstname or '',
		   'surname': u.public and u.surname or '',
		   'text': u.profile_text or '',
		   'picture': u.profile_picture and u.profile_picture.url or '',
		   'picture_thumbnail': u.profile_picture and u.profile_picture.thumbnail.url() or '',
		   }
		  for u in User.objects.annotate(**User.annotations).filter(registered_support__gt=from_date).order_by('-registered_support')
		  if ((not paying) or (u.payment_total > 0)) ]
	return http.HttpResponse(simplejson.dumps(result), mimetype='application/json')
