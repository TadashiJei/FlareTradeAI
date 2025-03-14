# Flare AI DeFAI

Flare AI Kit template for AI x DeFi (DeFAI).

## 🚀 Key Features

- **Secure AI Execution**  
  Runs within a Trusted Execution Environment (TEE) featuring remote attestation support for robust security.

- **Built-in Chat UI**  
  Interact with your AI via a TEE-served chat interface.

- **Flare Blockchain and Wallet Integration**  
  Perform token operations and generate wallets from within the TEE.

- **Gemini 2.0 + over 300 LLMs supported**  
  Utilize Google Gemini's latest model with structured query support for advanced AI functionalities.

- **DeFi Protocol Integrations**  
  Seamlessly interact with Flare ecosystem protocols (SparkDEX, Kinetic, Cyclo, RainDEX) using natural language.

- **Comprehensive Risk Assessment**  
  Evaluate transaction risks before execution with detailed risk scoring and warnings.

- **Natural Language Processing for DeFi**  
  Transform simple commands like "Swap 10 ETH to USDC" into executable blockchain transactions.

<img width="500" alt="Artemis" src="https://github.com/user-attachments/assets/921fbfe2-9d52-496c-9b48-9dfc32a86208" />

## 🎯 Getting Started

You can deploy Flare AI DeFAI using Docker (recommended) or set up the backend and frontend manually.

### Environment Setup

1. **Prepare the Environment File:**  
   Rename `.env.example` to `.env` and update the variables accordingly.
   > **Tip:** Set `SIMULATE_ATTESTATION=true` for local testing.

### Build using Docker (Recommended)

The Docker setup mimics a TEE environment and includes an Nginx server for routing, while Supervisor manages both the backend and frontend services in a single container.

1. **Build the Docker Image:**

   ```bash
   docker build -t flare-ai-defai .
   ```

2. **Run the Docker Container:**

   ```bash
   docker run -p 80:80 -it --env-file .env flare-ai-defai
   ```

3. **Access the Frontend:**  
   Open your browser and navigate to [http://localhost:80](http://localhost:80) to interact with the Chat UI.

## 🛠 Build Manually

Flare AI DeFAI is composed of a Python-based backend and a JavaScript frontend. Follow these steps for manual setup:

#### Backend Setup

1. **Install Dependencies:**  
   Use [uv](https://docs.astral.sh/uv/getting-started/installation/) to install backend dependencies:

   ```bash
   uv sync --all-extras
   ```

2. **Start the Backend:**  
   The backend runs by default on `0.0.0.0:8080`:

   ```bash
   uv run start-backend
   ```

#### Frontend Setup

1. **Install Dependencies:**  
   In the `chat-ui/` directory, install the required packages using [npm](https://nodejs.org/en/download):

   ```bash
   cd chat-ui/
   npm install
   ```

2. **Configure the Frontend:**  
   Update the backend URL in `chat-ui/src/App.js` for testing:

   ```js
   const BACKEND_ROUTE = "http://localhost:8080/api/routes/chat/";
   ```

   > **Note:** Remember to change `BACKEND_ROUTE` back to `'api/routes/chat/'` after testing.

3. **Start the Frontend:**

   ```bash
   npm start
   ```

## 🤖 Using the DeFi Agent

FlareTrade includes a powerful DeFi agent that can process natural language commands and execute them securely within a TEE environment.

### Demo Script

Run the included demo script to see the DeFi agent in action:

```bash
python3 demo.py --wallet YOUR_WALLET_ADDRESS
```

Add the `--no-tee` flag to run without TEE protection (for testing only).

### Supported Commands

The DeFi agent supports a wide range of natural language commands, including:

- **Swapping tokens**: "Swap 10 ETH to USDC on SparkDEX with 0.5% slippage"
- **Depositing assets**: "Deposit 100 USDC into Kinetic"
- **Withdrawing assets**: "Withdraw 50 USDC from Kinetic"
- **Staking tokens**: "Stake 10 FLR on Cyclo"
- **Unstaking tokens**: "Unstake 5 FLR from Cyclo"
- **Claiming rewards**: "Claim rewards from Cyclo"
- **Borrowing assets**: "Borrow 20 ETH from Kinetic"
- **Repaying loans**: "Repay 15 ETH loan on Kinetic"

### Programmatic Usage

You can also use the DeFi agent programmatically in your own code:

```python
from src.flare_ai_defai.agent.defi_agent import DeFiAgent

# Initialize the agent
agent = DeFiAgent(
    wallet_address="YOUR_WALLET_ADDRESS",
    use_tee=True,
    risk_threshold="medium",
    simulate_transactions=True,
)

# Process a natural language command
result = agent.process_natural_language_command("Swap 10 ETH to USDC on SparkDEX")

# Check the result
if result["success"]:
    print(f"Transaction Hash: {result['transaction_hash']}")
else:
    print(f"Error: {result['errors']}")

# Get portfolio information
portfolio = agent.get_portfolio()
print(f"Total Portfolio Value: ${portfolio['total_value']:.2f} USD")

# Get transaction history
transactions = agent.get_transaction_history(limit=5)
for tx in transactions:
    print(f"Transaction: {tx['hash']}")
```

## 📁 Repo Structure

```plaintext
src/flare_ai_defai/
├── agent/                  # DeFi agent implementation
│   └── defi_agent.py      # Main DeFi agent class
├── ai/                     # AI Provider implementations
│   ├── base.py            # Base AI provider interface
│   ├── gemini.py          # Google Gemini integration
│   └── openrouter.py      # OpenRouter integration
├── api/                    # API layer
│   ├── middleware/        # Request/response middleware
│   └── routes/           # API endpoint definitions
├── attestation/           # TEE attestation
│   ├── vtpm_attestation.py   # vTPM client
│   └── vtpm_validation.py    # Token validation
├── blockchain/              # Blockchain operations
│   ├── explorer.py        # Chain explorer client
│   ├── flare.py          # Flare network provider
│   ├── protocols/        # DeFi protocol implementations
│   ├── risk/             # Risk assessment system
│   ├── transaction.py    # Transaction simulation and validation
│   └── wallet.py         # Secure wallet management
├── nlp/                   # Natural language processing
│   └── defi_parser.py    # DeFi command parser
├── prompts/              # AI system prompts & templates
│    ├── library.py        # Prompt module library
│    ├── schemas.py        # Schema definitions
│    ├── service.py        # Prompt service module
│    └── templates.py       # Prompt templates
├── exceptions.py      # Custom errors
├── main.py          # Primary entrypoint
└── settings.py       # Configuration settings error
```

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [DeFi Protocol Integrations](docs/defi_integrations.md)
- [Protocol Factory](docs/protocol_factory.md)
- [Risk Assessment System](docs/risk_assessment.md)
- [Transaction Validation](docs/transaction_validation.md)
- [Secure Wallet Management](docs/wallet_management.md)
- [Natural Language Processing](docs/nlp_processing.md)
- [TEE Attestation](docs/tee_attestation.md)

## 🚀 Deploy on TEE

Deploy on a [Confidential Space](https://cloud.google.com/confidential-computing/confidential-space/docs/confidential-space-overview) using AMD SEV.

### Prerequisites

- **Google Cloud Platform Account:**  
  Access to the [`verifiable-ai-hackathon`](https://console.cloud.google.com/welcome?project=verifiable-ai-hackathon) project is required.

- **Gemini API Key:**  
  Ensure your [Gemini API key](https://aistudio.google.com/app/apikey) is linked to the project.

- **gcloud CLI:**  
  Install and authenticate the [gcloud CLI](https://cloud.google.com/sdk/docs/install).

### Environment Configuration

1. **Set Environment Variables:**  
   Update your `.env` file with:

   ```bash
   TEE_IMAGE_REFERENCE=ghcr.io/flare-foundation/flare-ai-defai:main  # Replace with your repo build image
   INSTANCE_NAME=<PROJECT_NAME-TEAM_NAME>
   ```

2. **Load Environment Variables:**

   ```bash
   source .env
   ```

   > **Reminder:** Run the above command in every new shell session or after modifying `.env`. On Windows, we recommend using [git BASH](https://gitforwindows.org) to access commands like `source`.

3. **Verify the Setup:**

   ```bash
   echo $TEE_IMAGE_REFERENCE # Expected output: Your repo build image
   ```

### Deploying to Confidential Space

Run the following command:

```bash
gcloud compute instances create $INSTANCE_NAME \
  --project=verifiable-ai-hackathon \
  --zone=us-west1-b \
  --machine-type=n2d-standard-2 \
  --network-interface=network-tier=PREMIUM,nic-type=GVNIC,stack-type=IPV4_ONLY,subnet=default \
  --metadata=tee-image-reference=$TEE_IMAGE_REFERENCE,\
tee-container-log-redirect=true,\
tee-env-GEMINI_API_KEY=$GEMINI_API_KEY,\
tee-env-GEMINI_MODEL=$GEMINI_MODEL,\
tee-env-WEB3_PROVIDER_URL=$WEB3_PROVIDER_URL,\
tee-env-SIMULATE_ATTESTATION=false \
  --maintenance-policy=MIGRATE \
  --provisioning-model=STANDARD \
  --service-account=confidential-sa@verifiable-ai-hackathon.iam.gserviceaccount.com \
  --scopes=https://www.googleapis.com/auth/cloud-platform \
  --min-cpu-platform="AMD Milan" \
  --tags=flare-ai,http-server,https-server \
  --create-disk=auto-delete=yes,\
boot=yes,\
device-name=$INSTANCE_NAME,\
image=projects/confidential-space-images/global/images/confidential-space-debug-250100,\
mode=rw,\
size=11,\
type=pd-standard \
  --shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --reservation-affinity=any \
  --confidential-compute-type=SEV
