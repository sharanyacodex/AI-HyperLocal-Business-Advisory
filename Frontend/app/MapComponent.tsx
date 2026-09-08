"use client";

import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Circle,
} from "react-leaflet";

import L from "leaflet";
import "leaflet/dist/leaflet.css";

import { useMemo } from "react";

/* ================================
   COMPETITOR DATA TYPE
================================ */

interface Competitor {
  name: string;
  latitude: number;
  longitude: number;
  category?: string;
}

/* ================================
   MAP PROPS
================================ */

interface MapComponentProps {
  latitude: number;
  longitude: number;
  competitors: Competitor[];

  // Backend competitor count
  competitorCount?: number;
}

/* ================================
   MAP COMPONENT
================================ */

export default function MapComponent({
  latitude,
  longitude,
  competitors,
  competitorCount,
}: MapComponentProps) {
  /*
   * Create Leaflet icons only after the
   * component is running in the browser.
   *
   * This prevents Leaflet-related problems
   * in Next.js.
   */
  const userIcon = useMemo(() => {
    return L.divIcon({
      className: "",
      html: `
        <div style="
          font-size: 32px;
          line-height: 32px;
          text-align: center;
        ">
          📍
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32],
    });
  }, []);

  const competitorIcon = useMemo(() => {
    return L.divIcon({
      className: "",
      html: `
        <div style="
          font-size: 28px;
          line-height: 28px;
          text-align: center;
        ">
          🏪
        </div>
      `,
      iconSize: [28, 28],
      iconAnchor: [14, 28],
      popupAnchor: [0, -28],
    });
  }, []);

  /*
   * Use backend count when provided.
   * Otherwise use the number of competitor objects.
   */
  const totalCompetitors =
    typeof competitorCount === "number"
      ? competitorCount
      : competitors.length;

  return (
    <div className="w-full">

      {/* ================================
          MAP
      ================================= */}

      <div
        className="w-full overflow-hidden rounded-2xl border border-gray-200"
        style={{
          height: "500px",
        }}
      >
        <MapContainer
          center={[latitude, longitude]}
          zoom={12}
          scrollWheelZoom={true}
          style={{
            height: "100%",
            width: "100%",
          }}
        >

          {/* ================================
              OPENSTREETMAP TILES
          ================================= */}

          <TileLayer
            attribution="&copy; OpenStreetMap contributors"
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* ================================
              SELECTED LOCATION
          ================================= */}

          <Marker
            position={[
              latitude,
              longitude,
            ]}
            icon={userIcon}
          >
            <Popup>
              <strong>
                Selected Location
              </strong>

              <br />

              Your business search location
            </Popup>
          </Marker>

          {/* ================================
              10 KM SEARCH AREA
          ================================= */}

          <Circle
            center={[
              latitude,
              longitude,
            ]}
            radius={10000}
          />

          {/* ================================
              COMPETITOR SHOPS
          ================================= */}

          {Array.isArray(competitors) &&
            competitors.map((shop, index) => {

              /*
               * Ignore invalid coordinates.
               */

              if (
                !Number.isFinite(
                  Number(shop.latitude)
                ) ||
                !Number.isFinite(
                  Number(shop.longitude)
                )
              ) {
                return null;
              }

              const shopLatitude =
                Number(shop.latitude);

              const shopLongitude =
                Number(shop.longitude);

              return (
                <Marker
                  key={
                    `${shop.name}-${shopLatitude}-${shopLongitude}-${index}`
                  }
                  position={[
                    shopLatitude,
                    shopLongitude,
                  ]}
                  icon={competitorIcon}
                >
                  <Popup>
                    <strong>
                      {shop.name ||
                        "Nearby Business"}
                    </strong>

                    <br />

                    Category:{" "}
                    {shop.category ||
                      "Business"}
                  </Popup>
                </Marker>
              );
            })}

        </MapContainer>
      </div>

      {/* ================================
          MAP INFORMATION
      ================================= */}

      <div className="mt-4 flex flex-wrap justify-center gap-5 text-sm text-gray-600">

        {/* Selected Location */}

        <div className="flex items-center gap-2">
          <span className="text-xl">
            📍
          </span>

          <span>
            Selected Location
          </span>
        </div>

        {/* Competitor Shops */}

        <div className="flex items-center gap-2">
          <span className="text-xl">
            🏪
          </span>

          <span>
            Competitor Shops
          </span>
        </div>

        {/* 10 KM Search Area */}

        <div className="flex items-center gap-2">
          <span
            className="
              inline-block
              h-3
              w-3
              rounded-full
              border
              border-gray-400
            "
          />

          <span>
            10 km Search Area
          </span>
        </div>

      </div>

      {/* ================================
          TOTAL COMPETITOR SHOPS
      ================================= */}

      <div className="mt-4 rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">

        <p className="text-lg font-semibold text-gray-800">
          Total Competitor Shops ={" "}
          {totalCompetitors}
        </p>

      </div>

    </div>
  );
}