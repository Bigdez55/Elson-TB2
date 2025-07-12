import React, { useEffect, useRef, useCallback } from 'react';
import { createChart, IChartApi, ISeriesApi, HistogramData } from 'lightweight-charts';

interface VolumeChartProps {
  data: HistogramData[];
  width?: number;
  height?: number;
  onVolumeHover?: (volume: number, time: number) => void;
}

const VolumeChart: React.FC<VolumeChartProps> = ({
  data,
  width = 800,
  height = 200,
  onVolumeHover
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi>();
  const seriesRef = useRef<ISeriesApi<'Histogram'>>();

  const handleCrosshairMove = useCallback((param: any, volumeSeries: any) => {
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

    const volume = param.seriesPrices.get(volumeSeries)?.value;
    if (volume && onVolumeHover) {
      onVolumeHover(volume as number, param.time as number);
    }
  }, [onVolumeHover, width, height]);

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
        visible: true,
        borderColor: '#2B2B43',
      },
    });

    // Create the volume histogram series
    const volumeSeries = chart.addHistogramSeries({
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '', // Separate scale for volume
    });

    // Set the data
    volumeSeries.setData(data);

    // Handle hover events
    if (onVolumeHover) {
      chart.subscribeCrosshairMove((param) => {
        handleCrosshairMove(param, volumeSeries);
      });
    }

    // Store references
    chartRef.current = chart;
    seriesRef.current = volumeSeries;

    // Color the volumes based on price movement
    volumeSeries.priceFormatter = () => '';

    // Cleanup
    return () => {
      chart.remove();
    };
  }, [width, height, data, handleCrosshairMove, onVolumeHover]);


  return (
    <div className="relative">
      <div ref={chartContainerRef} className="volume-chart" />
      <div className="absolute top-2 left-2 text-sm text-gray-400">
        Volume
      </div>
    </div>
  );
};

export default VolumeChart;