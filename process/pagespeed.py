import requests

# Function to fetch Google PageSpeed Insights metrics
def get_pagespeed_metrics(url, api_key, strategy):
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy={strategy}&key={api_key}"
    response = requests.get(api_url)
    metrics = {}

    if response.status_code == 200:
        data = response.json()
        lighthouse_result = data.get("lighthouseResult", {})
        categories = lighthouse_result.get("categories", {})
        performance = categories.get("performance", {}).get("score", None)
        fcp = lighthouse_result.get("audits", {}).get("first-contentful-paint", {}).get("displayValue", None)
        lcp = lighthouse_result.get("audits", {}).get("largest-contentful-paint", {}).get("displayValue", None)
        cls = lighthouse_result.get("audits", {}).get("cumulative-layout-shift", {}).get("displayValue", None)
        speed_index = lighthouse_result.get("audits", {}).get("speed-index", {}).get("displayValue", None)
        tbt = lighthouse_result.get("audits", {}).get("total-blocking-time", {}).get("displayValue", None)

        metrics = {
            "Performance Score": performance * 100 if performance is not None else "Null",
            "First Contentful Paint": fcp,
            "Largest Contentful Paint": lcp,
            "Cumulative Layout Shift": cls,
            "Speed Index": speed_index,
            "Total Blocking Time": tbt,
        }
    else:
        metrics["Error"] = f"Failed to fetch PageSpeed data. Status code: {response.status_code}"

    return metrics