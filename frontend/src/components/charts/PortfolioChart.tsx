import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface PortfolioChartProps {
  data: {
    labels: string[];
    portfolio: number[];
    benchmark: number[];
  };
  timeframe?: '1D' | '1W' | '1M' | '3M' | '1Y' | 'All';
  onTimeframeChange?: (timeframe: string) => void;
  className?: string;
}

export const PortfolioChart: React.FC<PortfolioChartProps> = ({
  data,
  timeframe = '1W',
  onTimeframeChange,
  className = '',
}) => {
  const timeframes = ['1D', '1W', '1M', '3M', '1Y', 'All'];

  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Portfolio Value',
        data: data.portfolio,
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        borderColor: 'rgba(139, 92, 246, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(139, 92, 246, 1)',
        pointBorderColor: '#fff',
        pointRadius: 4,
        pointHoverRadius: 6,
        tension: 0.3,
        fill: true,
      },
      {
        label: 'S&P 500',
        data: data.benchmark,
        borderColor: 'rgba(156, 163, 175, 0.7)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(156, 163, 175, 0.7)',
        pointBorderColor: '#fff',
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.3,
        borderDash: [5, 5],
        fill: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
        labels: {
          color: '#e2e8f0',
          font: {
            size: 12,
          },
          boxWidth: 12,
        },
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        borderColor: 'rgba(139, 92, 246, 0.5)',
        borderWidth: 1,
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        padding: 10,
        displayColors: false,
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: $${context.parsed.y.toLocaleString()}`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
          drawBorder: false,
        },
        ticks: {
          color: '#9ca3af',
        },
      },
      y: {
        grid: {
          color: 'rgba(75, 85, 99, 0.2)',
          drawBorder: false,
        },
        ticks: {
          color: '#9ca3af',
          callback: function(value: any) {
            return '$' + value.toLocaleString();
          },
        },
        beginAtZero: false,
      },
    },
  };

  return (
    <div className={`bg-gray-900 rounded-xl p-6 shadow-md ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-white">Portfolio Performance</h3>
        <div className="flex space-x-2">
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange?.(tf)}
              className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                timeframe === tf
                  ? 'bg-purple-800 text-purple-200'
                  : 'bg-gray-800 text-gray-300 hover:bg-purple-800 hover:text-purple-200'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>
      <div className="h-80">
        <Line data={chartData} options={options} />
      </div>
    </div>
  );
};