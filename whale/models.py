from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models as gis_models

# Create your models here.
class AreaOfInterest(gis_models.Model):
    id = gis_models.AutoField(primary_key = True)
    name = gis_models.CharField(max_length = 50)
    requestor = gis_models.CharField(max_length = 25)
    geometry = gis_models.GeometryField()
    sqkm = gis_models.FloatField()

    def __str__(self):
        #return f"{self.name} (ID: {self.id})"
        return self.name

class People(models.Model):
    id = models.AutoField(primary_key = True)
    name = models.CharField(max_length = 20)
    email = models.CharField(max_length = 30)
    organization = models.CharField(max_length = 25)
    sub_organization = models.CharField(max_length = 50)
    location = models.CharField(max_length = 50)

    def __str__(self):
        return self.name

class Targets(gis_models.Model):
    id = gis_models.AutoField(primary_key = True)
    target = gis_models.CharField(max_length = 30)
    scientific_name = gis_models.CharField(max_length = 25)

    def __str__(self):
        return self.target


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
    requestor = models.ForeignKey(People, on_delete=models.DO_NOTHING)
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

# Come back to this tomorrow
class PointsOfInterest(gis_models.Model):
    CLASSIFICATION_CHOICES = [
        ('water', 'Water'),
        ('cloud', 'Cloud'),
        ('bird', 'Bird'),
        ('waves', 'Waves'),
        ('plane', 'Plane'),
        ('ship', 'Ship'),
        ('shadow', 'Shadow'),
        ('oil', 'Oil'),
        ('aquaculture', 'Aquaculture'),
        ('debris', 'Debris'),
        ('rock', 'Rock'),
        ('mudflats_or_land', 'Mudflats or Water'),
        ('buoy', 'Buoy'),
        ('whale', 'Whale'),
        ('zooplankton', 'Zooplankton'),
        ('land', 'Land'),
        ('unsure', 'Unsure'),
    ]

    CONFIDENCE_CHOICES = [
        ('possible', 'Possible ( ≤ 75% )'),
        ('probable', 'Probable ( 75 - 85% )'),
        ('definite', 'Definite ( ≥ 85% )')
    ]

    SPECIES_CHOICES = [
        ('unknown', 'Unknown'),
        ('right', 'Right'),
        ('humpback', 'Humpback'),
        ('fin', 'Fin'),
        ('sei', 'Sei'),
        ('minke', 'Minke'),
        ('beluga', 'Beluga'),
        ('other', 'Other')
    ]

    # Mandatory and from ETL
    id = gis_models.IntegerField(primary_key = True)    
    catalog_id = gis_models.CharField(max_length = 16, null=True, blank=True)
    vendor_id = gis_models.CharField(max_length = 39, null=True, blank=True)
    entity_id = gis_models.CharField(max_length = 20, null=True, blank=True)

    # From Generate Interesting Points
    sample_idx = gis_models.CharField(max_length = 40, null=True, blank=True)
    area = gis_models.FloatField(null=True, blank=True)
    deviation = gis_models.FloatField(null=True, blank=True)
    epsg_code = gis_models.CharField(max_length = 6, null=True, blank=True)

    # For review process
    status = models.CharField(max_length = 20, default="Available")
    locked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    review_count = models.IntegerField(default=0)
    reviewed_by_users = models.ManyToManyField(User, related_name="reviewed_species", blank=True)
    
    email = gis_models.CharField(max_length = 35, null=True, blank=True)
    client_ip = gis_models.CharField(max_length = 13, null=True, blank=True)
    out_time = gis_models.DateField(null=True, blank=True)
    in_time = gis_models.DateField(null=True, blank=True)
    classification = gis_models.CharField(max_length = 20, choices=CLASSIFICATION_CHOICES, default='unsure')
    confidence = gis_models.CharField(max_length = 10, choices=CONFIDENCE_CHOICES, default='NA')
    species = gis_models.CharField(max_length = 50, choices=SPECIES_CHOICES, default='NA')
    comments = gis_models.CharField(max_length = 500, null=True, blank=True)

     # For review process
    user1_id = models.CharField(max_length=30, null=True, blank=True)
    user1_classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, null=True, blank=True)
    user1_comments = models.CharField(max_length=500, null=True, blank=True)
    user1_species = models.CharField(max_length=50, choices=SPECIES_CHOICES, null=True, blank=True)
    user1_confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES, null=True, blank=True)
    user2_id = models.CharField(max_length=30, null=True, blank=True)
    user2_classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, null=True, blank=True)
    user2_comments = models.CharField(max_length=500, null=True, blank=True)
    user2_species = models.CharField(max_length=50, choices=SPECIES_CHOICES, null=True, blank=True)
    user2_confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES, null=True, blank=True)
    user3_id = models.CharField(max_length=30, null=True, blank=True)
    user3_classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, null=True, blank=True)
    user3_comments = models.CharField(max_length=500, null=True, blank=True)
    user3_species = models.CharField(max_length=50, choices=SPECIES_CHOICES, null=True, blank=True)
    user3_confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES, null=True, blank=True)
    final_review = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES, null=True, blank=True)
    final_review_date = models.DateField(null=True, blank=True)

    # Mandatory
    point = gis_models.GeometryField(null=True, blank=True)

    class Meta:
        constraints = [
            gis_models.UniqueConstraint(fields=['id' ,'catalog_id', 'vendor_id', 'entity_id'], name='fk_img_id')
        ]
    
    def __str__(self):
        return self.classification
