import requests
from urllib.request import urlopen
from urllib.parse import urljoin, urlparse

def get_image_size(url):
    try:
        image = urlopen(url)
        image_size = len(image.read()) / 1024  # Size in KB
        return round(image_size, 2)
    except Exception as e:
        print(f"Error fetching image size: {e}")
        return "N/A"

def check_custom_404(url):
    test_url = urljoin(url, "nonexistentpage12345")
    response = requests.get(test_url)
    
    # Check for 404 status code and presence of '404' in the response text
    if response.status_code == 404 and "404" in response.text.lower():
        return "Yes"
    else:
        return "No"


def check_robots_sitemap_https(url):
    report = {"Robots.txt Available": "No", "Sitemap.xml Available": "No", "HTTPS": "No"}
    parsed_url = urlparse(url)
    
    # Check if the URL uses HTTPS
    if parsed_url.scheme == "https":
        report["HTTPS"] = "Yes"
    
    # Define the URLs for robots.txt and sitemap.xml
    robots_url = urljoin(url, "robots.txt")
    sitemap_url = urljoin(url, "sitemap.xml")
    
    # Check if robots.txt is available
    try:
        response = requests.get(robots_url)
        if response.status_code == 200:
            report["Robots.txt Available"] = "Yes"
    except requests.RequestException:
        # Handle possible exceptions like network issues
        pass
    
    # Check if sitemap.xml is available
    try:
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            report["Sitemap.xml Available"] = "Yes"
    except requests.RequestException:
        # Handle possible exceptions like network issues
        pass
    
    return report