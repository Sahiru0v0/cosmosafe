import pandas as pd
from rapidfuzz import fuzz, process

# ── Load processed datasets ───────────────────────────────────────────────────
ca_df     = pd.read_csv('datasets/processed/ca_product_risk.csv')
indian_df = pd.read_csv('datasets/processed/indian_product_risk.csv', encoding='latin1')

# Clean for searching
ca_df['ProductName'] = ca_df['ProductName'].str.strip().str.upper()
ca_df['BrandName']   = ca_df['BrandName'].str.strip().str.upper()
indian_df['product_name'] = indian_df['product_name'].str.strip().str.upper()
indian_df['brand']        = indian_df['brand'].str.strip().str.upper()

def search_product(query):
    """
    Search both datasets for a product/brand name.
    Returns a structured result dict or None.
    """
    query = query.strip().upper()

    # ── Step 1: Search Indian dataset first (exact/partial match) ────────
    indian_results = indian_df[
        indian_df['product_name'].str.contains(query, na=False) |
        indian_df['brand'].str.contains(query, na=False)
    ]

    if not indian_results.empty:
        top = indian_results.iloc[0]
        return build_result(
            product  = top['product_name'],
            brand    = top['brand'],
            category = top['category'],
            harmful_chemical_count = int(top['HarmfulChemicalCount']),
            risk_score = float(top['RiskScore']),
            risk_level = top['RiskLevel'],
            chemicals  = top['HarmfulChemicals'],
            source     = 'Indian Market',
            price      = top.get('price', 'N/A'),
            rating     = top.get('rating', 'N/A')
        )

    # ── Step 2: Search California dataset ────────────────────────────────
    ca_results = ca_df[
        ca_df['ProductName'].str.contains(query, na=False) |
        ca_df['BrandName'].str.contains(query, na=False)
    ]

    if not ca_results.empty:
        top = ca_results.iloc[0]
        return build_result(
            product  = top['ProductName'],
            brand    = top['BrandName'],
            category = top['PrimaryCategory'],
            harmful_chemical_count = int(top['HarmfulChemicalCount']),
            risk_score = float(top['RiskScore']),
            risk_level = top['RiskLevel'],
            chemicals  = top['HarmfulChemicals'],
            source     = 'California Database',
            price      = 'N/A',
            rating     = 'N/A'
        )

    # ── Step 3: Fuzzy match as last resort ───────────────────────────────
    all_names = indian_df['product_name'].dropna().tolist()
    fuzzy_result = process.extractOne(query, all_names, scorer=fuzz.partial_ratio)

    if fuzzy_result and fuzzy_result[1] >= 60:
        matched_name = fuzzy_result[0]
        top = indian_df[indian_df['product_name'] == matched_name].iloc[0]
        return build_result(
            product  = top['product_name'],
            brand    = top['brand'],
            category = top['category'],
            harmful_chemical_count = int(top['HarmfulChemicalCount']),
            risk_score = float(top['RiskScore']),
            risk_level = top['RiskLevel'],
            chemicals  = top['HarmfulChemicals'],
            source     = 'Indian Market (fuzzy match)',
            price      = top.get('price', 'N/A'),
            rating     = top.get('rating', 'N/A')
        )

    return None


def build_result(product, brand, category, harmful_chemical_count,
                 risk_score, risk_level, chemicals, source, price, rating):
    """Build a clean result dictionary."""

    # Risk color for UI
    color_map = {
        'SAFE'     : 'green',
        'LOW'      : 'yellowgreen',
        'MODERATE' : 'orange',
        'HIGH'     : 'red',
        'VERY HIGH': 'darkred'
    }

    # Risk message for user
    message_map = {
        'SAFE'     : 'This product appears safe based on our database.',
        'LOW'      : 'This product has 1 harmful chemical. Use with caution.',
        'MODERATE' : 'This product has moderate concern. Consider alternatives.',
        'HIGH'     : 'This product is HIGH risk. We recommend switching to a safer alternative.',
        'VERY HIGH': 'This product is VERY HIGH risk. Avoid use immediately.'
    }

    chemicals_list = [c.strip() for c in str(chemicals).split(',') if c.strip() and c.strip() != 'nan']

    return {
        'product'  : product,
        'brand'    : brand,
        'category' : category,
        'harmful_chemical_count': harmful_chemical_count,
        'risk_score': risk_score,
        'risk_level': risk_level,
        'chemicals' : chemicals_list,
        'source'    : source,
        'price'     : price,
        'rating'    : rating,
        'color'     : color_map.get(risk_level, 'gray'),
        'message'   : message_map.get(risk_level, 'Unknown risk level.')
    }


def get_chemical_info():
    """Returns list of all 123 harmful chemicals for info page."""
    ca_raw = pd.read_csv('datasets/California Chemicals/chemicals-in-cosmetics.csv',
                         encoding='latin1')
    return ca_raw['ChemicalName'].value_counts().reset_index().rename(
        columns={'ChemicalName': 'Chemical', 'count': 'ReportCount'}
    ).head(30).to_dict('records')