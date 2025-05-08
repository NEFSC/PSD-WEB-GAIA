import os
import django

########################################################################################################################
#
#  In Django, a view is what takes a Web request and returns a Web response. The response can be many things, but most
#  of the time it will be a Web page, a redirect, or a document. In this case, the response will almost always be data
#  in JSON format.
#
########################################################################################################################

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gaia.settings')
os.environ["CPL_DEBUG"] = "ON" # Should enable GDAL debuggin
django.setup()













