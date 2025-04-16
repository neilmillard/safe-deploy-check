# safe-deploy-check
[![Marketplace](https://img.shields.io/badge/GitHub%20Action-marketplace-blue?logo=github&logoColor=white)](https://github.com/marketplace/actions/safe-deploy-check)
[![GitHub tag](https://img.shields.io/github/v/tag/neilmillard/safe-deploy-check?label=version)](https://github.com/neilmillard/safe-deploy-check/tags)
[![Build Status](https://github.com/neilmillard/safe-deploy-check/actions/workflows/docker-build-push.yml/badge.svg)](https://github.com/neilmillard/safe-deploy-check/actions/workflows/docker-build-push.yml)
[![codecov](https://codecov.io/gh/neilmillard/safe-deploy-check/branch/main/graph/badge.svg)](https://codecov.io/gh/neilmillard/safe-deploy-check)

A smart deployment safety net that verifies, monitors, and ensures best practices before, during, and after deployments

## Inputs

## `github_token`

**Required** The github PAT to use to access the check and read the PR

```yaml
github_token: ${{ secrets.GITHUB_TOKEN }}
```

## max_file_count

The threshold to warn when the number of files in the PR exceed this amount: Default 20

## secret_file_globs

A comma separated list of file globs (extensions) to warn if any are found in the PR. They may contain sensitive data: Default ".env,.pem"

## min_certainty

The minimum certainty to mark the test as okay: Default 70

## block_on_failure

Whether to block the PR (return failed exit code) on failure: Default True

## check_work_hours: true

Enable or disable the Friday warning: Default True=Enabled

## Outputs

## certainty_score

The score number out of 100

## summary

The JSON output of the score results

```json
{
    "conclusion": "success",
    "score": 82,
    "reasons": ["No reviewers", "Changed env file"],
    "files": ["config/.env"]
}
```

# Example Usage

```
name: Deploy

on:
  pull_request:
    branches: [main]

jobs:
    safe-check:
    runs-on: ubuntu-latest

    permissions:
      checks: write
      pull-requests: read

    steps:
      - name: Safe Deploy Check
        uses: neilmillard/safe-deploy-check@v1.2
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          max_file_count: 20
          secret_file_globs: ".env,.key,.pem"
          min_certainty: 4
          block_on_failure: true
          check_work_hours: true
```
