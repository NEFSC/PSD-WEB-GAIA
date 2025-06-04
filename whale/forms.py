"""
Django forms module for whale observation and satellite imagery data management.

This module provides form classes for handling various aspects of whale observation data
and satellite imagery queries. It includes forms for API queries, data processing,
and whale observation recording with custom USWDS-styled widgets.

Classes:
    APIQueryForm: Form for querying various satellite imagery APIs with authentication
        and search parameters.
    
    ProcessingForm: Form for processing and filtering ETL data based on various parameters
        including spatial bounds, dates, and vendor information.
    
    USWDSButtonGroupWidget: Custom widget implementing USWDS-styled button groups with
        special handling for "Unsure" and "Whale" options.
    
    USWDSRadioButtonGroupWidget: Custom widget for rendering USWDS-styled radio button
        groups.
    
    PointsOfInterestForm: ModelForm for managing whale observation data from multiple
        users with fields for classification, species identification, and confidence
        levels.

Dependencies:
    - Django forms and GIS forms
    - datetime for default date handling
    - Custom models (AreaOfInterest, ExtractTransformLoad, PointsOfInterest)
    - Django utilities (safestring, forms.utils)

Note:
    All custom widgets follow USWDS (U.S. Web Design System) styling guidelines
    for consistent government web design standards.
"""

from datetime import datetime
from django import forms
from .models import AreaOfInterest, ExtractTransformLoad, PointsOfInterest, Annotations, Classification, Confidence, Target
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt

class APIQueryForm(forms.Form):
    """A Django Form for querying various satellite imagery APIs.

    This form provides fields for API selection, authentication, and search parameters
    for querying satellite imagery from multiple providers including USGS EarthExplorer,
    Global Enhanced GEOINT Delivery, and Maxar Geospatial Platform.

    Attributes:
        api (ChoiceField): Selection field for choosing the target API
        username (CharField): Input field for API username/credentials 
        password (CharField): Secured input field for API password
        aoi (ModelChoiceField): Selection field for choosing an Area of Interest
        start_date (DateField): Start date for the imagery search period
        end_date (DateField): End date for the imagery search period, defaults to current date
    """
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
    """
    A form class for processing data from ExtractTransformLoad model.

    This form provides fields for filtering and querying ETL data based on various parameters
    including table name, IDs, vendor information, spatial bounds, dates and area of interest.

    Attributes:
        table_name (ChoiceField): Dropdown of distinct table names from ETL model
        id (CharField): Optional ID field
        vendor_id (CharField): Optional vendor ID field
        entity_id (CharField): Optional entity ID field
        vendor (ChoiceField): Optional dropdown of distinct vendor names
        platform (ChoiceField): Optional dropdown of distinct platform names
        pixel_x_min (FloatField): Optional minimum x coordinate
        pixel_x_max (FloatField): Optional maximum x coordinate  
        pixel_y_min (FloatField): Optional minimum y coordinate
        pixel_y_max (FloatField): Optional maximum y coordinate
        date_min (DateField): Optional start date with year selection (2007-2033)
        date_max (DateField): Optional end date defaulting to current date
        publish_date_min (DateField): Optional publish start date
        publish_date_max (DateField): Optional publish end date defaulting to current date
        aoi (ModelChoiceField): Optional area of interest selection

    Meta:
        model: ExtractTransformLoad
        fields: All form fields listed above
    """
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
    """A custom widget class implementing a USWDS (U.S. Web Design System) styled button group.

    This widget creates a group of buttons following USWDS styling guidelines, with special
    handling for "Unsure" and "Whale" options. It includes a hidden input to store the
    selected value.

    Args:
        choices (iterable): An iterable of tuples containing (value, label) pairs for
            each button in the group.
        attrs (dict, optional): HTML attributes to be added to the hidden input element.
            Defaults to None.

    Attributes:
        choices (iterable): Stored choices for button creation.

    Methods:
        render(name, value, attrs=None, renderer=None): Renders the button group HTML.
            Special styling is applied to "Unsure" and "Whale" buttons using USWDS classes.
            Selected buttons receive an 'usa-button--active' class.

    Returns:
        SafeString: HTML markup for the button group including a hidden input for form submission.
    """
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
            submit_script = "" if label == "Whale" else "this.form.submit();"
            button_html = f'''<button {flatatt(button_attrs)} onclick="
                this.parentElement.nextElementSibling.value = this.dataset.value;
                {submit_script}">{label}</button>'''
            buttons.append(button_html)

        hidden_input = f'<input type="hidden" name="{name}" value="{value or ""}" {flatatt(attrs)}>'
        return mark_safe('<div id="classification-buttongroup" class="">' + ''.join(buttons) + '</div>' + hidden_input)

class USWDSRadioButtonGroupWidget(forms.Widget):
    """
    A custom Django form widget that renders a group of radio buttons styled
    according to the U.S. Web Design System (USWDS) standards.

    Attributes:
        choices (list): A list of tuples containing the value and label for each radio button option.
        attrs (dict, optional): Additional HTML attributes for the widget.

    Methods:
        render(name, value, attrs=None, renderer=None):
            Renders the HTML for the radio button group.

            Args:
                name (str): The name of the form field.
                value (str): The currently selected value.
                attrs (dict, optional): Additional HTML attributes for the widget.
                renderer (optional): An optional renderer instance.

            Returns:
                str: The HTML for the radio button group, marked safe for rendering.
    """
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
    """
    PointsOfInterestForm is a Django ModelForm for managing whale observation data from three users.

    This form allows multiple users to input their observations about potential whale sightings,
    with fields for classification, species identification, confidence levels and comments.
    It also includes final review fields for consensus determination.

    Fields for each user (user1, user2, user3):
    - user{n}_id: Unique identifier for the user
    - user{n}_comments: Free-text observations (max 500 chars)
    - user{n}_classification: Type of observation (uses USWDS button group)  
    - user{n}_species: Identified whale species (uses USWDS radio buttons)
    - user{n}_confidence: Confidence in identification (uses USWDS radio buttons)

    Final review fields:
    - final_review: Consensus classification
    - final_species: Consensus species identification  
    - final_confidence: Consensus confidence level

    All fields use USWDS (U.S. Web Design System) widgets for consistent styling:
    - Text areas with 500 char limit and 'usa-textarea' class
    - Button groups for classifications
    - Radio button groups for species and confidence selections

    Inherits from:
        forms.ModelForm

    Related Model:
        PointsOfInterest
    """
    class Meta:
        model = PointsOfInterest
        fields = ['id', 'final_review_date', 'final_species', 'final_classification']
        widgets = {

        }

class AnnotationForm(forms.ModelForm):
    class Meta:
        model = Annotations
        fields = ['poi', 'user', 'classification', 'comments', 'confidence', 'target']
        widgets = {
            'comments': forms.TextInput(attrs={'maxlength': 500, 'class': 'usa-input', 'id':'comments-textarea'}),
            'classification': USWDSButtonGroupWidget(choices=Classification),
            'target': USWDSRadioButtonGroupWidget(choices=Target),
            'confidence': USWDSRadioButtonGroupWidget(choices=Confidence),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        classification = cleaned_data.get('classification')
        target = cleaned_data.get('target')
        confidence = cleaned_data.get('confidence')

        if (str(classification).lower() == "whale") and (not target or not confidence):
            raise forms.ValidationError("Target and Confidence are required when Classification is Animal.")