import React from 'react';
import { Line } from 'react-chartjs-2';

const PriceChart = ({ data }) => {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Price',
        data: data.values,
        borderColor: 'rgba(75,192,192,1)',
        fill: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'day',
        },
      },
      y: {
        beginAtZero: false,
      },
    },
  };

  return (
    <div className="price-chart-container">
      <Line data={chartData} options={options} />
    </div>
  );
};

export default PriceChart;
