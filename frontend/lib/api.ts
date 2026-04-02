/**
 * API Service for communicating with Flask backend
 * Handles all HTTP requests to the emergency routing optimizer
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export interface RouteOption {
  type: 'fastest' | 'safest'
  path: Array<[number, number]>
  distance: number
  eta: number // in minutes
  risk_score: number
  risk_level: 'low' | 'medium' | 'high'
  recommendation: string
}

export interface Hospital {
  name: string
  latitude: number
  longitude: number
  distance_km: number
}

export interface NearbyHospitalsResponse {
  latitude: number
  longitude: number
  emergency_type: string
  radius_km: number
  hospitals: Hospital[]
}

export interface OptimizeRouteResponse {
  hospital: Hospital
  routes: RouteOption[]
  status: string
}

export interface RiskPredictionResponse {
  location: string
  risk_score: number
  risk_level: 'low' | 'medium' | 'high'
  explanation: string
  recommendation: string
}

export interface TrafficEstimateResponse {
  traffic_score: number
  explanation: string
  time_of_day: string
  normalized_time: string
  location_type: string
  random_variability: number
}

export interface DecisionRouteInput {
  name?: string
  type?: string
  distance: number
  eta: number
  traffic_score?: number
  risk_score: number
  recommendation?: string
  path?: Array<[number, number]>
}

export interface DecisionEngineResponse {
  best_route: {
    name: string
    distance_km: number
    eta_min: number
    traffic_score: number
    risk_score: number
    recommendation: string
    path: Array<[number, number]>
    decision_score: number
  }
  ranked_routes: Array<{
    name: string
    distance_km: number
    eta_min: number
    traffic_score: number
    risk_score: number
    recommendation: string
    path: Array<[number, number]>
    decision_score: number
  }>
  explanation: string
  recommendation: string
  criteria: {
    distance: number
    eta: number
    traffic: number
    risk: number
  }
}

export interface ApiError {
  error: string
  status: number
}

export interface OsrmRouteResponse {
  source: {
    latitude: number
    longitude: number
  }
  destination: {
    latitude: number
    longitude: number
  }
  route_coordinates: Array<[number, number]>
  distance_km: number
  duration_min: number
  distance_m: number
  duration_sec: number
}

/**
 * Optimize route for emergency response
 */
export async function optimizeRoute(
  latitude: number,
  longitude: number,
  emergencyType: string
): Promise<OptimizeRouteResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/optimize-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude,
        longitude,
        emergency_type: emergencyType,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to optimize route')
    }

    return await response.json()
  } catch (error) {
    console.error('Error optimizing route:', error)
    throw error
  }
}

/**
 * Predict risk at a specific location
 */
export async function predictRisk(
  latitude: number,
  longitude: number
): Promise<RiskPredictionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/predict-risk`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude,
        longitude,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to predict risk')
    }

    return await response.json()
  } catch (error) {
    console.error('Error predicting risk:', error)
    throw error
  }
}

/**
 * Get nearest hospital to coordinates
 */
export async function getNearestHospital(
  latitude: number,
  longitude: number
): Promise<Hospital> {
  try {
    const response = await fetch(`${API_BASE_URL}/nearest-hospital`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude,
        longitude,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to get nearest hospital')
    }

    return await response.json()
  } catch (error) {
    console.error('Error getting nearest hospital:', error)
    throw error
  }
}

/**
 * Fetch up to 3 nearby hospitals within 5km of a coordinate.
 */
export async function getNearbyHospitals(
  latitude: number,
  longitude: number,
  emergencyType = 'medical'
): Promise<NearbyHospitalsResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/nearby-hospitals`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        latitude,
        longitude,
        emergency_type: emergencyType,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to get nearby hospitals')
    }

    const payload = await response.json()
    return payload.data as NearbyHospitalsResponse
  } catch (error) {
    console.error('Error getting nearby hospitals:', error)
    throw error
  }
}

/**
 * Fetch a real driving route from OSRM between two coordinate pairs.
 */
export async function getOsrmRoute(
  sourceLatitude: number,
  sourceLongitude: number,
  destinationLatitude: number,
  destinationLongitude: number
): Promise<OsrmRouteResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/osrm-route`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        source_latitude: sourceLatitude,
        source_longitude: sourceLongitude,
        destination_latitude: destinationLatitude,
        destination_longitude: destinationLongitude,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to get OSRM route')
    }

    const payload = await response.json()
    return payload.data as OsrmRouteResponse
  } catch (error) {
    console.error('Error getting OSRM route:', error)
    throw error
  }
}

/**
 * Estimate traffic score using time of day, location type, and random variability.
 */
export async function estimateTraffic(
  timeOfDay: string,
  locationType: string,
  randomVariability?: number
): Promise<TrafficEstimateResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/estimate-traffic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        time_of_day: timeOfDay,
        location_type: locationType,
        random_variability: randomVariability,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to estimate traffic')
    }

    const payload = await response.json()
    return payload.data as TrafficEstimateResponse
  } catch (error) {
    console.error('Error estimating traffic:', error)
    throw error
  }
}

/**
 * Compare routes and return the best route with a human-readable explanation.
 */
export async function decideRoute(
  routes: DecisionRouteInput[]
): Promise<DecisionEngineResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/decision-engine`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ routes }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Failed to decide route')
    }

    const payload = await response.json()
    return payload.data as DecisionEngineResponse
  } catch (error) {
    console.error('Error deciding route:', error)
    throw error
  }
}
