import React from 'react';
import { render } from '@testing-library/react';
import { describe, test, vi, beforeEach } from 'vitest';
import CandlestickChart from './src/app/components/charts/CandlestickChart';
import IndicatorChart from './src/app/components/charts/IndicatorChart';
import VolumeChart from './src/app/components/charts/VolumeChart';

// Mock lightweight-charts
vi.mock('lightweight-charts', () => ({
  createChart: vi.fn().mockReturnValue({
    addSeries: vi.fn().mockReturnValue({
      setData: vi.fn(),
      priceFormatter: vi.fn(),
    }),
    subscribeCrosshairMove: vi.fn(),
    remove: vi.fn(),
  }),
}));

describe('Chart components', () => {
  test('CandlestickChart renders without crashing', () => {
    const mockData = [
      { time: 1, open: 10, high: 15, low: 8, close: 12 }
    ];
    render(<CandlestickChart data={mockData} />);
  });

  test('IndicatorChart renders without crashing', () => {
    const mockData = [
      { 
        name: 'MA', 
        data: [{ time: 1, value: 10 }], 
        color: 'red' 
      }
    ];
    render(<IndicatorChart indicators={mockData} />);
  });

  test('VolumeChart renders without crashing', () => {
    const mockData = [
      { time: 1, value: 1000 }
    ];
    render(<VolumeChart data={mockData} />);
  });
});