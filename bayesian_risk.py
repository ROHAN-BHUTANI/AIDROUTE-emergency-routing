import pymc as pm
import numpy as np
import pandas as pd
import arviz as az
from shapely import wkt

print("Loading POIs...")
pois = pd.read_csv('data/pois.csv')  # Updated path if you moved it to /data

# Convert geometry from WKT to shapely objects
pois['geometry'] = pois['geometry'].apply(wkt.loads)

# Add synthetic risk score if missing
if 'risk_score' not in pois.columns:
    print("Generating synthetic risk scores...")
    np.random.seed(42)
    pois['risk_score'] = np.random.beta(2, 5, size=len(pois))

    # Save updated POIs with risk_score back to file
    pois.to_csv('data/pois.csv', index=False)
    print("✅ Updated pois.csv with risk_score")

# Define high-risk as score > 0.5
high_risk = (pois['risk_score'] > 0.5).astype(int)

print("Building Bayesian model to estimate probability of high-risk POIs...")

with pm.Model() as model:
    p = pm.Beta('p', alpha=1, beta=1)
    obs = pm.Bernoulli('obs', p=p, observed=high_risk)
    trace = pm.sample(1000, tune=1000, cores=1, random_seed=42, progressbar=True)

print("Bayesian inference summary:")
summary = az.summary(trace, hdi_prob=0.95)
print(summary)

summary.to_csv('bayesian_risk_summary.csv')
print("✅ Saved Bayesian risk summary to bayesian_risk_summary.csv")


def compute_risk_score(amenity):
    # Placeholder logic - customize this later
    weights = {
        'hospital': 0.8,
        'clinic': 0.7,
        'shelter': 0.9,
        'fire_station': 0.6,
        'police': 0.5,
        'school': 0.4,
        'pharmacy': 0.6,
        'community_centre': 0.3
    }
    return weights.get(amenity, 0.2)
