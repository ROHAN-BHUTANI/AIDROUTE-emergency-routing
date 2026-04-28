"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Clock, Route, AlertTriangle, MessageSquare, Zap, MapPin, Siren, ShieldAlert } from "lucide-react"
import { cn } from "@/lib/utils"
import { AIInsights, EmergencyScenario, RouteOption, Hospital, SmartAlert } from "@/lib/api"

interface DecisionBrief {
  selected_route: string
  decision_priority: string
  score: number
  justification: string
}

interface AnalyticsCardsProps {
  hospital?: Hospital
  routes?: RouteOption[]
  selectedRouteType?: 'fastest' | 'safest'
  scenario?: EmergencyScenario
  alerts?: SmartAlert[]
  ai?: AIInsights
  decision?: DecisionBrief
  isLoading?: boolean
}

export function AnalyticsCards({ 
  hospital, 
  routes, 
  selectedRouteType = 'fastest',
  scenario,
  alerts = [],
  ai,
  decision,
  isLoading 
}: AnalyticsCardsProps) {
  const isFiniteNumber = (value: unknown): value is number =>
    typeof value === "number" && Number.isFinite(value)

  const selectedRoute = routes?.find(r => r.type === selectedRouteType)
  const alternateRoute = routes?.find(r => r.type !== selectedRouteType)
  const aiSeverity = ai?.disaster_analysis?.severity || null
  const aiRecommendation = ai?.recommended_action?.summary || selectedRoute?.recommendation || "AI recommendation will appear after analysis."
  const aiRouteExplanation = ai?.route_explanation?.explanation || selectedRoute?.risk_explanation || "Route explanation will appear after AI analysis."
  const aiConfidence = ai?.disaster_analysis?.confidence
  const resourceAllocation = ai?.recommended_action?.resource_allocation || []
  const trafficLabel = (() => {
    const risk = selectedRoute?.risk_score ?? 0
    if (risk >= 7) return "High ⚠️"
    if (risk >= 4) return "Moderate"
    return "Low"
  })()
  const etaValue = selectedRoute?.eta !== undefined ? `${selectedRoute.eta} mins` : "6 mins"
  const hospitalName = hospital?.name || "AIIMS"
  const recommendationValue = selectedRoute?.recommendation || (alternateRoute ? "Alternate route reduces delay by 2 mins" : "Alternate route reduces delay by 2 mins")
  const getSeverityMeta = (severity: string | null) => {
    switch (severity) {
      case "low":
        return {
          label: "Low",
          className: "border-green-500/20 bg-green-500/10 text-green-500",
        }
      case "medium":
        return {
          label: "Medium",
          className: "border-amber-500/20 bg-amber-500/10 text-amber-500",
        }
      case "high":
        return {
          label: "High",
          className: "border-red-500/20 bg-red-500/10 text-red-500",
        }
      default:
        return {
          label: "Unknown",
          className: "border-border bg-muted/10 text-muted-foreground",
        }
    }
  }
  const severityMeta = getSeverityMeta(aiSeverity)

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
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[1,2,3,4].map(i => (
            <Card key={i} className="h-[120px] bg-muted/20 animate-pulse border-border/50" />
          ))}
        </div>
      )}

      {!isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {cards.map((card) => (
            <Card
              key={card.title}
              className={cn(
                "group relative overflow-hidden border-border bg-card/50 backdrop-blur-sm transition-all hover:border-primary/30 hover:shadow-lg hover:shadow-primary/5",
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
      )}

      {/* AI Decision & Reasoning */}
      {decision && (
        <Card className="border-primary/20 bg-primary/5 overflow-hidden">
          <div className="bg-primary/10 px-4 py-2 flex items-center justify-between border-b border-primary/10">
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-primary" />
              <span className="text-xs font-bold uppercase tracking-wider text-primary">Intelligent Decision</span>
            </div>
            <span className={cn(
              "text-[10px] font-bold px-2 py-0.5 rounded-full uppercase",
              decision.decision_priority === 'safety' ? "bg-red-500/20 text-red-500" : "bg-primary/20 text-primary"
            )}>
              Priority: {decision.decision_priority}
            </span>
          </div>
          <CardContent className="p-5">
            <div className="space-y-4">
              <div className="space-y-1">
                <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-tight">AI Reasoning</p>
                <p className="text-sm font-medium leading-relaxed text-foreground">
                  {decision.justification}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-tight">Strategy</p>
                  <p className="text-sm font-bold text-primary">
                    {decision.selected_route === 'safest' ? 'Risk Avoidance' : 'Time Optimization'}
                  </p>
                </div>
                {aiConfidence && (
                  <div className="space-y-1">
                    <p className="text-[11px] font-semibold text-muted-foreground uppercase tracking-tight">Confidence</p>
                    <p className="text-sm font-bold text-foreground">
                      {(aiConfidence * 100).toFixed(0)}%
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

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
              <div className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wider", severityMeta.className)}>
                <span>Disaster Severity</span>
                <span>{severityMeta.label}</span>
              </div>
              <p className="break-words text-sm leading-relaxed text-foreground">
                {aiRecommendation}
              </p>
              <div className="rounded-lg border border-primary/20 bg-primary/10 p-3">
                <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-primary/80">Route Explanation</p>
                <p className="text-xs leading-relaxed text-foreground/90">{aiRouteExplanation}</p>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                <div className="rounded-lg border border-border/80 bg-background/40 p-2.5">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Confidence</p>
                  <p className="text-sm font-semibold text-foreground">{typeof aiConfidence === "number" ? `${Math.round(aiConfidence * 100)}%` : "—"}</p>
                </div>
                <div className="rounded-lg border border-border/80 bg-background/40 p-2.5">
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">Resources</p>
                  <p className="text-sm font-semibold text-foreground">
                    {resourceAllocation.length ? `${resourceAllocation.length} allocations` : "Standard support"}
                  </p>
                </div>
              </div>
              {resourceAllocation.length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1">
                  {resourceAllocation.slice(0, 4).map((item) => (
                    <span
                      key={item.resource}
                      className="rounded-full border border-border bg-background/60 px-2.5 py-1 text-[11px] font-medium text-muted-foreground"
                    >
                      {item.resource}: {item.units}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
