// Export all trading components for easy importing
export { default as OrderForm } from './OrderForm';
export { default as Portfolio } from './Portfolio';
export { default as LiveQuoteDisplay } from './LiveQuoteDisplay';
export { default as TradeHistory } from './TradeHistory';
export { default as Watchlist } from './Watchlist';
export { default as TradingDashboard } from './TradingDashboard';

// Enhanced Trading Components
export { TradingSidebar } from './TradingSidebar';
export { StockHeader } from './StockHeader';
export { EnhancedOrderForm } from './EnhancedOrderForm';
export { CompanyInfo } from './CompanyInfo';
export { AutoTradingSettings } from './AutoTradingSettings';
export { AITradingAssistant } from './AITradingAssistant';
export { default as TradingSafeguards } from './TradingSafeguards';
export { TradingSafeguardWrapper } from './TradingSafeguards';

// User-Friendly Trading Components (Acorns/Stash/Robinhood style)
export { default as BeginnerOrderForm } from './BeginnerOrderForm';
export { OrderPreviewScreen, calculateFees as calculateOrderFees } from './OrderPreviewScreen';
export { QuickInvestButtons } from './QuickInvestButtons';
export { TradingConfirmationModal } from './TradingConfirmationModal';

// Live Data Components
export { LiveMarketData, MiniLiveMarketData } from './LiveMarketData';
export { LivePortfolioUpdates, CompactPortfolioUpdates } from './LivePortfolioUpdates';
export { LiveOrderUpdates, OrderNotification } from './LiveOrderUpdates';

// Price Display with Flash Animation
export { PriceDisplay, CompactPriceDisplay, LargePriceDisplay } from './PriceDisplay';

// Re-export types for convenience
export type { Asset, Trade, OrderData, Portfolio as PortfolioType, MarketQuote, WatchlistItem } from '../../types';