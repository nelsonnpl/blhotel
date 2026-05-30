"use client";

import ReactECharts from "echarts-for-react";
import type { Photo } from "@/components/types";

type Props = { photos: Photo[] };

export default function PriceTrendChart({ photos }: Props) {
  const ordered = [...photos].reverse();
  const option = {
    animationDuration: 450,
    grid: { top: 22, left: 32, right: 18, bottom: 28 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: ordered.map((item) => new Date(item.scrapedAt).toLocaleDateString("es-ES", { day: "2-digit", month: "2-digit" })),
      axisLine: { lineStyle: { color: "#d1d5db" } },
      axisLabel: { color: "#6b7280" },
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      splitLine: { lineStyle: { color: "#eef2f7" } },
      axisLabel: {
        color: "#6b7280",
        formatter: (value: number) => `${Math.round(value)} €`,
      },
    },
    series: [
      {
        type: "line",
        smooth: true,
        data: ordered.map((item) => item.avgPricePerNight),
        lineStyle: { width: 3, color: "#c5112f" },
        itemStyle: { color: "#c5112f" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(197, 17, 47, 0.32)" },
              { offset: 1, color: "rgba(197, 17, 47, 0.02)" },
            ],
          },
        },
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 360, width: "100%" }} notMerge lazyUpdate />;
}
