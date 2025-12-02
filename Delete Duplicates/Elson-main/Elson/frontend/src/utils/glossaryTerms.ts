/**
 * Financial glossary terms database
 * This file contains definitions for common financial terms used in the application
 * Terms are organized by category for easier management
 */

export interface GlossaryTerm {
  term: string;
  definition: string;
  category: 'basics' | 'stocks' | 'trading' | 'portfolio' | 'risk' | 'advanced';
  link?: string;
}

// Stock Market Basics
const basicTerms: GlossaryTerm[] = [
  {
    term: 'Stock',
    definition: 'A share or piece of ownership in a company. When you buy stock, you are buying a small piece of that company.',
    category: 'basics',
    link: '/education/stocks'
  },
  {
    term: 'Stock Market',
    definition: 'A place where people buy and sell shares of companies. It can be a physical place or an electronic system.',
    category: 'basics',
    link: '/education/stock-market'
  },
  {
    term: 'Dividend',
    definition: 'Money that a company pays to its shareholders, usually from profits. Not all companies pay dividends.',
    category: 'basics',
    link: '/education/dividends'
  },
  {
    term: 'Bull Market',
    definition: 'When stock prices are rising and investors are optimistic about future performance.',
    category: 'basics',
    link: '/education/market-trends'
  },
  {
    term: 'Bear Market',
    definition: 'When stock prices are falling and investors are pessimistic about future performance.',
    category: 'basics',
    link: '/education/market-trends'
  }
];

// Stock-Specific Terms
const stockTerms: GlossaryTerm[] = [
  {
    term: 'Symbol',
    definition: 'A unique series of letters assigned to a security for trading purposes. For example, Apple\'s stock symbol is AAPL.',
    category: 'stocks',
    link: '/education/stock-symbols'
  },
  {
    term: 'Share',
    definition: 'A unit of ownership in a company or financial asset. Shareholders may receive dividends and have voting rights.',
    category: 'stocks'
  },
  {
    term: 'Price-to-Earnings Ratio (P/E)',
    definition: 'A valuation ratio of a company\'s current share price compared to its earnings per share (EPS).',
    category: 'stocks',
    link: '/education/stock-valuation'
  },
  {
    term: 'Market Capitalization',
    definition: 'The total value of a company\'s outstanding shares, calculated by multiplying the stock price by the number of shares.',
    category: 'stocks',
    link: '/education/market-cap'
  },
  {
    term: 'Earnings Per Share (EPS)',
    definition: 'The portion of a company\'s profit allocated to each outstanding share of common stock.',
    category: 'stocks'
  }
];

// Trading Terms
const tradingTerms: GlossaryTerm[] = [
  {
    term: 'Bid',
    definition: 'The highest price a buyer is willing to pay for a stock or security.',
    category: 'trading'
  },
  {
    term: 'Ask',
    definition: 'The lowest price a seller is willing to accept for a stock or security.',
    category: 'trading'
  },
  {
    term: 'Market Order',
    definition: 'An order to buy or sell a stock immediately at the best available current price.',
    category: 'trading',
    link: '/education/order-types'
  },
  {
    term: 'Limit Order',
    definition: 'An order to buy or sell a stock at a specific price or better.',
    category: 'trading',
    link: '/education/order-types'
  },
  {
    term: 'Stop Order',
    definition: 'An order to buy or sell a stock once the price reaches a specified amount, called the stop price.',
    category: 'trading',
    link: '/education/order-types'
  },
  {
    term: 'Slippage',
    definition: 'The difference between the expected price of a trade and the price at which the trade is actually executed.',
    category: 'trading'
  },
  {
    term: 'Commission',
    definition: 'A fee charged by a broker for executing a transaction.',
    category: 'trading'
  },
  {
    term: 'Fractional Share',
    definition: 'A portion of one full share of a company, allowing investors to buy a slice of a stock for a smaller amount of money.',
    category: 'trading',
    link: '/education/fractional-shares'
  }
];

// Portfolio Management Terms
const portfolioTerms: GlossaryTerm[] = [
  {
    term: 'Portfolio',
    definition: 'A collection of financial investments like stocks, bonds, commodities, cash, and cash equivalents.',
    category: 'portfolio',
    link: '/education/portfolios'
  },
  {
    term: 'Asset Allocation',
    definition: 'The strategy of dividing investments among different asset categories to balance risk and reward.',
    category: 'portfolio',
    link: '/education/asset-allocation'
  },
  {
    term: 'Diversification',
    definition: 'Spreading investments among various assets to reduce risk and exposure to any single asset or risk.',
    category: 'portfolio',
    link: '/education/diversification'
  },
  {
    term: 'Rebalancing',
    definition: 'The process of realigning the weightings of a portfolio\'s assets to maintain the original desired level of asset allocation.',
    category: 'portfolio'
  },
  {
    term: 'Return',
    definition: 'The gain or loss on an investment, typically expressed as a percentage of the amount invested.',
    category: 'portfolio'
  }
];

// Risk Management Terms
const riskTerms: GlossaryTerm[] = [
  {
    term: 'Risk',
    definition: 'The chance that an investment\'s actual return will be different from expected, including the possibility of losing money.',
    category: 'risk',
    link: '/education/risk'
  },
  {
    term: 'Volatility',
    definition: 'A statistical measure of the dispersion of returns for a given security or market index.',
    category: 'risk',
    link: '/education/volatility'
  },
  {
    term: 'Beta',
    definition: 'A measure of a stock\'s volatility in relation to the overall market.',
    category: 'risk'
  },
  {
    term: 'Standard Deviation',
    definition: 'A measure of the amount of variation or dispersion of a set of values, used to quantify investment risk.',
    category: 'risk'
  },
  {
    term: 'Drawdown',
    definition: 'The peak-to-trough decline during a specific period for an investment or fund.',
    category: 'risk'
  },
  {
    term: 'Risk Profile',
    definition: 'A evaluation of an individual\'s willingness and ability to take risks, used to determine suitable investments.',
    category: 'risk',
    link: '/education/risk-profiles'
  }
];

// Advanced Terms
const advancedTerms: GlossaryTerm[] = [
  {
    term: 'Blue-Chip Stock',
    definition: 'A stock of a large, well-established company with a solid financial history, typically seen as relatively low-risk.',
    category: 'advanced'
  },
  {
    term: 'Growth Stock',
    definition: 'A share in a company that is anticipated to grow at a rate significantly above the market average.',
    category: 'advanced'
  },
  {
    term: 'Value Stock',
    definition: 'A stock that appears to trade for less than its intrinsic value and is considered undervalued by investors.',
    category: 'advanced'
  },
  {
    term: 'Dollar-Cost Averaging',
    definition: 'A strategy of investing a fixed amount at regular intervals, regardless of the stock price.',
    category: 'advanced',
    link: '/education/investment-strategies'
  },
  {
    term: 'ETF (Exchange-Traded Fund)',
    definition: 'A type of investment fund that is traded on stock exchanges, much like stocks.',
    category: 'advanced',
    link: '/education/etfs'
  },
  {
    term: 'Mutual Fund',
    definition: 'An investment vehicle made up of a pool of money collected from many investors to invest in securities.',
    category: 'advanced',
    link: '/education/mutual-funds'
  },
  {
    term: 'Index Fund',
    definition: 'A type of mutual fund or ETF that aims to track the returns of a market index, like the S&P 500.',
    category: 'advanced',
    link: '/education/index-funds'
  }
];

// Combine all terms
export const glossaryTerms: GlossaryTerm[] = [
  ...basicTerms,
  ...stockTerms,
  ...tradingTerms,
  ...portfolioTerms,
  ...riskTerms,
  ...advancedTerms
];

// Helper function to get terms by category
export const getTermsByCategory = (category: GlossaryTerm['category']): GlossaryTerm[] => {
  return glossaryTerms.filter(term => term.category === category);
};

// Helper function to search terms
export const searchTerms = (query: string): GlossaryTerm[] => {
  const lowerQuery = query.toLowerCase();
  return glossaryTerms.filter(term => 
    term.term.toLowerCase().includes(lowerQuery) || 
    term.definition.toLowerCase().includes(lowerQuery)
  );
};

// Helper function to get a specific term
export const getTerm = (termName: string): GlossaryTerm | undefined => {
  return glossaryTerms.find(term => 
    term.term.toLowerCase() === termName.toLowerCase()
  );
};

export default glossaryTerms;