"use client"

import { useEffect, useState } from "react"
import { InputCard } from "@/components/dashboard/input-card"
import { MapSection } from "@/components/dashboard/map-section"
import { AnalyticsCards } from "@/components/dashboard/analytics-cards"
import { AIInsights, BlockedRoad, EmergencyScenario, getLiveAlerts, Hospital, optimizeRoute, RouteOption, simulateDisaster, SmartAlert } from "@/lib/api"
import { toast } from "sonner"
import { Badge } from "@/components/ui/badge"
import { Sparkles } from "lucide-react"

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(false)
  const [isLocating, setIsLocating] = useState(false)
  const [hasRoute, setHasRoute] = useState(false)
  const [hospital, setHospital] = useState<Hospital | undefined>()
  const [routes, setRoutes] = useState<RouteOption[]>([])
  const [selectedRouteType, setSelectedRouteType] = useState<"fastest" | "safest">("fastest")
  const [error, setError] = useState<string | null>(null)
  const [alerts, setAlerts] = useState<SmartAlert[]>([])
  const [scenario, setScenario] = useState<EmergencyScenario | undefined>()
  const [ai, setAi] = useState<AIInsights | undefined>()
  const [loadingStage, setLoadingStage] = useState<string>("")
  const [blockedRoads, setBlockedRoads] = useState<BlockedRoad[]>([])
  const [decision, setDecision] = useState<{
    selected_route: string
    decision_priority: string
    score: number
    justification: string
  } | undefined>()
  const [currentLocation, setCurrentLocation] = useState<{
    latitude: number
    longitude: number
  } | null>(null)

  const handleOptimize = async (data: {
    latitude: string
    longitude: string
    emergencyType: string
  }) => {
    setError(null)
    setIsLoading(true)
    setLoadingStage("Analyzing risk...")
    setAi(undefined)

    try {
      const lat = parseFloat(data.latitude)
      const lon = parseFloat(data.longitude)

      if (isNaN(lat) || isNaN(lon)) {
        throw new Error("Invalid latitude or longitude coordinates.")
      }

      setLoadingStage("Initializing AI engine...")
      const response = await optimizeRoute(lat, lon, data.emergencyType)
      
      setLoadingStage("Syncing hospital capacity...")
      await new Promise(r => setTimeout(r, 600))
      
      setLoadingStage("Evaluating Gemini justifications...")
      setHospital(response.hospital)
      setRoutes(response.routes)
      setAlerts(response.alerts || [])
      setScenario(response.scenario)
      setAi(response.ai)
      setHasRoute(true)
      setDecision(response.final_decision)
      
      if (response.final_decision?.selected_route) {
        setSelectedRouteType(response.final_decision.selected_route as "fastest" | "safest")
      } else {
        setSelectedRouteType("fastest")
      }

      toast.success("AI Analysis Complete: Optimal route calculated.")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to optimize route"
      setError(message)
      toast.error(message)
      setHasRoute(false)
    } finally {
      setLoadingStage("")
      setIsLoading(false)
    }
  }

  const handleSimulateDisaster = async (type: string) => {
    if (!currentLocation) {
      toast.error("Geolocation required for simulation center.")
      return
    }

    setIsLoading(true)
    setLoadingStage(`Triggering ${type} event...`)
    try {
      const res = await simulateDisaster(type, currentLocation.latitude, currentLocation.longitude)
      setBlockedRoads(res.blocked_roads)
      
      setLoadingStage("Propagating network changes...")
      await new Promise(r => setTimeout(r, 800))

      toast.warning(`Road blocks detected! Re-calculating AI routes...`, {
        duration: 5000,
        description: "New road blocks forced the intelligence engine to re-evaluate safest paths."
      })
      
      // Trigger re-optimize to get routes avoiding blocked roads
      await handleOptimize({
        latitude: currentLocation.latitude.toString(),
        longitude: currentLocation.longitude.toString(),
        emergencyType: type === "accident" ? "accident" : type === "flood" ? "flood" : "medical"
      })
    } catch (err) {
      toast.error("Simulation engine offline. Please retry.")
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    if (!currentLocation) {
      return
    }

    const refresh = async () => {
      try {
        const live = await getLiveAlerts(
          currentLocation.latitude,
          currentLocation.longitude,
          "medical"
        )
        setAlerts(live.alerts)
        setScenario(live.scenario)
      } catch {
        // Silent polling fallback to keep UX smooth.
      }
    }

    const id = window.setInterval(refresh, 18000)
    return () => window.clearInterval(id)
  }, [currentLocation])

  const handleGeolocation = async () => {
    if (!navigator.geolocation) {
      const message = "Geolocation is not supported by your browser"
      setError(message)
      toast.error(message)
      return
    }

    setError(null)
    setIsLocating(true)

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject, {
          enableHighAccuracy: true,
          timeout: 12000,
          maximumAge: 30000,
        })
      })

      const latitude = Number(position.coords.latitude.toFixed(6))
      const longitude = Number(position.coords.longitude.toFixed(6))

      setCurrentLocation({ latitude, longitude })
      setError(null)
      toast.success(`Location captured: ${latitude}, ${longitude}`)

      handleOptimize({
        latitude: latitude.toString(),
        longitude: longitude.toString(),
        emergencyType: "medical",
      })
    } catch (err) {
      let message = "Unable to get your location"

      if (err instanceof GeolocationPositionError) {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            message = "Location permission denied. Please enable geolocation in your browser."
            break
          case err.POSITION_UNAVAILABLE:
            message = "Location information is unavailable."
            break
          case err.TIMEOUT:
            message = "The request to get user location timed out. Try again."
            break
        }
      }

      setError(message)
      toast.error(message)
    } finally {
      setIsLocating(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="mb-6 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-primary/80">
              AIDRoute
            </p>
            {hasRoute && (
              <Badge variant="secondary" className="bg-primary/10 text-primary animate-pulse border-primary/20">
                <Sparkles className="mr-1 h-3 w-3" />
                AI Decision Mode Active
              </Badge>
            )}
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
            Emergency Response Dashboard
          </h1>
          <p className="max-w-2xl text-sm text-muted-foreground sm:text-base">
            Enter an incident location to generate the shortest safe route, live hospital context,
            and Gemini-powered disaster guidance.
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {isLoading && loadingStage && (
          <div className="mb-5 rounded-xl border border-primary/20 bg-primary/10 px-4 py-3 text-sm font-medium text-primary">
            {loadingStage}
          </div>
        )}

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.25fr)_minmax(0,1.75fr)]">
          <div className="space-y-6">
            <InputCard
              onOptimize={handleOptimize}
              onSimulate={handleSimulateDisaster}
              isLoading={isLoading}
              isLocating={isLocating}
              onLocationClick={handleGeolocation}
            />
            <AnalyticsCards
              hospital={hospital}
              routes={routes}
              selectedRouteType={selectedRouteType}
              alerts={alerts}
              scenario={scenario}
              ai={ai}
              decision={decision}
              isLoading={isLoading}
            />
          </div>

          <MapSection
            hasRoute={hasRoute}
            hospital={hospital}
            routes={routes}
            selectedRouteType={selectedRouteType}
            currentLocation={currentLocation}
            blockedRoads={blockedRoads}
          />
        </div>
      </main>
    </div>
  )
}
