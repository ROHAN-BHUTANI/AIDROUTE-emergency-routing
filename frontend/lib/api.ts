/**
 * API Service for communicating with Flask backend
 * Handles all HTTP requests to the emergency routing optimizer
 */

// Use Next.js rewrite proxy by default so users only need the frontend URL.
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/backend'

export interface RouteOption {
  type: 'fastest' | 'safest'
  path: Array<[number, number]>
  distance: number
  eta: number // in minutes
  risk_score: number
  risk_level: 'low' | 'medium' | 'high'
  risk_explanation?: string
  recommendation: string
}

export interface Hospital {
  name: string
  latitude: number
  longitude: number
  distance_km: number
}

export interface DisasterAnalysis {
  severity: 'low' | 'medium' | 'high'
  summary?: string
  indicators?: string[]
  confidence?: number
  provider?: string
}

export interface ResourceAllocationItem {
  resource: string
  units: number
}

export interface RecommendedAction {
  severity: 'low' | 'medium' | 'high'
  priority?: string
  resource_allocation?: ResourceAllocationItem[]
  summary?: string
  provider?: string
}

export interface RouteExplanation {
  route_name: string
  risk_level: 'low' | 'medium' | 'high'
  explanation: string
  reasons?: string[]
  provider?: string
}

export interface AIInsights {
  disaster_analysis?: DisasterAnalysis
  recommended_action?: RecommendedAction
  route_explanation?: RouteExplanation
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
  final_decision?: {
    selected_route: 'fastest' | 'safest'
    decision_priority: 'speed' | 'safety' | 'balanced'
    score: number
    justification: string
  }
  decision?: DecisionEngineResponse
  alerts?: SmartAlert[]
  scenario?: EmergencyScenario
  ai?: AIInsights
  status_text?: {
    risk: string
    route: string
    decision?: string
  }
}

export interface BlockedRoad {
  from_node: number
  to_node: number
  coordinates: [[number, number], [number, number]]
}

export interface SimulateDisasterResponse {
  disaster_type: string
  severity: string
  blocked_roads: BlockedRoad[]
  message: string
  rerouting_triggered: boolean
}

export interface EmergencyScenario {
  title: string
  summary: string
  traffic_state: string
  weather_state: string
  impact_scope: string
  updated_at: number
}

export interface SmartAlert {
  type: string
  title: string
  severity: 'info' | 'warning' | 'critical'
  message: string
}

export interface LiveAlertsResponse {
  alerts: SmartAlert[]
  scenario: EmergencyScenario
  risk_score: number
  emergency_type: string
  updated_at: number
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

interface ApiEnvelope<T> {
  status: string
  data?: T
  message?: string
  error?: string
}

async function parseApiResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  let payload: any
  try {
    payload = await response.json()
  } catch (e) {
    throw new Error(`Critical API connection failure: ${response.statusText || 'Internal Server Error'}`)
  }

  if (!response.ok) {
    const errorMsg = payload?.message || payload?.error || fallbackMessage
    // If it's a 500, we want a more technical but descriptive prefix for hackathon judging
    if (response.status >= 500) {
      throw new Error(`Backend Exception [${response.status}]: ${errorMsg}`)
    }
    throw new Error(errorMsg)
  }

  if (payload && typeof payload === 'object' && 'data' in payload && payload.data !== undefined) {
    return payload.data as T
  }

  return payload as T
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

    return await parseApiResponse<OptimizeRouteResponse>(response, 'Failed to optimize route')
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

    return await parseApiResponse<RiskPredictionResponse>(response, 'Failed to predict risk')
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

    const data = await parseApiResponse<{ hospital: Hospital }>(response, 'Failed to get nearest hospital')
    return data.hospital
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

    return await parseApiResponse<NearbyHospitalsResponse>(response, 'Failed to get nearby hospitals')
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

    return await parseApiResponse<OsrmRouteResponse>(response, 'Failed to get OSRM route')
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

    return await parseApiResponse<TrafficEstimateResponse>(response, 'Failed to estimate traffic')
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

    return await parseApiResponse<DecisionEngineResponse>(response, 'Failed to decide route')
  } catch (error) {
    console.error('Error deciding route:', error)
    throw error
  }
}

export async function getLiveAlerts(
  latitude: number,
  longitude: number,
  emergencyType = 'medical'
): Promise<LiveAlertsResponse> {
  const response = await fetch(`${API_BASE_URL}/live-alerts`, {
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

  return await parseApiResponse<LiveAlertsResponse>(response, 'Failed to fetch live alerts')
}

/**
 * Simulate a disaster (flood/accident/congestion) at coordinates.
 */
export async function simulateDisaster(
  type: string,
  latitude: number,
  longitude: number
): Promise<SimulateDisasterResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/simulate-disaster`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ type, latitude, longitude }),
    })

    return await parseApiResponse<SimulateDisasterResponse>(response, 'Failed to simulate disaster')
  } catch (error) {
    console.error('Error simulating disaster:', error)
    throw error
  }
}
