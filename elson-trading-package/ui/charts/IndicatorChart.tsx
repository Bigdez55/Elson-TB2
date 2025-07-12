import React, { useEffect, useRef, useCallback } from 'react';
import { createChart, IChartApi, ISeriesApi, LineData } from 'lightweight-charts';

interface Indicator {
  name: string;
  data: LineData[];
  color: string;
}

interface IndicatorChartProps {
  indicators: Indicator[];
  width?: number;
  height?: number;
  overlay?: boolean;
  onIndicatorHover?: (value: number, time: number, name: string) => void;
}

const IndicatorChart: React.FC<IndicatorChartProps> = ({
  indicators,
  width = 800,
  height = 200,
  overlay = false,
  onIndicatorHover
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi>();
  const seriesRefs = useRef<Map<string, ISeriesApi<'Line'>>>(new Map());

  const handleCrosshairMove = useCallback((param: any) => {
    if (
      param.point === undefined ||
      !param.time ||
      param.point.x < 0 ||
      param.point.x > width ||
      param.point.y < 0 ||
      param.point.y > height
    ) {
      return;
    }

    // Get values for all indicators at crosshair position
    seriesRefs.current.forEach((series, name) => {
      const value = param.seriesPrices.get(series);
      if (value && onIndicatorHover) {
        onIndicatorHover(value as number, param.time as number, name);
      }
    });
  }, [onIndicatorHover, width, height]);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create and configure the chart
    const chart = createChart(chartContainerRef.current, {
      width,
      height,
      layout: {
        background: { color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      rightPriceScale: {
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        visible: !overlay,
        borderColor: '#2B2B43',
      },
    });

    // Create line series for each indicator
    indicators.forEach((indicator) => {
      const lineSeries = chart.addLineSeries({
        color: indicator.color,
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: true,
        crosshairMarkerVisible: true,
        overlay,
      });

      lineSeries.setData(indicator.data);
      seriesRefs.current.set(indicator.name, lineSeries);
    });

    // Handle hover events
    if (onIndicatorHover) {
      chart.subscribeCrosshairMove(handleCrosshairMove);
    }

    // Store chart reference
    chartRef.current = chart;

    // Cleanup
    return () => {
      chart.remove();
    };
  }, [width, height, overlay, indicators, handleCrosshairMove, onIndicatorHover]);


  return (
    <div className="relative">
      <div ref={chartContainerRef} className="indicator-chart" />
      <div className="absolute top-2 right-2 flex space-x-4">
        {indicators.map((indicator) => (
          <div key={indicator.name} className="flex items-center space-x-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: indicator.color }}
            />
            <span className="text-sm text-gray-400">{indicator.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default IndicatorChart;