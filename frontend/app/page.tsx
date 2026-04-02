"use client"

import { useState } from "react"
import { Sidebar } from "@/components/dashboard/sidebar"
import { InputCard } from "@/components/dashboard/input-card"
import { MapSection } from "@/components/dashboard/map-section"
import { AnalyticsCards } from "@/components/dashboard/analytics-cards"
import { RouteComparison } from "@/components/dashboard/route-comparison"
import { Activity, Bell, Search, User, Menu, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { optimizeRoute, OptimizeRouteResponse, Hospital, RouteOption } from "@/lib/api"
import { toast } from "sonner"

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(false)
  const [isLocating, setIsLocating] = useState(false)
  const [hasRoute, setHasRoute] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [hospital, setHospital] = useState<Hospital | undefined>()
  const [routes, setRoutes] = useState<RouteOption[]>([])
  const [selectedRouteType, setSelectedRouteType] = useState<'fastest' | 'safest'>('fastest')
  const [error, setError] = useState<string | null>(null)
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

    try {
      const lat = parseFloat(data.latitude)
      const lon = parseFloat(data.longitude)

      if (isNaN(lat) || isNaN(lon)) {
        throw new Error("Invalid latitude or longitude")
      }

      if (lat < -90 || lat > 90) {
        throw new Error("Latitude must be between -90 and 90")
      }

      if (lon < -180 || lon > 180) {
        throw new Error("Longitude must be between -180 and 180")
      }

      const response = await optimizeRoute(lat, lon, data.emergencyType)
      
      setHospital(response.hospital)
      setRoutes(response.routes)
      setHasRoute(true)
      setSelectedRouteType('fastest')
      
      toast.success('Route optimized successfully!')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to optimize route'
      setError(message)
      toast.error(message)
      setHasRoute(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleGeolocation = async () => {
    if (!navigator.geolocation) {
      const message = 'Geolocation is not supported by your browser'
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

      // Auto-submit form with current location
      handleOptimize({
        latitude: latitude.toString(),
        longitude: longitude.toString(),
        emergencyType: 'medical',
      })
    } catch (err) {
      let message = 'Unable to get your location'
      
      if (err instanceof GeolocationPositionError) {
        switch (err.code) {
          case err.PERMISSION_DENIED:
            message = 'Location permission denied. Please enable geolocation in your browser.'
            break
          case err.POSITION_UNAVAILABLE:
            message = 'Location information is unavailable.'
            break
          case err.TIMEOUT:
            message = 'The request to get user location timed out. Try again.'
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
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      
      {/* Sidebar - hidden on mobile unless open */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 transition-transform duration-300`}>
        <Sidebar />
      </div>

      {/* Main Content */}
      <div className="lg:pl-64 transition-all duration-300">
        {/* Top Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/80 px-4 sm:px-6 backdrop-blur-md">
          <div className="flex items-center gap-4">
            {/* Mobile menu button */}
            <Button 
              variant="ghost" 
              size="icon" 
              className="lg:hidden text-muted-foreground"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="relative hidden sm:block">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="search"
                placeholder="Search routes, analytics..."
                className="w-64 border-input bg-input pl-10 transition-colors focus:border-primary"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Live Status */}
            <div className="hidden sm:flex items-center gap-2 rounded-full border border-success/30 bg-success/10 px-3 py-1.5">
              <Activity className="h-3.5 w-3.5 animate-pulse text-success" />
              <span className="text-xs font-medium text-success">System Online</span>
            </div>

            {/* Notifications */}
            <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-foreground">
              <Bell className="h-5 w-5" />
              <span className="absolute right-1.5 top-1.5 h-2 w-2 rounded-full bg-destructive" />
            </Button>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 px-2">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="/placeholder-avatar.jpg" alt="User" />
                    <AvatarFallback className="bg-primary text-primary-foreground">
                      JD
                    </AvatarFallback>
                  </Avatar>
                  <div className="hidden text-left sm:block">
                    <p className="text-sm font-medium text-foreground">John Doe</p>
                    <p className="text-xs text-muted-foreground">Dispatcher</p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>Settings</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="text-destructive">
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 sm:p-6">
          {/* Page Title */}
          <div className="mb-6">
            <h1 className="text-2xl font-bold tracking-tight text-foreground">
              Emergency Response Dashboard
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              AI-powered route optimization for faster emergency response times
            </p>
          </div>

          {/* Error Alert */}
          {error && (
            <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          {/* Dashboard Grid */}
          <div className="grid gap-6 lg:grid-cols-3">
            {/* Left Column - Input & Analytics */}
            <div className="space-y-6 lg:col-span-1">
              <InputCard 
                onOptimize={handleOptimize} 
                isLoading={isLoading}
                isLocating={isLocating}
                onLocationClick={handleGeolocation}
              />
              <AnalyticsCards 
                hospital={hospital}
                routes={routes}
                selectedRouteType={selectedRouteType}
                isLoading={isLoading}
              />
            </div>

            {/* Right Column - Map & Route Comparison */}
            <div className="space-y-6 lg:col-span-2">
              <MapSection 
                hasRoute={hasRoute}
                hospital={hospital}
                routes={routes}
                selectedRouteType={selectedRouteType}
                currentLocation={currentLocation}
              />
              <RouteComparison 
                hasData={hasRoute}
                routes={routes}
                selectedRouteType={selectedRouteType}
                onRouteTypeChange={setSelectedRouteType}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
