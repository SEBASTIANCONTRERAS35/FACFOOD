// Mapa de CU con Leaflet + OpenStreetMap. Lo usan la vista 02 (puestos) y la 08 (ruta del repartidor).
import L from "leaflet";
import { useEffect } from "react";
import { CircleMarker, MapContainer, Marker, Polyline, TileLayer, Tooltip, useMap } from "react-leaflet";

export type Pin = { id: number | string; lat: number; lon: number; etiqueta: string; color?: "dorado" | "marino" };

const iconos = {
  dorado: crearIcono("#E8A82B"),
  marino: crearIcono("#0D1B33"),
};

function crearIcono(color: string) {
  const svg = `<svg width="34" height="34" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 22s-7-6.2-7-12a7 7 0 1 1 14 0c0 5.8-7 12-7 12z" fill="${color}" stroke="#0D1B33" stroke-width="1.2"/>
    <circle cx="12" cy="10" r="3" fill="#FFFFFF"/></svg>`;
  return L.divIcon({ html: svg, className: "pin-mapa", iconSize: [34, 34], iconAnchor: [17, 32] });
}

function Recentrar({ lat, lon }: { lat: number; lon: number }) {
  const mapa = useMap();
  useEffect(() => {
    mapa.setView([lat, lon]);
  }, [mapa, lat, lon]);
  return null;
}

export function Mapa(props: {
  centro: { lat: number; lon: number };
  pines?: Pin[];
  yo?: { lat: number; lon: number };
  ruta?: [number, number][];
  alto?: number;
  zoom?: number;
  onPin?: (id: Pin["id"]) => void;
}) {
  const { centro, pines = [], alto = 280, zoom = 16 } = props;
  return (
    <div className="mapa" style={{ height: alto }}>
      <MapContainer center={[centro.lat, centro.lon]} zoom={zoom} zoomControl={false} attributionControl style={{ height: "100%" }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        />
        <Recentrar lat={centro.lat} lon={centro.lon} />
        {props.ruta && <Polyline positions={props.ruta} pathOptions={{ color: "#0D1B33", weight: 5, dashArray: "10 7" }} />}
        {pines.map((p) => (
          <Marker
            key={p.id}
            position={[p.lat, p.lon]}
            icon={iconos[p.color ?? "dorado"]}
            eventHandlers={{ click: () => props.onPin?.(p.id) }}
            title={p.etiqueta}
          >
            <Tooltip direction="top" offset={[0, -28]}>{p.etiqueta}</Tooltip>
          </Marker>
        ))}
        {props.yo && (
          <CircleMarker
            center={[props.yo.lat, props.yo.lon]}
            radius={9}
            pathOptions={{ color: "#FFFFFF", weight: 3, fillColor: "#3373F2", fillOpacity: 1 }}
          />
        )}
      </MapContainer>
    </div>
  );
}
