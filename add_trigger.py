import os
import django
from django.db import connection
from django.db import models

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
django.setup()

from whale.models import PointsOfInterest
def create_trigger():
    trigger_sql = """
    CREATE TRIGGER update_final_review
    AFTER UPDATE ON whale_pointsofinterest
    FOR EACH ROW
    WHEN NEW.user1_classification = 'whale' AND NEW.user2_classification = 'whale' AND NEW.user3_classification = 'whale'
    BEGIN
        UPDATE whale_pointsofinterest
        SET final_review = 'whale',
            final_review_date = DATE('now')
        WHERE id = NEW.id;
    END;
    """
    
    with connection.cursor() as cursor:
        cursor.execute(trigger_sql)
    print("Trigger created successfully.")

if __name__ == "__main__":
    create_trigger()