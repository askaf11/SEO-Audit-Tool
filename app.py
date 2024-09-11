from flask import Flask, render_template, request, send_file, jsonify
from process.audit import check_tags, generate_html_report
from process.helpers import check_robots_sitemap_https

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/audit', methods=['POST'])
def audit():
        
    url = request.form['url']
    api_key = '' #Replace your Google PageSpeed API key 

    try:
        # Fetch SEO audit details
        seo_report = check_tags(url, api_key)
        robots_report = check_robots_sitemap_https(url)

        # Combine the results
        full_report = {**seo_report, **robots_report}

        # Generate HTML report
        report_filename = "seo_audit_report.html"
        generate_html_report(full_report, filename=report_filename)
        
        return jsonify({"success": True, "filename": report_filename})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/download/<filename>')
def download_report(filename):
    try:
        return send_file(filename, as_attachment=True)
    except FileNotFoundError:
        return jsonify({"success": False, "error": "File not found"})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)

