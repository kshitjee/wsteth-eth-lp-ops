# Univ3 LP Bot

## Overview

This repository implements a liquidity provisioning bot for the wstETH/wETH pair on Uniswap V3. It calculates optimal tick ranges for concentrated liquidity positions using market metrics and a deterministic yield model, monitors positions, and sends email alerts for rebalancing decisions. A GitHub Actions workflow runs the bot every 24 hours.

## Setup

1. **Clone the Repository:**  
   Clone this repo to your local machine.

2. **Create Virtual Environment & Install Dependencies:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

3. Google OAuth Credentials:
    Place your `credentials.json` file in the `config` folder (or update the path in `src/rebalancer/rebalancer.py` if placed elsewhere).

4. Pre-Authenticate:
Run the rebalancer script locally to trigger the OAuth flow and generate token.pickle:
```bash
python -m src.rebalancer.rebalancer
```
This will open a browser for authentication. Once completed, a valid token.pickle will be created.

## Running the Bot
To run the rebalancer locally, execute:
```bash
python -m src.rebalancer.rebalancer
```

## GitHub Actions
A workflow is configured to run the rebalancer script every 24 hours. The workflow file is located at `.github/workflows/rebalancer-cron.yml.` Make sure your repository contains a valid token.pickle (or configure GitHub Secrets accordingly) so that the OAuth flow is bypassed in the CI environment.

## Security Notice
WARNING: The current configuration commits credentials.json and token.pickle for testing purposes. Do not use this approach in production. Use secure storage for secrets and tokens to protect sensitive information.
