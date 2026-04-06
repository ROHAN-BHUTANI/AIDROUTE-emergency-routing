"use client"

import { useEffect, useMemo, useRef } from "react"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { RouteOption, Hospital } from "@/lib/api"

const isFiniteNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value)

const hasValidLatLng = (
  value: { latitude?: number; longitude?: number } | null | undefined
): value is { latitude: number; longitude: number } =>
  value != null && isFiniteNumber(value.latitude) && isFiniteNumber(value.longitude)

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
  showRiskOverlay?: boolean
  currentLocation?: {
    latitude: number
    longitude: number
  } | null
}

export default function MapComponent({
  hospital,
  routes = [],
  selectedRouteType = "fastest",
  showRiskOverlay = true,
  currentLocation,
}: MapComponentProps) {
  const mapRef = useRef<L.Map | null>(null)
  const routeLayersRef = useRef<L.Layer[]>([])
  const markerLayersRef = useRef<L.Layer[]>([])
  const animationRef = useRef<number | null>(null)
  const ambulanceMarkerRef = useRef<L.Marker | null>(null)
  const mapContainerRef = useRef<HTMLDivElement | null>(null)

  const validCurrentLocation = useMemo(
    () => (hasValidLatLng(currentLocation) ? currentLocation : null),
    [currentLocation]
  )

  const validHospital = useMemo(
    () =>
      hasValidLatLng(hospital)
        ? {
            latitude: hospital.latitude,
            longitude: hospital.longitude,
            name: hospital.name,
          }
        : null,
    [hospital]
  )

  useEffect(() => {
    if (mapRef.current) {
      return
    }

    if (!mapContainerRef.current) {
      return
    }

    const initialCenter = validCurrentLocation
      ? [validCurrentLocation.latitude, validCurrentLocation.longitude]
      : validHospital
        ? [validHospital.latitude, validHospital.longitude]
        : [0, 0]

    const map = L.map(mapContainerRef.current).setView(
      initialCenter as [number, number],
      validCurrentLocation || validHospital ? 13 : 2
    )

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    }).addTo(map)

    mapRef.current = map

    return () => {
      if (animationRef.current) {
        window.clearInterval(animationRef.current)
      }
      map.remove()
      mapRef.current = null
      routeLayersRef.current = []
      markerLayersRef.current = []
      ambulanceMarkerRef.current = null
    }
  }, [validCurrentLocation, validHospital])

  useEffect(() => {
    if (!mapRef.current) {
      return
    }

    const map = mapRef.current

    markerLayersRef.current.forEach((layer) => map.removeLayer(layer))
    markerLayersRef.current = []

    if (validHospital) {
      const hospitalMarker = L.marker([validHospital.latitude, validHospital.longitude], { icon: hospitalIcon })
        .addTo(map)
        .bindPopup(`<strong>${validHospital.name}</strong><br/>Hospital`)

      markerLayersRef.current.push(hospitalMarker)
    }

    if (validCurrentLocation) {
      const currentMarker = L.marker([validCurrentLocation.latitude, validCurrentLocation.longitude], { icon: defaultIcon })
        .addTo(map)
        .bindPopup(
          `<strong>Your Location</strong><br/>Lat: ${validCurrentLocation.latitude.toFixed(6)}<br/>Lng: ${validCurrentLocation.longitude.toFixed(6)}`
        )

      const locationCircle = L.circle([validCurrentLocation.latitude, validCurrentLocation.longitude], {
        color: "#3b82f6",
        fill: true,
        fillColor: "#3b82f6",
        fillOpacity: 0.12,
        radius: 250,
        weight: 2,
      }).addTo(map)

      markerLayersRef.current.push(currentMarker, locationCircle)
    }
  }, [validCurrentLocation, validHospital])

  // Update route visualization when routes or selectedRouteType changes
  useEffect(() => {
    if (!mapRef.current) return

    const map = mapRef.current

    routeLayersRef.current.forEach((layer) => map.removeLayer(layer))
    routeLayersRef.current = []
    if (animationRef.current) {
      window.clearInterval(animationRef.current)
      animationRef.current = null
    }
    if (ambulanceMarkerRef.current) {
      map.removeLayer(ambulanceMarkerRef.current)
      ambulanceMarkerRef.current = null
    }

    if (!routes.length) {
      if (validCurrentLocation) {
        map.setView([validCurrentLocation.latitude, validCurrentLocation.longitude], 14)
      } else if (validHospital) {
        map.setView([validHospital.latitude, validHospital.longitude], 13)
      }
      return
    }

    // Find the selected route
    const selectedRoute = routes.find((r) => r.type === selectedRouteType)
    if (!selectedRoute || !Array.isArray(selectedRoute.path)) return

    // Draw route polyline
    const pathLatLngs = selectedRoute.path
      .filter(([lat, lon]) => isFiniteNumber(lat) && isFiniteNumber(lon))
      .map(([lat, lon]) => [lat, lon] as [number, number])

    if (!pathLatLngs.length) {
      return
    }
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

    const routeLabel = L.marker(pathLatLngs[Math.floor(pathLatLngs.length / 2)], {
      interactive: false,
      icon: L.divIcon({
        className: "",
        html: `<div style="background:rgba(15,23,42,.8);border:1px solid rgba(34,197,94,.35);color:#d1fae5;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:600;">${selectedRouteType === "safest" ? "Safe Route" : "Priority Route"}</div>`,
      }),
    }).addTo(map)

    routeLayersRef.current.push(routeLabel)

    if (pathLatLngs.length > 0) {
      const [startLat, startLon] = pathLatLngs[0]
      const startMarker = L.marker([startLat, startLon], {
        icon: activeRouteIcon,
      })
        .addTo(map)
        .bindPopup(
          `<strong>Start Point</strong><br/>Distance: ${isFiniteNumber(selectedRoute.distance) ? selectedRoute.distance.toFixed(2) : "—"} km<br/>ETA: ${selectedRoute.eta} min`
        )

        routeLayersRef.current.push(startMarker)

      const riskCircleColor =
        selectedRoute.risk_level === "low"
          ? "#10b981"
          : selectedRoute.risk_level === "medium"
            ? "#f59e0b"
            : "#ef4444"

      if (showRiskOverlay) {
        const riskCircle = L.circle([startLat, startLon], {
          color: riskCircleColor,
          fill: true,
          fillColor: riskCircleColor,
          fillOpacity: 0.1,
          radius: 500,
          weight: 2,
        }).addTo(map)

        routeLayersRef.current.push(riskCircle)

        const riskZoneLabel = L.marker([startLat, startLon], {
          interactive: false,
          icon: L.divIcon({
            className: "",
            html: `<div style="background:rgba(127,29,29,.75);border:1px solid rgba(248,113,113,.45);color:#fee2e2;padding:3px 8px;border-radius:999px;font-size:10px;font-weight:700;">High Risk Zone</div>`,
          }),
        }).addTo(map)

        routeLayersRef.current.push(riskZoneLabel)

        // Mock heat-map feel using gradient risk bubbles along the route.
        pathLatLngs.forEach((point, index) => {
          const opacity = 0.08 + (index / Math.max(pathLatLngs.length, 1)) * 0.2
          const bubble = L.circle(point, {
            color: "#f97316",
            fillColor: "#fb923c",
            fillOpacity: Math.min(opacity, 0.26),
            radius: 140 + (index % 3) * 35,
            weight: 0,
          }).addTo(map)
          routeLayersRef.current.push(bubble)
        })
      }

      // Ambulance animation along route points.
      const ambulanceIcon = L.divIcon({
        className: "",
        html: `<div style="font-size:20px;line-height:1;filter:drop-shadow(0 0 6px rgba(59,130,246,.6));">🚑</div>`,
      })
      const ambulance = L.marker(pathLatLngs[0], { icon: ambulanceIcon }).addTo(map)
      ambulanceMarkerRef.current = ambulance

      let frame = 0
      animationRef.current = window.setInterval(() => {
        if (!ambulanceMarkerRef.current || !pathLatLngs.length) {
          return
        }
        frame = (frame + 1) % pathLatLngs.length
        ambulanceMarkerRef.current.setLatLng(pathLatLngs[frame])
      }, 800)
    }

    const bounds = L.latLngBounds(pathLatLngs.map((p) => L.latLng(p[0], p[1])))
    map.fitBounds(bounds, { padding: [50, 50] })
  }, [routes, selectedRouteType, showRiskOverlay, validCurrentLocation, validHospital])

  return (
    <div
      ref={mapContainerRef}
      className="h-full w-full"
      style={{ position: "relative" }}
    />
  )
}
