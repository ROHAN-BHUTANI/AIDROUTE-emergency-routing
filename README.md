# AIDRoute

AI-based disaster relief routing system that combines graph algorithms and Bayesian risk modeling to recommend faster and safer emergency paths.

## Overview
AIDRoute is a decision-support project for disaster and emergency logistics. Traditional shortest-path routing often ignores operational uncertainty such as congestion, incident probability, and dynamic risk. AIDRoute addresses this by combining route optimization with probabilistic risk scoring so responders can choose routes that are both efficient and reliable.

This project showcases applied AI for high-impact public safety use cases and demonstrates strong backend, algorithmic, and systems design skills.

## Features
- Optimized routing with graph-based algorithms for efficient path selection.
- Risk-aware navigation using Bayesian modeling to account for uncertain conditions.
- Real-world simulation workflows for testing routing performance across emergency scenarios.
- API-first backend suitable for dashboard and operations-center integration.
- Extensible architecture for new data sources (traffic, weather, incidents, road closures).

## Tech Stack
- Python
- Flask
- Graph Algorithms
- MongoDB

## How it works
1. Collect incident context and routing inputs (origin, constraints, emergency type).
2. Represent the transport network as a weighted graph.
3. Generate candidate routes using shortest-path and weighted-optimization logic.
4. Compute Bayesian risk estimates for each route under uncertainty.
5. Rank route options using a speed-safety tradeoff score.
6. Return the recommended route and alternatives for operator review or automated dispatch.

## Future improvements
- Real-time re-routing with live traffic and weather feeds.
- Multi-objective optimization with configurable policy weights by emergency type.
- Explainable AI layer to surface why a route was selected.
- Scenario benchmarking suite to track model quality over time.
- Containerized deployment and monitoring pipeline for production readiness.

## Repository Structure
```text
AIDRoute/
├── app.py
├── routing.py
├── data/
├── models/
├── requirements.txt
├── README.md
├── scripts/
├── docs/
├── static/
├── templates/
└── frontend/
```
