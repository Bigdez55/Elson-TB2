import React, { useState, useEffect, Suspense, lazy } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Paper, 
  Tabs, 
  Tab, 
  Button, 
  Container, 
  Card, 
  CardContent, 
  Divider,
  useTheme,
  useMediaQuery
} from '@mui/material';

// Import the mobile portfolio component lazily for better performance
const MobilePortfolio = lazy(() => import('../app/components/portfolio/MobilePortfolio'));
import { 
  AccountBalance, 
  DonutLarge, 
  BarChart, 
  Assessment, 
  TrendingUp, 
  Add
} from '@mui/icons-material';

// Import our portfolio components
import PortfolioBuilder from '../app/components/portfolio/PortfolioBuilder';
import DiversificationScorer from '../app/components/portfolio/DiversificationScorer';
import PortfolioTemplates from '../app/components/portfolio/PortfolioTemplates';

// Import existing components
import { useTrading } from '../hooks/useTrading';
import { formatCurrency, formatPercentage } from '../utils/formatters';
import Loading from '../app/components/common/Loading';
import EducationalTooltip from '../app/components/common/EducationalTooltip';
import LoadingState from '../app/components/common/LoadingState';

// Portfolio tabs
type PortfolioTab = 'overview' | 'builder' | 'templates' | 'diversification';

export default function Portfolio() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.down('md'));
  const { portfolio, isLoading, error } = useTrading();
  const { positions, balance, equity, margin } = portfolio || {};
  const [activeTab, setActiveTab] = useState<PortfolioTab>('overview');
  
  // Check if we should render the mobile version of the portfolio
  if (isMobile) {
    return (
      <Suspense fallback={<Loading />}>
        <MobilePortfolio />
      </Suspense>
    );
  }
  
  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: PortfolioTab) => {
    setActiveTab(newValue);
  };
  
  // Create skeleton for portfolio data
  const portfolioSkeleton = (
    <Box sx={{ width: '100%' }}>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {[1, 2, 3, 4].map((i) => (
          <Grid item xs={12} sm={6} md={3} key={i}>
            <Paper sx={{ p: { xs: 2, sm: 3 }, height: '100%' }}>
              <div className="animate-pulse">
                <div className="h-4 bg-gray-700 rounded w-1/2 mb-2"></div>
                <div className="h-8 bg-gray-700 rounded w-2/3"></div>
              </div>
            </Paper>
          </Grid>
        ))}
      </Grid>
      
      <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 4 }}>
        <div className="animate-pulse">
          <div className="flex flex-col sm:flex-row sm:justify-between gap-2 sm:gap-0 mb-4">
            <div className="h-6 bg-gray-700 rounded w-1/3 sm:w-1/4"></div>
            <div className="h-8 bg-gray-700 rounded w-40"></div>
          </div>
          <div className="h-1 bg-gray-700 rounded w-full mb-6"></div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-700 rounded"></div>
            ))}
          </div>
        </div>
      </Paper>
    </Box>
  );
  
  // Use the LoadingState component for handling loading and error states
  return (
    <LoadingState 
      isLoading={isLoading} 
      error={error} 
      skeleton={portfolioSkeleton}
      onRetry={() => window.location.reload()}
    >
      <Container maxWidth="xl" sx={{ px: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ mb: { xs: 2, sm: 4 } }}>
          <Typography 
            variant={isMobile ? "h5" : "h4"} 
            component="h1" 
            gutterBottom 
            sx={{ 
              display: 'flex', 
              alignItems: 'center',
              fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' },
              mb: { xs: 1, sm: 2 }
            }}
          >
            <AccountBalance sx={{ mr: 1.5, color: 'primary.main', fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } }} />
            Portfolio Management
            <EducationalTooltip
              term="Portfolio"
              definition="A collection of financial investments like stocks, bonds, and other assets that represent your total holdings."
              placement={isMobile ? "bottom" : "right"}
            />
          </Typography>
          
          {/* Portfolio Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: { xs: 2, sm: 3 } }}>
            <Tabs 
              value={activeTab} 
              onChange={handleTabChange} 
              aria-label="portfolio tabs"
              variant="scrollable"
              scrollButtons="auto"
              sx={{
                '.MuiTab-root': {
                  minWidth: { xs: 'auto', sm: 120 },
                  padding: { xs: '6px 12px', sm: '12px 16px' },
                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                }
              }}
            >
              <Tab 
                icon={<BarChart fontSize={isMobile ? "small" : "medium"} />} 
                iconPosition="start" 
                label="Overview" 
                value="overview" 
              />
              <Tab 
                icon={<DonutLarge fontSize={isMobile ? "small" : "medium"} />} 
                iconPosition="start" 
                label="Portfolio Builder" 
                value="builder" 
              />
              <Tab 
                icon={<AccountBalance fontSize={isMobile ? "small" : "medium"} />} 
                iconPosition="start" 
                label="Template Portfolios" 
                value="templates" 
              />
              <Tab 
                icon={<Assessment fontSize={isMobile ? "small" : "medium"} />} 
                iconPosition="start" 
                label="Diversification Analysis" 
                value="diversification" 
              />
            </Tabs>
          </Box>
          
          {/* Tab Content */}
          {activeTab === 'overview' && (
            <Box>
              {/* Portfolio Overview Cards - Horizontal scroll on mobile */}
              <Box sx={{ mb: { xs: 3, sm: 4 } }}>
                <Typography variant="h6" sx={{ mb: 1, pl: { xs: 1, sm: 0 }, fontSize: { xs: '1rem', sm: '1.25rem' } }}>
                  Portfolio Overview
                </Typography>
                
                <Box 
                  sx={{ 
                    display: { xs: 'flex', sm: 'grid' },
                    gridTemplateColumns: { sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
                    gap: 2,
                    overflowX: { xs: 'auto', sm: 'visible' },
                    pb: { xs: 2, sm: 0 },
                    marginX: { xs: -2, sm: 0 },
                    px: { xs: 2, sm: 0 },
                  }}
                >
                  <Paper 
                    sx={{ 
                      p: { xs: 2, sm: 3 }, 
                      height: '100%',
                      flexShrink: 0,
                      width: { xs: '75%', sm: 'auto' },
                      minWidth: { xs: '220px', sm: 'auto' }
                    }}
                  >
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Total Balance
                    </Typography>
                    <Typography 
                      variant={isMobile ? "h5" : "h4"} 
                      sx={{ 
                        fontWeight: 'bold',
                        fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } 
                      }}
                    >
                      {formatCurrency(balance)}
                    </Typography>
                  </Paper>
                  
                  <Paper 
                    sx={{ 
                      p: { xs: 2, sm: 3 }, 
                      height: '100%',
                      flexShrink: 0,
                      width: { xs: '75%', sm: 'auto' },
                      minWidth: { xs: '220px', sm: 'auto' }
                    }}
                  >
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Equity
                    </Typography>
                    <Typography 
                      variant={isMobile ? "h5" : "h4"} 
                      sx={{ 
                        fontWeight: 'bold',
                        fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } 
                      }}
                    >
                      {formatCurrency(equity)}
                    </Typography>
                  </Paper>
                  
                  <Paper 
                    sx={{ 
                      p: { xs: 2, sm: 3 }, 
                      height: '100%',
                      flexShrink: 0,
                      width: { xs: '75%', sm: 'auto' },
                      minWidth: { xs: '220px', sm: 'auto' }
                    }}
                  >
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Margin Used
                    </Typography>
                    <Typography 
                      variant={isMobile ? "h5" : "h4"} 
                      sx={{ 
                        fontWeight: 'bold',
                        fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } 
                      }}
                    >
                      {formatCurrency(margin)}
                    </Typography>
                  </Paper>
                  
                  <Paper 
                    sx={{ 
                      p: { xs: 2, sm: 3 }, 
                      height: '100%',
                      flexShrink: 0,
                      width: { xs: '75%', sm: 'auto' },
                      minWidth: { xs: '220px', sm: 'auto' }
                    }}
                  >
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Available Margin
                    </Typography>
                    <Typography 
                      variant={isMobile ? "h5" : "h4"} 
                      sx={{ 
                        fontWeight: 'bold',
                        fontSize: { xs: '1.25rem', sm: '1.5rem', md: '2rem' } 
                      }}
                    >
                      {formatCurrency(balance - margin)}
                    </Typography>
                  </Paper>
                </Box>
              </Box>

              {/* Open Positions */}
              <Paper sx={{ p: { xs: 2, sm: 3 }, mb: { xs: 3, sm: 4 } }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: { xs: 'column', sm: 'row' }, 
                    alignItems: { xs: 'flex-start', sm: 'center' }, 
                    justifyContent: 'space-between',
                    mb: { xs: 2, sm: 1 },
                    gap: { xs: 2, sm: 0 }
                  }}
                >
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      fontSize: { xs: '1rem', sm: '1.25rem' }
                    }}
                  >
                    <TrendingUp sx={{ mr: 1, color: 'primary.main', fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
                    Open Positions
                  </Typography>
                  
                  <Button
                    variant="contained"
                    color="primary"
                    size={isMobile ? "small" : "medium"}
                    startIcon={<Add />}
                    onClick={() => setActiveTab('builder')}
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    {isMobile ? "New Position" : "Create New Position"}
                  </Button>
                </Box>
                
                <Divider sx={{ mb: 2 }} />
                
                {positions && positions.length > 0 ? (
                  <Box 
                    sx={{ 
                      display: { xs: 'flex', sm: 'grid' },
                      gridTemplateColumns: { sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
                      gap: 2,
                      overflowX: { xs: 'auto', sm: 'visible' },
                      pb: { xs: 2, sm: 0 },
                      marginX: { xs: -2, sm: 0 },
                      px: { xs: 2, sm: 0 },
                    }}
                  >
                    {positions.map((position) => (
                      <Card 
                        variant="outlined" 
                        key={position.symbol}
                        sx={{
                          flexShrink: 0,
                          width: { xs: '85%', sm: 'auto' },
                          minWidth: { xs: '240px', sm: 'auto' }
                        }}
                      >
                        <CardContent sx={{ p: { xs: 2, sm: 3 } }}>
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                            <Typography 
                              variant="h6" 
                              sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                            >
                              {position.symbol}
                            </Typography>
                            <Typography 
                              variant="body2" 
                              sx={{ 
                                color: position.unrealizedPnL >= 0 ? 'success.main' : 'error.main',
                                fontWeight: 'bold',
                                fontSize: { xs: '0.75rem', sm: '0.875rem' }
                              }}
                            >
                              {formatPercentage(position.unrealizedPnLPercentage)}
                            </Typography>
                          </Box>
                          
                          <Typography 
                            variant="body2" 
                            color="text.secondary" 
                            gutterBottom
                            sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                          >
                            {position.amount} shares @ {formatCurrency(position.averagePrice)}
                          </Typography>
                          
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                            <Box>
                              <Typography 
                                variant="caption" 
                                color="text.secondary"
                                sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                              >
                                Current Value
                              </Typography>
                              <Typography 
                                variant="body2" 
                                fontWeight="bold"
                                sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                              >
                                {formatCurrency(position.totalValue)}
                              </Typography>
                            </Box>
                            <Box>
                              <Typography 
                                variant="caption" 
                                color="text.secondary"
                                sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' } }}
                              >
                                Profit/Loss
                              </Typography>
                              <Typography 
                                variant="body2" 
                                fontWeight="bold"
                                color={position.unrealizedPnL >= 0 ? 'success.main' : 'error.main'}
                                sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                              >
                                {formatCurrency(position.unrealizedPnL)}
                              </Typography>
                            </Box>
                          </Box>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: { xs: 3, sm: 4 } }}>
                    <Typography 
                      variant="body1" 
                      color="text.secondary" 
                      paragraph
                      sx={{ fontSize: { xs: '0.875rem', sm: '1rem' } }}
                    >
                      You don't have any open positions yet.
                    </Typography>
                    <Button
                      variant="contained"
                      color="primary"
                      size={isMobile ? "small" : "medium"}
                      onClick={() => setActiveTab('templates')}
                      sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                    >
                      Browse Portfolio Templates
                    </Button>
                  </Box>
                )}
              </Paper>
              
              {/* Portfolio Analytics Preview */}
              <Paper sx={{ p: { xs: 2, sm: 3 } }}>
                <Typography 
                  variant="h6" 
                  gutterBottom 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    fontSize: { xs: '1rem', sm: '1.25rem' },
                    mb: { xs: 1, sm: 1.5 }
                  }}
                >
                  <Assessment sx={{ mr: 1, color: 'primary.main', fontSize: { xs: '1.1rem', sm: '1.25rem' } }} />
                  Portfolio Analytics
                </Typography>
                
                <Divider sx={{ mb: { xs: 2, sm: 2.5 } }} />
                
                <Grid container spacing={{ xs: 2, md: 3 }}>
                  <Grid item xs={12} md={6} order={{ xs: 2, md: 1 }}>
                    <Box sx={{ mb: { xs: 3, md: 2 } }}>
                      <Typography 
                        variant="subtitle2" 
                        gutterBottom
                        sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
                      >
                        Diversification Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: { xs: '65%', sm: '75%' }, mr: 2 }}>
                          <Box sx={{ 
                            height: { xs: 6, sm: 8 }, 
                            width: '100%', 
                            bgcolor: 'grey.300', 
                            borderRadius: 4,
                            overflow: 'hidden'
                          }}>
                            <Box sx={{ 
                              width: '65%', 
                              height: '100%', 
                              bgcolor: 'success.main',
                              borderRadius: 4,
                            }} />
                          </Box>
                        </Box>
                        <Typography 
                          variant={isMobile ? "subtitle1" : "h6"} 
                          color="success.main"
                          sx={{ fontSize: { xs: '0.9rem', sm: '1.25rem' } }}
                        >
                          65/100
                        </Typography>
                      </Box>
                    </Box>
                    
                    <Box>
                      <Typography 
                        variant="subtitle2" 
                        gutterBottom
                        sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
                      >
                        Risk Profile
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ display: 'flex', width: { xs: '65%', sm: '75%' }, mr: 2 }}>
                          {[...Array(10)].map((_, i) => (
                            <Box
                              key={i}
                              sx={{
                                width: '10%',
                                height: { xs: 6, sm: 8 },
                                mx: '1px',
                                bgcolor: i < 6 ? 'warning.main' : 'grey.300',
                                borderRadius: i === 0 ? '4px 0 0 4px' : i === 9 ? '0 4px 4px 0' : 0,
                              }}
                            />
                          ))}
                        </Box>
                        <Typography 
                          variant={isMobile ? "subtitle1" : "h6"} 
                          color="warning.main"
                          sx={{ fontSize: { xs: '0.9rem', sm: '1.25rem' } }}
                        >
                          6/10
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} md={6} order={{ xs: 1, md: 2 }}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                      <Typography 
                        variant="subtitle2" 
                        gutterBottom
                        sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem' } }}
                      >
                        Quick Recommendations
                      </Typography>
                      <Paper 
                        variant="outlined" 
                        sx={{ 
                          p: { xs: 1.5, sm: 2 }, 
                          bgcolor: 'background.paper', 
                          flexGrow: 1,
                          mb: { xs: 2, md: 0 } 
                        }}
                      >
                        <Typography 
                          variant="body2" 
                          paragraph
                          sx={{ 
                            fontSize: { xs: '0.75rem', sm: '0.875rem' },
                            mb: { xs: 1, sm: 1.5 }  
                          }}
                        >
                          Based on your current portfolio:
                        </Typography>
                        <Box component="ul" sx={{ pl: 2, mb: 0 }}>
                          <Box component="li" sx={{ mb: { xs: 0.5, sm: 1 } }}>
                            <Typography 
                              variant="body2"
                              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                            >
                              Consider increasing your international stock exposure for better diversification.
                            </Typography>
                          </Box>
                          <Box component="li" sx={{ mb: { xs: 0.5, sm: 1 } }}>
                            <Typography 
                              variant="body2"
                              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                            >
                              Your technology sector allocation is higher than recommended (40% vs 25% target).
                            </Typography>
                          </Box>
                          <Box component="li">
                            <Typography 
                              variant="body2"
                              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                            >
                              Adding some bond exposure would reduce portfolio volatility.
                            </Typography>
                          </Box>
                        </Box>
                      </Paper>
                      
                      <Button 
                        variant="outlined" 
                        color="primary" 
                        size={isMobile ? "small" : "medium"}
                        sx={{ 
                          mt: { xs: 1, sm: 2 }, 
                          alignSelf: { xs: 'center', sm: 'flex-end' },
                          fontSize: { xs: '0.75rem', sm: '0.875rem' }
                        }}
                        onClick={() => setActiveTab('diversification')}
                      >
                        View Full Analysis
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </Paper>
            </Box>
          )}
          
          {activeTab === 'builder' && (
            <PortfolioBuilder />
          )}
          
          {activeTab === 'templates' && (
            <PortfolioTemplates 
              onSelectTemplate={(template) => {
                // In a real app, this would load the template into the builder
                console.log('Selected template:', template);
                setActiveTab('builder');
              }}
            />
          )}
          
          {activeTab === 'diversification' && (
            <DiversificationScorer />
          )}
        </Box>
      </Container>
    </LoadingState>
  );
}