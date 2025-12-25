// Chart components using react-chartjs-2
export { PortfolioChart } from './PortfolioChart';
export { AllocationChart } from './AllocationChart';
export { StockChart } from './StockChart';

// Legacy chart components temporarily disabled due to lightweight-charts compatibility issues
// export { default as RealTimePriceChart } from './RealTimePriceChart';
// export { default as SimplePriceChart } from './SimplePriceChart';
// export { default as VolumeChart } from './VolumeChart';
// export { default as TechnicalIndicatorsPanel, TechnicalIndicators } from './TechnicalIndicators';
// export { default as PriceWidget } from './PriceWidget';
// export { default as ChartExample } from './ChartExample';

// Type exports
export interface PriceData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface SimplePriceData {
  time: number;
  price: number;
}

export interface VolumeData {
  time: number;
  volume: number;
  direction?: 'up' | 'down';
}