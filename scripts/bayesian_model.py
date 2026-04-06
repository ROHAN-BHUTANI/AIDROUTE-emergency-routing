# bayesian_model.py
import pandas as pd
import pymc as pm
import arviz as az
import numpy as np

def run_bayesian_priority_model():
    print("Loading POIs...")
    pois = pd.read_csv('pois.csv')

    # Simple priority model example:
    # Count number of each amenity type and assign weights
    amenity_counts = pois['amenity'].value_counts()

    # Assign manual weights to amenities for priority scoring
    weights = {
        'hospital': 5,
        'clinic': 4,
        'shelter': 3,
        'fire_station': 4,
        'police': 4,
        'school': 2,
        'pharmacy': 3,
        'community_centre': 1
    }

    # Build observed data vector y (weighted counts)
    y_obs = []
    amenity_types = []
    for amenity, count in amenity_counts.items():
        if amenity in weights:
            y_obs.append(count)
            amenity_types.append(amenity)

    y_obs = np.array(y_obs)

    print(f"Running Bayesian model on amenities: {amenity_types}")

    with pm.Model() as model:
        # Prior for base rate of POI occurrence
        base_rate = pm.Exponential('base_rate', 1)

        # Amenity effects modeled as Gamma distributed
        amenity_effects = pm.Gamma('amenity_effects', alpha=2, beta=1, shape=len(y_obs))

        # Expected count modeled as base_rate * amenity_effect * weights
        mu = base_rate * amenity_effects * np.array([weights[a] for a in amenity_types])

        # Likelihood: observed counts are Poisson distributed
        observed = pm.Poisson('observed', mu=mu, observed=y_obs)

        trace = pm.sample(1000, tune=1000, cores=1, return_inferencedata=True)

    print("Bayesian model complete, summary:")
    print(az.summary(trace, var_names=['base_rate', 'amenity_effects']))

    # Save trace summary for later dashboard use
    trace.to_netcdf('bayesian_trace.nc')

if __name__ == "__main__":
    run_bayesian_priority_model()
