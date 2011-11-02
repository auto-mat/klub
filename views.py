# Create your views here.
import datetime
from django import forms, http
from django.db import models
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.contrib.admin import widgets

from models import User

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

def regular(request):
    if request.method == 'POST': # If the form has been submitted...
        form = RegularUserForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
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
	    new_user.regular_payments = True
            new_user.variable_symbol = variable_symbol
	    new_user.source = 'web'
	    # Save new user instance
	    new_user.save()
	    # TODO: Unlock DB access here
            return http.HttpResponseRedirect('/thanks/') # Redirect after POST
    else:
        form = RegularUserForm() # An unbound form

    return render_to_response('regular.html', {
        'form': form,
    })

def thanks(request):
	return render_to_response('thanks.html') 
