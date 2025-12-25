import React from 'react';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

interface AllocationChartProps {
  data: {
    labels: string[];
    values: number[];
    colors: string[];
  };
  className?: string;
}

export const AllocationChart: React.FC<AllocationChartProps> = ({
  data,
  className = '',
}) => {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        data: data.values,
        backgroundColor: data.colors.map(color => color.replace('1)', '0.8)')),
        borderColor: data.colors,
        borderWidth: 1,
        hoverOffset: 5,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: 'rgba(17, 24, 39, 0.9)',
        titleFont: {
          size: 14,
        },
        bodyFont: {
          size: 13,
        },
        padding: 10,
        callbacks: {
          label: function(context: any) {
            return `${context.label}: ${context.parsed}%`;
          },
        },
      },
    },
  };

  return (
    <div className={`bg-gray-900 rounded-xl p-6 shadow-md ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-white">Asset Allocation</h3>
        <button className="text-purple-400 hover:text-purple-300 text-sm">
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </div>
      <div className="h-64 mb-4">
        <Doughnut data={chartData} options={options} />
      </div>
      <div className="grid grid-cols-1 gap-2">
        {data.labels.map((label, index) => (
          <div key={label} className="flex items-center justify-between">
            <div className="flex items-center">
              <div 
                className="w-3 h-3 rounded-full mr-2" 
                style={{ backgroundColor: data.colors[index] }}
              />
              <span className="text-gray-300 text-sm">{label}</span>
            </div>
            <span className="text-gray-300 text-sm">{data.values[index]}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};