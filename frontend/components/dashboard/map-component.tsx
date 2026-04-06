"use client"

import { useEffect, useRef } from "react"
import L from "leaflet"
import { RouteOption, Hospital } from "@/lib/api"

const defaultIcon = L.icon({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const activeRouteIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

const hospitalIcon = L.icon({
  iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
})

interface MapComponentProps {
  hospital?: Hospital
  routes?: RouteOption[]
  selectedRouteType?: "fastest" | "safest"
  currentLocation?: {
    latitude: number
    longitude: number
  } | null
}

export default function MapComponent({
  hospital,
  routes = [],
  selectedRouteType = "fastest",
  currentLocation,
}: MapComponentProps) {
  const mapRef = useRef<L.Map | null>(null)
  const routeLayersRef = useRef<L.Layer[]>([])
  const markerLayersRef = useRef<L.Layer[]>([])
  const mapContainerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    if (mapRef.current) {
      return
    }

    if (!mapContainerRef.current) {
      return
    }

    const initialCenter = currentLocation
      ? [currentLocation.latitude, currentLocation.longitude]
      : hospital
        ? [hospital.latitude, hospital.longitude]
        : [0, 0]

    const map = L.map(mapContainerRef.current).setView(
      initialCenter as [number, number],
      currentLocation || hospital ? 13 : 2
    )

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map)

    mapRef.current = map

    return () => {
      map.remove()
      mapRef.current = null
      routeLayersRef.current = []
      markerLayersRef.current = []
    }
  }, [currentLocation, hospital])

  useEffect(() => {
    if (!mapRef.current) {
      return
    }

    const map = mapRef.current

    markerLayersRef.current.forEach((layer) => map.removeLayer(layer))
    markerLayersRef.current = []

    if (hospital) {
      const hospitalMarker = L.marker([hospital.latitude, hospital.longitude], { icon: hospitalIcon })
        .addTo(map)
        .bindPopup(`<strong>${hospital.name}</strong><br/>Hospital`)

      markerLayersRef.current.push(hospitalMarker)
    }

    if (currentLocation) {
      const currentMarker = L.marker([currentLocation.latitude, currentLocation.longitude], { icon: defaultIcon })
        .addTo(map)
        .bindPopup(
          `<strong>Your Location</strong><br/>Lat: ${currentLocation.latitude.toFixed(6)}<br/>Lng: ${currentLocation.longitude.toFixed(6)}`
        )

      const locationCircle = L.circle([currentLocation.latitude, currentLocation.longitude], {
        color: "#3b82f6",
        fill: true,
        fillColor: "#3b82f6",
        fillOpacity: 0.12,
        radius: 250,
        weight: 2,
      }).addTo(map)

      markerLayersRef.current.push(currentMarker, locationCircle)
    }
  }, [currentLocation, hospital])

  // Update route visualization when routes or selectedRouteType changes
  useEffect(() => {
    if (!mapRef.current) return

    const map = mapRef.current

    routeLayersRef.current.forEach((layer) => map.removeLayer(layer))
    routeLayersRef.current = []

    if (!routes.length) {
      if (currentLocation) {
        map.setView([currentLocation.latitude, currentLocation.longitude], 14)
      } else if (hospital) {
        map.setView([hospital.latitude, hospital.longitude], 13)
      }
      return
    }

    // Find the selected route
    const selectedRoute = routes.find((r) => r.type === selectedRouteType)
    if (!selectedRoute) return

    // Draw route polyline
    const pathLatLngs = selectedRoute.path.map(([lat, lon]) => [lat, lon] as [number, number])
    const polylineColor =
      selectedRouteType === "fastest"
        ? "#3b82f6" // blue
        : "#10b981" // green

    const polyline = L.polyline(pathLatLngs, {
      color: polylineColor,
      weight: 4,
      opacity: 0.8,
      lineCap: "round",
      lineJoin: "round",
    }).addTo(map)

    routeLayersRef.current.push(polyline)

    if (selectedRoute.path.length > 0) {
      const startPoint = selectedRoute.path[0]
      const startMarker = L.marker([startPoint[0], startPoint[1]], {
        icon: activeRouteIcon,
      })
        .addTo(map)
        .bindPopup(
          `<strong>Start Point</strong><br/>Distance: ${selectedRoute.distance.toFixed(2)} km<br/>ETA: ${selectedRoute.eta} min`
        )

        routeLayersRef.current.push(startMarker)

      const riskCircleColor =
        selectedRoute.risk_level === "low"
          ? "#10b981"
          : selectedRoute.risk_level === "medium"
            ? "#f59e0b"
            : "#ef4444"

      const riskCircle = L.circle([startPoint[0], startPoint[1]], {
        color: riskCircleColor,
        fill: true,
        fillColor: riskCircleColor,
        fillOpacity: 0.1,
        radius: 500, // 500 meters
        weight: 2,
      }).addTo(map)

      routeLayersRef.current.push(riskCircle)
    }

    const bounds = L.latLngBounds(pathLatLngs.map((p) => L.latLng(p[0], p[1])))
    map.fitBounds(bounds, { padding: [50, 50] })
  }, [routes, selectedRouteType, currentLocation, hospital])

  return (
    <div
      ref={mapContainerRef}
      className="h-full w-full"
      style={{ position: "relative" }}
    />
  )
}
