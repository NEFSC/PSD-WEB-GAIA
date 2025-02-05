from datetime import datetime
from django import forms
from django.contrib.gis import forms as gis_forms
from .models import AreaOfInterest, ExtractTransformLoad
from .models import PointsOfInterest
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt

class APIQueryForm(forms.Form):
    API_CHOICES = [
        ('ee', 'USGS EarthExplorer'),
        ('gegd', 'Global Enhanced GEOINT Delivery'),
        ('mgp', 'Maxar Geospatial Platform'),
    ]

    api = forms.ChoiceField(choices=API_CHOICES,
                            label="Select API",
                            required=False)
    username = forms.CharField(widget=forms.TextInput(attrs={'autocomplete': 'off'}),
                               max_length=100,
                               label="API Username",
                               required=False)
    password = forms.CharField(widget=forms.PasswordInput(),
                               label="API Password",
                               required=False)
    aoi = forms.ModelChoiceField(queryset=AreaOfInterest.objects.all(),
                                 label="Area of Interest",
                                 required=False)
    start_date = forms.DateField(widget=forms.SelectDateWidget(years=range(2007, 2034)),
                                 label="Start Date",
                                 required=False)
    end_date = forms.DateField(widget=forms.SelectDateWidget(years=range(2007, 2034)),
                               label="End Date",
                               initial = datetime.now(),
                               required=False)

class ProcessingForm(forms.Form):
    table_name = forms.ChoiceField(choices=[(table, table) for table in ExtractTransformLoad.objects.values_list('table_name', flat=True).distinct()])
    id = forms.CharField(required=False)
    vendor_id = forms.CharField(required=False)
    entity_id = forms.CharField(required=False)
    vendor = forms.ChoiceField(choices=[(vendor, vendor) for vendor in ExtractTransformLoad.objects.values_list('vendor', flat=True).distinct()],
                               required=False)
    platform = forms.ChoiceField(choices=[(platform, platform) for platform in ExtractTransformLoad.objects.values_list('platform', flat=True).distinct()],
                                 required=False)
    pixel_x_min = forms.FloatField(required=False)
    pixel_x_max = forms.FloatField(required=False)
    pixel_y_min = forms.FloatField(required=False)
    pixel_y_max = forms.FloatField(required=False)
    date_min = forms.DateField(required=False,
                               widget=forms.SelectDateWidget(years=range(2007, 2034)))
    date_max = forms.DateField(required=False,
                               widget=forms.SelectDateWidget(years=range(2007, 2034)),
                               initial = datetime.now())
    publish_date_min = forms.DateField(required=False,
                                       widget=forms.SelectDateWidget(years=range(2007, 2034)))
    publish_date_max = forms.DateField(required=False,
                                       widget=forms.SelectDateWidget(years=range(2007, 2034)),
                                       initial = datetime.now())
    aoi = forms.ModelChoiceField(required=False, queryset=AreaOfInterest.objects.all())

    class Meta:
        model = ExtractTransformLoad
        fields = ['table_name', 'id', 'vendor_id', 'entity_id', 'vendor', 'platform',
                  'pixel_x_min', 'pixel_x_max', 'pixel_y_min', 'pixel_y_max',
                  'date_min', 'date_max', 'publish_date_min', 'publish_date_max', 'aoi']

class USWDSButtonGroupWidget(forms.Widget):
    def __init__(self, choices, attrs=None):
        super().__init__(attrs)
        self.choices = choices

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['id'] = attrs.get('id', f'id_{name}')

        # Reorder choices to prioritize "Unsure" and "Whale"
        def prioritize_choice(choice):
            return (choice[1] not in {"Unsure", "Whale"}, choice[1])

        reordered_choices = sorted(self.choices, key=prioritize_choice)

        buttons = []
        for val, label in reordered_choices:
            if val in [None, '']:
                continue
            button_attrs = {
                'type': 'button',
                'class': 'usa-button margin-1',
                'data-value': val,
            }
            if label in {"Unsure", "Whale"}:
                button_attrs['class'] += ' usa-button--outline'
            if str(value) == str(val):
                button_attrs['class'] += ' usa-button--active'
            button_html = f'<button {flatatt(button_attrs)}>{label}</button>'
            buttons.append(button_html)

        hidden_input = f'<input type="hidden" name="{name}" value="{value or ""}" {flatatt(attrs)}>'
        return mark_safe('<div id="classification-buttongroup" class="">' + ''.join(buttons) + '</div>' + hidden_input)

class USWDSRadioButtonGroupWidget(forms.Widget):
    def __init__(self, choices, attrs=None):
        super().__init__(attrs)
        self.choices = choices

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['id'] = attrs.get('id', f'id_{name}')
        radios = []
        for val, label in self.choices:
            if val in [None, '']:
                continue
            input_attrs = {
                'type': 'radio',
                'name': name,
                'value': val,
                'id': f'{attrs["id"]}_{val}',
                'class': 'usa-radio__input'
            }
            if str(value) == str(val):
                input_attrs['checked'] = 'checked'
            radio_input = f'<input {flatatt(input_attrs)}>'
            label_html = f'<label for="{input_attrs["id"]}" class="usa-radio__label">{label}</label>'
            radios.append(
                f'<div class="usa-radio">{radio_input}{label_html}</div>'
            )
        return mark_safe('<fieldset class="usa-fieldset">' + ''.join(radios) + '</fieldset>')

class PointsOfInterestForm(forms.ModelForm):
    class Meta:
        model = PointsOfInterest
        fields = ['user1_id', 'user1_comments', 'user1_classification', 'user1_species', 'user1_confidence', 'user2_id', 'user2_comments', 'user2_classification', 'user2_species', 'user2_confidence', 'user3_id', 'user3_comments', 'user3_classification', 'user3_species', 'user3_confidence']
        widgets = {
            'user1_comments': forms.Textarea(attrs={'maxlength': 500, 'class': 'usa-textarea', 'id':'comments-textarea'}),
            'user1_classification': USWDSButtonGroupWidget(choices=PointsOfInterest.CLASSIFICATION_CHOICES),
            'user1_species': USWDSRadioButtonGroupWidget(choices=PointsOfInterest.SPECIES_CHOICES),
            'user1_confidence': USWDSRadioButtonGroupWidget(choices=PointsOfInterest.CONFIDENCE_CHOICES),
            'user2_comments': forms.Textarea(attrs={'maxlength': 500, 'class': 'usa-textarea', 'id':'comments-textarea'}),
            'user2_classification': USWDSButtonGroupWidget(choices=PointsOfInterest.CLASSIFICATION_CHOICES),
            'user2_species': USWDSRadioButtonGroupWidget(choices=PointsOfInterest.SPECIES_CHOICES),
            'user2_confidence': USWDSRadioButtonGroupWidget(choices=PointsOfInterest.CONFIDENCE_CHOICES),
            'user3_comments': forms.Textarea(attrs={'maxlength': 500, 'class': 'usa-textarea', 'id':'comments-textarea'}),
            'user3_classification': USWDSButtonGroupWidget(choices=PointsOfInterest.CLASSIFICATION_CHOICES),
            'user3_species': USWDSRadioButtonGroupWidget(choices=PointsOfInterest.SPECIES_CHOICES),
            'user3_confidence': USWDSRadioButtonGroupWidget(choices=PointsOfInterest.CONFIDENCE_CHOICES),
        }