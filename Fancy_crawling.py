import zipfile
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import csv
import io
import os
import requests
import tempfile  # for creating a temporary directory to store files


# Set up Flask app
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)


def extract_text_from_url(url):
    """
    Reuse your text extractor logic here:
    - GET the URL
    - If 'mainFrame' iframe is present, follow it
    - Extract the <div> with class 'se-viewer se-theme-default'
    - Return the joined text
    """

    if not url or "naver.com" not in url:
        raise ValueError("Invalid or missing Naver URL")

    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch URL: {url}")

    soup = BeautifulSoup(response.content, 'html.parser')
    iframe = soup.find('iframe', {'id': 'mainFrame'})
    if iframe:
        iframe_src = iframe.get('src')
        iframe_url = requests.compat.urljoin(url, iframe_src)
        iframe_response = requests.get(iframe_url)
        if iframe_response.status_code == 200:
            soup = BeautifulSoup(iframe_response.content, 'html.parser')

    target_div = soup.find('div', {'class': 'se-viewer se-theme-default', 'lang': 'ko-KR'})
    if not target_div:
        raise ValueError("Target <div> not found or no text available")

    # Extract all text within span tags
    texts = [
        span.get_text(strip=True)
        for span in target_div.find_all('span')
        if span.get_text(strip=True)
    ]
    extracted_text = "\n".join(texts)
    return extracted_text

# Routes
@app.route('/')
def home():
    return render_template('main_page.html')

# URL Extractor (Project A)
@app.route('/url_extractor')
def url_extractor():
    return render_template('urlextractor.html')

@app.route('/extract', methods=['GET'])
def extract_data():
    keyword = request.args.get('keyword')
    number = request.args.get('number')
    order_by = request.args.get('orderBy', 'sim')

    if not keyword or not number.isdigit():
        return jsonify({"error": "Invalid inputs!"}), 400

    num_pages = int(number)
    base_url = "https://section.blog.naver.com/Search/Post.naver"
    result_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        


        # Loop through pages to scrape
        for page_no in range(1, num_pages + 1):
            params = f"?pageNo={page_no}&rangeType=ALL&orderBy={order_by}&keyword={keyword}"
            full_url = base_url + params

            page.goto(full_url, wait_until="load")
            page.wait_for_selector(".list_search_post .desc_inner", timeout=10000)  # Wait for elements to appear
            

            # Extract URLs and Titles
            posts = page.locator(".list_search_post .desc_inner")
            if posts.count() == 0:
                print(f"No posts found on page {page_no}")
                continue

            for i in range(posts.count()):
                try:
                    # Get the URL from the <a> tag
                    url = posts.nth(i).get_attribute("href", timeout=None)
                    # Get the title from the <span> with the class "title"
                    title = posts.nth(i).locator(".title").inner_text(timeout=None)
                    result_data.append({"url": url, "title": title})
                except Exception as e:
                    print(f"Error extracting post {i}: {e}")
                    continue

        browser.close()


    # Generate CSV in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["url", "title"])
    writer.writeheader()
    writer.writerows(result_data)

    # Now we create a downloadable response 
    from flask import make_response
    from urllib.parse import quote

    csv_data = output.getvalue()
    response = make_response(csv_data)
    
    # Set your filename here. Example:
    filename = f"{keyword}_CountNumber_{number}.csv"

    filename_encoded = quote(filename)
    
    # 4) Set Content-Disposition with RFC 5987 filename*
    #    (Modern browsers will use filename*, older ones might fall back to filename=)
    response.headers["Content-Disposition"] = (
        f"attachment; filename={filename_encoded}; "
        f"filename*=UTF-8''{filename_encoded}"
    )

    return response


# Text Extractor (Project B)
@app.route('/text_extractor')
def text_extractor():
    return render_template('NaverBlogTextIsMine.html')

@app.route('/extract_text', methods=['POST'])
def extract_text():
    try:
        url = request.json.get('url')
        if not url or "naver.com" not in url:
            return jsonify({'error': 'Invalid URL'}), 400

        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch URL'}), 400

        soup = BeautifulSoup(response.content, 'html.parser')
        
        iframe = soup.find('iframe', {'id': 'mainFrame'})
        if iframe:
            iframe_src = iframe.get('src')
            iframe_url = requests.compat.urljoin(url, iframe_src)
            iframe_response = requests.get(iframe_url)
            if iframe_response.status_code == 200:
                soup = BeautifulSoup(iframe_response.content, 'html.parser')

        # Extract all text within the specific <div>
        target_div = soup.find('div', {'class': 'se-viewer se-theme-default', 'lang': 'ko-KR'})
        if not target_div:
            return jsonify({'error': 'Target <div> not found'}), 404        

        # Extract all text within span tags
        texts = [span.get_text(strip=True) for span in target_div.find_all('span') if span.get_text(strip=True)]
        extracted_text = "\n".join(texts)
        
        #Extract the first line for the filename
        first_line = texts[0] if texts else "extracted_text"

        return jsonify({'text': extracted_text, 'filename': first_line}), 200

    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    console.log("Response from backend:", data);

@app.route('/bulk_text_extractor')
def bulk_text_extractor():
    """
    Simply returns the HTML upload form (bulkextractor.html).
    """
    return render_template('bulkextractor.html')

@app.route('/bulk_extract_text', methods=['POST'])
def bulk_extract_text():
    """
    1) Receives CSV file via POST request.
    2) Reads each 'url' from CSV.
    3) Uses extract_text_from_url() to get the text.
    4) Generates .txt files for each entry.
    5) Bundles them into one ZIP and returns it.
    """
    if 'csv_file' not in request.files:
        return jsonify({"error": "No CSV file provided"}), 400
    
    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    # Convert uploaded CSV to StringIO for reading
    csv_data = io.StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(csv_data)

    # Create a temporary directory to store text files
    temp_dir = tempfile.mkdtemp()
    created_files = []

    for idx, row in enumerate(reader):
        url = row.get('url')
        # You could also incorporate a 'blog name' or 'title' field from CSV if you want:
        title = row.get('title', f"extracted_text_{idx}")

        if not url:
            # Skip if no URL in this row
            continue

        # Extract text (reuse your logic)
        try:
            extracted_text = extract_text_from_url(url)
        except Exception as e:
            # If there's a problem extracting text, handle it here
            extracted_text = f"Error extracting {url}:\n{str(e)}"

        # Sanitize title for filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).rstrip()
        filename = f"{safe_title or 'extracted_text'}.txt"
        
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(extracted_text)
        
        created_files.append(file_path)

    # Now, zip all text files
    zip_filename = "extracted_texts.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in created_files:
            zipf.write(file_path, arcname=os.path.basename(file_path))

    # Send the ZIP to the user as attachment
    return send_file(zip_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
