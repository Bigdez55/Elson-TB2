import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Slider,
  Button,
  Divider,
  Chip,
  Paper,
  Alert,
  AlertTitle,
  IconButton,
  Tooltip,
  TextField,
  MenuItem,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  CircularProgress,
  useTheme,
  LinearProgress,
} from '@mui/material';
import {
  DonutLarge,
  Remove,
  Add,
  Info,
  Done,
  Warning,
  Delete,
  ArrowUpward,
  ArrowDownward,
  TrendingUp,
  BarChart,
  AccountBalance,
  Save,
  Refresh,
  PlayArrow,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import EducationalTooltip from '../common/EducationalTooltip';

// Asset class types and colors
const ASSET_CLASSES = [
  { id: 'us_stocks', name: 'US Stocks', color: '#3f51b5', riskScore: 8 },
  { id: 'intl_stocks', name: 'International Stocks', color: '#2196f3', riskScore: 9 },
  { id: 'bonds', name: 'Bonds', color: '#4caf50', riskScore: 4 },
  { id: 'real_estate', name: 'Real Estate', color: '#ff9800', riskScore: 7 },
  { id: 'commodities', name: 'Commodities', color: '#f44336', riskScore: 9 },
  { id: 'cash', name: 'Cash', color: '#9e9e9e', riskScore: 1 },
];

// Risk profiles
const RISK_PROFILES = [
  { 
    id: 'conservative',
    name: 'Conservative',
    description: 'Lower risk, lower potential returns. Focused on capital preservation.',
    allocation: { 
      us_stocks: 20, 
      intl_stocks: 10, 
      bonds: 50, 
      real_estate: 5, 
      commodities: 0, 
      cash: 15 
    },
    riskScore: 3,
    ageRange: '8-12, 60+',
  },
  { 
    id: 'moderate',
    name: 'Moderate',
    description: 'Balanced approach with moderate risk and growth potential.',
    allocation: { 
      us_stocks: 40, 
      intl_stocks: 15, 
      bonds: 30, 
      real_estate: 5, 
      commodities: 5, 
      cash: 5 
    },
    riskScore: 5,
    ageRange: '13-17, 45-59',
  },
  { 
    id: 'growth',
    name: 'Growth',
    description: 'Higher risk with focus on long-term growth.',
    allocation: { 
      us_stocks: 55, 
      intl_stocks: 25, 
      bonds: 10, 
      real_estate: 5, 
      commodities: 5, 
      cash: 0 
    },
    riskScore: 7,
    ageRange: '18-44',
  },
  { 
    id: 'aggressive',
    name: 'Aggressive',
    description: 'Highest risk profile for maximum growth potential.',
    allocation: { 
      us_stocks: 60, 
      intl_stocks: 30, 
      bonds: 0, 
      real_estate: 5, 
      commodities: 5, 
      cash: 0 
    },
    riskScore: 9,
    ageRange: '18-30',
  },
];

// Sample ETFs for each asset class
const SUGGESTED_ETFS = {
  us_stocks: [
    { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF', expense: 0.03 },
    { symbol: 'SPY', name: 'SPDR S&P 500 ETF', expense: 0.09 },
    { symbol: 'IVV', name: 'iShares Core S&P 500 ETF', expense: 0.03 },
  ],
  intl_stocks: [
    { symbol: 'VXUS', name: 'Vanguard Total International Stock ETF', expense: 0.08 },
    { symbol: 'EFA', name: 'iShares MSCI EAFE ETF', expense: 0.33 },
    { symbol: 'IXUS', name: 'iShares Core MSCI Total International Stock ETF', expense: 0.09 },
  ],
  bonds: [
    { symbol: 'BND', name: 'Vanguard Total Bond Market ETF', expense: 0.03 },
    { symbol: 'AGG', name: 'iShares Core U.S. Aggregate Bond ETF', expense: 0.03 },
    { symbol: 'BNDX', name: 'Vanguard Total International Bond ETF', expense: 0.08 },
  ],
  real_estate: [
    { symbol: 'VNQ', name: 'Vanguard Real Estate ETF', expense: 0.12 },
    { symbol: 'SCHH', name: 'Schwab U.S. REIT ETF', expense: 0.07 },
    { symbol: 'IYR', name: 'iShares U.S. Real Estate ETF', expense: 0.41 },
  ],
  commodities: [
    { symbol: 'GLD', name: 'SPDR Gold Shares', expense: 0.40 },
    { symbol: 'DBC', name: 'Invesco DB Commodity Index Tracking Fund', expense: 0.85 },
    { symbol: 'PDBC', name: 'Invesco Optimum Yield Diversified Commodity Strategy', expense: 0.59 },
  ],
  cash: [
    { symbol: 'SHV', name: 'iShares Short Treasury Bond ETF', expense: 0.15 },
    { symbol: 'BIL', name: 'SPDR Bloomberg 1-3 Month T-Bill ETF', expense: 0.14 },
    { symbol: 'SGOV', name: 'iShares 0-3 Month Treasury Bond ETF', expense: 0.07 },
  ],
};

// Asset class educational content
const ASSET_CLASS_EDUCATION = {
  us_stocks: {
    title: 'U.S. Stocks',
    description: 'Represent ownership in U.S. companies. Higher risk but potentially higher returns over the long term.',
    examples: ['Apple', 'Microsoft', 'Amazon'],
    riskLevel: 'Medium to High',
    timeHorizon: 'Long-term (5+ years)',
  },
  intl_stocks: {
    title: 'International Stocks',
    description: 'Represent ownership in companies outside the U.S. Provides global diversification but may have additional risks.',
    examples: ['Toyota', 'Nestle', 'Samsung'],
    riskLevel: 'Medium to High',
    timeHorizon: 'Long-term (5+ years)',
  },
  bonds: {
    title: 'Bonds',
    description: 'Loans to governments or companies. Generally lower risk and provide steady income, but with lower potential returns.',
    examples: ['U.S. Treasury Bonds', 'Corporate Bonds', 'Municipal Bonds'],
    riskLevel: 'Low to Medium',
    timeHorizon: 'Medium-term (2-5 years)',
  },
  real_estate: {
    title: 'Real Estate',
    description: 'Investments in property or property-related assets. Can provide both income and growth potential.',
    examples: ['REITs', 'Commercial Real Estate', 'Residential Real Estate'],
    riskLevel: 'Medium',
    timeHorizon: 'Long-term (5+ years)',
  },
  commodities: {
    title: 'Commodities',
    description: 'Physical goods like gold, oil, or agricultural products. Can help protect against inflation but may be volatile.',
    examples: ['Gold', 'Oil', 'Agricultural Products'],
    riskLevel: 'High',
    timeHorizon: 'Medium to Long-term (3+ years)',
  },
  cash: {
    title: 'Cash',
    description: 'Money in savings accounts, money market funds, or short-term government securities. Very low risk but also low return.',
    examples: ['Savings Accounts', 'Money Market Funds', 'Treasury Bills'],
    riskLevel: 'Very Low',
    timeHorizon: 'Short-term (0-2 years)',
  },
};

const PortfolioBuilder: React.FC = () => {
  const theme = useTheme();
  const [allocation, setAllocation] = useState<{ [key: string]: number }>({
    us_stocks: 40,
    intl_stocks: 15,
    bonds: 30,
    real_estate: 5,
    commodities: 5,
    cash: 5,
  });
  const [selectedProfile, setSelectedProfile] = useState<string>('moderate');
  const [portfolioName, setPortfolioName] = useState<string>('My Custom Portfolio');
  const [investmentAmount, setInvestmentAmount] = useState<string>('10000');
  const [saving, setSaving] = useState<boolean>(false);
  const [saved, setSaved] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [riskScore, setRiskScore] = useState<number>(5);
  const [activeAssetClass, setActiveAssetClass] = useState<string | null>(null);
  const [diversificationScore, setDiversificationScore] = useState<number>(85);
  const [showRecommendations, setShowRecommendations] = useState<boolean>(false);

  // Convert allocation to chart data
  const pieChartData = ASSET_CLASSES.map(assetClass => ({
    name: assetClass.name,
    value: allocation[assetClass.id],
    color: assetClass.color,
  }));

  // Calculate ETF allocation
  const calculateEtfAllocations = () => {
    const amount = parseFloat(investmentAmount) || 0;
    const allocations: any = {};
    
    Object.keys(allocation).forEach(assetClass => {
      const percentage = allocation[assetClass] / 100;
      const assetAmount = amount * percentage;
      const key = assetClass as keyof typeof SUGGESTED_ETFS;

      if (assetAmount > 0 && SUGGESTED_ETFS[key]) {
        // Use first ETF for each asset class as default
        const etf = SUGGESTED_ETFS[key][0];
        allocations[etf.symbol] = {
          amount: assetAmount,
          percentage: percentage * 100,
          assetClass: assetClass,
          name: etf.name,
        };
      }
    });
    
    return allocations;
  };

  // Calculate risk score based on allocation
  useEffect(() => {
    let score = 0;
    let totalWeight = 0;
    
    ASSET_CLASSES.forEach(assetClass => {
      const weight = allocation[assetClass.id] / 100;
      score += assetClass.riskScore * weight;
      totalWeight += weight;
    });
    
    setRiskScore(Math.round(score / totalWeight));
    
    // Calculate diversification score
    const activeDiversifiers = Object.keys(allocation).filter(key => allocation[key] > 0).length;
    const maxDiversity = ASSET_CLASSES.length;
    const rawScore = (activeDiversifiers / maxDiversity) * 100;
    
    // Penalize if any single asset class is > 60%
    const hasConcentration = Object.values(allocation).some(val => val > 60);
    
    setDiversificationScore(hasConcentration ? rawScore * 0.8 : rawScore);
    
  }, [allocation]);

  // Handle slider change
  const handleAllocationChange = (assetClass: string, newValue: number) => {
    // Calculate total of all other allocations
    const currentTotal = Object.keys(allocation)
      .filter(key => key !== assetClass)
      .reduce((sum, key) => sum + allocation[key], 0);
    
    // Calculate the maximum possible value for this asset class
    const maxValue = 100 - currentTotal;
    
    // Ensure the new value doesn't exceed the maximum
    const adjustedValue = Math.min(newValue, maxValue);
    
    setAllocation(prev => ({
      ...prev,
      [assetClass]: adjustedValue,
    }));
    
    // Reset selected profile if user makes manual changes
    setSelectedProfile('custom');
  };

  // Handle risk profile selection
  const handleProfileSelect = (profileId: string) => {
    setSelectedProfile(profileId);
    
    if (profileId !== 'custom') {
      const profile = RISK_PROFILES.find(p => p.id === profileId);
      if (profile) {
        setAllocation(profile.allocation);
      }
    }
  };

  // Save portfolio
  const handleSavePortfolio = () => {
    setSaving(true);
    setError(null);
    
    // Simulate API call
    setTimeout(() => {
      try {
        // This would be a real API call in a production app
        console.log('Saving portfolio:', {
          name: portfolioName,
          allocation,
          investmentAmount: parseFloat(investmentAmount),
          riskProfile: selectedProfile,
          etfAllocations: calculateEtfAllocations(),
        });
        
        setSaved(true);
        setSaving(false);
        
        // Reset saved status after 3 seconds
        setTimeout(() => {
          setSaved(false);
        }, 3000);
      } catch (err) {
        console.error('Error saving portfolio:', err);
        setError('Failed to save portfolio. Please try again.');
        setSaving(false);
      }
    }, 1500);
  };

  // Handle investment amount change
  const handleInvestmentAmountChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    // Only allow numbers
    if (/^\d*$/.test(value)) {
      setInvestmentAmount(value);
    }
  };

  // Calculate allocation colors based on percentage
  const getAllocationColor = (percentage: number) => {
    if (percentage === 0) return theme.palette.text.disabled;
    if (percentage < 5) return theme.palette.warning.main;
    if (percentage > 60) return theme.palette.error.main;
    return theme.palette.success.main;
  };

  // Handle view asset class details
  const handleViewAssetClass = (assetClassId: string) => {
    setActiveAssetClass(assetClassId === activeAssetClass ? null : assetClassId);
  };

  // Toggle ETF recommendations
  const handleToggleRecommendations = () => {
    setShowRecommendations(!showRecommendations);
  };

  return (
    <Box sx={{ mb: 4 }}>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <DonutLarge sx={{ mr: 1.5, color: 'primary.main' }} />
        Portfolio Builder
        <EducationalTooltip
          term="Portfolio Builder"
          definition="Create a diversified investment portfolio based on your risk profile and financial goals."
          placement="right"
        />
      </Typography>
      
      <Grid container spacing={3}>
        {/* Left Column - Allocation Controls */}
        <Grid item xs={12} md={6}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Settings
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <TextField
                  label="Portfolio Name"
                  variant="outlined"
                  fullWidth
                  value={portfolioName}
                  onChange={(e) => setPortfolioName(e.target.value)}
                  margin="normal"
                />
                
                <TextField
                  label="Investment Amount ($)"
                  variant="outlined"
                  fullWidth
                  value={investmentAmount}
                  onChange={handleInvestmentAmountChange}
                  margin="normal"
                  InputProps={{
                    startAdornment: <Box component="span" sx={{ mr: 1 }}>$</Box>
                  }}
                />
              </Box>
              
              <Typography variant="subtitle1" gutterBottom>
                Risk Profile
                <EducationalTooltip
                  term="Risk Profile"
                  definition="Your risk profile determines how your portfolio is allocated between different types of investments, balancing potential returns with risk."
                  placement="right"
                />
              </Typography>
              
              <Grid container spacing={2} sx={{ mb: 3 }}>
                {RISK_PROFILES.map((profile) => (
                  <Grid item xs={6} sm={3} key={profile.id}>
                    <Paper
                      elevation={0}
                      sx={{
                        p: 2,
                        textAlign: 'center',
                        cursor: 'pointer',
                        border: '1px solid',
                        borderColor: selectedProfile === profile.id ? 'primary.main' : 'divider',
                        bgcolor: selectedProfile === profile.id ? 'primary.light' : 'background.paper',
                        color: selectedProfile === profile.id ? 'primary.contrastText' : 'text.primary',
                        '&:hover': {
                          bgcolor: selectedProfile === profile.id ? 'primary.light' : 'action.hover',
                        },
                        position: 'relative',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                      }}
                      onClick={() => handleProfileSelect(profile.id)}
                    >
                      <Typography variant="subtitle2">{profile.name}</Typography>
                      <Box 
                        sx={{ 
                          display: 'flex', 
                          justifyContent: 'center', 
                          mt: 1,
                          alignItems: 'center' 
                        }}
                      >
                        {[...Array(10)].map((_, i) => (
                          <Box
                            key={i}
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              mx: 0.2,
                              bgcolor: i < profile.riskScore ? 'error.main' : 'divider',
                            }}
                          />
                        ))}
                      </Box>
                      <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                        Ages: {profile.ageRange}
                      </Typography>
                      {selectedProfile === profile.id && (
                        <Box 
                          sx={{ 
                            position: 'absolute', 
                            top: 8, 
                            right: 8,
                            color: 'primary.dark' 
                          }}
                        >
                          <Done fontSize="small" />
                        </Box>
                      )}
                    </Paper>
                  </Grid>
                ))}
              </Grid>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="subtitle1" gutterBottom>
                Asset Allocation
                <EducationalTooltip
                  term="Asset Allocation"
                  definition="The distribution of your investments across different asset classes like stocks, bonds, and cash."
                  placement="right"
                />
              </Typography>
              
              {/* Asset Allocation Sliders */}
              {ASSET_CLASSES.map((assetClass) => (
                <Box key={assetClass.id} sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography
                        variant="body2"
                        onClick={() => handleViewAssetClass(assetClass.id)}
                        sx={{ 
                          cursor: 'pointer',
                          fontWeight: activeAssetClass === assetClass.id ? 'bold' : 'normal',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                      >
                        <Box
                          component="span"
                          sx={{
                            display: 'inline-block',
                            width: 12,
                            height: 12,
                            borderRadius: '50%',
                            bgcolor: assetClass.color,
                            mr: 1,
                          }}
                        />
                        {assetClass.name}
                        <Info 
                          fontSize="small" 
                          sx={{ 
                            ml: 0.5, 
                            color: 'action.active',
                            opacity: 0.6,
                            fontSize: 16
                          }} 
                        />
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <IconButton
                        size="small"
                        onClick={() => {
                          const currentValue = allocation[assetClass.id];
                          if (currentValue > 0) {
                            handleAllocationChange(assetClass.id, currentValue - 5);
                          }
                        }}
                        disabled={allocation[assetClass.id] === 0}
                      >
                        <Remove fontSize="small" />
                      </IconButton>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          mx: 1, 
                          fontWeight: 'bold',
                          color: getAllocationColor(allocation[assetClass.id]),
                          minWidth: '36px',
                          textAlign: 'center'
                        }}
                      >
                        {allocation[assetClass.id]}%
                      </Typography>
                      <IconButton
                        size="small"
                        onClick={() => {
                          const currentValue = allocation[assetClass.id];
                          const otherTotal = Object.keys(allocation)
                            .filter(key => key !== assetClass.id)
                            .reduce((sum, key) => sum + allocation[key], 0);
                          
                          if (otherTotal > 0) {
                            handleAllocationChange(assetClass.id, currentValue + 5);
                          }
                        }}
                        disabled={Object.keys(allocation)
                          .filter(key => key !== assetClass.id)
                          .reduce((sum, key) => sum + allocation[key], 0) === 0}
                      >
                        <Add fontSize="small" />
                      </IconButton>
                    </Box>
                  </Box>
                  <Slider
                    value={allocation[assetClass.id]}
                    onChange={(_, newValue) => handleAllocationChange(assetClass.id, newValue as number)}
                    aria-labelledby={`${assetClass.id}-slider`}
                    step={5}
                    marks
                    min={0}
                    max={100}
                    sx={{
                      color: assetClass.color,
                      height: 8,
                      '& .MuiSlider-track': {
                        border: 'none',
                      },
                      '& .MuiSlider-thumb': {
                        height: 16,
                        width: 16,
                        '&:focus, &:hover, &.Mui-active, &.Mui-focusVisible': {
                          boxShadow: 'inherit',
                        },
                      },
                    }}
                  />
                </Box>
              ))}
              
              {/* Active Asset Class Details */}
              {activeAssetClass && (() => {
                const eduKey = activeAssetClass as keyof typeof ASSET_CLASS_EDUCATION;
                const education = ASSET_CLASS_EDUCATION[eduKey];
                return (
                  <Paper
                    variant="outlined"
                    sx={{ p: 2, mt: 2, bgcolor: 'background.paper' }}
                  >
                    <Typography variant="subtitle2" color="primary" gutterBottom>
                      {education.title}
                    </Typography>
                    <Typography variant="body2" paragraph>
                      {education.description}
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Risk Level
                        </Typography>
                        <Typography variant="body2">
                          {education.riskLevel}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="caption" color="text.secondary">
                          Recommended Time Horizon
                        </Typography>
                        <Typography variant="body2">
                          {education.timeHorizon}
                        </Typography>
                      </Grid>
                    </Grid>
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="caption" color="text.secondary">
                        Examples
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                        {education.examples.map((example, index) => (
                          <Chip key={index} label={example} size="small" />
                        ))}
                      </Box>
                    </Box>
                  </Paper>
                );
              })()}
              
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={() => handleProfileSelect('moderate')}
                  sx={{ mr: 2 }}
                >
                  Reset
                </Button>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleSavePortfolio}
                  disabled={saving}
                  startIcon={saving ? <CircularProgress size={20} /> : <Save />}
                >
                  {saving ? 'Saving...' : 'Save Portfolio'}
                </Button>
              </Box>
              
              {saved && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  Portfolio saved successfully!
                </Alert>
              )}
              
              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Right Column - Visualization */}
        <Grid item xs={12} md={6}>
          {/* Portfolio Visualization */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Portfolio Visualization
              </Typography>
              
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Legend />
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              {/* Portfolio Metrics */}
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Risk Score
                    <EducationalTooltip
                      term="Risk Score"
                      definition="A measure of the overall risk level of your portfolio on a scale of 1-10. Higher scores indicate higher risk and potentially higher returns."
                      placement="top"
                    />
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">Low Risk</Typography>
                        <Typography variant="caption" color="text.secondary">High Risk</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ flexGrow: 1 }}>
                          <Box sx={{ display: 'flex' }}>
                            {[...Array(10)].map((_, i) => (
                              <Box
                                key={i}
                                sx={{
                                  width: '100%',
                                  height: 8,
                                  bgcolor: i < riskScore ? 'error.main' : 'divider',
                                  mx: 0.1,
                                  borderRadius: i === 0 ? '4px 0 0 4px' : i === 9 ? '0 4px 4px 0' : 0,
                                }}
                              />
                            ))}
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                    <Typography variant="h6" color="error">{riskScore}</Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Diversification Score
                    <EducationalTooltip
                      term="Diversification Score"
                      definition="A measure of how well your investments are spread across different asset classes to reduce risk."
                      placement="top"
                    />
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">Poor</Typography>
                        <Typography variant="caption" color="text.secondary">Excellent</Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={diversificationScore}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          bgcolor: theme.palette.grey[300],
                          '& .MuiLinearProgress-bar': {
                            bgcolor: diversificationScore < 50 ? 'error.main' : 
                                    diversificationScore < 70 ? 'warning.main' : 'success.main',
                            borderRadius: 4,
                          },
                        }}
                      />
                    </Box>
                    <Typography 
                      variant="h6" 
                      color={
                        diversificationScore < 50 ? 'error.main' : 
                        diversificationScore < 70 ? 'warning.main' : 'success.main'
                      }
                    >
                      {Math.round(diversificationScore)}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
              
              {/* Portfolio Summary */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Investment Breakdown
                </Typography>
                
                {investmentAmount && parseFloat(investmentAmount) > 0 ? (
                  <List dense>
                    {ASSET_CLASSES.filter(asset => allocation[asset.id] > 0).map((asset) => {
                      const amount = (parseFloat(investmentAmount) * allocation[asset.id] / 100).toFixed(2);
                      return (
                        <ListItem key={asset.id}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <Box
                              sx={{
                                width: 12,
                                height: 12,
                                borderRadius: '50%',
                                bgcolor: asset.color,
                              }}
                            />
                          </ListItemIcon>
                          <ListItemText
                            primary={asset.name}
                            secondary={`${allocation[asset.id]}%`}
                          />
                          <Typography variant="body2">${amount}</Typography>
                        </ListItem>
                      );
                    })}
                    <Divider sx={{ my: 1 }} />
                    <ListItem>
                      <ListItemText
                        primary="Total Investment"
                        primaryTypographyProps={{ fontWeight: 'bold' }}
                      />
                      <Typography variant="body2" fontWeight="bold">
                        ${parseFloat(investmentAmount).toLocaleString()}
                      </Typography>
                    </ListItem>
                  </List>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    Enter an investment amount to see the breakdown.
                  </Typography>
                )}
              </Box>
              
              {/* Risk Assessment */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Risk Assessment
                </Typography>
                
                <Alert 
                  severity={
                    riskScore <= 3 ? "info" : 
                    riskScore <= 6 ? "success" : 
                    riskScore <= 8 ? "warning" : "error"
                  }
                  sx={{ mb: 2 }}
                >
                  <AlertTitle>
                    {riskScore <= 3 ? "Conservative Risk" : 
                     riskScore <= 6 ? "Moderate Risk" : 
                     riskScore <= 8 ? "Growth-Oriented" : "Aggressive Growth"}
                  </AlertTitle>
                  {riskScore <= 3 ? 
                    "Your portfolio has a conservative risk profile, focused on capital preservation with modest growth potential." : 
                   riskScore <= 6 ? 
                    "Your portfolio has a balanced risk profile with moderate growth potential while managing downside risk." : 
                   riskScore <= 8 ? 
                    "Your portfolio has a growth-oriented risk profile with higher potential returns and increased volatility." : 
                    "Your portfolio has an aggressive risk profile focused on maximum growth potential with significant volatility."}
                </Alert>
                
                {/* Portfolio Suitability */}
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                  <Typography variant="body2" sx={{ mr: 1 }}>Suitable for ages:</Typography>
                  <Chip 
                    label={
                      riskScore <= 3 ? "8-12, 60+" : 
                      riskScore <= 6 ? "13-17, 45-59" : 
                      riskScore <= 8 ? "18-44" : "18-30"
                    }
                    size="small"
                    color="primary"
                  />
                </Box>
                
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                  <Typography variant="body2" sx={{ mr: 1 }}>Recommended time horizon:</Typography>
                  <Chip 
                    label={
                      riskScore <= 3 ? "1-3 years" : 
                      riskScore <= 6 ? "3-5 years" : 
                      riskScore <= 8 ? "5-10 years" : "10+ years"
                    }
                    size="small"
                    color="secondary"
                  />
                </Box>
              </Box>
              
              {/* Recommendations */}
              <Box sx={{ mt: 3 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  endIcon={showRecommendations ? <ArrowUpward /> : <ArrowDownward />}
                  onClick={handleToggleRecommendations}
                  fullWidth
                >
                  {showRecommendations ? "Hide ETF Recommendations" : "Show ETF Recommendations"}
                </Button>
                
                {showRecommendations && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Recommended ETFs
                      <EducationalTooltip
                        term="ETF"
                        definition="Exchange-Traded Funds are baskets of securities that trade on an exchange like a stock. They offer diversification by holding many different stocks or bonds in a single fund."
                        placement="top"
                      />
                    </Typography>
                    
                    <Grid container spacing={2}>
                      {ASSET_CLASSES.filter(asset => allocation[asset.id] > 0).map((asset) => (
                        <Grid item xs={12} key={asset.id}>
                          <Paper variant="outlined" sx={{ p: 1.5 }}>
                            <Typography variant="subtitle2" sx={{ mb: 1, color: asset.color }}>
                              {asset.name} ({allocation[asset.id]}%)
                            </Typography>
                            
                            <List dense disablePadding>
                              {SUGGESTED_ETFS[asset.id as keyof typeof SUGGESTED_ETFS].map((etf, index) => (
                                <ListItem 
                                  key={etf.symbol}
                                  selected={index === 0}
                                  sx={{ 
                                    borderRadius: 1,
                                    mb: 0.5,
                                    bgcolor: index === 0 ? `${asset.color}10` : 'transparent'
                                  }}
                                >
                                  <ListItemText
                                    primary={
                                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                        <Typography variant="body2" fontWeight="bold" sx={{ mr: 1 }}>
                                          {etf.symbol}
                                        </Typography>
                                        {index === 0 && (
                                          <Chip 
                                            label="Recommended" 
                                            size="small" 
                                            color="primary" 
                                            variant="outlined" 
                                            sx={{ height: 20, fontSize: '0.625rem' }}
                                          />
                                        )}
                                      </Box>
                                    }
                                    secondary={etf.name}
                                    secondaryTypographyProps={{ variant: 'caption' }}
                                  />
                                  <Typography variant="caption" color="text.secondary">
                                    {etf.expense}% fee
                                  </Typography>
                                </ListItem>
                              ))}
                            </List>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                    
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<PlayArrow />}
                        onClick={() => {
                          // Handle implementation
                          console.log('Implement portfolio with recommended ETFs');
                        }}
                      >
                        Implement with Recommended ETFs
                      </Button>
                    </Box>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioBuilder;