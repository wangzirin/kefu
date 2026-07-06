import type { EChartsOption } from "echarts";
import { BarChart, LineChart, RadarChart } from "echarts/charts";
import { GridComponent, LegendComponent, RadarComponent, TooltipComponent } from "echarts/components";
import { init, use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";

use([BarChart, LineChart, RadarChart, GridComponent, LegendComponent, RadarComponent, TooltipComponent, CanvasRenderer]);

export function OpsDashboardChart({
  option,
  ariaLabel,
  className = ""
}: {
  option: EChartsOption;
  ariaLabel: string;
  className?: string;
}) {
  const chartRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!chartRef.current) {
      return;
    }

    const chart = init(chartRef.current, undefined, { renderer: "canvas" });
    chart.setOption(option, true);

    const resize = () => chart.resize();
    const resizeObserver =
      typeof ResizeObserver === "undefined"
        ? null
        : new ResizeObserver(() => {
            resize();
          });

    resizeObserver?.observe(chartRef.current);
    window.addEventListener("resize", resize);

    return () => {
      resizeObserver?.disconnect();
      window.removeEventListener("resize", resize);
      chart.dispose();
    };
  }, [option]);

  return <div ref={chartRef} className={`ops-chart ${className}`.trim()} role="img" aria-label={ariaLabel} />;
}
