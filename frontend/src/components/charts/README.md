# Real-Time Price Charts

A comprehensive set of React components for displaying real-time price charts with basic technical indicators for personal trading use.

## Components

### 1. RealTimePriceChart
Advanced candlestick chart with volume and moving averages.

**Features:**
- Real-time candlestick price display
- Volume histogram overlay
- Simple Moving Average (SMA) indicator
- Price change tracking
- Real-time updates with live indicator
- Crosshair interaction

**Usage:**
```tsx
import { RealTimePriceChart } from './components/charts';

<RealTimePriceChart
  symbol="AAPL"
  data={priceData}
  width={800}
  height={600}
  showVolume={true}
  showMA={true}
  maLength={20}
  onPriceUpdate={(price, time) => console.log('Price update:', price)}
/>
```

### 2. SimplePriceChart
Clean line chart for basic price display.

**Features:**
- Simple line chart display
- Price change tracking
- Hover interactions
- Configurable colors and styling
- Lightweight and fast

**Usage:**
```tsx
import { SimplePriceChart } from './components/charts';

<SimplePriceChart
  symbol="AAPL"
  data={simpleData}
  width={600}
  height={300}
  color="#2196F3"
  showGrid={true}
  onPriceHover={(price, time) => console.log('Hover:', price)}
/>
```

### 3. VolumeChart
Dedicated volume histogram chart.

**Features:**
- Volume bars with directional colors
- Up/down volume indication
- Hover interactions
- Configurable colors

**Usage:**
```tsx
import { VolumeChart } from './components/charts';

<VolumeChart
  data={volumeData}
  width={800}
  height={200}
  upColor="#26a69a"
  downColor="#ef5350"
/>
```

### 4. TechnicalIndicatorsPanel
Display panel for calculated technical indicators.

**Features:**
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Relative Strength Index (RSI)
- MACD (configurable)
- Bollinger Bands (configurable)

**Usage:**
```tsx
import { TechnicalIndicatorsPanel } from './components/charts';

<TechnicalIndicatorsPanel
  data={priceData}
  showSMA={true}
  showEMA={true}
  showRSI={true}
  smaLength={20}
  emaLength={12}
/>
```

### 5. PriceWidget
Compact price display widget for embedding.

**Features:**
- Compact design for dashboard use
- Real-time price updates
- Simple price change indication
- Easy integration
- Configurable update intervals

**Usage:**
```tsx
import { PriceWidget } from './components/charts';

<PriceWidget
  symbol="AAPL"
  width={400}
  height={200}
  updateInterval={5000}
/>
```

## Data Formats

### PriceData
```typescript
interface PriceData {
  time: number;      // Unix timestamp
  open: number;      // Opening price
  high: number;      // High price
  low: number;       // Low price
  close: number;     // Closing price
  volume: number;    // Trading volume
}
```

### SimplePriceData
```typescript
interface SimplePriceData {
  time: number;      // Unix timestamp
  price: number;     // Price value
}
```

### VolumeData
```typescript
interface VolumeData {
  time: number;              // Unix timestamp
  volume: number;            // Volume value
  direction?: 'up' | 'down'; // Price direction
}
```

## Technical Indicators

The `TechnicalIndicators` class provides static methods for calculating common indicators:

- **SMA (Simple Moving Average)**: `TechnicalIndicators.sma(data, period)`
- **EMA (Exponential Moving Average)**: `TechnicalIndicators.ema(data, period)`
- **RSI (Relative Strength Index)**: `TechnicalIndicators.rsi(data, period)`
- **MACD**: `TechnicalIndicators.macd(data, fast, slow, signal)`
- **Bollinger Bands**: `TechnicalIndicators.bollinger(data, period, stdDev)`

## Dependencies

- `lightweight-charts`: Professional financial charting library
- `react`: React framework
- `typescript`: TypeScript support

## Installation

1. Install the lightweight-charts dependency:
```bash
npm install lightweight-charts@^4.1.3
```

2. Import and use the components in your React application.

## Example Implementation

See `ChartExample.tsx` for a complete implementation example with mock data generation and real-time updates.

## Styling

The components use Tailwind CSS classes for styling. Dark theme support is built into the advanced charts, while simple charts use light themes by default.

## Performance Considerations

- Charts automatically limit data points for performance (typically 100 points)
- Real-time updates are throttled to prevent excessive re-renders
- Volume and technical indicators can be disabled to improve performance
- Use SimplePriceChart for lightweight implementations

## Customization

All components accept various props for customization:
- Dimensions (width/height)
- Colors
- Update intervals
- Feature toggles
- Event handlers

This charting system is designed for personal trading use and provides essential functionality without complex enterprise features.