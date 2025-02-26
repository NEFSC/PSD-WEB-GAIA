import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
import django
from django.utils import timezone
from django.db import models
from django.test import TestCase


# Set up Django environment
django.setup()

# Import your models
from django.contrib.auth.models import User
from whale.models import PointsOfInterest
from faker import Faker
import unittest

def add_fake_reviews(n):
    # Get first n rows from PointsOfInterest table
    pois = PointsOfInterest.objects.all()[:n]
    
    if not pois:
        print("No Points of Interest found in database")
        return
        
    fake = Faker()
    for poi in pois:
        num_users = fake.random_int(min=1, max=3)  # Randomly choose how many users to add
        users_to_add = fake.random_elements(elements=[1, 2, 3], length=num_users, unique=True)

        for user_num in users_to_add:
            if user_num == 1:
                poi.user1_comments = fake.text()
                poi.user1_classification = "whale" if fake.boolean() else fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0]
                if poi.user1_classification == "whale":
                    poi.user1_species = fake.random_element(PointsOfInterest.SPECIES_CHOICES)[0]
                    poi.user1_confidence = fake.random_element(PointsOfInterest.CONFIDENCE_CHOICES)[0]
            elif user_num == 2:
                poi.user2_comments = fake.text()
                poi.user2_classification = "whale" if fake.boolean() else fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0]
                if poi.user2_classification == "whale":
                    poi.user2_species = fake.random_element(PointsOfInterest.SPECIES_CHOICES)[0]
                    poi.user2_confidence = fake.random_element(PointsOfInterest.CONFIDENCE_CHOICES)[0]
            else:
                poi.user3_comments = fake.text()
                poi.user3_classification = "whale" if fake.boolean() else fake.random_element(PointsOfInterest.CLASSIFICATION_CHOICES)[0]
                if poi.user3_classification == "whale":
                    poi.user3_species = fake.random_element(PointsOfInterest.SPECIES_CHOICES)[0]
                    poi.user3_confidence = fake.random_element(PointsOfInterest.CONFIDENCE_CHOICES)[0]
        poi.save()

if __name__ == "__main__":
    add_fake_reviews(100)
    print("Added 100 fake entries to PointsOfInterest table.")

