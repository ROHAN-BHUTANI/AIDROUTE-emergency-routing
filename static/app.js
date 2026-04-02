(function () {
  const state = {
    map: null,
    mapLayerGroup: null,
    ambulanceMarker: null,
    animationTimer: null,
    etaTimer: null,
    latestResult: null,
    selectedRouteType: "fastest",
  };

  const dom = {
    form: document.getElementById("route-form"),
    latitudeInput: document.getElementById("latitude"),
    longitudeInput: document.getElementById("longitude"),
    emergencyTypeInput: document.getElementById("emergency_type"),
    submitBtn: document.getElementById("submit-btn"),
    locateBtn: document.getElementById("locate-btn"),
    status: document.getElementById("status"),
    routeSwitcher: document.getElementById("route-switcher"),
    switchButtons: Array.from(document.querySelectorAll(".switch-btn")),

    hospitalValue: document.getElementById("hospital-value"),
    routeValue: document.getElementById("route-value"),
    riskValue: document.getElementById("risk-value"),
    etaValue: document.getElementById("eta-value"),
    distanceValue: document.getElementById("distance-value"),
    bandValue: document.getElementById("band-value"),
    explanationValue: document.getElementById("explanation-value"),
    recommendationValue: document.getElementById("recommendation-value"),
  };

  const api = {
    async optimizeRoute(payload) {
      const response = await fetch("/optimize-route", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      let data;
      try {
        data = await response.json();
      } catch (_error) {
        throw new Error("Server returned an invalid JSON payload.");
      }

      if (!response.ok) {
        throw new Error(data.error || "Route optimization request failed.");
      }

      if (!data.hospital || !Array.isArray(data.routes)) {
        throw new Error("Response schema mismatch: missing hospital/routes.");
      }

      return data;
    },
  };

  const ui = {
    setStatus(message, variant) {
      dom.status.textContent = message;
      dom.status.classList.remove("is-error", "is-success");
      if (variant === "error") dom.status.classList.add("is-error");
      if (variant === "success") dom.status.classList.add("is-success");
    },

    resetDashboard() {
      dom.hospitalValue.textContent = "-";
      dom.routeValue.textContent = "-";
      dom.riskValue.textContent = "-";
      dom.etaValue.textContent = "-";
      dom.distanceValue.textContent = "-";
      dom.bandValue.textContent = "-";
      dom.explanationValue.textContent = "-";
      dom.recommendationValue.textContent = "-";
      dom.bandValue.classList.remove("risk-low", "risk-medium", "risk-high");
      dom.routeSwitcher.hidden = true;
    },

    normalizeRiskLevel(level) {
      const value = String(level || "").trim().toLowerCase();
      if (value === "high") return { text: "High", css: "risk-high" };
      if (value === "medium" || value === "moderate") return { text: "Medium", css: "risk-medium" };
      return { text: "Low", css: "risk-low" };
    },

    setRiskLevel(level) {
      const normalized = ui.normalizeRiskLevel(level);
      dom.bandValue.classList.remove("risk-low", "risk-medium", "risk-high");
      dom.bandValue.classList.add(normalized.css);
      dom.bandValue.textContent = normalized.text;
    },

    updateRouteSwitcher(activeType) {
      dom.switchButtons.forEach((btn) => {
        const isActive = btn.dataset.route === activeType;
        btn.classList.toggle("active", isActive);
      });
    },

    renderMetrics(result, route) {
      dom.hospitalValue.textContent = `${result.hospital.name} (${result.hospital.lat}, ${result.hospital.lon})`;
      dom.routeValue.textContent = route.path
        .map((point) => `${Number(point[0]).toFixed(4)}, ${Number(point[1]).toFixed(4)}`)
        .join(" -> ");
      dom.riskValue.textContent = Number(route.risk_score).toFixed(2);
      dom.etaValue.textContent = `${route.eta} min`;
      dom.distanceValue.textContent = `${Number(route.distance).toFixed(2)} km`;
      dom.explanationValue.textContent = buildExplanation(route);
      dom.recommendationValue.textContent = route.recommendation || "No recommendation provided.";
      ui.setRiskLevel(route.risk_level);
      dom.routeSwitcher.hidden = false;
      ui.updateRouteSwitcher(route.type);
    },
  };

  const mapModule = {
    init(center) {
      if (state.map) return;

      state.map = L.map("route-map", { zoomControl: true }).setView(center, 12);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(state.map);

      state.mapLayerGroup = L.layerGroup().addTo(state.map);
    },

    clearAnimation() {
      if (state.animationTimer) {
        clearInterval(state.animationTimer);
        state.animationTimer = null;
      }
      if (state.etaTimer) {
        clearInterval(state.etaTimer);
        state.etaTimer = null;
      }
      state.ambulanceMarker = null;
    },

    interpolate(startPoint, endPoint, t) {
      return [
        startPoint[0] + (endPoint[0] - startPoint[0]) * t,
        startPoint[1] + (endPoint[1] - startPoint[1]) * t,
      ];
    },

    riskCircleRadius(riskScore) {
      const baseRadius = 380;
      const bounded = Math.min(Math.max(Number(riskScore) || 0, 0), 10);
      return baseRadius + bounded * 80;
    },

    startAmbulanceAnimation(routePath, etaMinutes) {
      if (!state.mapLayerGroup || routePath.length < 2) return;

      mapModule.clearAnimation();

      const ambulanceIcon = L.divIcon({
        className: "ambulance-icon",
        html: "🚑",
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      });

      state.ambulanceMarker = L.marker(routePath[0], { icon: ambulanceIcon }).addTo(state.mapLayerGroup);

      const totalSegments = routePath.length - 1;
      const totalSeconds = Math.max(Number(etaMinutes || 0) * 60, totalSegments);
      let elapsed = 0;
      let remaining = totalSeconds;

      state.animationTimer = setInterval(() => {
        elapsed += 1;
        const progress = Math.min(elapsed / totalSeconds, 1);
        const scaled = progress * totalSegments;
        const segmentIndex = Math.min(Math.floor(scaled), totalSegments - 1);
        const segmentT = Math.min(scaled - segmentIndex, 1);

        const currentPoint = mapModule.interpolate(
          routePath[segmentIndex],
          routePath[segmentIndex + 1],
          segmentT
        );

        if (state.ambulanceMarker) {
          state.ambulanceMarker.setLatLng(currentPoint);
        }

        if (progress >= 1) {
          clearInterval(state.animationTimer);
          state.animationTimer = null;
        }
      }, 1000);

      state.etaTimer = setInterval(() => {
        remaining = Math.max(remaining - 1, 0);
        dom.etaValue.textContent = remaining > 0 ? `${Math.ceil(remaining / 60)} min` : "Arrived";
        if (remaining === 0) {
          clearInterval(state.etaTimer);
          state.etaTimer = null;
        }
      }, 1000);
    },

    showUserLocation(latitude, longitude) {
      const userPoint = [latitude, longitude];
      mapModule.init(userPoint);
      mapModule.clearAnimation();
      state.mapLayerGroup.clearLayers();

      L.marker(userPoint)
        .bindPopup("Your current location")
        .addTo(state.mapLayerGroup)
        .openPopup();

      state.map.setView(userPoint, 13);
    },

    render(payload, result, route) {
      const userPoint = [payload.latitude, payload.longitude];
      const hospitalPoint = [result.hospital.lat, result.hospital.lon];
      const routePath = Array.isArray(route.path) && route.path.length > 1 ? route.path : [userPoint, hospitalPoint];

      mapModule.init(userPoint);
      mapModule.clearAnimation();
      state.mapLayerGroup.clearLayers();

      L.marker(userPoint).bindPopup("Incident Source").addTo(state.mapLayerGroup);
      L.marker(hospitalPoint).bindPopup(result.hospital.name || "Nearest Hospital").addTo(state.mapLayerGroup);

      const routeColor = route.type === "safest" ? "#16a34a" : "#2563eb";
      L.polyline(routePath, {
        color: routeColor,
        weight: 5,
        opacity: 0.9,
      }).addTo(state.mapLayerGroup);

      const riskRadius = mapModule.riskCircleRadius(route.risk_score);
      L.circle(userPoint, {
        radius: riskRadius,
        color: "#ef4444",
        fillColor: "#ef4444",
        fillOpacity: 0.11,
        weight: 2,
      }).addTo(state.mapLayerGroup);

      state.map.fitBounds(L.latLngBounds(routePath).pad(0.24));
      mapModule.startAmbulanceAnimation(routePath, route.eta);
    },
  };

  function getPayloadFromForm() {
    const payload = {
      latitude: Number(dom.latitudeInput.value),
      longitude: Number(dom.longitudeInput.value),
      emergency_type: dom.emergencyTypeInput.value,
    };

    if (!Number.isFinite(payload.latitude) || !Number.isFinite(payload.longitude)) {
      throw new Error("Latitude and longitude must be valid numeric values.");
    }
    return payload;
  }

  function setBusyState(isBusy) {
    dom.submitBtn.disabled = isBusy;
    if (dom.locateBtn) {
      dom.locateBtn.disabled = isBusy;
    }
  }

  function geolocationErrorMessage(error) {
    if (!error || typeof error.code !== "number") {
      return "Unable to fetch location. Please enter coordinates manually.";
    }

    switch (error.code) {
      case error.PERMISSION_DENIED:
        return "Location permission denied. Please allow access or enter coordinates manually.";
      case error.POSITION_UNAVAILABLE:
        return "Location unavailable right now. Check GPS/network and try again.";
      case error.TIMEOUT:
        return "Location request timed out. Please retry or enter coordinates manually.";
      default:
        return "Unexpected geolocation error. Please enter coordinates manually.";
    }
  }

  function getCurrentPosition() {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error("Geolocation is not supported in this browser."));
        return;
      }

      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 12000,
        maximumAge: 30000,
      });
    });
  }

  function buildExplanation(route) {
    const level = String(route.risk_level || "Low");
    if (level.toLowerCase() === "high") {
      return "High traffic detected in central zone, alternate route recommended.";
    }
    if (level.toLowerCase() === "medium") {
      return "Moderate congestion observed. Keep monitoring traffic advisories.";
    }
    return "Low congestion corridor detected for current dispatch path.";
  }

  function getRouteByType(result, type) {
    const preferred = result.routes.find((route) => route.type === type);
    if (preferred) return preferred;
    return result.routes[0] || null;
  }

  function setActiveRoute(type) {
    if (!state.latestResult) return;
    state.selectedRouteType = type;
    const selectedRoute = getRouteByType(state.latestResult, type);
    if (!selectedRoute) return;

    ui.renderMetrics(state.latestResult, selectedRoute);
    mapModule.render(state.latestResult.payload, state.latestResult, selectedRoute);
  }

  async function optimizeFromPayload(payload) {
    mapModule.clearAnimation();
    ui.resetDashboard();
    setBusyState(true);
    ui.setStatus("Computing optimized emergency routes...", "");

    try {
      const result = await api.optimizeRoute(payload);
      result.payload = payload;
      state.latestResult = result;

      setActiveRoute(state.selectedRouteType);
      ui.setStatus("Route optimization complete. Switch between fastest and safest plans.", "success");
    } catch (error) {
      ui.setStatus(`Error: ${error.message}`, "error");
    } finally {
      setBusyState(false);
    }
  }

  async function onSubmit(event) {
    event.preventDefault();

    let payload;
    try {
      payload = getPayloadFromForm();
    } catch (error) {
      ui.setStatus(error.message, "error");
      return;
    }

    await optimizeFromPayload(payload);
  }

  async function onLocateClick() {
    setBusyState(true);
    ui.setStatus("Fetching your current location...", "");

    try {
      const position = await getCurrentPosition();
      const latitude = Number(position.coords.latitude.toFixed(6));
      const longitude = Number(position.coords.longitude.toFixed(6));

      dom.latitudeInput.value = latitude;
      dom.longitudeInput.value = longitude;

      mapModule.showUserLocation(latitude, longitude);
      ui.setStatus("Location captured. Sending coordinates to backend...", "");

      await optimizeFromPayload({
        latitude,
        longitude,
        emergency_type: dom.emergencyTypeInput.value,
      });
    } catch (error) {
      const message = error && typeof error.code === "number"
        ? geolocationErrorMessage(error)
        : error.message;
      ui.setStatus(message, "error");
      setBusyState(false);
    }
  }

  function bindEvents() {
    dom.form.addEventListener("submit", onSubmit);
    if (dom.locateBtn) {
      dom.locateBtn.addEventListener("click", onLocateClick);
    }

    dom.switchButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const routeType = button.dataset.route;
        if (!routeType) return;
        setActiveRoute(routeType);
      });
    });
  }

  function bootstrap() {
    ui.resetDashboard();
    bindEvents();
    ui.setStatus("Tip: use 'Use My Current Location' for one-click live routing.", "");
  }

  bootstrap();
})();
