import os
import sys
import django


# -- Root path setup -----------------------------------------------
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../core/tests'))
sys.path.insert(0, os.path.abspath('../bookings/tests')) 
sys.path.insert(0, os.path.abspath('../reservations/tests'))

# -- Django setup --------------------------------------------------
os.environ['DJANGO_SETTINGS_MODULE'] = 'maineblanc_project.settings'
django.setup()

# -- General configuration -----------------------------------------
project = 'Camping Le Maine Blanc'
copyright = '2025, Nathalie Darnaudat'
author = 'Nathalie Darnaudat'
release = '1.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML  --------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# -- Options for autodoc ------------------------------------------
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'