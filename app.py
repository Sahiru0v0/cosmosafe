from flask import Flask, render_template, request
import pandas as pd
import easyocr
import os
from safety import search_product, get_chemical_info
from recommend import get_recommendations, get_safer_brands

app = Flask(__name__)

# ── Initialize EasyOCR once ───────────────────────────────────────────────────
print("Loading EasyOCR... (first time may take a minute)")
reader = easyocr.Reader(['en'], gpu=False)
print("EasyOCR ready!")

# ── Upload folder ─────────────────────────────────────────────────────────────
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return render_template('index.html',
        result=None,
        recommendations=None,
        safer_brands=None,
        extracted_text=None,
        message=None
    )


@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('product_name', '').strip()

    if not query:
        return render_template('index.html',
            result=None,
            recommendations=None,
            safer_brands=None,
            extracted_text=None,
            message="Please enter a product or brand name."
        )

    result = search_product(query)

    if not result:
        return render_template('index.html',
            result=None,
            recommendations=None,
            safer_brands=None,
            extracted_text=None,
            message=f"No product found for '{query}'. Please try another name."
        )

    # Get recommendations and safer brands
    recommendations = get_recommendations(
        category     = result['category'],
        current_brand= result['brand'],
        risk_level   = result['risk_level']
    )
    safer_brands = get_safer_brands(result['category'])

    return render_template('index.html',
        result          = result,
        recommendations = recommendations,
        safer_brands    = safer_brands,
        extracted_text  = None,
        message         = None
    )


@app.route('/scan', methods=['POST'])
def scan():
    if 'product_image' not in request.files:
        return render_template('index.html',
            result=None,
            recommendations=None,
            safer_brands=None,
            extracted_text=None,
            message="No image uploaded."
        )

    file = request.files['product_image']

    if file.filename == '':
        return render_template('index.html',
            result=None,
            recommendations=None,
            safer_brands=None,
            extracted_text=None,
            message="No image selected."
        )

    # Save uploaded image
    image_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(image_path)

    # Run EasyOCR
    ocr_results  = reader.readtext(image_path)
    extracted_text = ' '.join([
        text for (_, text, confidence) in ocr_results
        if confidence > 0.3
    ])

    if not extracted_text.strip():
        return render_template('index.html',
            result=None,
            recommendations=None,
            safer_brands=None,
            extracted_text=None,
            message="Could not extract text from image. Please type the product name manually."
        )

    # Try searching with extracted text
    result = search_product(extracted_text)

    if result:
        recommendations = get_recommendations(
            category      = result['category'],
            current_brand = result['brand'],
            risk_level    = result['risk_level']
        )
        safer_brands = get_safer_brands(result['category'])
        return render_template('index.html',
            result          = result,
            recommendations = recommendations,
            safer_brands    = safer_brands,
            extracted_text  = extracted_text,
            message         = None
        )
    else:
        return render_template('index.html',
            result          = None,
            recommendations = None,
            safer_brands    = None,
            extracted_text  = extracted_text,
            message         = "Product not found from image. Edit the text below and search manually."
        )


@app.route('/chemicals')
def chemicals():
    info = get_chemical_info()
    return render_template('chemicals.html', chemicals=info)


if __name__ == '__main__':
    app.run(debug=True)