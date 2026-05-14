import pandas as pd

# Load processed Indian dataset
indian_df = pd.read_csv('datasets/processed/indian_product_risk.csv', encoding='latin1')

# Clean immediately after loading
indian_df['product_name'] = indian_df['product_name'].str.strip().str.upper()
indian_df['brand']        = indian_df['brand'].str.strip().str.upper()
indian_df['category']     = indian_df['category'].str.strip().str.upper()
indian_df['rating']       = pd.to_numeric(indian_df['rating'], errors='coerce').fillna(0)
indian_df['price']        = pd.to_numeric(indian_df['price'], errors='coerce').fillna(0)

def get_recommendations(category, current_brand, risk_level, n=5):
    if risk_level == 'SAFE':
        return []

    filtered = indian_df[
        (indian_df['category'].str.contains(str(category).upper(), na=False)) &
        (indian_df['brand'] != str(current_brand).upper())
    ].copy()

    if filtered.empty:
        filtered = indian_df[
            indian_df['brand'] != str(current_brand).upper()
        ].copy()

    filtered = filtered.sort_values(
        ['RiskScore', 'rating'],
        ascending=[True, False]
    )

    safe_products = filtered[
        filtered['RiskLevel'].isin(['SAFE', 'LOW'])
    ].head(n)

    if len(safe_products) < n:
        moderate = filtered[
            filtered['RiskLevel'] == 'MODERATE'
        ].head(n - len(safe_products))
        safe_products = pd.concat([safe_products, moderate])

    recommendations = []
    for _, row in safe_products.iterrows():
        recommendations.append({
            'product'  : row['product_name'],
            'brand'    : row['brand'],
            'category' : row['category'],
            'risk_level': row['RiskLevel'],
            'risk_score': row['RiskScore'],
            'rating'   : round(float(row['rating']), 1),
            'price'    : round(float(row['price']), 1),
            'chemicals': row['HarmfulChemicals']
                         if pd.notna(row['HarmfulChemicals']) else 'None detected'
        })

    return recommendations


def get_safer_brands(category, n=5):
    filtered = indian_df[
        indian_df['category'].str.contains(str(category).upper(), na=False)
    ].copy()

    if filtered.empty:
        filtered = indian_df.copy()

    brand_stats = filtered.groupby('brand').agg(
        AvgRiskScore = ('RiskScore', 'mean'),
        AvgRating    = ('rating', 'mean'),
        ProductCount = ('product_name', 'count')
    ).reset_index()

    brand_stats = brand_stats[brand_stats['ProductCount'] >= 2]
    brand_stats['AvgRating'] = brand_stats['AvgRating'].round(1)
    brand_stats['AvgRiskScore'] = brand_stats['AvgRiskScore'].round(1)

    brand_stats = brand_stats.sort_values(
        ['AvgRiskScore', 'AvgRating'],
        ascending=[True, False]
    )

    return brand_stats.head(n).to_dict('records')