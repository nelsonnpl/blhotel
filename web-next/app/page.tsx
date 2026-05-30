"use client";

import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";
import type { HeatPoint, Metrics, Photo, SnapshotRow, Target } from "@/components/types";
import { api, dateTime, eur } from "@/components/utils";

const MarketHeatMap = dynamic(() => import("@/components/MarketHeatMap"), { ssr: false });
const PriceTrendChart = dynamic(() => import("@/components/PriceTrendChart"), { ssr: false });

const DEFAULT_TARGET_NAME = "Gran Canaria (Sur)";
const DEFAULT_BOOKING_URL =
  "https://www.booking.com/searchresults.es.html?label=gog235jc-10CAEoggI46AdIClgDaEaIAQGYATO4ARfIAQzYAQPoAQH4AQGIAgGoAgG4AsSSyNAGwAIB0gIkZDIxZjM3ZTUtODFkYS00YzRkLWI2OGEtY2YxZjg4MWFkZDAz2AIB4AIB&aid=397594&ss=Sur+de+Gran+Canaria%2C+Espa%C3%B1a&ssne=Maspalomas&ssne_untouched=Maspalomas&lang=es&src=searchresults&dest_id=14200&dest_type=region&checkin=2026-07-06&checkout=2026-07-12&group_adults=2&no_rooms=1&group_children=0&nflt=mealplan%3D4%3Bht_id%3D204%3Bhotelfacility%3D433";

export default function Page() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [activeTargetId, setActiveTargetId] = useState<number | null>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [activePhotoId, setActivePhotoId] = useState<number | null>(null);
  const [rows, setRows] = useState<SnapshotRow[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [heatmap, setHeatmap] = useState<{ points: HeatPoint[] }>({ points: [] });
  const [heatmapPhotos, setHeatmapPhotos] = useState(6);
  const [status, setStatus] = useState("Conectando con backend Flask...");
  const [showCapture, setShowCapture] = useState(false);
  const [capture, setCapture] = useState({ checkIn: "2026-08-24", nights: 6, weeks: 4, limit: 40 });

  const activeTarget = useMemo(() => targets.find((target) => target.id === activeTargetId) ?? null, [targets, activeTargetId]);
  const activePhoto = useMemo(() => photos.find((photo) => photo.id === activePhotoId) ?? null, [photos, activePhotoId]);

  useEffect(() => {
    void boot();
  }, []);

  useEffect(() => {
    if (!activeTargetId) return;
    void loadPhotos(activeTargetId);
    void loadMetrics(activeTargetId);
  }, [activeTargetId]);

  useEffect(() => {
    if (!activeTargetId) return;
    void loadHeatmap(activeTargetId, heatmapPhotos);
  }, [activeTargetId, heatmapPhotos]);

  async function boot() {
    try {
      const data = await api<{ targets: Target[] }>("targets");
      setTargets(data.targets || []);
      if (data.targets?.length) {
        setActiveTargetId(data.targets[0].id);
      } else {
        setStatus("No hay mercados aún. Pulsa Capturar para crear la primera foto.");
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Error de conexión");
    }
  }

  async function loadPhotos(targetId: number) {
    const data = await api<{ photos: Photo[] }>(`photos/history?targetId=${targetId}&limit=24`);
    const photoRows = data.photos || [];
    setPhotos(photoRows);
    if (photoRows.length) {
      const photoId = activePhotoId && photoRows.some((photo) => photo.id === activePhotoId) ? activePhotoId : photoRows[0].id;
      setActivePhotoId(photoId);
      await loadPhotoDetail(photoId);
      setStatus(`Foto #${photoId} cargada.`);
    } else {
      setRows([]);
      setActivePhotoId(null);
    }
  }

  async function loadPhotoDetail(photoId: number) {
    const data = await api<{ rows: SnapshotRow[] }>(`photos/${photoId}`);
    setRows(data.rows || []);
  }

  async function loadMetrics(targetId: number) {
    const data = await api<Metrics>(`dashboard/metrics?targetId=${targetId}`);
    setMetrics(data);
  }

  async function loadHeatmap(targetId: number, photosWindow: number) {
    const data = await api<{ points: HeatPoint[] }>(`hotels/heatmap?targetId=${targetId}&photos=${photosWindow}`);
    setHeatmap({ points: data.points || [] });
  }

  function buildBookingUrl(baseUrl: string, checkIn: string, nights: number) {
    const url = new URL(baseUrl);
    const start = new Date(`${checkIn}T00:00:00`);
    const end = new Date(start);
    end.setDate(start.getDate() + nights);
    url.searchParams.set("checkin", start.toISOString().slice(0, 10));
    url.searchParams.set("checkout", end.toISOString().slice(0, 10));
    return url.toString();
  }

  function addWeeks(checkIn: string, offset: number) {
    const date = new Date(`${checkIn}T00:00:00`);
    date.setDate(date.getDate() + offset * 7);
    return date.toISOString().slice(0, 10);
  }

  async function runCapture() {
    setShowCapture(false);
    setStatus("Lanzando captura semanal...");
    try {
      let targetId = activeTargetId;
      const baseUrl = activeTarget?.url || DEFAULT_BOOKING_URL;
      for (let week = 0; week < capture.weeks; week += 1) {
        const checkIn = addWeeks(capture.checkIn, week);
        const url = buildBookingUrl(baseUrl, checkIn, capture.nights);
        const body = {
          targetId: targetId || undefined,
          targetName: activeTarget?.name || DEFAULT_TARGET_NAME,
          url,
          limit: capture.limit,
        };
        const result = await api<{ target: Target; snapshot: { id: number } }>("scrape/search", {
          method: "POST",
          body: JSON.stringify(body),
        });
        targetId = result.target.id;
      }
      const refreshed = await api<{ targets: Target[] }>("targets");
      setTargets(refreshed.targets || []);
      if (targetId) setActiveTargetId(targetId);
      setStatus("Captura completada correctamente.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Error en captura");
    }
  }

  const kpis = [
    { label: "Precio hab / noche", value: eur(metrics?.market?.avgPricePerNight) },
    { label: "Precio pers / noche", value: eur(metrics?.market?.avgPricePerPersonNight) },
    { label: "Rango ADR", value: `${eur(metrics?.market?.minPricePerNight)} - ${eur(metrics?.market?.maxPricePerNight)}` },
    {
      label: "Mapa cobertura",
      value: `${metrics?.locationCoverage?.pct ?? 0}%`,
      hint: `${metrics?.locationCoverage?.located ?? 0}/${metrics?.locationCoverage?.total ?? 0} hoteles`,
    },
  ];

  return (
    <div className="grid min-h-screen grid-cols-[260px_1fr] bg-page">
      <aside className="border-r border-line bg-white px-6 py-8">
        <div className="mb-8 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-riu text-xs font-black text-white">RIU</div>
          <div>
            <p className="text-lg font-bold">Revenue Pilot</p>
            <p className="text-xs font-semibold text-muted">Market Intelligence</p>
          </div>
        </div>
        <nav className="space-y-2 text-sm font-semibold">
          {[
            "Dashboard",
            "Área trabajo",
            "Capturas",
            "Mapa",
            "Explorador",
            "Settings",
          ].map((item, index) => (
            <button
              key={item}
              className={`w-full rounded-full px-4 py-2 text-left ${index === 0 ? "bg-riu text-white" : "text-slate-700 hover:bg-slate-100"}`}
              type="button"
            >
              {item}
            </button>
          ))}
        </nav>
      </aside>

      <main className="overflow-auto">
        <header className="sticky top-0 z-10 border-b border-line bg-white/90 px-8 py-4 backdrop-blur">
          <input
            className="h-11 w-full max-w-xl rounded-full border border-line bg-page px-4 text-sm outline-none focus:border-riu"
            placeholder="Buscar hotel, mercado o zona..."
          />
        </header>

        <section className="space-y-5 px-8 py-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-6xl font-bold leading-[1.02] tracking-tight">Dashboard general</h1>
              <p className="mt-3 text-lg text-muted">Benchmark competitivo, capturas semanales y señales accionables para Revenue Management.</p>
            </div>
            <button className="rounded-full bg-riu px-6 py-3 text-sm font-bold text-white shadow-soft" onClick={() => setShowCapture(true)} type="button">
              Capturar
            </button>
          </div>

          <div className="flex flex-wrap gap-3">
            <label className="rounded-full border border-line bg-white px-4 py-2 text-sm">
              <span className="mr-2 text-xs font-bold uppercase tracking-wider text-muted">Foto</span>
              <select
                className="bg-transparent font-semibold outline-none"
                value={activePhotoId ?? ""}
                onChange={async (event) => {
                  const id = Number(event.target.value);
                  setActivePhotoId(id);
                  await loadPhotoDetail(id);
                  setStatus(`Foto #${id} cargada.`);
                }}
              >
                {photos.map((photo) => (
                  <option key={photo.id} value={photo.id}>
                    Foto #{photo.id} · {dateTime(photo.scrapedAt)} · ADR {eur(photo.avgPricePerNight)}
                  </option>
                ))}
              </select>
            </label>

            <label className="rounded-full border border-line bg-white px-4 py-2 text-sm">
              <span className="mr-2 text-xs font-bold uppercase tracking-wider text-muted">Heatmap</span>
              <select
                className="bg-transparent font-semibold outline-none"
                value={heatmapPhotos}
                onChange={(event) => setHeatmapPhotos(Number(event.target.value))}
              >
                <option value={3}>Últimas 3 fotos</option>
                <option value={6}>Últimas 6 fotos</option>
                <option value={12}>Últimas 12 fotos</option>
              </select>
            </label>

            <button
              className="rounded-full border border-line bg-white px-5 py-2 text-sm font-semibold"
              type="button"
              onClick={async () => {
                if (!photos.length) return;
                setActivePhotoId(photos[0].id);
                await loadPhotoDetail(photos[0].id);
                setStatus(`Foto #${photos[0].id} cargada.`);
              }}
            >
              Ir a última foto
            </button>
          </div>

          <div className="rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-800">{status}</div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {kpis.map((kpi) => (
              <article key={kpi.label} className="rounded-2xl border border-line bg-card p-5 shadow-soft">
                <p className="text-sm font-semibold text-muted">{kpi.label}</p>
                <p className="mt-2 text-5xl font-bold tracking-tight">{kpi.value}</p>
                <p className="mt-2 text-sm text-muted">{kpi.hint ?? ""}</p>
              </article>
            ))}
          </div>

          <div className="grid gap-5 xl:grid-cols-[1.65fr_1fr]">
            <article className="rounded-2xl border border-line bg-card p-5 shadow-soft">
              <h2 className="text-3xl font-bold tracking-tight">Mapa de calor de precios</h2>
              <p className="mt-1 text-sm text-muted">MapLibre GL con intensidad de ADR por zona.</p>
              <div className="mt-4 heatmap-shell rounded-2xl p-1">
                <MarketHeatMap points={heatmap.points} selectedHotelName={rows[0]?.hotelName} />
              </div>
            </article>

            <article className="rounded-2xl border border-line bg-card p-5 shadow-soft">
              <h2 className="text-3xl font-bold tracking-tight">Evolución del mercado</h2>
              <p className="mt-1 text-sm text-muted">Apache ECharts para tendencia ADR.</p>
              <div className="mt-3">
                <PriceTrendChart photos={photos} />
              </div>
            </article>
          </div>

          <article className="rounded-2xl border border-line bg-card p-5 shadow-soft">
            <h2 className="text-2xl font-bold tracking-tight">Señales accionables</h2>
            <div className="mt-3 grid gap-3 md:grid-cols-2">
              {(metrics?.insights || []).slice(0, 6).map((insight, index) => (
                <div key={`${insight.title}-${index}`} className="rounded-xl border border-line bg-slate-50 p-4">
                  <p className="text-sm font-bold">{insight.title}</p>
                  <p className="mt-1 text-sm text-muted">{insight.message}</p>
                </div>
              ))}
              {(!metrics?.insights || !metrics.insights.length) && <p className="text-sm text-muted">Aún no hay señales disponibles.</p>}
            </div>
          </article>
        </section>
      </main>

      {showCapture && (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-900/45 p-4">
          <div className="w-full max-w-xl rounded-2xl border border-line bg-white p-6 shadow-soft">
            <h3 className="text-2xl font-bold">Configurar captura</h3>
            <p className="mt-1 text-sm text-muted">Define fechas y volumen de scraping semanal.</p>

            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              <label className="rounded-xl border border-line p-3 text-sm">
                <span className="block text-xs uppercase tracking-wide text-muted">Check-in</span>
                <input type="date" className="mt-1 w-full bg-transparent font-semibold outline-none" value={capture.checkIn} onChange={(event) => setCapture((prev) => ({ ...prev, checkIn: event.target.value }))} />
              </label>
              <label className="rounded-xl border border-line p-3 text-sm">
                <span className="block text-xs uppercase tracking-wide text-muted">Noches</span>
                <input type="number" min={1} max={30} className="mt-1 w-full bg-transparent font-semibold outline-none" value={capture.nights} onChange={(event) => setCapture((prev) => ({ ...prev, nights: Number(event.target.value) }))} />
              </label>
              <label className="rounded-xl border border-line p-3 text-sm">
                <span className="block text-xs uppercase tracking-wide text-muted">Semanas</span>
                <input type="number" min={1} max={26} className="mt-1 w-full bg-transparent font-semibold outline-none" value={capture.weeks} onChange={(event) => setCapture((prev) => ({ ...prev, weeks: Number(event.target.value) }))} />
              </label>
              <label className="rounded-xl border border-line p-3 text-sm">
                <span className="block text-xs uppercase tracking-wide text-muted">Hoteles</span>
                <input type="number" min={1} max={200} className="mt-1 w-full bg-transparent font-semibold outline-none" value={capture.limit} onChange={(event) => setCapture((prev) => ({ ...prev, limit: Number(event.target.value) }))} />
              </label>
            </div>

            <div className="mt-5 flex justify-end gap-2">
              <button type="button" className="rounded-full border border-line px-4 py-2 text-sm font-semibold" onClick={() => setShowCapture(false)}>
                Cancelar
              </button>
              <button type="button" className="rounded-full bg-riu px-5 py-2 text-sm font-bold text-white" onClick={() => void runCapture()}>
                Lanzar captura
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
