"""
Django forms module for animal observation and satellite imagery data management.

This module provides form classes for handling various aspects of animal observation data
and satellite imagery queries. It includes forms for API queries, data processing,
and animal observation recording with custom USWDS-styled widgets.

Classes:
    APIQueryForm: Form for querying various satellite imagery APIs with authentication
        and search parameters.
    
    ProcessingForm: Form for processing and filtering ETL data based on various parameters
        including spatial bounds, dates, and vendor information.
    
    USWDSButtonGroupWidget: Custom widget implementing USWDS-styled button groups with
        special handling for "Unsure" and "Animal" options.
    
    USWDSRadioButtonGroupWidget: Custom widget for rendering USWDS-styled radio button
        groups.
    
    PointsOfInterestForm: ModelForm for managing animal observation data from multiple
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
from .models import AreaOfInterest, ExtractTransformLoad, PointsOfInterest, Annotations, Classification, Confidence, Target, FishnetReviews, Category
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
import logging
logger = logging.getLogger('animal')

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
    def __init__(self, choices, attrs=None):
        super().__init__(attrs)
        self.choices = choices

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        attrs['id'] = attrs.get('id', f'id_{name}')

        # Get all classifications with their categories
        from .models import Classification, Category
        classifications = Classification.objects.select_related('category').all()
        
        # Group classifications by category
        categories_dict = {}
        uncategorized = []
        
        for classification in classifications:
            if classification.category:
                category_id = classification.category.id
                if category_id not in categories_dict:
                    categories_dict[category_id] = {
                        'category': classification.category,
                        'classifications': []
                    }
                categories_dict[category_id]['classifications'].append(classification)
            else:
                uncategorized.append(classification)
        
        # Sort categories by their order field
        sorted_categories = sorted(categories_dict.values(), key=lambda x: x['category'].order)
        
        buttons = []
        
        # Render buttons grouped by category
        for category_group in sorted_categories:
            category = category_group['category']
            category_classifications = category_group['classifications']
            
            # Sort classifications within category by their order field
            sorted_classifications = sorted(category_classifications, key=lambda x: x.order)
            
            # Add category header
            if category.name:
                buttons.append(f'<div class="usa-button-group__label margin-top-2 margin-bottom-1"><strong>{category.name}</strong></div>')
            
            # Add buttons for this category
            for classification in sorted_classifications:
                if classification.id in [None, '']:
                    continue
                button_attrs = {
                    'type': 'button',
                    'class': 'usa-button margin-1',
                    'data-value': classification.id,
                }
                if classification.label in {"Unsure", "Animal"}:
                    button_attrs['class'] += ' usa-button--outline'
                if str(value) == str(classification.id):
                    button_attrs['class'] += ' usa-button--active'
                submit_script = "" if classification.label == "Animal" else "this.form.submit();"
                button_html = f'''<button {flatatt(button_attrs)} onclick="
                    this.parentElement.nextElementSibling.value = this.dataset.value;
                    {submit_script}">{classification.label}</button>'''
                buttons.append(button_html)
        
        # Add uncategorized classifications at the end
        if uncategorized:
            # Sort uncategorized by their order field
            sorted_uncategorized = sorted(uncategorized, key=lambda x: x.order)
            
            buttons.append(f'<div class="usa-button-group__label margin-top-2 margin-bottom-1"><strong>Other</strong></div>')
            for classification in sorted_uncategorized:
                if classification.id in [None, '']:
                    continue
                button_attrs = {
                    'type': 'button',
                    'class': 'usa-button margin-1',
                    'data-value': classification.id,
                }
                if classification.label in {"Unsure", "Animal"}:
                    button_attrs['class'] += ' usa-button--outline'
                if str(value) == str(classification.id):
                    button_attrs['class'] += ' usa-button--active'
                submit_script = "" if classification.label == "Animal" else "this.form.submit();"
                button_html = f'''<button {flatatt(button_attrs)} onclick="
                    this.parentElement.nextElementSibling.value = this.dataset.value;
                    {submit_script}">{classification.label}</button>'''
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
        
        # Sort choices alphabetically by label
        sorted_choices = sorted(self.choices, key=lambda x: x[1])
        
        for val, label in sorted_choices:
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
        fields = ['id', 'vendor_id', 'point', 'final_review_date', 'final_species', 'final_classification']
        widgets = {

        }

class AnnotationForm(forms.ModelForm):
    classification = forms.ModelChoiceField(
        queryset=Classification.objects.select_related('category').all(),
        widget=USWDSButtonGroupWidget(
            choices=[]  # Choices will be handled dynamically in the widget
        )
    )
    class Meta:
        model = Annotations
        fields = ['poi', 'user', 'classification', 'comments', 'confidence', 'target']
        widgets = {
            'comments': forms.Textarea(attrs={'maxlength': 500, 'class': 'usa-textarea', 'id':'comments-textarea'}),
            'target': USWDSRadioButtonGroupWidget(choices=Target),
            'confidence': USWDSRadioButtonGroupWidget(choices=Confidence),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        classification = cleaned_data.get('classification')
        target = cleaned_data.get('target')
        confidence = cleaned_data.get('confidence')

        if (str(classification).lower() == "animal") and (not target or not confidence):
            raise forms.ValidationError("Target and Confidence are required when Classification is Animal.")
        
class FishnetForm(forms.ModelForm):
    class Meta:
        model = FishnetReviews
        fields = ['fishnet', 'user', 'id', 'date']