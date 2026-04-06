"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Clock, Route, AlertTriangle, MessageSquare, Zap, MapPin, Siren, ShieldAlert } from "lucide-react"
import { cn } from "@/lib/utils"
import { EmergencyScenario, RouteOption, Hospital, SmartAlert } from "@/lib/api"

interface AnalyticsCardsProps {
  hospital?: Hospital
  routes?: RouteOption[]
  selectedRouteType?: 'fastest' | 'safest'
  scenario?: EmergencyScenario
  alerts?: SmartAlert[]
  isLoading?: boolean
}

export function AnalyticsCards({ 
  hospital, 
  routes, 
  selectedRouteType = 'fastest',
  scenario,
  alerts = [],
  isLoading 
}: AnalyticsCardsProps) {
  const isFiniteNumber = (value: unknown): value is number =>
    typeof value === "number" && Number.isFinite(value)

  const selectedRoute = routes?.find(r => r.type === selectedRouteType)
  const alternateRoute = routes?.find(r => r.type !== selectedRouteType)
  const trafficLabel = (() => {
    const risk = selectedRoute?.risk_score ?? 0
    if (risk >= 7) return "High ⚠️"
    if (risk >= 4) return "Moderate"
    return "Low"
  })()
  const etaValue = selectedRoute?.eta !== undefined ? `${selectedRoute.eta} mins` : "6 mins"
  const hospitalName = hospital?.name || "AIIMS"
  const recommendationValue = selectedRoute?.recommendation || (alternateRoute ? "Alternate route reduces delay by 2 mins" : "Alternate route reduces delay by 2 mins")
  const riskExplanation = selectedRoute?.risk_explanation || "AI explanation will appear after route intelligence is generated."

  const getRiskColor = (level: string | null) => {
    switch (level) {
      case "low":
        return "text-green-500 bg-green-500/10 border-green-500/20"
      case "medium":
        return "text-amber-500 bg-amber-500/10 border-amber-500/20"
      case "high":
        return "text-red-500 bg-red-500/10 border-red-500/20"
      default:
        return "text-muted-foreground bg-muted/10 border-muted/20"
    }
  }

  const getRiskLabel = (level: string | null) => {
    switch (level) {
      case "low":
        return "Low Risk"
      case "medium":
        return "Medium Risk"
      case "high":
        return "High Risk"
      default:
        return "—"
    }
  }

  const cards = [
    {
      title: "ETA",
      value: selectedRoute?.eta !== undefined ? `${selectedRoute.eta}` : "—",
      unit: "min",
      icon: Clock,
      description: "Estimated arrival time",
    },
    {
      title: "Distance",
      value: isFiniteNumber(selectedRoute?.distance) ? `${selectedRoute.distance.toFixed(1)}` : "—",
      unit: "km",
      icon: Route,
      description: "Total route distance",
    },
    {
      title: "Risk Level",
      value: selectedRoute ? getRiskLabel(selectedRoute.risk_level) : "—",
      unit: "",
      icon: AlertTriangle,
      customClass: selectedRoute ? getRiskColor(selectedRoute.risk_level) : "",
      description: "Route risk assessment",
    },
    {
      title: "Risk Score",
      value: selectedRoute?.risk_score !== undefined ? `${selectedRoute.risk_score}` : "—",
      unit: "/10",
      icon: Zap,
      description: "Numerical risk value",
    },
  ]

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        {cards.map((card) => (
          <Card
            key={card.title}
            className={cn(
              "group relative overflow-hidden border-border bg-card/50 backdrop-blur-sm transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5",
              isLoading && "animate-pulse"
            )}
          >
            <CardContent className="p-5">
              <div className="flex items-start justify-between">
                <div className="space-y-3 flex-1">
                  <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    {card.title}
                  </p>
                  <div className="flex flex-wrap items-baseline gap-1">
                    <span
                      className={cn(
                        "text-2xl font-bold tracking-tight",
                        card.customClass ? card.customClass.split(" ")[0] : "text-foreground"
                      )}
                    >
                      {card.value}
                    </span>
                    {card.unit && (
                      <span className="text-sm text-muted-foreground">{card.unit}</span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">{card.description}</p>
                </div>
                <div className={cn(
                  "flex h-10 w-10 items-center justify-center rounded-lg shrink-0",
                  card.customClass || "bg-primary/10 text-primary"
                )}>
                  <card.icon className="h-5 w-5" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Hospital and Route Info Cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="border-border bg-card/50 backdrop-blur-sm">
          <CardContent className="p-5">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-red-500/20 bg-red-500/10">
                <MapPin className="h-5 w-5 text-red-500" />
              </div>
              <div className="space-y-1 flex-1 min-w-0">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Destination Hospital
                </p>
                <p className="text-sm font-semibold text-foreground truncate">
                  {hospital?.name || "—"}
                </p>
                <p className="text-xs text-muted-foreground">
                  {isFiniteNumber(hospital?.distance_km) ? `${hospital.distance_km.toFixed(1)} km away` : "—"}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-border bg-card/50 backdrop-blur-sm">
          <CardContent className="p-5">
            <div className="flex items-start gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
                <Route className="h-5 w-5 text-blue-500" />
              </div>
              <div className="space-y-1 flex-1 min-w-0">
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Route Type
                </p>
                <p className="text-sm font-semibold text-foreground">
                  {selectedRouteType === 'fastest' ? 'Fastest Route' : 'Safest Route'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {selectedRouteType === 'fastest' 
                    ? 'Minimizes travel time' 
                    : 'Prioritizes safety'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Live Scenario & Alerts */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-border bg-gradient-to-br from-card/80 to-card/40 backdrop-blur-sm">
          <CardContent className="p-5">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-cyan-400/30 bg-cyan-500/10">
                <ShieldAlert className="h-5 w-5 text-cyan-300" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Simulation Scenario</p>
                <p className="text-sm font-semibold text-foreground">{scenario?.title || "Awaiting simulation"}</p>
              </div>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">
              {scenario?.summary || "Run optimization to generate a realistic emergency scenario with risk-linked route intelligence."}
            </p>
          </CardContent>
        </Card>

        <Card className="border-border bg-gradient-to-br from-card/80 to-card/40 backdrop-blur-sm">
          <CardContent className="p-5">
            <div className="mb-3 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-amber-400/30 bg-amber-500/10">
                <Siren className="h-5 w-5 text-amber-300" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Smart Alerts</p>
                <p className="text-sm font-semibold text-foreground">Live emergency feed</p>
              </div>
            </div>
            <div className="space-y-2">
              {alerts.length ? alerts.slice(0, 3).map((alert) => (
                <div key={alert.type} className="rounded-lg border border-border/80 bg-background/40 p-2.5">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <p className="text-xs font-semibold text-foreground">{alert.title}</p>
                    <span className={cn(
                      "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
                      alert.severity === "critical" && "bg-red-500/15 text-red-300",
                      alert.severity === "warning" && "bg-amber-500/15 text-amber-300",
                      alert.severity === "info" && "bg-cyan-500/15 text-cyan-300",
                    )}>
                      {alert.severity}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed text-muted-foreground">{alert.message}</p>
                </div>
              )) : (
                <p className="text-xs text-muted-foreground">No active alerts. Live feed updates automatically.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Emergency Intelligence Panel */}
      <Card className="border-border bg-gradient-to-br from-card/50 to-card/30 backdrop-blur-sm">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-rose-500/20 bg-rose-500/10">
              <AlertTriangle className="h-5 w-5 text-rose-500" />
            </div>
            <div className="space-y-2 flex-1">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Emergency Intelligence Panel
              </p>
              <div className="grid gap-1 text-sm text-foreground">
                <p><span className="font-medium">Nearest Hospital:</span> {hospitalName}</p>
                <p><span className="font-medium">ETA:</span> {etaValue}</p>
                <p><span className="font-medium">Traffic:</span> {trafficLabel}</p>
                <p><span className="font-medium">Recommendation:</span> {recommendationValue}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* AI Recommendation Card */}
      <Card className="border-border bg-gradient-to-br from-card/50 to-card/30 backdrop-blur-sm">
        <CardContent className="p-5">
          <div className="flex items-start gap-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
              <MessageSquare className="h-5 w-5 text-primary" />
            </div>
            <div className="space-y-2 flex-1">
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                AI Recommendation
              </p>
              <p className="break-words text-sm leading-relaxed text-foreground">
                {selectedRoute?.recommendation || (
                  <span className="text-muted-foreground italic">
                    Enter route details to receive AI-powered optimization recommendations based on real-time conditions.
                  </span>
                )}
              </p>
              <div className="mt-3 rounded-lg border border-primary/20 bg-primary/10 p-3">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-primary/80">Risk Explanation</p>
                <p className="text-xs leading-relaxed text-foreground/90">{riskExplanation}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
