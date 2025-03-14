import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Wallet, RefreshCw, X, AlertCircle, Check, ChevronRight, UserCircle, Info } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './index.css';

const BACKEND_ROUTE = 'http://localhost:8081/api/routes/chat/'

// Available wallet types for connection
const WALLET_TYPES = {
  METAMASK: 'metamask',
  WALLETCONNECT: 'walletconnect',
  COINBASE: 'coinbase',
  LEDGER: 'ledger',
  TEE: 'tee' // Built-in TEE wallet
};

// Wallet Connection Component
const WalletConnection = ({ onConnect, connectedWallet, onDisconnect, isOnboarding = false }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(isOnboarding ? true : false);
  const [connecting, setConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  
  const connectWallet = async (walletType) => {
    setConnecting(true);
    setConnectionError(null);
    
    try {
      // In a real implementation, this would use actual wallet providers
      // For now, we'll simulate connections with a timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Get a mock address based on wallet type
      const mockAddress = getMockAddress(walletType);
      
      onConnect({
        type: walletType,
        address: mockAddress,
        chainId: '0x13',  // Flare network
        isConnected: true
      });
      
      // Close the menu after successful connection
      setIsMenuOpen(false);
    } catch (error) {
      console.error('Wallet connection error:', error);
      setConnectionError('Failed to connect wallet. Please try again.');
    } finally {
      setConnecting(false);
    }
  };
  
  const getMockAddress = (walletType) => {
    // Generate deterministic mock addresses for each wallet type
    const addresses = {
      [WALLET_TYPES.METAMASK]: '0x71C7656EC7ab88b098defB751B7401B5f6d8976F',
      [WALLET_TYPES.WALLETCONNECT]: '0x2B5AD5c4795c026514f8317c7a215E218DcCD6cF',
      [WALLET_TYPES.COINBASE]: '0x6813Eb9362372EEF6200f3b1dbC3f819671cBA69',
      [WALLET_TYPES.LEDGER]: '0x1efF47bc3a10a45D4B230B5d10E37751FE6AA718',
      [WALLET_TYPES.TEE]: '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'
    };
    return addresses[walletType] || '0x0000000000000000000000000000000000000000';
  };
  
  const handleDisconnect = () => {
    onDisconnect();
  };
  
  return (
    <div className="wallet-connection">
      {connectedWallet ? (
        <div className="connected-wallet">
          <span className="wallet-address">
            <Check size={16} className="connected-icon" />
            {connectedWallet.address.substring(0, 6)}...{connectedWallet.address.substring(38)}
          </span>
          <button className="disconnect-button" onClick={handleDisconnect}>
            <X size={16} />
          </button>
        </div>
      ) : (
        <div className="wallet-dropdown">
          <button 
            className="connect-wallet-button" 
            onClick={() => setIsMenuOpen(!isMenuOpen)}
          >
            <Wallet size={16} />
            Connect Wallet
          </button>
          
          {isMenuOpen && (
            <div className="wallet-menu">
              <button 
                className="wallet-option" 
                onClick={() => connectWallet(WALLET_TYPES.METAMASK)}
                disabled={connecting}
              >
                <img 
                  src="https://metamask.io/images/metamask-fox.svg" 
                  alt="MetaMask" 
                  className="wallet-icon"
                />
                MetaMask
                {connecting && <RefreshCw size={16} className="loading-icon" />}
              </button>
              
              <button 
                className="wallet-option" 
                onClick={() => connectWallet(WALLET_TYPES.WALLETCONNECT)}
                disabled={connecting}
              >
                <img 
                  src="https://walletconnect.com/images/walletconnect-logo.svg" 
                  alt="WalletConnect" 
                  className="wallet-icon"
                />
                WalletConnect
                {connecting && <RefreshCw size={16} className="loading-icon" />}
              </button>
              
              <button 
                className="wallet-option" 
                onClick={() => connectWallet(WALLET_TYPES.LEDGER)}
                disabled={connecting}
              >
                <img 
                  src="https://www.ledger.com/wp-content/uploads/2021/04/ledger_picto_onlyone_blue.svg" 
                  alt="Ledger" 
                  className="wallet-icon"
                />
                Ledger
                {connecting && <RefreshCw size={16} className="loading-icon" />}
              </button>
              
              <button 
                className="wallet-option" 
                onClick={() => connectWallet(WALLET_TYPES.TEE)}
                disabled={connecting}
              >
                <img 
                  src="https://flare.network/wp-content/uploads/2021/02/FLR_favicon.png" 
                  alt="TEE Wallet" 
                  className="wallet-icon"
                />
                TEE Wallet
                {connecting && <RefreshCw size={16} className="loading-icon" />}
              </button>
              
              {connectionError && (
                <div className="connection-error">
                  <AlertCircle size={16} />
                  {connectionError}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Onboarding component for new users
const Onboarding = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [userName, setUserName] = useState('');
  const [connectedWallet, setConnectedWallet] = useState(null);
  
  const steps = [
    {
      title: "Welcome to FlareTrade",
      description: "Your AI-powered DeFi companion on the Flare Network.",
      type: "welcome"
    },
    {
      title: "What's your name?",
      description: "We'll use this to personalize your experience.",
      type: "name"
    },
    {
      title: "Connect your wallet",
      description: "Connect your wallet to start using FlareTrade.",
      type: "wallet"
    },
    {
      title: "How FlareTrade Works",
      description: "Learn how to make the most of your DeFi AI assistant.",
      type: "guide"
    }
  ];
  
  const handleWalletConnect = (wallet) => {
    setConnectedWallet(wallet);
    if (currentStep === 2) { // If we're on the wallet step
      nextStep();
    }
  };
  
  const handleWalletDisconnect = () => {
    setConnectedWallet(null);
  };
  
  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      // Complete onboarding
      onComplete({ userName, connectedWallet });
    }
  };
  
  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };
  
  const handleNameSubmit = (e) => {
    e.preventDefault();
    if (userName.trim()) {
      nextStep();
    }
  };
  
  // Render step content based on type
  const renderStepContent = () => {
    const step = steps[currentStep];
    
    switch (step.type) {
      case "welcome":
        return (
          <div className="welcome-screen">
            <div className="logo-container">
              <img src="/logo-dark.svg" alt="FlareTrade Logo" className="onboarding-logo" />
            </div>
            <h1 className="welcome-title">Welcome to FlareTrade</h1>
            <p className="welcome-description">
              Your AI-driven DeFi companion that helps you navigate the Flare ecosystem with ease. 
              FlareTrade transforms your natural language commands into secure DeFi operations.
            </p>
            <button className="primary-button" onClick={nextStep}>
              Get Started <ChevronRight size={18} />
            </button>
          </div>
        );
        
      case "name":
        return (
          <div className="name-input-screen">
            <div className="icon-container">
              <UserCircle size={48} className="step-icon" />
            </div>
            <h2>What should we call you?</h2>
            <p>We'll use this to personalize your FlareTrade experience</p>
            
            <form onSubmit={handleNameSubmit} className="name-form">
              <input 
                type="text" 
                value={userName}
                onChange={e => setUserName(e.target.value)}
                placeholder="Enter your name"
                className="name-input"
                autoFocus
              />
              <button 
                type="submit" 
                className="primary-button"
                disabled={!userName.trim()}
              >
                Continue <ChevronRight size={18} />
              </button>
            </form>
          </div>
        );
        
      case "wallet":
        return (
          <div className="wallet-connect-screen">
            <div className="icon-container">
              <Wallet size={48} className="step-icon" />
            </div>
            <h2>Connect Your Wallet</h2>
            <p>Connect your wallet to interact with the Flare ecosystem</p>
            
            <div className="wallet-connect-container">
              <WalletConnection 
                onConnect={handleWalletConnect}
                connectedWallet={connectedWallet}
                onDisconnect={handleWalletDisconnect}
                isOnboarding={true}
              />
            </div>
            
            {connectedWallet && (
              <button className="primary-button" onClick={nextStep}>
                Continue <ChevronRight size={18} />
              </button>
            )}
            
            <button className="skip-button" onClick={nextStep}>
              Skip for now
            </button>
          </div>
        );
        
      case "guide":
        return (
          <div className="guide-screen">
            <div className="icon-container">
              <Info size={48} className="step-icon" />
            </div>
            <h2>How FlareTrade Works</h2>
            
            <div className="feature-grid">
              <div className="feature-card">
                <h3>Natural Language Commands</h3>
                <p>Simply tell Artemis what you want to do in plain English, like "Swap 10 FLR for USDC" or "Check my balance"</p>
              </div>
              
              <div className="feature-card">
                <h3>Risk Assessment</h3>
                <p>Every transaction is analyzed for risk, giving you confidence in your DeFi operations</p>
              </div>
              
              <div className="feature-card">
                <h3>Portfolio Management</h3>
                <p>Track your assets and get insights on your DeFi positions across the Flare ecosystem</p>
              </div>
              
              <div className="feature-card">
                <h3>Secure by Design</h3>
                <p>Built with TEE protection, your keys and transactions are secured by hardware-level encryption</p>
              </div>
            </div>
            
            <button className="primary-button" onClick={nextStep}>
              Start Using FlareTrade <ChevronRight size={18} />
            </button>
          </div>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="onboarding-container">
      {/* Progress indicator */}
      <div className="progress-indicator">
        {steps.map((step, index) => (
          <div 
            key={index} 
            className={`progress-step ${index <= currentStep ? 'active' : ''}`}
            onClick={() => index < currentStep && setCurrentStep(index)}
          >
            <div className="step-number">{index + 1}</div>
            <div className="step-label">{step.title}</div>
          </div>
        ))}
      </div>
      
      <div className="step-content">
        {renderStepContent()}
      </div>
      
      {/* Navigation buttons */}
      <div className="step-navigation">
        {currentStep > 0 && (
          <button className="back-button" onClick={prevStep}>
            Back
          </button>
        )}
      </div>
    </div>
  );
};

const ChatInterface = () => {
  const [showOnboarding, setShowOnboarding] = useState(true);
  // eslint-disable-next-line no-unused-vars
  const [isDemoMode, setIsDemoMode] = useState(true); // Set demo mode for hackathon presentation
  const [userData, setUserData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [pendingTransaction, setPendingTransaction] = useState(null);
  const [connectedWallet, setConnectedWallet] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Initialize messages when onboarding completes
  useEffect(() => {
    if (userData) {
      const greeting = `Hi${userData.userName ? ' ' + userData.userName : ''}! 👋 I'm Artemis, your Copilot for Flare, ready to help you with operations like generating wallets, sending tokens, and executing token swaps. \n\n⚠️ While I aim to be accurate, never risk funds you can't afford to lose.`;
      
      setMessages([
        { text: greeting, type: 'bot' }
      ]);
      
      // If user connected wallet during onboarding, set it
      if (userData.connectedWallet) {
        setConnectedWallet(userData.connectedWallet);
      }
    }
  }, [userData]);

  const handleSendMessage = async (text) => {
    try {
      console.log('Sending message to:', BACKEND_ROUTE);
      
      // Include wallet information if connected
      const payload = { 
        message: text,
        wallet: connectedWallet ? {
          address: connectedWallet.address,
          type: connectedWallet.type,
          chainId: connectedWallet.chainId
        } : null
      };
      
      // Set demo mode flag for hackathon demonstration
      // This allows us to run without all backend dependencies installed
      payload.demo_mode = true;
      
      console.log('Request payload:', JSON.stringify(payload));
      
      const response = await fetch(BACKEND_ROUTE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(payload),
        credentials: 'omit', // Don't send cookies
        mode: 'cors' // Explicitly request CORS
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error:', errorText, 'Status:', response.status);
        throw new Error(`API error: ${response.status} ${errorText}`);
      }

      console.log('Response received');
      const data = await response.json();
      console.log('Response data:', data);
      
      // Check for transaction-related keywords in the response that might require confirmation
      const confirmationKeywords = [
        'Transaction Preview:', 
        'Type CONFIRM to proceed', 
        'confirmation required', 
        'Please confirm',
        'Awaiting confirmation',
        'successfully executed',
        'Risk Assessment:'
      ];
      
      const shouldAwaitConfirmation = confirmationKeywords.some(keyword => 
        data.response.includes(keyword)) || data.requires_confirmation === true;
      
      if (shouldAwaitConfirmation) {
        setAwaitingConfirmation(true);
        setPendingTransaction(text);
      }
      
      // Check if response includes a transaction result with risk assessment
      if (data.response.includes('Risk Assessment:') || data.response.includes('Risk Level:')) {
        // The DeFi command handler has already formatted the response with risk information
        return data.response;
      }
      
      // Format additional risk assessment data if present but not already in response
      let responseText = data.response;
      if (data.risk_assessment && !responseText.includes('Risk Assessment')) {
        const { risk_level, risk_factors, warnings, recommendations } = data.risk_assessment;
        const riskColor = getRiskLevelColor(risk_level || 'medium');
        
        let riskDetails = `\n\n**Risk Assessment**\n\n`;
        riskDetails += `**Risk Level:** <span style="color:${riskColor}">${(risk_level || 'UNKNOWN').toUpperCase()}</span>\n\n`;
        
        // Include risk factors if available
        if (risk_factors && risk_factors.length > 0) {
          riskDetails += `**Risk Factors:**\n`;
          risk_factors.forEach(factor => {
            const factorColor = getRiskLevelColor(factor.level || 'medium');
            riskDetails += `- <span style="color:${factorColor}">${factor.name}:</span> ${factor.description}\n`;
          });
          riskDetails += '\n';
        }
        
        if (warnings && warnings.length > 0) {
          riskDetails += `**Warnings:**\n`;
          warnings.forEach(warning => {
            riskDetails += `- ⚠️ ${warning}\n`;
          });
          riskDetails += '\n';
        }
        
        if (recommendations && recommendations.length > 0) {
          riskDetails += `**Recommendations:**\n`;
          recommendations.forEach(rec => {
            riskDetails += `- 💡 ${rec}\n`;
          });
        }
        
        responseText += riskDetails;
      }
      
      // Format transaction hash as a link if present
      if (data.transaction_hash) {
        const explorerUrl = `https://coston2-explorer.flare.network/tx/${data.transaction_hash}`;
        responseText = responseText.replace(
          data.transaction_hash,
          `[${data.transaction_hash.substring(0, 8)}...${data.transaction_hash.substring(62)}](${explorerUrl})`
        );
      }
      
      return responseText;
    } catch (error) {
      console.error('Error:', error);
      // Make the error details available in the UI
      return `Sorry, there was an error processing your request: ${error.message}. Please try again.`;
    }
  };

    const handleConnectWallet = useCallback((wallet) => {
    setConnectedWallet(wallet);
    // Announce the connection to the chat
    setMessages(prev => [
      ...prev,
      { 
        text: `Connected to wallet ${wallet.type}: ${wallet.address.substring(0, 6)}...${wallet.address.substring(38)}`, 
        type: 'system' 
      }
    ]);
  }, []);
  
  const handleDisconnectWallet = useCallback(() => {
    const walletType = connectedWallet?.type || 'wallet';
    setConnectedWallet(null);
    // Announce the disconnection to the chat
    setMessages(prev => [
      ...prev,
      { text: `Disconnected from ${walletType}`, type: 'system' }
    ]);
  }, [connectedWallet]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputText.trim() || isLoading) return;

    const messageText = inputText.trim();
    setInputText('');
    setIsLoading(true);
    setMessages(prev => [...prev, { text: messageText, type: 'user' }]);

    try {
      // Handle transaction confirmation
      if (awaitingConfirmation) {
        if (messageText.toUpperCase() === 'CONFIRM') {
          setAwaitingConfirmation(false);
          
          // Show temporary confirmation message
          setMessages(prev => [...prev, { 
            text: '⏳ Processing your transaction...', 
            type: 'system' 
          }]);
          
          const response = await handleSendMessage(pendingTransaction);
          
          // Replace the temporary message with the actual response
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages.pop(); // Remove the temporary message
            return [...newMessages, { text: response, type: 'bot' }];
          });
        } else {
          setAwaitingConfirmation(false);
          setPendingTransaction(null);
          setMessages(prev => [...prev, { 
            text: 'Transaction cancelled. How else can I help you?', 
            type: 'bot' 
          }]);
        }
      } else {
        // Handle DeFi keyword detection
        const defiKeywords = [
          'swap', 'trade', 'exchange', 'buy', 'sell', 'transfer', 'send', 
          'stake', 'unstake', 'deposit', 'withdraw', 'borrow', 'supply',
          'repay', 'liquidity', 'yield', 'farm', 'harvest', 'claim',
          'bridge', 'lend', 'pool', 'token', 'flr', 'sfin', 'usdc', 'usdt',
          'sparkdex', 'kinetic', 'cyclo', 'raindex', 'flare', 'ftso'
        ];
        
        // Check if message contains DeFi keywords but no wallet is connected
        const containsDefiKeyword = defiKeywords.some(keyword => 
          messageText.toLowerCase().includes(keyword));
          
        if (containsDefiKeyword && !connectedWallet) {
          // Prompt user to connect wallet first
          setMessages(prev => [...prev, { 
            text: '⚠️ You need to connect a wallet before performing DeFi operations. Please connect a wallet using the button in the top right corner.', 
            type: 'bot' 
          }]);
          
          // In demo mode, also provide a hint about the capabilities
          if (isDemoMode) {
            setTimeout(() => {
              setMessages(prev => [...prev, { 
                text: 'FlareTrade is running in demo mode for this hackathon presentation. You can connect any wallet to explore DeFi capabilities without executing actual blockchain transactions. Try commands like "Swap 100 FLR for USDC" after connecting a wallet.', 
                type: 'system' 
              }]);
            }, 1000);  // Show this message after a short delay
          }
        } else {
          // Process the message normally
          try {
            const response = await handleSendMessage(messageText);
            setMessages(prev => [...prev, { text: response, type: 'bot' }]);
          } catch (error) {
            console.error('API error:', error);
            
            // If in demo mode and the backend fails, simulate a response
            if (isDemoMode && containsDefiKeyword && connectedWallet) {
              // Generate a simulated DeFi response for demo purposes
              const simulatedResponse = generateDemoResponse(messageText);
              setMessages(prev => [...prev, { text: simulatedResponse, type: 'bot' }]);
            } else {
              throw error; // Re-throw for the outer catch handler
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in submit handler:', error);
      setMessages(prev => [...prev, { 
        text: `Sorry, there was an error processing your request: ${error.message}. Please try again.`, 
        type: 'bot' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function to get color based on risk level
  const getRiskLevelColor = (riskLevel) => {
    const riskColors = {
      'low': '#4CAF50',      // Green
      'medium': '#FF9800',   // Orange
      'high': '#F44336',     // Red
      'critical': '#9C27B0', // Purple
      'unknown': '#757575'   // Gray
    };
    return riskColors[(riskLevel || 'unknown').toLowerCase()] || '#757575'; // Default gray
  };
  
  // Helper function to get emoji based on risk level
  // eslint-disable-next-line no-unused-vars
  const getRiskLevelEmoji = (riskLevel) => {
    const riskEmojis = {
      'low': '🟢',       // Green circle
      'medium': '🟠',    // Orange circle
      'high': '🔴',      // Red circle
      'critical': '⛔',   // No entry
      'unknown': '⚪'     // White circle
    };
    return riskEmojis[(riskLevel || 'unknown').toLowerCase()] || '⚪'; // Default white
  };
  
  // Generate demo responses for DeFi operations when backend is unavailable
  const generateDemoResponse = (message) => {
    const msg = message.toLowerCase();
    let response = "";
    
    // Generate appropriate demo responses based on message content
    if (msg.includes('swap') || msg.includes('exchange') || msg.includes('trade')) {
      // Extract token amounts and pairs if possible
      const tokenMatches = msg.match(/\d+\s*([a-z]+)\s*(?:to|for)\s*([a-z]+)/i);
      const amount = msg.match(/\d+/) ? msg.match(/\d+/)[0] : '100';
      const fromToken = tokenMatches ? tokenMatches[1].toUpperCase() : 'FLR';
      const toToken = tokenMatches ? tokenMatches[2].toUpperCase() : 'USDC';
      
      response = `I'll help you swap ${amount} ${fromToken} for ${toToken} using SparkDEX.\n\n`;
      response += `**Transaction Preview:**\n`;
      response += `- Sending: ${amount} ${fromToken}\n`;
      response += `- Receiving: ~${(amount * 0.85).toFixed(2)} ${toToken} (after fees)\n`;
      response += `- Slippage: 0.5%\n`;
      response += `- Protocol: SparkDEX\n\n`;
      response += `**Risk Assessment**\n\n`;
      response += `**Risk Level:** <span style="color:#FF9800">MEDIUM</span>\n\n`;
      response += `**Risk Factors:**\n`;
      response += `- <span style="color:#FF9800">Price Impact:</span> This transaction has a medium price impact of 1.2%\n`;
      response += `- <span style="color:#4CAF50">Slippage Protection:</span> Slippage protection is enabled with a 0.5% limit\n\n`;
      response += `**Warnings:**\n`;
      response += `- ⚠️ The ${toToken} price has been volatile in the last 24 hours\n\n`;
      response += `**Recommendations:**\n`;
      response += `- 💡 Consider splitting this transaction into smaller amounts to reduce price impact\n`;
      response += `- 💡 Verify the current price on another source before proceeding\n\n`;
      response += `Type CONFIRM to proceed with this transaction or any other text to cancel.`;
    } 
    else if (msg.includes('stake') || msg.includes('delegat')) {
      const amount = msg.match(/\d+/) ? msg.match(/\d+/)[0] : '100';
      const token = msg.includes('flr') ? 'FLR' : 'SFIN';
      
      response = `I'll help you stake ${amount} ${token} with Kinetic.\n\n`;
      response += `**Transaction Preview:**\n`;
      response += `- Staking: ${amount} ${token}\n`;
      response += `- Protocol: Kinetic\n`;
      response += `- Annual Yield: ~5.2%\n`;
      response += `- Unbonding Period: 14 days\n\n`;
      response += `**Risk Assessment**\n\n`;
      response += `**Risk Level:** <span style="color:#4CAF50">LOW</span>\n\n`;
      response += `**Risk Factors:**\n`;
      response += `- <span style="color:#4CAF50">Protocol Risk:</span> Kinetic has been audited and operational for over 2 years\n`;
      response += `- <span style="color:#FF9800">Liquidity Lock:</span> Your tokens will be locked for the unbonding period\n\n`;
      response += `**Recommendations:**\n`;
      response += `- 💡 Consider diversifying your stake across multiple validators\n\n`;
      response += `Type CONFIRM to proceed with this transaction or any other text to cancel.`;
    }
    else if (msg.includes('portfolio') || msg.includes('balance') || msg.includes('holdings')) {
      response = `Here's your current portfolio overview:\n\n`;
      response += `**Wallet Balance:**\n`;
      response += `- FLR: 2,450.75\n`;
      response += `- USDC: 1,200.50\n`;
      response += `- SFIN: 15.32\n`;
      response += `- cEUR: 500.00\n\n`;
      response += `**DeFi Positions:**\n`;
      response += `- SparkDEX FLR-USDC LP: 450.25 ($620.50)\n`;
      response += `- Kinetic Staked FLR: 1,000.00 ($350.00)\n`;
      response += `- Cyclo Lending Pool: 500 USDC ($500.00)\n\n`;
      response += `**Total Portfolio Value:** $3,620.75`;
    }
    else {
      response = `I understand you're interested in DeFi operations. Currently, FlareTrade is running in demo mode for the hackathon. `;
      response += `I can help with the following operations:\n\n`;
      response += `- **Token Swaps:** Try "Swap 100 FLR for USDC"\n`;
      response += `- **Staking:** Try "Stake 100 FLR with Kinetic"\n`;
      response += `- **Portfolio Overview:** Try "Show me my portfolio"\n\n`;
      response += `What would you like to do?`;
    }
    
    return response;
  };
  
  // Custom components for ReactMarkdown
  const MarkdownComponents = {
    // Override paragraph to remove default margins
    p: ({ children }) => <span className="inline">{children}</span>,
    // Style code blocks
    code: ({ node, inline, className, children, ...props }) => (
      inline ? 
        <code className="bg-gray-200 rounded px-1 py-0.5 text-sm">{children}</code> :
        <pre className="bg-gray-200 rounded p-2 my-2 overflow-x-auto">
          <code {...props} className="text-sm">{children}</code>
        </pre>
    ),
    // Support HTML in spans with specific styles
    span: ({ node, ...props }) => <span {...props} />,
    // Style links
    a: ({ node, children, ...props }) => (
      <a {...props} className="text-pink-600 hover:underline">{children}</a>
    )
  };

  const handleOnboardingComplete = (userData) => {
    setShowOnboarding(false);
    setUserData(userData);
  };
  
  if (showOnboarding) {
    return <Onboarding onComplete={handleOnboardingComplete} />;
  }

  return (
    <div className="flex flex-col h-screen bg-gray-100">
      <div className="flex flex-col h-full max-w-4xl mx-auto w-full shadow-lg bg-white">
        {/* Header with gradient background */}
        <div className="bg-gradient-to-r from-pink-600 to-purple-600 text-white p-4 flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">Artemis</h1>
            <p className="text-sm opacity-80">DeFAI Copilot for Flare (gemini-2.0-flash)</p>
          </div>
          <WalletConnection 
            onConnect={handleConnectWallet}
            onDisconnect={handleDisconnectWallet}
            connectedWallet={connectedWallet}
          />
        </div>

        {/* Messages container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.type === 'user' ? 'justify-end' : message.type === 'system' ? 'justify-center' : 'justify-start'}`}
            >
              {message.type === 'system' ? (
                <div className="message system w-3/4 bg-blue-100 border-l-4 border-blue-500 p-2 my-2 rounded">{message.text}</div>
              ) : (
                <>
                  {message.type === 'bot' && (
                    <div className="w-8 h-8 rounded-full bg-pink-600 flex items-center justify-center text-white font-bold mr-2">
                      A
                    </div>
                  )}
              <div
                className={`max-w-xs px-4 py-2 rounded-xl ${
                  message.type === 'user'
                    ? 'bg-pink-600 text-white rounded-br-none'
                    : 'bg-gray-100 text-gray-800 rounded-bl-none'
                }`}
              >
                <ReactMarkdown 
                  components={MarkdownComponents}
                  className="text-sm break-words whitespace-pre-wrap"
                >
                  {message.text}
                </ReactMarkdown>
              </div>
              {message.type === 'user' && (
                <div className="w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center text-white font-bold ml-2">
                  U
                </div>
              )}
              </>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="w-8 h-8 rounded-full bg-pink-600 flex items-center justify-center text-white font-bold mr-2">
                A
              </div>
              <div className="bg-gray-100 text-gray-800 px-4 py-2 rounded-xl rounded-bl-none">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input form */}
        <div className="border-t border-gray-200 p-4">
          <form onSubmit={handleSubmit} className="flex space-x-4">
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={awaitingConfirmation ? "Type CONFIRM to proceed or anything else to cancel" : "Type your message... (Markdown supported)"}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading}
              className="bg-pink-600 text-white p-2 rounded-full hover:bg-pink-700 focus:outline-none focus:ring-2 focus:ring-pink-500 focus:ring-offset-2 disabled:opacity-50"
            >
              <Send className="w-5 h-5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;