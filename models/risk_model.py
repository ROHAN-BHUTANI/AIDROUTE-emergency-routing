# risk_model.py
import pandas as pd
import numpy as np
import pymc as pm

def simulate_road_risks(roads_df):
    """
    Adds Bayesian risk scores to roads_df.
    Uses road length and highway type (encoded) as predictors.
    Returns the dataframe with columns: risk_mean, risk_std
    """
    # Encode highway type (simplified)
    highway_types = roads_df['highway'].astype('category').cat.codes.values

    length = roads_df['length'].values

    with pm.Model() as model:
        # Priors
        alpha = pm.Normal('alpha', 0, 1)
        beta_length = pm.Normal('beta_length', 0, 1)
        beta_highway = pm.Normal('beta_highway', 0, 1)
        sigma = pm.HalfNormal('sigma', 1)

        # Linear model for log-odds of risk
        logit_p = alpha + beta_length * (length / 1000) + beta_highway * highway_types

        # Probability of risk (e.g., probability that road is risky)
        p = pm.Deterministic('p', pm.math.sigmoid(logit_p))

        # Observed data: simulate risks (here we simulate because no real data)
        # Let's pretend half of roads are risky for demo purposes
        risk_obs = pm.Bernoulli('risk_obs', p=p, observed=(np.random.rand(len(length)) > 0.5).astype(int))

        # Sample posterior
        trace = pm.sample(1000, tune=1000, chains=2, cores=1, progressbar=False)

    # Extract posterior mean and std for risk probability p
    risk_posterior_samples = trace.posterior['p'].stack(samples=("chain", "draw")).values
    risk_mean = risk_posterior_samples.mean(axis=1)
    risk_std = risk_posterior_samples.std(axis=1)

    # Add to dataframe
    roads_df = roads_df.copy()
    roads_df['risk_mean'] = risk_mean
    roads_df['risk_std'] = risk_std

    return roads_df

if __name__ == "__main__":
    # For standalone testing
    roads = pd.read_csv('roads.csv')
    roads_with_risk = simulate_road_risks(roads)
    roads_with_risk.to_csv('roads_with_risk.csv', index=False)
    print("Roads with Bayesian risk scores saved to roads_with_risk.csv")
