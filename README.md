# safe-deploy-check
[![Marketplace](https://img.shields.io/badge/GitHub%20Action-marketplace-blue?logo=github&logoColor=white)](https://github.com/marketplace/actions/safe-deploy-check)
[![GitHub tag](https://img.shields.io/github/v/tag/neilmillard/safe-deploy-check?label=version)](https://github.com/neilmillard/safe-deploy-check/tags)
[![Build Status](https://github.com/neilmillard/safe-deploy-check/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/neilmillard/safe-deploy-check/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/neilmillard/safe-deploy-check/branch/main/graph/badge.svg)](https://codecov.io/gh/neilmillard/safe-deploy-check)

A smart deployment safety net that verifies, monitors, and ensures best practices before, during, and after deployments

# Usage

```
name: Deploy

on:
  pull_request:
    branches: [main]

jobs:
  safe-check:
    runs-on: ubuntu-latest
    
    # Give checks write permission to the Default GITHUB_TOKEN
    permissions:
      checks: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Safe Deploy Check
        uses: neilmillard/safe-deploy-check@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          max_file_count: 20
          secret_file_globs: ".env,.key,.pem"
          min_certainty: 4
          block_on_failure: true
          check_work_hours: true
```
