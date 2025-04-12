# safe-deploy-check
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
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Safe Deploy Check
        uses: your-org/safe-deploy-check@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          max_file_count: 20
          secret_file_globs: ".env,.key,.pem"
          min_certainty: 4
          block_on_failure: true
          check_work_hours: true
```
