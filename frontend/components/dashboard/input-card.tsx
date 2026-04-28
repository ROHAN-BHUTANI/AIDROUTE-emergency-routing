"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { MapPin, Navigation, AlertTriangle, Loader2, Locate, Flame, Waves, Car } from "lucide-react"

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const emergencyTypes = [
  { value: "medical", label: "Medical Emergency" },
  { value: "fire", label: "Fire Emergency" },
  { value: "accident", label: "Traffic Accident" },
  { value: "flood", label: "Flood Emergency" },
  { value: "earthquake", label: "Earthquake" },
  { value: "landslide", label: "Landslide" },
]

interface InputCardProps {
  onOptimize: (data: {
    latitude: string
    longitude: string
    emergencyType: string
  }) => void
  onSimulate?: (type: string) => void
  isLoading?: boolean
  isLocating?: boolean
  onLocationClick?: () => void
}

export function InputCard({ onOptimize, onSimulate, isLoading, isLocating, onLocationClick }: InputCardProps) {
  const [latitude, setLatitude] = useState("")
  const [longitude, setLongitude] = useState("")
  const [emergencyType, setEmergencyType] = useState("")

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!latitude || !longitude || !emergencyType) {
      alert("Please fill in all fields")
      return
    }
    onOptimize({ latitude, longitude, emergencyType })
  }

  return (
    <Card className="border-border bg-card/50 backdrop-blur-sm">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg font-semibold">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
            <Navigation className="h-4 w-4 text-primary" />
          </div>
          Route Input
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="latitude" className="text-sm text-muted-foreground">
                Latitude
              </Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="latitude"
                  type="text"
                  placeholder="40.7128"
                  value={latitude}
                  onChange={(e) => setLatitude(e.target.value)}
                  className="border-input bg-input pl-10 transition-colors focus:border-primary"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="longitude" className="text-sm text-muted-foreground">
                Longitude
              </Label>
              <div className="relative">
                <MapPin className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="longitude"
                  type="text"
                  placeholder="-74.0060"
                  value={longitude}
                  onChange={(e) => setLongitude(e.target.value)}
                  className="border-input bg-input pl-10 transition-colors focus:border-primary"
                />
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="emergency-type" className="text-sm text-muted-foreground">
              Emergency Type
            </Label>
            <Select value={emergencyType} onValueChange={setEmergencyType}>
              <SelectTrigger className="border-input bg-input transition-colors focus:border-primary">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                  <SelectValue placeholder="Select emergency type" />
                </div>
              </SelectTrigger>
              <SelectContent>
                {emergencyTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="sticky bottom-2 z-10 -mx-1 mt-2 flex flex-col gap-2 rounded-xl border border-border/60 bg-background/80 p-2 backdrop-blur sm:static sm:z-auto sm:mx-0 sm:mt-0 sm:border-0 sm:bg-transparent sm:p-0 sm:backdrop-blur-none sm:flex-row">
            <Button
              type="button"
              variant="outline"
              className="h-11 w-full border-border hover:bg-primary/5 sm:flex-1"
              disabled={isLoading || isLocating}
              onClick={onLocationClick}
            >
              <Locate className={`mr-2 h-4 w-4 ${isLocating ? 'animate-pulse' : ''}`} />
              {isLocating ? 'Locating...' : 'My Location'}
            </Button>
            <Button
              type="submit"
              className="h-11 w-full bg-gradient-to-r from-primary to-primary/80 font-medium text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30 sm:flex-1"
              disabled={isLoading || isLocating}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Optimizing...
                </>
              ) : (
                <>
                  <Navigation className="mr-2 h-4 w-4" />
                  Optimize
                </>
              )}
            </Button>
          </div>
        </form>

        <div className="mt-8 space-y-3 pt-6 border-t border-border/40">
          <div className="flex items-center gap-2">
            <div className="h-1 w-1 rounded-full bg-destructive animate-pulse" />
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Disaster Simulation</h3>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button type="button" className="inline-flex items-center">
                    <AlertTriangle className="h-3 w-3 text-muted-foreground/50 cursor-help" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="right" className="max-w-[200px]">
                  <p className="text-xs">Injects real-time road blocks into the network to test AI rerouting and resiliency.</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex flex-col h-auto py-3 gap-1.5 border-destructive/20 hover:bg-destructive/5 hover:border-destructive/40 group"
              onClick={() => onSimulate?.('flood')}
            >
              <Waves className="h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
              <span className="text-[10px] font-medium">Flood</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex flex-col h-auto py-3 gap-1.5 border-destructive/20 hover:bg-destructive/5 hover:border-destructive/40 group"
              onClick={() => onSimulate?.('fire')}
            >
              <Flame className="h-4 w-4 text-orange-500 group-hover:scale-110 transition-transform" />
              <span className="text-[10px] font-medium">Fire</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex flex-col h-auto py-3 gap-1.5 border-destructive/20 hover:bg-destructive/5 hover:border-destructive/40 group"
              onClick={() => onSimulate?.('accident')}
            >
              <Car className="h-4 w-4 text-yellow-500 group-hover:scale-110 transition-transform" />
              <span className="text-[10px] font-medium">Crash</span>
            </Button>
          </div>
          <p className="text-[10px] leading-relaxed text-muted-foreground italic">
            * Simulates blocked road clusters to test AI rerouting capabilities.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
