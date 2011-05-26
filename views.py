# Create your views here.
from django import forms, http
from django.db import models
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _

from models import User

class RegularUserForm(forms.ModelForm):
        required_css_class = 'required' 

        # the fields defined here will override those defined on the model
        regular_frequency = forms.ChoiceField(choices=User.REGULAR_PAYMENT_FREQUENCIES, required=True, widget=forms.RadioSelect())
 
	class Meta:
		model = User
		fields = ('title_before', 'firstname', 'surname', 'title_after',
			  'street', 'city', 'country', 'zip_code',
			  'language', 'email', 'telephone',
			  'regular_frequency', 'regular_amount',
                          'public',
		)
		widgets = {
			'language': forms.RadioSelect, # should be set automatically
		}

	
def regular(request):
    if request.method == 'POST': # If the form has been submitted...
        form = RegularUserForm(request.POST) # A form bound to the POST data
        if form.is_valid(): # All validation rules pass
            # Process the data in form.cleaned_data
            # ...
	    form.save()
            return http.HttpResponseRedirect('/thanks/') # Redirect after POST
    else:
        form = RegularUserForm() # An unbound form

    return render_to_response('regular.html', {
        'form': form,
    })

def thanks(request):
	return render_to_response('thanks.html') 
