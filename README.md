# 🌲 Camping Le Maine Blanc – Booking Website

![Django](https://img.shields.io/badge/Django-5.2-green?style=flat&logo=django)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-blueviolet?style=flat&logo=bootstrap)
![SEO](https://img.shields.io/badge/SEO-Optimized-success?style=flat)
![Status](https://img.shields.io/badge/Status-Production-green?style=flat)

Professional website for **Camping Le Maine Blanc**, built with **Django** and **Bootstrap 5**.  
The site is **responsive**, **secure**, and **SEO-friendly**, providing a smooth booking experience.

---

## Table of Contents

1. [Project Description](#project-description)  
2. [Features](#features)  
3. [Technologies Used](#technologies-used) 
4. [Folder Structure](#folder-structure) 
5. [Installation and Setup](#installation-and-setup)  
6. [Multilingual Configuration](#multilingual-configuration)   
7. [SEO and Optimization](#seo-and-optimization) 
8. [Contributing](#contributing)  
9. [License](#license)
10. [Author](#author)

---

### Project Description

This website is built with **Django 5** and offers:  
- Presentation of the campsite, accommodations, and services.  
- Practical information and nearby activities.  
- Contact form for reservation requests.  
- Multilingual support: French, English, Spanish, German, Dutch.  
- SEO optimization with XML sitemap, robots.txt, and proper HTML meta tags.  
- Responsive design using Bootstrap 5 and optimized images (WebP, lazy loading).
---

### Features

- Main pages: Home, About, Practical Info, Services, Accommodations & Reservations, Nearby Activities, Contact.  
- Language selection with flag icons.  
- Display of times and dates according to the active language.  
- Accessibility optimization: ARIA roles on main sections, decorative images with `aria-hidden`.  
- Secure payment information and practical details displayed.  
- Django admin to manage content and reservations.

---

### Technologies Used

- **Backend**: Django 5, Python 3.13  
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript  
- **Database**: SQLite (development)  
- **Multilingual**: Django i18n, `gettext`  
- **SEO**: sitemap.xml, robots.txt, meta tags  
- **Images**: WebP for performance, lazy loading

---

### Folder structure

| App                  | Main role                                                                                                          |
|----------------------|--------------------------------------------------------------------------------------------------------------------|
| `core`               | Main pages (Home, About, Services, Practical Infos, Nearby Activities) and shared templates / filters base layout  |
| `reservations`       | Handling reservation requests and contact form submissions                                                         |
| `templatetags`       | Custom template filters for formatting dates and times according to locale (inside core)                           |
| `static`             | CSS, JS, images, documents (static assets)                                                                         |
| `media`              | User-uploaded files (if any, e.g., photos or attachments)                                                          |
| `manage.py`          | Django management script                                                                                           |
| `db.sqlite3`         | SQLite database (development)                                                                                      |

---

### Installation and Setup

#### Prerequisites

- VSCode or PyCharm
- Python
- Pip
- Django

#### Installation

1. Clone the repository : 
```bash
    git clone https://github.com/Nathi33/maineblanc_project.git
```
2. Navigate to the project directory : 
```bash
   cd maineblanc_project
```
3. Create and activate a virtual environment:
```bash
    python -m venv env 
    env\Scripts\activate # Windows
    source env/bin/activate # Linux / MacOS
```
4. Install dependencies : 
```bash
   pip install -r requirements.txt
```
5. Configure the database (SQLite by default) : 
```bash
   python manage.py migrate
```
6. Create a superuser (Optional) : 
```bash
   python manage.py createsuperuser
```
7. Launch the server : 
```bash
   python manage.py runserver
```
8. The application will be accessible at http://localhost:8000

#### Deployment Setup

- To build the project for deployment, use the commands : 
```bash
    python manage.py collectstatic --noinput
    python manage.py migrate
```
- Run unit tests with Pytest : 
```bash
   pytest
```

---

### Multilingual Configuration

Supported languages: French (default), English, Spanish, German, Dutch.
Times and dates are formatted according to the active language using format_time_by_locale and format_date_by_locale template filters.
Language selector keeps users on the current page after switching.

---

### SEO and Optimization

The website has been built with a strong focus on **SEO**, **performance**, and **accessibility** to ensure a seamless user experience and optimal search engine visibility.

#### **SEO**
- Dynamic `robots.txt` accessible at: `/robots.txt`
- XML sitemap with `hreflang` support for multilingual indexing: `/sitemap.xml`
- Optimized meta tags (`title`, `description`, `lang`) for better search engine ranking
- Clean semantic HTML structure with proper heading hierarchy
- SEO-friendly URLs and multilingual slugs
- Optimized for Core Web Vitals to improve page speed and user experience

#### **Performance**
- Lazy loading for images to reduce initial load time
- WebP image format with JPEG fallback for cross-browser compatibility
- Minified and compressed CSS and JavaScript for faster delivery
- Django caching enabled to enhance server response time

#### **Accessibility (A11y)**
- Proper use of ARIA attributes (`role`, `aria-labelledby`, etc.)
- Keyboard-friendly navigation across all pages
- Verified color contrast for readability and WCAG compliance
- Decorative images marked with `aria-hidden` to improve screen reader experience

---

### Contributing 
1. Fork the project
2. Create a branch for your feature : git checkout -b feature/my-feature
3. Commit your changes : git commit -m "Add my feature"
4. Push the branch : git push origin feature/my-feature
5. Open a Pull Request

---

### License
This project is licensed under the MIT License.
You are free to use, modify, and distribute it, but you must include the original license notice.

---

### Author
Nathalie Darnaudat
Web & Mobile Developer (Career Transition)
📍 Based in Saint-Christoly-de-Blaye, Gironde (33), France
🌐 Portfolio : https://mes-sites.ovh/Portfolio_Nath





