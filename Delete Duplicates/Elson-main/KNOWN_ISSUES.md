# Known Issues - Elson Wealth Trading Platform

This document outlines known minor issues and limitations in the current production release of the Elson Wealth Trading Platform.

## Low Severity Issues

### 1. WebSocket Reconnection
- **Description**: WebSocket reconnection might require multiple attempts in rare network conditions.
- **Impact**: Real-time data updates may be briefly interrupted during severe network fluctuations.
- **Workaround**: The client automatically attempts reconnection with exponential backoff.
- **Fix Status**: Scheduled for next patch release.

### 2. Mobile UI in Landscape Mode
- **Description**: Some charts don't fully optimize for mobile landscape orientation.
- **Impact**: Chart visualizations may not utilize full screen space in landscape mode.
- **Workaround**: Use portrait orientation for best experience on mobile devices.
- **Fix Status**: Optimization scheduled for next patch release.

### 3. PDF Export Format
- **Description**: PDF export of reports occasionally has minor formatting issues.
- **Impact**: Generated PDFs may have slight alignment issues with complex data tables.
- **Workaround**: Use the CSV or Excel export options when detailed formatting is needed.
- **Fix Status**: Fix confirmed, scheduled for next patch release.

## Performance Considerations

### 1. Initial Load Time
- **Description**: First-time app load may take 5-8 seconds on slower connections.
- **Impact**: Slight delay on first load for users on slow networks.
- **Workaround**: None needed, but subsequent loads are faster due to effective caching.
- **Status**: Progressive improvements ongoing.

### 2. Large Portfolio Rendering
- **Description**: Portfolios with 100+ positions may experience slight rendering delays.
- **Impact**: Performance dashboard may take 1-2 seconds longer to render with very large portfolios.
- **Workaround**: Use portfolio filters to view subsets of positions when analyzing large portfolios.
- **Status**: Performance optimization in progress.

## Known Limitations

### 1. Concurrent Portfolio Simulations
- **Current limit**: 5 concurrent portfolio simulations per user.
- **Reason**: Resource optimization for shared infrastructure.
- **Future plans**: Will be increased to 10 concurrent simulations in Q2 2025.

### 2. Market Data Providers
- **Current limitation**: Primary and one backup provider only.
- **Reason**: Licensing and integration complexity.
- **Future plans**: Adding additional providers in Q2 2025.

### 3. Historical Data Range
- **Current limitation**: 10 years of historical data for analysis.
- **Reason**: Storage and performance optimization.
- **Future plans**: Extended historical data planned for Q3 2025.

---

For any issues not listed here, please contact support through the help portal or by creating a support ticket.

Last Updated: March 26, 2025