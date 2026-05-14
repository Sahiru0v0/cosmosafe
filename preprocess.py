import pandas as pd
import os

def load_and_preprocess():
    print("Loading datasets...")

    ca_df = pd.read_csv(
        'datasets/California Chemicals/chemicals-in-cosmetics.csv',
        encoding='latin1'
    )

    ca_df = ca_df[['ProductName', 'BrandName', 'PrimaryCategory',
                   'ChemicalName', 'CasNumber']].copy()

    ca_df['ProductName']  = ca_df['ProductName'].str.strip().str.upper()
    ca_df['BrandName']    = ca_df['BrandName'].str.strip().str.upper()
    ca_df['ChemicalName'] = ca_df['ChemicalName'].str.strip().str.upper()

    harmful_chemicals = ca_df['ChemicalName'].unique().tolist()

    # Fix encoding for Indian dataset
    indian_df = pd.read_csv(
        'datasets/indian/indianprod.csv',
        encoding='latin1',
    )

    # Keep country column this time!
    indian_df = indian_df[['product_name', 'brand', 'category',
                            'subcategory', 'ingredients', 'price',
                            'rating', 'noofratings', 'country']].copy()

    indian_df['product_name'] = indian_df['product_name'].str.strip().str.upper()
    indian_df['brand']        = indian_df['brand'].str.strip().str.upper()
    indian_df['category']     = indian_df['category'].str.strip().str.upper()

    # Fix noofratings — strip commas before converting
    indian_df['noofratings'] = indian_df['noofratings'].astype(str).str.replace(',', '').str.strip()
    indian_df['noofratings'] = pd.to_numeric(indian_df['noofratings'], errors='coerce').fillna(0)
    indian_df['rating']      = pd.to_numeric(indian_df['rating'], errors='coerce').fillna(0)
    indian_df['price']       = pd.to_numeric(indian_df['price'], errors='coerce').fillna(0)

    # Filter Indian only products
    indian_df = indian_df[indian_df['country'].str.upper().str.strip() == 'INDIA'].copy()
    print(f"Indian only products: {len(indian_df)}")

    print("Building CA risk scores...")
    ca_product_risk = ca_df.groupby(
        ['ProductName', 'BrandName', 'PrimaryCategory']
    )['ChemicalName'].agg(
        HarmfulChemicalCount='count',
        HarmfulChemicals=lambda x: ', '.join(x.unique())
    ).reset_index()

    print("Checking Indian products...")
    def check_ingredients(ingredients):
        if pd.isna(ingredients):
            return [], 0
        found = [c for c in harmful_chemicals if c in ingredients.upper()]
        return found, len(found)

    indian_df['HarmfulChemicals']     = indian_df['ingredients'].apply(lambda x: ', '.join(check_ingredients(x)[0]))
    indian_df['HarmfulChemicalCount'] = indian_df['ingredients'].apply(lambda x: check_ingredients(x)[1])

    def risk_score(count):
        if count >= 10: return 10.0
        elif count >= 7: return 8.0
        elif count >= 4: return 6.0
        elif count >= 2: return 4.0
        elif count == 1: return 2.0
        else: return 0.0

    def risk_level(count):
        if count >= 7:   return 'VERY HIGH'
        elif count >= 4: return 'HIGH'
        elif count >= 2: return 'MODERATE'
        elif count == 1: return 'LOW'
        else:            return 'SAFE'

    ca_product_risk['RiskScore'] = ca_product_risk['HarmfulChemicalCount'].apply(risk_score)
    ca_product_risk['RiskLevel'] = ca_product_risk['HarmfulChemicalCount'].apply(risk_level)
    indian_df['RiskScore']       = indian_df['HarmfulChemicalCount'].apply(risk_score)
    indian_df['RiskLevel']       = indian_df['HarmfulChemicalCount'].apply(risk_level)

    os.makedirs('datasets/processed', exist_ok=True)
    ca_product_risk.to_csv('datasets/processed/ca_product_risk.csv', index=False)
    indian_df.to_csv('datasets/processed/indian_product_risk.csv', index=False)

    print(f"CA products: {len(ca_product_risk)}")
    print(f"Indian products: {len(indian_df)}")
    print("Done!")

    return ca_product_risk, indian_df, harmful_chemicals

if __name__ == '__main__':
    load_and_preprocess()