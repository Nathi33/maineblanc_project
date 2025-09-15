import pytest
from django.urls import reverse

# ==============================
# Tests for simple views
# ==============================

@pytest.mark.django_db
def test_home_view(client):
    """Home page should load successfully and use the correct template."""
    url = reverse('home')
    response = client.get(url)
    assert response.status_code == 200
    assert 'core/home.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_about_view(client):
    """About page should load successfully and use the correct template."""
    url = reverse('about')
    response = client.get(url)
    assert response.status_code == 200
    assert 'core/about.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_accommodations_view(client):
    """Accommodations page should load successfully and use the correct template."""
    url = reverse('accommodations')
    response = client.get(url)
    assert response.status_code == 200
    assert 'core/accommodations.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_activities_view(client):
    """Activities page should load successfully and use the correct template."""
    url = reverse('activities')
    response = client.get(url)
    assert response.status_code == 200
    assert 'core/activities.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_legal_view(client):
    """Legal page should load successfully and use the correct template."""
    url = reverse('legal')
    response = client.get(url)
    assert response.status_code == 200
    assert 'core/legal.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_privacy_view(client):
    """Privacy policy page should load successfully and use the correct template."""
    url = reverse('privacy-policy')
    response = client.get(url)
    assert response.status_code == 200
    assert 'core/privacy-policy.html' in [t.name for t in response.templates]

@pytest.mark.django_db
def test_not_found_view(client):
    """Not found page should return 404 and use the correct template."""
    url = reverse('not_found')
    response = client.get(url)
    assert response.status_code == 404
    assert 'core/not_found.html' in [t.name for t in response.templates]

# ==============================
# Tests for infos_view
# ==============================

@pytest.mark.django_db
def test_infos_view(client, campinginfo_fr, mobilehome_fr):
    """Infos view should load successfully and provide camping info and mobilehome data."""
    url = reverse('infos')
    response = client.get(url)
    assert response.status_code == 200
    context = response.context
    # Check if important context variables exist
    assert 'camping_info' in context
    assert 'mobilhomes' in context
    assert context['camping_info'].pk == campinginfo_fr.pk
    assert len(context['mobilhomes']) == 1
    # Check that mobilehome translation is set
    mobilehome = context['mobilhomes'][0]
    assert mobilehome.description_display == "Description en français"
    assert mobilehome.name_display == "Home 1"

# ==============================
# Tests for services_view
# ==============================

@pytest.mark.django_db
def test_services_view(client, swimmingpoolinfo_fr, foodinfo_fr, laundryinfo_fr):
    """Services view should load successfully and provide swimming, food, and laundry info."""
    url = reverse('services')
    response = client.get(url)
    assert response.status_code == 200
    context = response.context
    assert context['swimming_info'].pk == swimmingpoolinfo_fr.pk
    assert context['food_info'].pk == foodinfo_fr.pk
    assert context['laundry_info'].pk == laundryinfo_fr.pk
