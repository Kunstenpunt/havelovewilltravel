# https://stackoverflow.com/questions/50380769/how-to-create-a-autocomplete-input-field-in-a-form-using-django

from django import forms
import datetime

from .models import Concert, Genre, Artist, Organisation, Location

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Div, ButtonHolder, Submit, HTML, Button

from dal import autocomplete

class ConcertForm(forms.ModelForm):
    location = forms.ModelChoiceField(
            queryset=Location.objects.all(),
            widget=autocomplete.ModelSelect2(url='location_autocomplete_select', attrs={
                # Set some placeholder
                'data-placeholder': 'Autocomplete ...',
                # Only trigger autocompletion after 3 characters have been typed
                'data-minimum-input-length': 3,
            },),
            required=False,
        )

    class Meta:
        model = Concert
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ConcertForm, self).__init__(*args, **kwargs)
        self.fields['artist'] = forms.ModelMultipleChoiceField(
            queryset=Artist.objects.all(),
            widget=autocomplete.ModelSelect2Multiple(url='artist_autocomplete_select')
        )
        self.fields['organisation']=forms.ModelMultipleChoiceField(
            queryset=Organisation.objects.all(),
            widget=autocomplete.ModelSelect2Multiple(url='organisation_autocomplete_select',
            forward=['location'])
        )
        self.fields['date']=forms.DateField(help_text=datetime.date.today)
        self.fields['cancelled']=forms.BooleanField(
            widget=forms.CheckboxInput(),
            required=False)
        self.fields['verified']=forms.BooleanField(
            widget=forms.CheckboxInput(),
            required=False)
        self.fields['manual']=forms.BooleanField(widget=forms.CheckboxInput(), required=False)
        self.fields['ignore']=forms.BooleanField(widget=forms.CheckboxInput(), required=False)
        self.fields['genre']=forms.ModelMultipleChoiceField(
            queryset=Genre.objects.all(),
            widget=forms.CheckboxSelectMultiple,
            required=False)

        self.fields['description']=forms.CharField(widget=forms.Textarea(attrs={'rows': 1 }), required=False)
        self.fields['annotation']=forms.CharField(widget=forms.Textarea(attrs={'rows': 1}), required=False)
        self.fields['program']=forms.CharField(widget=forms.Textarea(attrs={'rows': 1}), required=False)
        self.fields['evidence']=forms.CharField(widget=forms.Textarea(attrs={'rows': 1}), required=False)


        self.fields['organisation'].widget.attrs.update({'class' : 'autocomplete-list'})
        self.fields['artist'].widget.attrs.update({'class' : 'autocomplete-list'})
        self.fields['location'].widget.attrs.update({'class' : 'autocomplete-list'})
        self.fields['until_date']=forms.DateField(help_text=datetime.date.today, required=False)
        self.fields['time']=forms.TimeField(help_text=str(datetime.time(11,30))[0:5], required=False)

        self.helper=FormHelper()

        self.helper.layout=Layout(
            HTML("""
            <h2>Create/update a concert</h2>
            """),
            Row(
                Column('title', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            Row(
                Column('artist', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            Row(
                Column('date', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),
            Row(
                Column('organisation', css_class='form-group col-md-6 mb-0'),    
                Column('location', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('description', css_class='form-group col-md-12 mb-0'),
                css_class='form-row'
                ),

            Div(            
                Row(
                    Column('evidence', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                    ),
                Row(
                    Column('annotation', css_class='form-group col-md-12 mb-0')
                    ),
                Row(
                    Column('program', css_class='form-group col-md-12 mb-0')
                    ),
                Row(
                    Column('cancelled', css_class='form-group col-md-3 mb-0'),
                    Column('verified', css_class='form-group col-md-3 mb-0'),
                    Column('manual', css_class='form-group col-md-3 mb-0'),
                    Column('ignore', css_class='form-group col-md-3 mb-0'),
                    css_class='form-row'
                    ),
                Row(
                    Column('until_date', css_class='form-group col-md-4 mb-0'),
                    Column('time', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                    ),
                Row(
                    Column('genre', css_class='form-group col-md-12 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('latitude', css_class='form-group col-md-6 mb-0'),
                    Column('longitude', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                css_id='extra-fields'
            ),
            Row(
                Button('show-details', 'Toggle-details', onclick="toggleDetails()", css_class="btn-toggle")),
        )

        self.helper.add_input(Submit('submit', 'Submit', css_class='btn btn-outline-primary btn-custom form-left-button'))
        self.helper.form_method = 'POST'
