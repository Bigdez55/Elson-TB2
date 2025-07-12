import React, { useEffect, useRef, useCallback } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts';

interface CandlestickChartProps {
  data: CandlestickData[];
  width?: number;
  height?: number;
  timeframe?: string;
  onCrosshairMove?: (price: number, time: number) => void;
}

const CandlestickChart: React.FC<CandlestickChartProps> = ({
  data,
  width = 800,
  height = 400,
  timeframe = '1h',
  onCrosshairMove
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi>();
  const seriesRef = useRef<ISeriesApi<'Candlestick'>>();

  const handleCrosshairMove = useCallback((param: any, candlestickSeries: any) => {
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

    const price = param.seriesPrices.get(candlestickSeries)?.value;
    if (price && onCrosshairMove) {
      onCrosshairMove(price as number, param.time as number);
    }
  }, [onCrosshairMove, width, height]);

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
      crosshair: {
        mode: 0,
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // Create the candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Set the data
    candlestickSeries.setData(data);

    // Handle crosshair movement
    if (onCrosshairMove) {
      chart.subscribeCrosshairMove((param) => {
        handleCrosshairMove(param, candlestickSeries);
      });
    }

    // Store references
    chartRef.current = chart;
    seriesRef.current = candlestickSeries;

    // Cleanup
    return () => {
      chart.remove();
    };
  }, [width, height, data, handleCrosshairMove, onCrosshairMove]);


  return (
    <div className="relative">
      <div ref={chartContainerRef} className="candlestick-chart" />
      <div className="absolute top-4 right-4 bg-gray-800 px-2 py-1 rounded text-sm text-gray-300">
        {timeframe}
      </div>
    </div>
  );
};

export default CandlestickChart;