"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { GitCompare, Zap, Shield, Clock, Route, AlertTriangle, CheckCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import { RouteOption } from "@/lib/api"

interface RouteComparisonProps {
  hasData?: boolean
  routes?: RouteOption[]
  selectedRouteType?: 'fastest' | 'safest'
  onRouteTypeChange?: (type: 'fastest' | 'safest') => void
}

export function RouteComparison({ 
  hasData, 
  routes = [], 
  selectedRouteType = 'fastest',
  onRouteTypeChange 
}: RouteComparisonProps) {
  const getRiskStyles = (level: string) => {
    switch (level) {
      case "low":
        return {
          badge: "bg-green-500/10 text-green-500 border-green-500/20",
          icon: "text-green-500",
          bg: "bg-green-500/5",
        }
      case "medium":
        return {
          badge: "bg-amber-500/10 text-amber-500 border-amber-500/20",
          icon: "text-amber-500",
          bg: "bg-amber-500/5",
        }
      case "high":
        return {
          badge: "bg-red-500/10 text-red-500 border-red-500/20",
          icon: "text-red-500",
          bg: "bg-red-500/5",
        }
      default:
        return {
          badge: "bg-muted text-muted-foreground",
          icon: "text-muted-foreground",
          bg: "bg-muted/5",
        }
    }
  }

  return (
    <Card className="border-border bg-card/50 backdrop-blur-sm">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <GitCompare className="h-4 w-4 text-primary" />
          </div>
          Route Comparison
        </CardTitle>
      </CardHeader>
      <CardContent>
        {hasData && routes.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">
            {routes.map((route) => {
              const riskStyles = getRiskStyles(route.risk_level)
              const isSelected = selectedRouteType === route.type
              
              return (
                <button
                  key={route.type}
                  onClick={() => onRouteTypeChange?.(route.type)}
                  className={cn(
                    "relative overflow-hidden rounded-xl border p-4 transition-all hover:border-primary/30 text-left",
                    isSelected
                      ? "border-primary/50 bg-primary/10"
                      : "border-border bg-muted/20 hover:bg-muted/30"
                  )}
                >
                  {isSelected && (
                    <div className="absolute right-0 top-0">
                      <div className="flex items-center gap-1 rounded-bl-lg bg-primary px-2 py-1 text-xs font-medium text-primary-foreground">
                        <CheckCircle className="h-3 w-3" />
                        Active
                      </div>
                    </div>
                  )}

                  <div className="mb-4 flex items-center gap-2">
                    <div
                      className={cn(
                        "flex h-8 w-8 items-center justify-center rounded-lg",
                        route.type === "fastest"
                          ? "bg-blue-500/10 text-blue-500"
                          : "bg-green-500/10 text-green-500"
                      )}
                    >
                      {route.type === "fastest" ? (
                        <Zap className="h-4 w-4" />
                      ) : (
                        <Shield className="h-4 w-4" />
                      )}
                    </div>
                    <h3 className="font-semibold text-foreground capitalize">
                      {route.type} Route
                    </h3>
                  </div>

                  <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="h-3.5 w-3.5" />
                        <span className="text-xs">ETA</span>
                      </div>
                      <p className="text-lg font-bold text-foreground">
                        {route.eta}
                        <span className="text-xs font-normal text-muted-foreground"> min</span>
                      </p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <Route className="h-3.5 w-3.5" />
                        <span className="text-xs">Distance</span>
                      </div>
                      <p className="text-lg font-bold text-foreground">
                        {route.distance.toFixed(1)}
                        <span className="text-xs font-normal text-muted-foreground"> km</span>
                      </p>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center gap-1 text-muted-foreground">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        <span className="text-xs">Risk</span>
                      </div>
                      <Badge
                        variant="outline"
                        className={cn("capitalize", riskStyles.badge)}
                      >
                        {route.risk_level}
                      </Badge>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs font-medium text-muted-foreground">
                      Risk Score: {route.risk_score}/10
                    </p>
                    <p className="break-words text-sm leading-relaxed text-muted-foreground sm:line-clamp-2">
                      {route.recommendation}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-dashed border-border bg-muted/30">
              <GitCompare className="h-6 w-6 text-muted-foreground/50" />
            </div>
            <p className="mb-1 text-sm font-medium text-muted-foreground">
              No routes to compare
            </p>
            <p className="text-xs text-muted-foreground/70">
              Optimize a route to see fastest vs safest comparison
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
