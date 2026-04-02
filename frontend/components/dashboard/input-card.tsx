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
import { MapPin, Navigation, AlertTriangle, Loader2, Locate } from "lucide-react"

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
  isLoading?: boolean
  isLocating?: boolean
  onLocationClick?: () => void
}

export function InputCard({ onOptimize, isLoading, isLocating, onLocationClick }: InputCardProps) {
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

          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              className="flex-1 border-border hover:bg-primary/5"
              disabled={isLoading || isLocating}
              onClick={onLocationClick}
            >
              <Locate className={`mr-2 h-4 w-4 ${isLocating ? 'animate-pulse' : ''}`} />
              {isLocating ? 'Locating...' : 'My Location'}
            </Button>
            <Button
              type="submit"
              className="flex-1 bg-gradient-to-r from-primary to-primary/80 font-medium text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:shadow-xl hover:shadow-primary/30"
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
      </CardContent>
    </Card>
  )
}
