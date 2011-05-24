# Create your views here.
from django import forms, http
from django.shortcuts import render_to_response

from models import User

class RegularUserForm(forms.ModelForm):
	class Meta:
		model = User
		fields = ('title_before', 'firstname', 'surname', 'title_after',
			  'sex', 
			  'street', 'city', 'country', 'zip_code',
			  'language', 'email', 'telephone',
			  'regular_frequency', 'regular_amount',
		)
		widgets = {
			'sex': forms.RadioSelect,
			'language': forms.RadioSelect,
			'regular_frequency': forms.RadioSelect,
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
