import requests
from bs4 import BeautifulSoup
from collections import Counter
from datetime import datetime
import re
from urllib.parse import urljoin, urlparse
from nltk.corpus import stopwords
import whois
from process.pagespeed import get_pagespeed_metrics
from process.helpers import get_image_size, check_custom_404


def get_domain_details(domain_name):
    try:
        # Perform the WHOIS lookup
        domain_info = whois.whois(domain_name)
        
        # Handling the case where domain_info is a string or a list
        if isinstance(domain_info, str):
            return {'Error': 'WHOIS information returned as a string. Please check the domain name or WHOIS data source.'}
        
        # Ensure single values are handled properly
        details = {
            'Domain Name': domain_info.domain_name if isinstance(domain_info.domain_name, (list, str)) else 'N/A',
            'Registrar': domain_info.registrar if domain_info.registrar else 'N/A',
            'Creation Date': domain_info.creation_date if domain_info.creation_date else 'N/A',
            'Expiration Date': domain_info.expiration_date if domain_info.expiration_date else 'N/A',
            'Last Updated': domain_info.updated_date if domain_info.updated_date else 'N/A',
            'Name Servers': domain_info.name_servers if isinstance(domain_info.name_servers, (list, str)) else 'N/A',
            'Status': domain_info.status if isinstance(domain_info.status, (list, str)) else 'N/A'
        }
        
        return details
    
    except Exception as e:
        return {'Error': str(e)}

def extract_top_keywords(soup):
        # Get the text content from the soup
        text = soup.get_text()

        # Convert text to lowercase and extract words
        words = re.findall(r'\w+', text.lower())

        # Define common stop words to exclude
        stop_words = set(stopwords.words('english'))  # Using NLTK's stop words

        # Filter out stop words
        filtered_words = [word for word in words if word not in stop_words]

        # Count the frequency of remaining words
        word_counts = Counter(filtered_words)

        # Return the top 15 keywords
        return word_counts.most_common(15)


def check_tags(url, api_key):
    response = requests.get(url)
    report = {
        "URL": url,
        'Favicon Link': "",
        "Title": "",
        "Description": "",
        "H1 Tags Text": {},
        "H1 Count": 0,
        "H2 Count": 0,
        "H3 Count": 0,
        "H4 Count": 0,
        "H5 Count": 0,
        "H6 Count": 0,
        "Canonical Tag": "",
        "Robots Tag": "",
        "OG Tags Available": "",
        "Schema Markup Available": "",
        'social_media_links': [],
        'iframes': {},
        'broken_links':[],
        "Image Details": [],
        "Internal Links": [],
        "External Links": [],
        "Top Keywords": [],
        "PageSpeed Metrics Mobile": {},
        "PageSpeed Metrics Desktop": {},
        "Custom 404 Page": "",
        "Robots.txt Available": "",
        "Sitemap.xml Available": "",
        "HTTPS": "" 
        
    }
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract the domain name from the URL
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc

        # Pass the domain name to the get_domain_details function
        whois_info = get_domain_details(domain_name)

        # Add WHOIS information to the report
        report.update(whois_info)
        # Process title, description, h1.
        favicon = soup.find('link', rel='icon') or soup.find('link', rel='shortcut icon')
        if favicon and 'href' in favicon.attrs:
            # Join the base URL with the favicon href to ensure it's a full URL
            favicon_url = urljoin(url, favicon['href'])
            report['Favicon Link'] = favicon_url
        else:
            report['Favicon Link'] = 'No favicon link'
        report["Title"] = soup.find('title').text if soup.find('title') else "No title"
        report["Description"] = soup.find('meta', attrs={'name': 'description'})['content'] if soup.find('meta', attrs={'name': 'description'}) else "No description"
        report["H1 Tags Text"] = [h1.get_text(strip=True) for h1 in soup.find_all('h1')] if soup.find_all('h1') else "No H1 tags"
        # Heading Tags Count
        report["H1 Count"] = len(soup.find_all('h1'))
        report["H2 Count"] = len(soup.find_all('h2'))
        report["H3 Count"] = len(soup.find_all('h3'))
        report["H4 Count"] = len(soup.find_all('h4'))
        report["H5 Count"] = len(soup.find_all('h5'))
        report["H6 Count"] = len(soup.find_all('h6'))
        # ... add more parsing logic for images, links, etc.
        report["Canonical Tag"] = soup.find('link', rel='canonical')['href'] if soup.find('link', rel='canonical') else "No canonical tag"
        report["Robots Tag"] = soup.find('meta', attrs={'name': 'robots'})['content'] if soup.find('meta', attrs={'name': 'robots'}) else "No robots tag"
        report["OG Tags Available"] = "Yes" if soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('og:')}) else "No"
        schema_tag = soup.find_all('script', type='application/ld+json')
        report["Schema Markup Available"] = "Yes" if schema_tag else "No"
        # # iFrame detection
        # iFrame detection with multiple 'src'-like attributes
        iframes = soup.find_all('iframe')
        # Check for 'src', 'data-src', or any other 'src'-like attributes
        report['iframes'] = [
            {attr: iframe.get(attr, 'No value') for attr in iframe.attrs if 'src' in attr} 
            for iframe in iframes
        ] if iframes else ["Great! No iframes"]

        # Social media links detection
        social_links = []
        social_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'youtube.com']
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(social_domain in href for social_domain in social_domains):
                social_links.append(href)
        report['social_media_links'] = social_links if social_links else 'No social media links'
        # Broken links detection
        broken_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            try:
                link_response = requests.get(full_url)
                if link_response.status_code == 404:
                    broken_links.append(full_url)
            except requests.RequestException:
                broken_links.append(full_url)
        report['broken_links'] = broken_links if broken_links else "All links well good"
        # Image        
        images = soup.find_all('img')
        report["Image Count"] = len(images)
        report["Images with Alt Text"] = sum(1 for img in images if img.get('alt'))
    
        for img in images:
            src = img.get('src')
            alt = img.get('alt', 'N/A')
            full_url = urljoin(url, src)
            size = get_image_size(full_url)
            report["Image Details"].append({"src": full_url, "alt": alt, "size": size})

            internal_links = []
            external_links = []
            parsed_url = urlparse(url)
        # Links
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            if urlparse(full_url).netloc == parsed_url.netloc:
                internal_links.append(full_url)
            else:
                external_links.append(full_url)
                
        report["Internal Links"] = internal_links
        report["External Links"] = external_links
        
        report["Top Keywords"] = extract_top_keywords(soup)
    
        # Fetch Google PageSpeed Insights metrics
        report["PageSpeed Metrics Mobile"] = get_pagespeed_metrics(url, api_key, "mobile")
        report["PageSpeed Metrics Desktop"] = get_pagespeed_metrics(url, api_key, "desktop")
        
        # Custom 404 page check
        report["Custom 404 Page"] = check_custom_404(url)

    return report

def generate_html_report(report, filename="seo_audit_report.html"):
    internal_links = report.get("Internal Links", [])
    external_links = report.get("External Links", [])
    num_rows = max(len(internal_links), len(external_links))
    rows_html = ''
    
    for i in range(num_rows):
        internal_link = internal_links[i] if i < len(internal_links) else ''
        external_link = external_links[i] if i < len(external_links) else ''
        rows_html += f"<tr><td>{internal_link}</td><td>{external_link}</td></tr>"
                
    current_date = datetime.now().strftime("%I:%M %p %d-%m-%y")

    for key, value in report.items():
        if value is None:
            report[key] = "Null"

    html_content = f"""
    <html>
    <head>
        <title>Report - Website & SEO Audit</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.1/dist/js/bootstrap.bundle.min.js"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.min.css">
        <style>
            body {{ font-family: Poppins, sans-serif; margin: 50px; }}
            h2 {{ color: #00B899; margin-top: 50px }}
            h1{{font-size: 35px;color: #00B899;}}
            h2{{font-size: 30px;}}
            h3{{font-size: 25px; color: #545454;}} 
            p{{font-size: 18px; margin: 5px 0px 5px 0px;}}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .collapsible {{cursor: pointer; padding: 10px; text-align: left; }}
            .content {{ display: none; padding: 0 18px; }}
            .tabsplit{{width: 48% !important;}}
            .tabspace th, .tabspace td{{padding: 20px 5px !important; text-align: center;}}
        </style>
    </head>
    <body>
        <div class="d-flex justify-content-between">
            <div>
                <h1>Website & SEO Audit Report</h1>
                <p><strong>URL:</strong> {report["URL"]}</p>
                <p><strong>Generated on:</strong> {current_date}</p>
            </div>
            <div class="my-auto">
                <img src="{report["URL"]}{report["Favicon Link"]}" width="100px", height="100px"/>
            </div>
        </div>

        <h2>On-Page SEO Metrics</h2>
        <div class="card p-4">
            <div class="card-body">
                <h3>Title</h3>
                <div class="d-flex flex-row justify-content-between">
                    <p class="w-75 text-justify">{report['Title']}</p>
                    <p><span class="badge text-bg-secondary p-2 text-center">{len(report['Title'])} char</span></p>
                </div>
            </div>
            <div class="card-body">
                <h3>Description</h3>
                <div class="d-flex flex-row justify-content-between">
                    <p class="w-75 text-justify">{report['Description']}</p>
                    <p><span class="badge text-bg-secondary p-2 text-center">{len(report['Description'])} char</span></p>
                </div>
            </div>
            <div class="card-body">
                <h3>H1 Tags</h3>
                <div>
                    <p>{"".join(f"<p>{text}</P>" for text in report['H1 Tags Text'])}</p>
                </div>
            </div>
            <div class="card">
                <div class="d-flex justify-content-around card-body">
                        <div class="text-center">
                            <h3>{report["H1 Count"]}</h3>
                            <p>H1 Tags</p>
                        </div>
                        <div class="text-center">
                            <h3>{report["H2 Count"]}</h3>
                            <p>H2 Tags</p>
                        </div>
                        <div class="text-center">
                            <h3>{report["H3 Count"]}</h3>
                            <p>H3 Tags</p>
                        </div>
                        <div class="text-center">
                            <h3>{report["H4 Count"]}</h3>
                            <p>H4 Tags</p>
                        </div>
                        <div class="text-center">
                            <h3>{report["H5 Count"]}</h3>
                            <p>H5 Tags</p>
                        </div>
                        <div class="text-center">
                            <h3>{report["H6 Count"]}</h3>
                            <p>H6 Tags</p>
                        </div>
                </div>
            </div>
          </div>
        <h2>Image & Links</h2>
          <div class="accordion accordion-flush" id="accordionFlushExample">
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseOne" aria-expanded="false" aria-controls="flush-collapseOne">
                  List of Image Details
                </button>
              </h2>
              <div id="flush-collapseOne" class="accordion-collapse collapse" data-bs-parent="#accordionFlushExample">
                <table class="accordion-body tabspace table-striped table-hover">
                    <tr><th>Source</th><th>Alt Text</th><th>Size (KB)</th></tr>
                    {''.join(f"<tr><td>{img['src']}</td><td>{img['alt']}</td><td>{img['size']}</td></tr>" for img in report["Image Details"])}
                </table>
              </div>
            </div>
            <div class="accordion-item">
              <h2 class="accordion-header">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#flush-collapseTwo" aria-expanded="false" aria-controls="flush-collapseTwo">
                  List of Links Details
                </button>
              </h2>
              <div id="flush-collapseTwo" class="accordion-collapse collapse" data-bs-parent="#accordionFlushExample">
                <table class="accordion-body tabspace table-striped table-hover">
                    <tr><th>Internal Links</th><th>External Links</th></tr>
                    {rows_html}
                </table>
              </div>
            </div>
          </div>
          
          <div class="card mt-5">
            <div class="d-flex justify-content-around card-body">
                    <div class="text-center">
                        <h3>{report['Image Count']}</h3>
                        <p>Img Count</p>
                    </div>
                    <div class="text-center">
                        <h3>{report['Images with Alt Text']}</h3>
                        <p>Img With Alt</p>
                    </div>
                    <div class="text-center">
                        <h3>{len(report['Internal Links'])}</h3>
                        <p>Internal Links</p>
                    </div>
                    <div class="text-center">
                        <h3>{len(report['External Links'])}</h3>
                        <p>External Links</p>
                    </div>
            </div>
        </div>
        <h2>Technical SEO Metrics</h2>
        <div class="d-flex justify-content-between">
            <table class="table tabspace tabsplit table-striped table-hover">
                <tbody>
                <tr>
                    <th scope="row">Canonical Tag</th>
                    <td>{report['Canonical Tag']}</td>
                </tr>
                <tr>
                    <th scope="row">Robots Tag</th>
                    <td>{report['Robots Tag']}</td>
                </tr>
                <tr>
                    <th scope="row">OG Tags</th>
                    <td>{report['OG Tags Available']}</td>
                </tr>
                <tr>
                    <th scope="row">Schema Markup Tags</th>
                    <td>{report['Schema Markup Available']}</td>
                </tr>
                </tbody>
            </table>
            <table class="table tabspace tabsplit table-striped table-hover">
                <tbody>
                <tr>
                    <th scope="row">HTTPS</th>
                    <td>{report['HTTPS']}</td>
                </tr>
                <tr>
                    <th scope="row">Custom 404 Page</th>
                    <td>{report['Custom 404 Page']}</td>
                </tr>
                <tr>
                    <th scope="row">Robots.txt</th>
                    <td>{report['Robots.txt Available']}</td>
                </tr>
                <tr>
                    <th scope="row">Sitemap.xml</th>
                    <td>{report['Sitemap.xml Available']}</td>
                </tr>
                </tbody>
            </table>
        </div>  
        <h2>PageSpeed Insights</h2>
        <table class="table tabspace table-striped table-hover w-100">
            <thead>
                <tr>
                  <th scope="col">Metrics</th>
                  <th scope="col">Mobile</th>
                  <th scope="col">Desktop</th>
                </tr>
              </thead>
            <tbody>
            <tr>
                <th scope="row">Performance Score</th>
                <td>{report['PageSpeed Metrics Mobile']['Performance Score']}</td>
                <td>{report['PageSpeed Metrics Desktop']['Performance Score']}</td>
            </tr>
            <tr>
                <th scope="row">First Contentful Paint</th>
                <td>{report['PageSpeed Metrics Mobile']['First Contentful Paint']}</td>
                <td>{report['PageSpeed Metrics Desktop']['First Contentful Paint']}</td>
            </tr>
            <tr>
                <th scope="row">Largest Contentful Paint</th>
                <td>{report['PageSpeed Metrics Mobile']['Largest Contentful Paint']}</td>
                <td>{report['PageSpeed Metrics Desktop']['Largest Contentful Paint']}</td>
            </tr>
            <tr>
                <th scope="row">Cumulative Layout Shift</th>
                <td>{report['PageSpeed Metrics Mobile']['Cumulative Layout Shift']}</td>
                <td>{report['PageSpeed Metrics Desktop']['Cumulative Layout Shift']}</td>
            </tr>
            <tr>
                <th scope="row">Speed Index</th>
                <td>{report['PageSpeed Metrics Mobile']['Speed Index']}</td>
                <td>{report['PageSpeed Metrics Desktop']['Speed Index']}</td>
            </tr>
            <tr>
                <th scope="row">Total Blocking Time</th>
                <td>{report['PageSpeed Metrics Mobile']['Total Blocking Time']}</td>
                <td>{report['PageSpeed Metrics Desktop']['Total Blocking Time']}</td>
            </tr>
            </tbody>
        </table>
        <h2>Top 15 Keywords</h2>
            {" ".join(f'<span class="badge text-bg-secondary p-2 my-2">{keyword} {count}</span>' for keyword, count in report["Top Keywords"])}
        <h2>Other Links</h2>
        <div class="d-flex justify-content-between">
                <table class="table tabspace table-striped table-hover text-start">
                    <tbody>
                    <tr>
                        <th scope="row" class="text-start">Social Media Links: {len(report['social_media_links'])}</th>
                    </tr>
                    <tr>
                        <td class="text-start">{", ".join(report['social_media_links'])}</td>
                    </tr>
                    <tr>
                        <th scope="row" class="text-start">Broken Links: {len(report['broken_links'])}</th>
                    </tr>
                    <tr>
                        <td class="text-start">{", ".join(report['broken_links'])}</td>
                    </tr>
                    <tr>
                        <th scope="row" class="text-start">iFrame Detection: {len(report['iframes'])}</th>
                    </tr>
                    <tr>
                        <td class="text-start">{", ".join([iframe['src'] for iframe in report['iframes'] if 'src' in iframe])}</td>
                    </tr>
                    </tbody>
                </table>
            </div> 
            
        <h2>WHOIS Domain Information</h2>
            <table class="table tabspace table-striped table-hover">
                <tbody>
                <tr>
                    <th scope="row">Domain Name</th>
                    <td>{report.get("Domain Name", "No data available")}</td>
                    <th scope="row">Registrar</th>
                    <td>{report.get("Registrar", "No data available")}</td>
                </tr>
                <tr>
                    <th scope="row">Creation Date</th>
                    <td>{report.get("Creation Date", "No data available")}</td>
                    <th scope="row">Expiration Date</th>
                    <td>{report.get("Expiration Date", "No data available")}</td>
                </tr>
                <tr>
                    <th scope="row" colspan="3">Last Updated</th>
                    <td>{report.get("Last Updated", "No data available")}</td>
                </tr>
                </tbody>
            </table>

    </body>
    </html>
    """
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return filename
