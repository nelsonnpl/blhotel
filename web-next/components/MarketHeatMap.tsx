"use client";

import { useEffect, useRef } from "react";
import maplibregl, { GeoJSONSource, Map } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { HeatPoint } from "@/components/types";

type Props = {
  points: HeatPoint[];
  selectedHotelName?: string;
};

export default function MarketHeatMap({ points, selectedHotelName }: Props) {
  const mapRef = useRef<Map | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://demotiles.maplibre.org/style.json",
      center: [-15.56, 27.76],
      zoom: 9,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-right");

    map.on("load", () => {
      map.addSource("hotels", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: [],
        },
      });

      map.addLayer({
        id: "hotels-heat",
        type: "heatmap",
        source: "hotels",
        maxzoom: 14,
        paint: {
          "heatmap-weight": ["interpolate", ["linear"], ["get", "intensity"], 0, 0, 1, 1],
          "heatmap-radius": ["interpolate", ["linear"], ["zoom"], 4, 12, 10, 28, 14, 44],
          "heatmap-opacity": 0.74,
          "heatmap-color": [
            "interpolate",
            ["linear"],
            ["heatmap-density"],
            0,
            "rgba(199, 35, 62, 0)",
            0.2,
            "rgba(199, 35, 62, 0.25)",
            0.4,
            "rgba(199, 35, 62, 0.45)",
            0.65,
            "rgba(197, 17, 47, 0.7)",
            1,
            "rgba(144, 8, 26, 0.95)",
          ],
        },
      });

      map.addLayer({
        id: "hotels-points",
        type: "circle",
        source: "hotels",
        minzoom: 8,
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 3, 13, 6],
          "circle-color": [
            "case",
            ["==", ["get", "hotelName"], selectedHotelName ?? ""],
            "#C5112F",
            "#1d4ed8",
          ],
          "circle-stroke-width": 1,
          "circle-stroke-color": "#fff",
        },
      });

      map.on("click", "hotels-points", (event) => {
        const feature = event.features?.[0];
        if (!feature || feature.geometry.type !== "Point") return;
        const coordinates = feature.geometry.coordinates as [number, number];
        const hotelName = String(feature.properties?.hotelName || "Hotel");
        const adr = Number(feature.properties?.avgPricePerNight || 0);
        new maplibregl.Popup({ closeButton: false, closeOnClick: true })
          .setLngLat(coordinates)
          .setHTML(`<strong>${hotelName}</strong><br/>ADR: ${new Intl.NumberFormat("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(adr)}`)
          .addTo(map);
      });
    });

    mapRef.current = map;

    return () => {
      mapRef.current?.remove();
      mapRef.current = null;
    };
  }, [selectedHotelName]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;
    const source = map.getSource("hotels") as GeoJSONSource | undefined;
    if (!source) return;

    const features = points
      .filter((point) => Number.isFinite(point.latitude) && Number.isFinite(point.longitude))
      .map((point) => ({
        type: "Feature" as const,
        properties: {
          hotelName: point.hotelName,
          avgPricePerNight: point.avgPricePerNight,
          intensity: point.intensity,
        },
        geometry: {
          type: "Point" as const,
          coordinates: [point.longitude, point.latitude],
        },
      }));

    source.setData({ type: "FeatureCollection", features });

    if (features.length) {
      const bounds = new maplibregl.LngLatBounds();
      features.forEach((feature) => bounds.extend(feature.geometry.coordinates as [number, number]));
      map.fitBounds(bounds, { padding: 42, maxZoom: 12, duration: 500 });
    }
  }, [points]);

  return <div ref={containerRef} className="h-[360px] w-full rounded-2xl border border-line" />;
}
