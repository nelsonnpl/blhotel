export type Target = {
  id: number;
  name: string;
  url: string;
};

export type Photo = {
  id: number;
  scrapedAt: string;
  capturedRows: number;
  avgPricePerNight: number;
  avgPricePerPersonNight: number;
  minPricePerNight: number;
  maxPricePerNight: number;
  comparableRows: number;
};

export type HeatPoint = {
  hotelKey: string;
  hotelName: string;
  latitude: number;
  longitude: number;
  avgPricePerNight: number;
  intensity: number;
  samples: number;
};

export type Metrics = {
  market?: {
    avgPricePerNight?: number;
    avgPricePerPersonNight?: number;
    minPricePerNight?: number;
    maxPricePerNight?: number;
  };
  locationCoverage?: {
    total: number;
    located: number;
    pct: number;
  };
  insights?: Array<{ title: string; message: string; severity: "info" | "warning" | "critical" }>;
};

export type SnapshotRow = {
  id: number;
  hotelName: string;
  roomType: string | null;
  rating: number | null;
  price: number | null;
  pricePerNight: number | null;
  pricePerPersonPerNight: number | null;
  checkIn: string | null;
  checkOut: string | null;
  latitude: number | null;
  longitude: number | null;
};
