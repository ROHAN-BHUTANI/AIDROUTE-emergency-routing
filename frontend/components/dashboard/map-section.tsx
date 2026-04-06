"use client"

import dynamic from "next/dynamic"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Map, Layers, Maximize2 } from "lucide-react"
import { RouteOption, Hospital } from "@/lib/api"

const DynamicMapComponent = dynamic(() => import("./map-component"), {
  ssr: false,
  loading: () => <MapLoadingPlaceholder />,
})

interface MapSectionProps {
  hasRoute?: boolean
  hospital?: Hospital
  routes?: RouteOption[]
  selectedRouteType?: "fastest" | "safest"
  currentLocation?: {
    latitude: number
    longitude: number
  } | null
}

function MapLoadingPlaceholder() {
  return (
    <div className="flex h-full min-h-[400px] items-center justify-center rounded-xl border border-border bg-background">
      <div className="flex flex-col items-center gap-3 text-muted-foreground">
        <div className="animate-pulse">
          <div className="h-16 w-16 rounded-2xl bg-muted/30" />
        </div>
        <p className="text-sm">Loading map...</p>
      </div>
    </div>
  )
}

export function MapSection({
  hasRoute,
  hospital,
  routes,
  selectedRouteType = "fastest",
  currentLocation,
}: MapSectionProps) {
  const hasMapData = Boolean(currentLocation || (hasRoute && hospital && routes?.length))

  return (
    <Card className="flex h-full flex-col border-border bg-card/50 backdrop-blur-sm">
      <CardHeader className="flex flex-col gap-3 pb-4 sm:flex-row sm:items-center sm:justify-between">
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Map className="h-4 w-4 text-primary" />
          </div>
          Route Map
        </CardTitle>
        <div className="flex flex-wrap items-center gap-1">
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground">
            <Layers className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground">
            <Maximize2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="relative flex-1 p-4 pt-0">
        <div className="relative h-full min-h-[320px] overflow-hidden rounded-xl border border-border bg-background sm:min-h-[400px]">
          {hasMapData ? (
            <DynamicMapComponent
              hospital={hospital}
              routes={routes}
              selectedRouteType={selectedRouteType}
              currentLocation={currentLocation}
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="flex flex-col items-center gap-3 text-muted-foreground">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-dashed border-border bg-muted/30">
                  <Map className="h-8 w-8 text-muted-foreground/50" />
                </div>
                <p className="text-sm">Find Emergency Help Near Me</p>
                <p className="text-xs text-muted-foreground/70">Routes will display here</p>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
