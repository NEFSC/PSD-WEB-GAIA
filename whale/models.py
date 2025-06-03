from django.db import models
from django.contrib.auth.models import User
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError

class AreaOfInterest(gis_models.Model):
    id = gis_models.AutoField(primary_key = True)
    name = gis_models.CharField(max_length = 50)
    requestor = gis_models.CharField(max_length = 25)
    geometry = gis_models.GeometryField()
    sqkm = gis_models.FloatField()

    def __str__(self):
        return self.name

class Targets(gis_models.Model):
    id = gis_models.AutoField(primary_key = True)
    value = gis_models.CharField(max_length = 30)
    label = gis_models.CharField(max_length = 25)

    def __str__(self):
        return self.label

class Confidence(models.Model):
    id = models.AutoField(primary_key=True)
    value = models.CharField(max_length=10)
    label = models.CharField(max_length=25)

    def __str__(self):
        return self.label
    
class Classification(models.Model):
    id = models.AutoField(primary_key=True)
    label = models.CharField(max_length=25)
    value = models.CharField(max_length=25)

    def __str__(self):
        return self.label
    
# Needs to be revisited with cleaned data from Lauren
class Tasking(models.Model):
    MONO_STERO_CHOICES = [
        ('mono', 'Mono'),
        ('stereo', 'Stereo'),
    ]
    
    id = models.AutoField(primary_key = True)
    dar = models.IntegerField()
    aoi = models.ForeignKey(AreaOfInterest, on_delete=models.DO_NOTHING)
    location = models.CharField(max_length = 12)
    target = models.CharField(max_length = 30)
    requestor = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    vendor = models.CharField(max_length = 10)
    mono_stereo = models.CharField(max_length = 6, choices=MONO_STERO_CHOICES)
    date_entered = models.DateField()
    acquisition_start = models.DateField()
    acquisition_end = models.DateField()
    ona_wv2 = models.CharField(max_length = 10)
    ona_wv3 = models.CharField(max_length = 10)
    tasking_description = models.CharField(max_length = 10)
    comments = models.CharField(max_length = 250)
    status = models.CharField(max_length = 8)
    output_format = models.CharField(max_length = 7)
    processing_level = models.CharField(max_length = 41)
    website_link = models.CharField(max_length = 50)
    permission_to_share = models.CharField(max_length = 500)

    def __str__(self):
        return self.id
    
class EarthExplorer(gis_models.Model):
    """
    A Django model representing satellite imagery metadata from EarthExplorer.

    This model stores detailed information about satellite imagery including acquisition details,
    technical specifications, and geographical metadata.

    Attributes:
        entity_id (CharField): Primary key identifier for the imagery, max 20 chars
        aoi_id (ForeignKey): Reference to AreaOfInterest model
        catalog_id (CharField): Catalog identifier, max 16 chars
        acquisition_date (DateField): Date when imagery was captured
        vendor (CharField): Name of imagery vendor, max 18 chars
        vendor_id (CharField): Vendor-specific identifier, max 39 chars
        cloud_cover (IntegerField): Percentage of cloud cover in imagery
        satellite (CharField): Name of satellite platform, max 11 chars
        sensor (CharField): Type of sensor used, max 3 chars
        number_of_bands (IntegerField): Number of spectral bands
        map_projection (CharField): Map projection code, max 3 chars
        datum (CharField): Geodetic datum used, max 5 chars
        processing_level (CharField): Processing level code, max 3 chars
        file_format (CharField): Format of imagery file, max 7 chars
        license_id (IntegerField): License identifier
        sun_azimuth (FloatField): Sun azimuth angle during capture
        sun_elevation (FloatField): Sun elevation angle during capture
        pixel_size_x (FloatField): Pixel resolution in X direction
        pixel_size_y (FloatField): Pixel resolution in Y direction
        license_uplift_update (DateField): Date of license update
        event (CharField): Event identifier, max 5 chars
        event_date (DateField): Date of associated event
        date_entered (DateField): Date record was entered into system
        center_latitude_dec (FloatField): Center latitude in decimal degrees
        center_longitude_dec (FloatField): Center longitude in decimal degrees
        thumbnail (CharField): Path or URL to thumbnail image, max 76 chars
        publish_date (DateTimeField): DateTime when imagery was published
        bounds (GeometryField): Geographical bounds of the imagery

    Returns:
        str: String representation in format "entity_id in Category ID: aoi_id"
    """
    entity_id = gis_models.CharField(max_length = 20, primary_key = True)
    aoi_id = gis_models.ForeignKey(AreaOfInterest, on_delete=models.DO_NOTHING)
    catalog_id = gis_models.CharField(max_length = 16)
    acquisition_date = gis_models.DateField(null=True, blank=True)
    vendor = gis_models.CharField(max_length = 18)
    vendor_id = gis_models.CharField(max_length = 39)
    cloud_cover = gis_models.IntegerField()
    satellite = gis_models.CharField(max_length = 11)
    sensor = gis_models.CharField(max_length = 3)
    number_of_bands = gis_models.IntegerField()
    map_projection = gis_models.CharField(max_length = 3)
    datum = gis_models.CharField(max_length = 5)
    processing_level = gis_models.CharField(max_length = 3)
    file_format = gis_models.CharField(max_length = 7)
    license_id = gis_models.IntegerField()
    sun_azimuth = gis_models.FloatField()
    sun_elevation = gis_models.FloatField()
    pixel_size_x = gis_models.FloatField()
    pixel_size_y = gis_models.FloatField()
    license_uplift_update = gis_models.DateField(null=True, blank=True)
    event = gis_models.CharField(max_length = 5)
    event_date = gis_models.DateField(null=True, blank=True)
    date_entered = gis_models.DateField(null=True, blank=True)
    center_latitude_dec = gis_models.FloatField()
    center_longitude_dec = gis_models.FloatField()
    thumbnail = gis_models.CharField(max_length = 76)
    publish_date = gis_models.DateTimeField(null=True, blank=True)
    bounds = gis_models.GeometryField()

    def __str__(self):
        return f"{self.entity_id} in Category ID: {self.aoi_id.id}"

class GEOINTDiscovery(gis_models.Model):
    """A Django model representing GEOINT (Geospatial Intelligence) discovery data.

    This model stores detailed information about geospatial intelligence discoveries,
    including metadata about imagery, acquisition details, and geometric properties.

    Attributes:
        id (CharField): Primary key identifier (max length: 32)
        aoi_id (ForeignKey): Reference to AreaOfInterest model
        legacy_id (CharField): Legacy identifier (max length: 16)
        factory_order_number (CharField): Factory order reference (max length: 12)
        acquisition_date (DateField): Date when the data was acquired
        source (CharField): Source of the GEOINT data (max length: 9)
        source_unit (CharField): Unit of the source (max length: 5)
        product_type (CharField): Type of product (max length: 36)
        cloud_cover (FloatField): Percentage of cloud cover
        off_nadir_angle (FloatField): Off-nadir angle measurement
        sun_elevation (FloatField): Sun elevation angle
        sun_azimuth (FloatField): Sun azimuth angle
        ground_sample_distance (FloatField): Ground sample distance measurement
        data_layer (CharField): Layer of data (max length: 10)
        legacy_description (CharField): Legacy description (max length: 12)
        color_band_order (CharField): Order of color bands (max length: 3)
        asset_name (CharField): Name of the asset (max length: 8)
        per_pixel_x (FloatField): X-axis pixel measurement
        per_pixel_y (FloatField): Y-axis pixel measurement
        crs_from_pixels (CharField): Coordinate reference system (max length: 10)
        age_days (FloatField): Age of data in days
        ingest_date (DateField): Date when data was ingested
        company_name (CharField): Name of company (max length: 12)
        copyright (CharField): Copyright information (max length: 37)
        niirs (FloatField): National Imagery Interpretability Rating Scale value
        geometry (GeometryField): Geometric data representation

    Methods:
        __str__(): Returns string representation of the discovery
    """
    id = gis_models.CharField(max_length = 32, primary_key = True)
    aoi_id = gis_models.ForeignKey(AreaOfInterest, on_delete=models.DO_NOTHING)
    legacy_id = gis_models.CharField(max_length = 16)
    factory_order_number = gis_models.CharField(max_length = 12)
    acquisition_date = gis_models.DateField()
    source = gis_models.CharField(max_length = 9)
    source_unit = gis_models.CharField(max_length = 5)
    product_type = gis_models.CharField(max_length = 36)
    cloud_cover = gis_models.FloatField()
    off_nadir_angle = gis_models.FloatField()
    sun_elevation = gis_models.FloatField()
    sun_azimuth = gis_models.FloatField()
    ground_sample_distance = gis_models.FloatField()
    data_layer = gis_models.CharField(max_length = 10)
    legacy_description = gis_models.CharField(max_length = 12)
    color_band_order = gis_models.CharField(max_length = 3)
    asset_name = gis_models.CharField(max_length = 8)
    per_pixel_x = gis_models.FloatField()
    per_pixel_y = gis_models.FloatField()
    crs_from_pixels = gis_models.CharField(max_length = 10)
    age_days = gis_models.FloatField()
    ingest_date = gis_models.DateField()
    company_name = gis_models.CharField(max_length = 12)
    copyright = gis_models.CharField(max_length = 37)
    niirs = gis_models.FloatField()
    geometry = gis_models.GeometryField()

    def __str__(self):
        return f"{self.name} in Category ID: {self.aoi_id.id}"

    # def save(self, *args, **kwargs):
    #     datetime_fields = ['acquisition_date', 'ingest_date']

    #     for field in datetime_fields:
    #         field_value = getattr(self, field)
    #         if field_value and timezone.is_naive(field_value):
    #             aware_datetime = timezone.make_aware(field_value)
    #             setattr(self, field, aware_datetime)

    #     super().save(*args, **kwargs)

class MaxarGeospatialPlatform(gis_models.Model):
    """
    A Django model representing Maxar Geospatial Platform satellite imagery metadata.

    This model stores detailed metadata about satellite imagery from Maxar's geospatial platforms,
    including sensor information, image quality metrics, and geometric properties.

    Attributes:
        id (CharField): Unique identifier for the imagery, max length 16 characters.
        aoi_id (ForeignKey): Reference to the AreaOfInterest model.
        platform (CharField): Satellite platform name, max length 11 characters.
        instruments (CharField): Sensor instruments used, max length 4 characters.
        gsd (FloatField): Ground Sample Distance in meters.
        pan_resolution_avg (FloatField): Average panchromatic resolution.
        multi_resolution_avg (FloatField): Average multispectral resolution.
        datetime (DateTimeField): Acquisition date and time of the imagery.
        off_nadir (FloatField): Off-nadir angle in degrees.
        azimuth (FloatField): Azimuth angle in degrees.
        sun_azimuth (FloatField): Sun azimuth angle in degrees.
        sun_elevation (FloatField): Sun elevation angle in degrees.
        bbox (GeometryField): Bounding box geometry of the imagery coverage.

    Methods:
        __str__: Returns a string representation of the model instance.
    """
    id = gis_models.CharField(max_length = 16, primary_key = True)
    aoi_id = gis_models.ForeignKey(AreaOfInterest, on_delete=models.DO_NOTHING)
    platform = gis_models.CharField(max_length = 11)
    instruments = gis_models.CharField(max_length = 4)
    gsd = gis_models.FloatField()
    pan_resolution_avg = gis_models.FloatField()
    multi_resolution_avg = gis_models.FloatField()
    datetime = gis_models.DateTimeField()
    off_nadir = gis_models.FloatField()
    azimuth = gis_models.FloatField()
    sun_azimuth = gis_models.FloatField()
    sun_elevation = gis_models.FloatField()
    bbox = gis_models.GeometryField()

    def __str__(self):
        return f"{self.name} in Category ID: {self.aoi_id.id}"

# This table was built from other tables
#      Some places this is called a denormalized table, materalized view,
#      aggregate table, staging table, etc. It is effectively a starting
#      point for other work and should not be expected to matriculate
#      changes to earlier tables.

class ExtractTransformLoad(gis_models.Model):
    """
    A Django model representing the Extract, Transform, Load (ETL) process for geospatial imagery data.

    This model stores metadata about imagery including vendor information, spatial characteristics,
    and temporal data. It maps to an existing database table 'etl' and is not managed by Django migrations.

    Attributes:
        table_name (CharField): Name of the table, max length 4 characters
        aoi_id (IntegerField): Area of Interest identifier
        id (CharField): Primary key, max length 16 characters
        vendor_id (CharField): Vendor's unique identifier, max length 39 characters
        entity_id (CharField): Entity identifier, max length 20 characters
        vendor (CharField): Name of the vendor, max length 18 characters
        platform (CharField): Platform identifier, max length 11 characters
        pixel_size_x (FloatField): Pixel width in ground units
        pixel_size_y (FloatField): Pixel height in ground units
        date (DateField): Date of image capture
        publish_date (DateField): Date of image publication
        geometry (TextField): Geometry information of the image footprint
        sea_state_qual (CharField): Qualitative sea state description, optional, max length 15 characters
        sea_state_quant (IntegerField): Quantitative sea state measurement, optional
        shareable (CharField): Sharing permissions indicator, optional, max length 3 characters

    Note:
        The model has a unique constraint on the combination of id, vendor_id, and entity_id fields.
    """
    table_name = gis_models.CharField(max_length = 4)
    aoi_id = gis_models.IntegerField()
    id = gis_models.CharField(max_length = 16, primary_key = True)
    vendor_id = gis_models.CharField(max_length = 39)
    entity_id = gis_models.CharField(max_length = 20)
    vendor = gis_models.CharField(max_length = 18)
    platform = gis_models.CharField(max_length = 11)
    pixel_size_x = gis_models.FloatField()
    pixel_size_y = gis_models.FloatField()
    date = gis_models.DateField()
    publish_date = gis_models.DateField()
    geometry = gis_models.TextField() # Might need to *rebuild* as Geometry type
    sea_state_qual = gis_models.CharField(max_length = 15, null = True, blank = True)
    sea_state_quant = gis_models.IntegerField(null = True, blank = True)
    shareable = gis_models.CharField(max_length = 3, null = True, blank = True)

    class Meta:
        db_table = 'etl'
        managed = False

        constraints = [
            gis_models.UniqueConstraint(fields=['id', 'vendor_id', 'entity_id'], name='img_id')
        ]

    def __str__(self):
        return f"{self.id} {self.vendor_id} {self.entity_id}"

class PointsOfInterest(gis_models.Model):
    # Mandatory and from ETL
    id = gis_models.AutoField(primary_key = True)
    catalog_id = gis_models.CharField(max_length = 16, null=True, blank=True)
    vendor_id = gis_models.CharField(max_length = 39, null=True, blank=True)
    entity_id = gis_models.CharField(max_length = 20, null=True, blank=True)

    # From Generate Interesting Points
    sample_idx = gis_models.CharField(max_length = 40, null=True, blank=True)
    area = gis_models.FloatField(null=True, blank=True)
    deviation = gis_models.FloatField(null=True, blank=True)
    epsg_code = gis_models.CharField(max_length = 6, null=True, blank=True)

    # For review process
    final_species = models.ForeignKey(Targets, on_delete=models.CASCADE, null=True, blank=True)
    final_classification = models.ForeignKey(Classification, on_delete=models.CASCADE, null=True, blank=True)
    final_review_date = models.DateField(null=True, blank=True)

    # Mandatory
    point = gis_models.GeometryField(null=True, blank=True)
    
    def __str__(self):
        return self
    
class Annotations(models.Model):
    id = models.AutoField(primary_key = True)
    poi = models.ForeignKey(PointsOfInterest, related_name='annotations', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE)
    comments = models.CharField(max_length=500, null=True, blank=True)
    confidence = models.ForeignKey(Confidence, on_delete=models.CASCADE, null=True, blank=True)
    target = models.ForeignKey(Targets, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Annotation {self.id} by {self.user}"
    
    def clean(self):
        super().clean()
        if self.classification == 14:
            if not self.target:
                raise ValidationError({'Target': 'This field cannot be null when classification is Animal.'})
            if not self.confidence:
                raise ValidationError({'Confidence': 'This field cannot be null when classification is Animal.'})