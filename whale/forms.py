from datetime import datetime
from django import forms
from django.contrib.gis import forms as gis_forms
from .models import AreaOfInterest, ExtractTransformLoad
from .models import PointsOfInterest as Species

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

class PointsOfInterestForm(forms.ModelForm):
    class Meta:
        model = Species
        fields = ['classification', 'confidence','species', 'comments']
        widgets = {
            'classification': forms.Select(),
            'confidence': forms.Select(),
            'species': forms.Select(),
            'comments': forms.Textarea(attrs={'maxlength': 500}),
        }