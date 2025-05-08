import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
import django
django.setup()
from django.contrib.auth.models import User
from whale.models import PointsOfInterest
from whale.models import Validation
from faker import Faker

# Print field names
for field in Validation._meta.get_fields():
    print(field.name, field.get_internal_type())

# Create a Faker instance
fake = Faker()

poi = PointsOfInterest.objects.order_by('?').first()

# Create a sample Validation instance
validation = Validation.objects.create(
    primary=poi,
    user1_id=User.objects.create(username=fake.user_name()),
    user1_classify=fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0],
    user1_comments=fake.text(max_nb_chars=200),
    user1_species=fake.random_element(PointsOfInterest.SPECIES_CHOICES)[0],
    user1_confidence=fake.random_element(PointsOfInterest.CONFIDENCE_CHOICES)[0],
    user2_id=User.objects.create(username=fake.user_name()),
    user2_classify=fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0],
    user2_comments=fake.text(max_nb_chars=200),
    user2_species=fake.random_element(PointsOfInterest.SPECIES_CHOICES)[0],
    user2_confidence=fake.random_element(PointsOfInterest.CONFIDENCE_CHOICES)[0],
    user3_id=User.objects.create(username=fake.user_name()),
    user3_classify=fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0],
    user3_comments=fake.text(max_nb_chars=200),
    user3_species=fake.random_element(PointsOfInterest.SPECIES_CHOICES)[0],
    user3_confidence=fake.random_element(PointsOfInterest.CONFIDENCE_CHOICES)[0],
    final_review=fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0],
    final_review_date=fake.date_this_decade()
)

print("Sample Validation instance created:", validation)
for field in Validation._meta.get_fields():
    print(f"{field.name}: {getattr(validation, field.name)}")
    print("\nFake data saved in Validation instance:")
    for field in Validation._meta.get_fields():
        if field.concrete and not field.many_to_many:
            print(f"{field.name}: {getattr(validation, field.name)}")