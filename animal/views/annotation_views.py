import requests
import datetime
from datetime import datetime, timedelta
from pyproj import CRS, Transformer
from azure.core.credentials import AzureNamedKeyCredential
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect
from django.db.models import Q, Count, Prefetch
import json
from django.contrib.gis.geos import Point

from ..models import PointsOfInterest, Annotations, Fishnet, FishnetReviews
from ..forms import AnnotationForm, FishnetForm, PointsOfInterestForm
from django.core.paginator import Paginator
import logging
from django.contrib.gis.geos import Polygon

logger = logging.getLogger('animal')  # use your app name here

def annotation_page(request, project_id, item_id=None):
    # Initialize default coordinates (Fisherman's Wharf, Provincetown, MA)
    longitude, latitude = -70.183762, 42.049081
    id = item_id
    project = project_id
    user = request.user
    annotation = None
    annotations = None
    form = AnnotationForm(instance=annotation, initial={})
    vendor_id = None

    def cog_exists(vendor_id):
        cached_result = cache.get(f'cog_existence_{vendor_id}')
        if cached_result is not None:
            return cached_result

        blob_name = check_cog_existence(vendor_id, directory='cogs/')
        cache.set(f'cog_existence_{vendor_id}', (blob_name), timeout=300)  
        return blob_name 

    def get_next_poi(user, project):
        # Get IDs of POIs the user has already annotated
        annotated_poi_ids = set(Annotations.objects.filter(
            user_id=user.id
        ).values_list('poi_id', flat=True))
        
        # Get IDs of POIs with 3+ annotations
        full_poi_ids = set(Annotations.objects.values('poi_id')
            .annotate(count=Count('poi_id'))
            .filter(count__gte=3)
            .values_list('poi_id', flat=True))
        
        # Base query filtered by project if needed
        query = PointsOfInterest.objects.filter(project_id=project)
        
        # Apply exclusions and get first available POI
        return query.exclude(
            id__in=annotated_poi_ids | full_poi_ids
        ).order_by('id').first()

    if id is None:
        poi = get_next_poi(user, project)
        return redirect(f'/project/{project_id}/annotation/{poi.id}')

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
    form = AnnotationForm(instance=annotation, initial={})

    if request.method == "POST":
        form = AnnotationForm(request.POST, instance=annotation)
        if form.is_valid():
            if user.is_superuser and annotations.count() > 2:
                poi.final_review_date = datetime.now()
                poi.final_classification = form.cleaned_data['classification']
                poi.final_species = form.cleaned_data['target']
                poi.save(update_fields=['final_species', 'final_classification', 'final_review_date'])
            else:
                annotation = form.save(commit=False)
                annotation.full_clean()
                annotation.save()
            poi = get_next_poi(user, project)
            return redirect(f'/project/{project_id}/annotation/{poi.id}')

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

    cogurl = cog_exists(poi.vendor_id) if poi else None
    return render(request, 'annotation_page.html', {
        'poi': poi,
        'annotation': annotation,
        'annotations': annotations,
        'user_is_superuser': user.is_superuser,
        'form': form,
        'vendor_id': vendor_id,
        'longitude': longitude,
        'latitude': latitude,
        'error_message': form.errors,
        'cogurl': cogurl
    })

def cog_view(request, vendor_id=None):
    try:
        blob_url = generate_sas_token(vendor_id)
        print(f"Constructed Blob URL with SAS Token: {blob_url}")

        session = requests.Session()
        retries = requests.adapters.Retry(total = 5, backoff_factor = 1, status_forcelist = [500, 502, 503, 504])
        adapter = requests.adapters.HTTPAdapter(max_retries = retries)
        session.mount('https://', adapter)

        range_header = request.META.get('HTTP_RANGE', None)
        headers = {}

        if range_header:
            start, end = range_header.strip().split('=')[1].split('-')
            headers['Range'] = f"bytes={start}-{end}" if end else f"bytes={start}-"

        response = requests.get(blob_url, headers=headers, timeout = 10)

        if response.status_code in [200, 206]:
            print("Successful status code {response.status_code}")

            if range_header:
                content_range = response.headers.get('Content-Range')
                tile_response = HttpResponse(response.content, content_type = 'image/tiff', status = 206)
                tile_response['Content-Range'] = content_range
                tile_response['Accept-Ranges'] = 'bytes'
                tile_response['Content-Length'] = len(response.content)
            else:
                tile_response = HttpResponse(response.content, content_type="image/tiff")   
            return tile_response
        else: 
            return HttpResponseForbidden(f"Error fetching COG: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        return HttpResponse(f"Network error: {str(e)}", status = 503)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=403)

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
            expiry = datetime.now() + timedelta(hours=2)
        )
    
        blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_path}?{sas_token}"
    
        return blob_url

    except Exception as e:
        print(f"Error generating SAS token for blob '{blob_name}': {e}")
        return None

def check_cog_existence(vendor_id, directory='None'):
    """ Checks if a Cloud Optimized GeoTIFF eixsts in Azure. """
    account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
    account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
    container_name = settings.AZURE_CONTAINER_NAME
    vendor_id = vendor_id.replace('P1BS', 'S1BS')

    try:
        credential = AzureNamedKeyCredential(account_name, account_key)
    
        blob_service_client = BlobServiceClient(
            account_url = f"https://{account_name}.blob.core.windows.net/",
            credential=credential
        )
        container_client = blob_service_client.get_container_client(container_name)
        prefix = directory if directory else ""
        
        blobs = container_client.list_blobs(name_starts_with=prefix)
        blob_names = [blob.name for blob in blobs]
        matching_blobs = [blob_name for blob_name in blob_names if vendor_id in blob_name]
        if matching_blobs:
            return matching_blobs[0]
        return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return False, None

def validation(request, project_id):
    sort_order = request.GET.get('sort', 'asc')
    show_final_reviews = request.GET.get('showfinals', 'false')
    page_number = request.GET.get('page')

    POIs = PointsOfInterest.objects.filter(
        annotations__classification=14,
        project_id=project_id
    ).distinct().only('id')

    if show_final_reviews == 'false':
        POIs = POIs.filter(final_classification_id__isnull=True)

    three_reviews = Annotations.objects.filter(poi__in=POIs).select_related('classification', 'target', 'confidence')

    POIs = POIs.prefetch_related(
        Prefetch('annotations', queryset=three_reviews, to_attr='three_reviews')
    ).order_by('id')

    paginator = Paginator(POIs, 100)
    page_obj = paginator.get_page(page_number)

    return render(request, 'validation_page.html', {'page_obj': page_obj, 'sort_order': sort_order})

def detect_page(request, project_id, id=None):
    # Initialize default coordinates (Fisherman's Wharf, Provincetown, MA)
    longitude, latitude = -70.183762, 42.049081
    user = request.user

    def get_next_cell(user, project_id):
        # Get IDs of Fishnets the user has already annotated
        reviewed_fishnet_ids = set(FishnetReviews.objects.filter(
            user_id=user.id
        ).values_list('fishnet_id', flat=True))
        
        # Get IDs of Fishnets with 2+ annotations
        full_fishnet_ids = set(FishnetReviews.objects.values('fishnet_id')
            .annotate(count=Count('fishnet_id'))
            .filter(count__gte=2)
            .values_list('fishnet_id', flat=True))
        
        # Base query filtered by project if needed
        query = Fishnet.objects.filter(project_id=project_id)
        
        # Apply exclusions and get first available fishnet cell
        return query.exclude(
            id__in=list(reviewed_fishnet_ids | full_fishnet_ids)
        ).order_by('id').first()

    if id is None:
        fishnet = get_next_cell(user, project_id)
        if fishnet is None:
            return render(request, 'detect_page.html', {
            'info_message': 'No points cells left to review.',
        })
        else:
            return redirect(f'/project/{project_id}/detect/{fishnet.id}')

    def cog_exists(vendor_id):
        cached_result = cache.get(f'cog_existence_{vendor_id}')
        if cached_result is not None:
            return cached_result

        blob_name = check_cog_existence(vendor_id, directory='cogs/')
        cache.set(f'cog_existence_{vendor_id}', (blob_name), timeout=300)  
        return blob_name 

    fishnet = Fishnet.objects.get(id=id)
    vendor_id = fishnet.vendor_id

    if request.method == "POST":
        form = FishnetForm(request.POST, instance=fishnet)
        if form.is_valid():
            FishnetReviews.objects.create(
                fishnet=fishnet,
                user=user,
                date=datetime.now()
            )
            fishnet = get_next_cell(user, project_id)
            return redirect(f'/project/{project_id}/detect/{fishnet.id}')

    source_crs = CRS(f"EPSG:3857")
    target_crs = CRS("EPSG:4326")
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    centroid = fishnet.cell.centroid
    easting = centroid.x
    northing = centroid.y
    print(f"easting: {easting}, northing: {northing}")
    longitude, latitude = transformer.transform(easting, northing)

    # Transform the fishnet cell polygon
    # Get the exterior ring of the polygon
    exterior_ring = fishnet.cell.exterior_ring
    transformed_coords = []
    # Transform each point in the polygon
    for point in exterior_ring:
        lon, lat = transformer.transform(point[0], point[1])
        transformed_coords.append((lon, lat))
    # Create a new polygon with transformed coordinates
    transformed_polygon = Polygon(transformed_coords)
    # Store the transformed polygon for rendering
    fishnet.transformed_cell = transformed_polygon

    cogurl = cog_exists(vendor_id) if fishnet else None
    return render(request, 'detect_page.html', {
        'id': fishnet.id,
        'cell': fishnet.transformed_cell,
        'vendor_id': vendor_id,
        'longitude': longitude,
        'latitude': latitude,
        'cogurl': cogurl,
        'project_id': project_id
    })

def create_point(request, project_id):
    if request.method == "POST":
        # Accept both JSON and form-data
        points_data = None

        # Try to get points from form-data (as in your JS)
        if 'points' in request.POST:
            # The frontend sends a single stringified JSON array under 'points'
            try:
                points_data = json.loads(request.POST['points'])
            except Exception as e:
                return JsonResponse({'error': f'Invalid points data: {e}'}, status=400)
        else:
            # Try to parse JSON body (for application/json requests)
            try:
                body = request.body.decode('utf-8')
                data = json.loads(body)
                points_data = data.get('points')
            except Exception:
                pass

        if not points_data or not isinstance(points_data, list):
            return JsonResponse({'error': 'No valid points provided.'}, status=400)

        created_points = []
        for point_data in points_data:
            try:
                geom = point_data.get('geometry')
                vendor_id = point_data.get('vendor_id')
                # Accept geometry as GeoJSON
                if geom and geom.get('type') == 'Point':
                    coords = geom.get('coordinates')
                    point_geom = Point(coords[0], coords[1])
                else:
                    return JsonResponse({'error': 'Invalid geometry.'}, status=400)

                poi = PointsOfInterest.objects.create(
                    point=point_geom,
                    vendor_id=vendor_id,
                    project_id=project_id
                )
                created_points.append({'id': poi.id})
                logger.info(f"Point {poi.id} created")
            except Exception as e:
                logger.error(f"Error creating point: {e}")
                return JsonResponse({'error': str(e)}, status=400)

        return JsonResponse({'points': created_points})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
