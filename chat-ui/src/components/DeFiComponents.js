import React from 'react';

const DeFiActionButton = ({ action, onClick }) => {
  return (
    <button 
      className="defi-action-button"
      onClick={onClick}
    >
      {action}
    </button>
  );
};

const TransactionPreview = ({ details }) => {
  return (
    <div className="transaction-preview">
      <h3>Transaction Preview</h3>
      <pre>{JSON.stringify(details, null, 2)}</pre>
    </div>
  );
};

const RiskIndicator = ({ level }) => {
  const colorMap = {
    low: 'green',
    medium: 'orange',
    high: 'red',
    critical: 'darkred'
  };

  return (
    <div className="risk-indicator" style={{ backgroundColor: colorMap[level] }}>
      Risk Level: {level}
    </div>
  );
};

export { DeFiActionButton, TransactionPreview, RiskIndicator };
