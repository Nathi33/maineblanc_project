from django.shortcuts import render

def home_view(request):
    return render(request, 'core/home.html')

def about_view(request):
    return render(request, 'core/about.html')

def accommodations_view(request):
    return render(request, 'core/accommodations.html')

def services_view(request):
    return render(request, 'core/services.html')

def activities_view(request):
    return render(request, 'core/activities.html')

def pricing_view(request):
    return render(request, 'core/pricing.html')

def contact_view(request):
    return render(request, 'core/contact.html')

def bookings_view(request):
    return render(request, 'core/bookings.html')

def legal_view(request):
    return render(request, 'core/legal.html')
