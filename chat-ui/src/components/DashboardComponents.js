import React from 'react';

const PortfolioOverview = ({ positions }) => {
  return (
    <div className="portfolio-overview">
      <h3>Portfolio Overview</h3>
      <div className="positions-grid">
        {positions.map((position, index) => (
          <div key={index} className="position-card">
            <h4>{position.asset}</h4>
            <p>Balance: {position.balance}</p>
            <p>Value: ${position.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const PriceChart = ({ data }) => {
  return (
    <div className="price-chart">
      <h3>Price Chart</h3>
      {/* Chart implementation would go here */}
    </div>
  );
};

const ProtocolPositions = ({ protocols }) => {
  return (
    <div className="protocol-positions">
      <h3>Protocol Positions</h3>
      <ul>
        {protocols.map((protocol, index) => (
          <li key={index}>
            {protocol.name}: {protocol.position}
          </li>
        ))}
      </ul>
    </div>
  );
};

export { PortfolioOverview, PriceChart, ProtocolPositions };
