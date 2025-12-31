---
title: "README"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Elson Wealth + Trading API Documentation

This directory contains detailed documentation for the Elson API endpoints, including wealth management and family account features.

## Contents

- [Authentication](./authentication.md) - API authentication methods
- [Users](./users.md) - User management endpoints
- [Portfolios](./portfolios.md) - Portfolio management endpoints
- [Trades](./trades.md) - Trade execution and history endpoints
- [Family](./family.md) - Guardian-minor relationship and account management
- [AI](./ai.md) - AI-powered recommendations and portfolio optimization
- [Education](./education.md) - Financial education content for young investors

## Base URL

All API endpoints are prefixed with `/api/v1`.

## Authentication

Most endpoints require authentication. See the [Authentication](./authentication.md) documentation for details.

## Rate Limiting

The API enforces rate limiting to prevent abuse. See individual endpoint documentation for specific limits.

## Error Handling

The API returns standard HTTP status codes along with JSON error messages.

```json
{
  "detail": "Error message description"
}
```

Common status codes:
- 200 - Success
- 400 - Bad Request
- 401 - Unauthorized
- 403 - Forbidden
- 404 - Not Found
- 429 - Too Many Requests
- 500 - Internal Server Error