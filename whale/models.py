from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.contrib.gis.db import models as gis_models

class AreaOfInterest(gis_models.Model):
    """
    A Django model representing an Area of Interest (AOI) with geographic information.

    This model stores spatial data for areas of interest, including their names,
    requestors, geometric boundaries, and area measurements.

    Attributes:
        id (AutoField): Primary key for the area of interest.
        name (CharField): Name of the area of interest, limited to 50 characters.
        requestor (CharField): Name of the person who requested the AOI, limited to 25 characters.
        geometry (GeometryField): Geographic boundary data of the area.
        sqkm (FloatField): Area measurement in square kilometers.

    Returns:
        str: String representation of the area of interest, using the name field.
    """
    id = gis_models.AutoField(primary_key = True)
    name = gis_models.CharField(max_length = 50)
    requestor = gis_models.CharField(max_length = 25)
    geometry = gis_models.GeometryField()
    sqkm = gis_models.FloatField()

    def __str__(self):
        #return f"{self.name} (ID: {self.id})"
        return self.name

class People(models.Model):
    """
    A Django model representing individuals in the system.

    This model stores personal and organizational information about people.

    Attributes:
        id (AutoField): Primary key for the person record.
        name (CharField): The person's full name, limited to 20 characters.
        email (CharField): The person's email address, limited to 30 characters.
        organization (CharField): The person's organization name, limited to 25 characters.
        sub_organization (CharField): A subdivision or department within the organization, limited to 50 characters.
        location (CharField): The person's physical location or address, limited to 50 characters.

    Methods:
        __str__: Returns the person's name as string representation.
    """
    id = models.AutoField(primary_key = True)
    name = models.CharField(max_length = 20)
    email = models.CharField(max_length = 30)
    organization = models.CharField(max_length = 25)
    sub_organization = models.CharField(max_length = 50)
    location = models.CharField(max_length = 50)

    def __str__(self):
        return self.name

class Targets(gis_models.Model):
    """Target species model that holds information about each whale target.

    This model represents individual whale target species and their scientific names.

    Attributes:
        id (AutoField): Primary key for the target species.
        target (CharField): Common name of the whale species, max length 30 characters.
        scientific_name (CharField): Scientific/Latin name of the species, max length 25 characters.

    Returns:
        str: The target (common) name of the whale species when object is converted to string.
    """
    id = gis_models.AutoField(primary_key = True)
    target = gis_models.CharField(max_length = 30)
    scientific_name = gis_models.CharField(max_length = 25)

    def __str__(self):
        return self.target


# Needs to be revisited with cleaned data from Lauren
class Tasking(models.Model):
    """
    A Django model representing a tasking entry for satellite imagery acquisition.
    Attributes:
        id (AutoField): Primary key for the tasking entry
        dar (int): Digital Acquisition Request number
        aoi (ForeignKey): Reference to an Area of Interest
        location (str): Location identifier, max 12 chars
        target (str): Target identifier, max 30 chars
        requestor (ForeignKey): Reference to the person making the request
        vendor (str): Vendor name, max 10 chars
        mono_stereo (str): Type of imagery - either 'mono' or 'stereo'
        date_entered (Date): Date when the tasking was entered
        acquisition_start (Date): Start date for image acquisition
        acquisition_end (Date): End date for image acquisition
        ona_wv2 (str): WorldView-2 ONA identifier, max 10 chars
        ona_wv3 (str): WorldView-3 ONA identifier, max 10 chars
        tasking_description (str): Brief description of the tasking, max 10 chars
        comments (str): Additional comments, max 250 chars
        status (str): Current status of the tasking, max 8 chars
        output_format (str): Required output format, max 7 chars
        processing_level (str): Required processing level, max 41 chars
        website_link (str): Related website URL, max 50 chars
        permission_to_share (str): Sharing permissions details, max 500 chars
    Returns:
        str: String representation of the tasking entry ID
    """
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
    """
    A Django model representing Points of Interest in satellite imagery, specifically designed for whale and marine observation.
    This model stores geographical points of interest with associated metadata, classification information,
    and review status. It supports a multi-user review process for identifying and classifying objects
    in satellite imagery.
    Attributes:
        CLASSIFICATION_CHOICES (list): Predefined options for classifying observed objects
        CONFIDENCE_CHOICES (list): Confidence levels for classifications
        SPECIES_CHOICES (list): Available whale species options
    Fields:
        Identification:
            id (int): Primary key
            catalog_id (str): Catalog identifier
            vendor_id (str): Vendor identifier
            entity_id (str): Entity identifier
        Geometric Properties:
            sample_idx (str): Sample index identifier
            area (float): Area measurement
            deviation (float): Deviation measurement
            epsg_code (str): EPSG coordinate system code
            point (geometry): Geographical point location
        Review Process:
            status (str): Current review status
            locked_by (User): User currently reviewing the point
            review_count (int): Number of reviews completed
            reviewed_by_users (ManyToManyField): Users who have reviewed this point
        Metadata:
            email (str): Associated email address
            client_ip (str): Client IP address
            out_time (date): Check-out timestamp
            in_time (date): Check-in timestamp
        Classification:
            classification (str): Current classification
            confidence (str): Confidence level
            species (str): Species identification
            comments (str): General comments
        User Reviews:
            user[1-3]_id (str): Reviewer IDs
            user[1-3]_classification (str): Individual classifications
            user[1-3]_comments (str): Individual comments
            user[1-3]_species (str): Individual species identifications
            user[1-3]_confidence (str): Individual confidence levels
        Final Review:
            final_review (str): Final classification
            final_review_date (date): Date of final review
    Meta:
        constraints: Ensures unique combination of id, catalog_id, vendor_id, and entity_id
    """
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
        ('unknown', 'Unkown'),
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
    classification = gis_models.CharField(max_length = 20, choices=CLASSIFICATION_CHOICES, default='Unclassified')
    confidence = gis_models.CharField(max_length = 10, choices=CONFIDENCE_CHOICES, default='NA')
    species = gis_models.CharField(max_length = 50, choices=SPECIES_CHOICES, default='NA')
    comments = gis_models.CharField(max_length = 500, null=True, blank=True)
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
    final_species = models.CharField(max_length=50, choices=SPECIES_CHOICES, null=True, blank=True)
    final_confidence = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES, null=True, blank=True)

    # Mandatory
    point = gis_models.GeometryField(null=True, blank=True)

    class Meta:
        constraints = [
            gis_models.UniqueConstraint(fields=['id' ,'catalog_id', 'vendor_id', 'entity_id'], name='fk_img_id')
        ]
    
    def __str__(self):
        return self.classification