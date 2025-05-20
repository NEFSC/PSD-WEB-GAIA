import requests
import datetime
from datetime import datetime, timedelta
from pyproj import CRS, Transformer

from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.db.models import Q, Count, Prefetch

from ..models import PointsOfInterest, Annotations
from ..forms import AnnotationForm
from django.core.paginator import Paginator

def annotation_page(request):
    # Initialize default coordinates (Fisherman's Wharf, Provincetown, MA)
    longitude, latitude = -70.183762, 42.049081
    id = request.GET.get('id')
    user = request.user
    annotation = None
    annotations = None

    def get_next_poi(user):
        # Filter POIs to only include those with less than 3 annotations
        # and exclude those already annotated by current user
        next_poi = PointsOfInterest.objects.exclude(
            annotations__user_id=user.id
        ).annotate(
            annotation_count=Count('annotations')
        ).filter(
            annotation_count__lt=3,
            cog_available=True
        ).first()

        return next_poi

    if id is None:
        poi = get_next_poi(user)
        if poi:
            return redirect(f'{request.path}?id={poi.id}')

    elif id:
        try:
            poi = PointsOfInterest.objects.get(id=id)
            vendor_id = poi.vendor_id
            
            if user.is_superuser:
                annotations = Annotations.objects.filter(poi=poi)
            try:
                annotation = Annotations.objects.select_related(
                    'classification', 
                    'target',
                    'confidence'
                ).get(poi=poi, user_id=user.id)
            except Annotations.DoesNotExist:
                annotation = Annotations(poi=poi, user_id=user.id)
        except PointsOfInterest.DoesNotExist:
            poi = None
        form = AnnotationForm(instance=annotation)

    if request.method == "POST":
        form = AnnotationForm(request.POST, instance=annotation)
        print(request.POST)
        if form.is_valid():
            if user.is_superuser and annotations.count() > 2:
                poi.final_review_date = datetime.now()
                poi.final_classification = form.cleaned_data['classification']
                poi.final_species = form.cleaned_data['target']
                poi.save(update_fields=['final_species', 'final_classification', 'final_review_date'])
            else:
                annotation = form.save()
            poi = get_next_poi(user)
            if poi:
                return redirect(f'{request.path}?id={poi.id}')
        else:
            print("Form is invalid")
            print(form.errors)

    # Since the points were generated from projected imagery, we need to transform them to
    #      geographic coordinates (i.e., EPSG:4326) to show them.
    if poi and poi.point and poi.epsg_code:
        print(f"Your geometry is: {poi.point} and your EPSG code is: {poi.epsg_code}")
        source_crs = CRS(f"EPSG:{poi.epsg_code}")
        target_crs = CRS("EPSG:4326")
        transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
        easting, northing = poi.point.coords
        print(f"easting: {easting}, northing: {northing}")
        longitude, latitude = transformer.transform(easting, northing)

    return render(request, 'annotation_page.html', {
        'poi': poi,
        'annotation': annotation,
        'annotations': annotations,
        'user_is_superuser': user.is_superuser,
        'form': form,
        'vendor_id': vendor_id,
        'longitude': longitude,
        'latitude': latitude,
        'error_message': None,
        'cog_url': None, #temporary fix until we get cog_url working again
    })

def proxy_openlayers_js(request):
    """ Proxy view for serving OpenLayers supporting COG viewing. """
    url = "https://cdn.jsdelivr.net/npm/ol@6.15.1/ol.js"
    response = requests.get(url)
    return HttpResponse(response.content, content_type="application/javascript")

def proxy_webgls_js(request):
    """ Proxy view for serving WebGLS supporting COG viewing. """
    url = "https://cdn.jsdelivr.net/npm/ol-webgl/dist/ol-webgl.min.js"
    response = requests.get(url)
    return HttpResponse(response.content, content_type="application/javascript")

def convert_date_or_none(date_str):
    """ Used to convert date formats from USGS EarthExplorer and NGA GEGD. """
    success = False
    
    if date_str and date_str != "None":
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                result = datetime.datetime.strptime(date_str, fmt)
                success = True
                return result
            except ValueError:
                continue
        if not success:
            return datetime.datetime.strptime(date_str, "%Y/%m/%d").strftime("%Y-%m-%d")
        raise ValueError(f"Date string {date_str} does not match supported formats!")
    return None

def generate_sas_token(blob_name):
    """ Generates a Shared Access Signature (SAS) Token on-the-fly. """
    try:
        account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        container_name = settings.AZURE_CONTAINER_NAME

        blob_path = 'cogs/' + blob_name
        print(f"Your blob path is: {blob_path}")
        
        sas_token = generate_blob_sas(
            account_name = account_name,
            container_name = container_name,
            blob_name = blob_path,
            account_key = account_key,
            permission = BlobSasPermissions(read=True),
            expiry = datetime.now() + timedelta(hours=1)
        )
    
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_path}?{sas_token}"
    
        return blob_url

    except Exception as e:
        print(f"Error generating SAS token for blob '{blob_name}': {e}")
        return None

def validation(request):
    sort_order = request.GET.get('sort', 'asc')
    show_final_reviews = request.GET.get('showfinals', 'false')
    page_number = request.GET.get('page')

    POIs = PointsOfInterest.objects.annotate(
        num_reviews=Count('annotations', filter=Q(annotations__classification=14))
    ).filter(num_reviews=2)

    if show_final_reviews == 'false':
        POIs = POIs.filter(final_classification__isnull=True)

    three_reviews = Annotations.objects.all().order_by('id')

    POIs = POIs.prefetch_related(
        Prefetch('annotations', queryset=three_reviews, to_attr='three_reviews')
    ).order_by('id')

    paginator = Paginator(POIs, 100)
    page_obj = paginator.get_page(page_number)

    return render(request, 'validation_page.html', {'page_obj': page_obj, 'sort_order': sort_order})