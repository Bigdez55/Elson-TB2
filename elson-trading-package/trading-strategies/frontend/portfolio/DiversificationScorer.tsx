import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  List,
  ListItem,
  ListItemText,
  LinearProgress,
  Divider,
  Chip,
  Button,
  Alert,
  AlertTitle,
  useTheme,
} from '@mui/material';
import {
  AssessmentOutlined,
  WarningAmber,
  CheckCircle,
  Info,
  ArrowForward,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';
import EducationalTooltip from '../common/EducationalTooltip';

interface DiversificationScorerProps {
  portfolioData?: any;
  standalone?: boolean;
  onAnalyzeComplete?: (score: number, issues: string[], strengths: string[]) => void;
}

const DiversificationScorer: React.FC<DiversificationScorerProps> = ({
  portfolioData,
  standalone = true,
  onAnalyzeComplete
}) => {
  const theme = useTheme();
  const [score, setScore] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [assetConcentration, setAssetConcentration] = useState<number>(0);
  const [sectors, setSectors] = useState<{ [key: string]: number }>({});
  const [issues, setIssues] = useState<string[]>([]);
  const [strengths, setStrengths] = useState<string[]>([]);
  
  // Mock portfolio data for demonstration
  const demoPortfolio = {
    allocation: {
      'US Stocks': 45,
      'International Stocks': 15,
      'Bonds': 25,
      'Real Estate': 5,
      'Commodities': 5,
      'Cash': 5,
    },
    sectors: {
      'Technology': 30,
      'Healthcare': 12,
      'Financial': 15,
      'Consumer Cyclical': 8,
      'Industrial': 10,
      'Energy': 5,
      'Utilities': 5,
      'Basic Materials': 5,
      'Communication Services': 5,
      'Consumer Defensive': 5,
    },
    holdings: [
      { symbol: 'AAPL', name: 'Apple Inc.', percentage: 12, sector: 'Technology' },
      { symbol: 'MSFT', name: 'Microsoft Corp.', percentage: 10, sector: 'Technology' },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', percentage: 8, sector: 'Consumer Cyclical' },
      { symbol: 'JNJ', name: 'Johnson & Johnson', percentage: 5, sector: 'Healthcare' },
      { symbol: 'JPM', name: 'JPMorgan Chase & Co.', percentage: 5, sector: 'Financial' },
      { symbol: 'V', name: 'Visa Inc.', percentage: 4, sector: 'Financial' },
      { symbol: 'PG', name: 'Procter & Gamble Co.', percentage: 3, sector: 'Consumer Defensive' },
      { symbol: 'UNH', name: 'UnitedHealth Group Inc.', percentage: 3, sector: 'Healthcare' },
      { symbol: 'HD', name: 'Home Depot Inc.', percentage: 3, sector: 'Consumer Cyclical' },
      { symbol: 'NVDA', name: 'NVIDIA Corp.', percentage: 3, sector: 'Technology' },
      { symbol: 'Other', name: 'Other Holdings', percentage: 44, sector: 'Various' },
    ]
  };
  
  const actualPortfolio = portfolioData || demoPortfolio;
  
  // Analyze the portfolio diversification
  const analyzePortfolio = () => {
    setLoading(true);
    
    // Simulate API call or complex calculation
    setTimeout(() => {
      try {
        // 1. Analyze asset class diversification
        const assetClassCount = Object.keys(actualPortfolio.allocation).length;
        const assetClassScore = Math.min(assetClassCount * 10, 50); // Max 50 points for asset classes
        
        // 2. Check for over-concentration in any single asset class
        const maxAssetClass = Math.max(...Object.values(actualPortfolio.allocation).map(Number));
        setAssetConcentration(maxAssetClass);
        
        const concentrationPenalty = maxAssetClass > 60 ? 30 : 
                                    maxAssetClass > 50 ? 20 : 
                                    maxAssetClass > 40 ? 10 : 0;
        
        // 3. Analyze sector diversification
        const sectorCount = Object.keys(actualPortfolio.sectors).length;
        const sectorScore = Math.min(sectorCount * 5, 30); // Max 30 points for sectors
        
        // 4. Individual holding concentration
        const individualHoldings = actualPortfolio.holdings.filter(h => h.symbol !== 'Other');
        const individualScore = individualHoldings.length >= 20 ? 20 :
                               individualHoldings.length >= 15 ? 15 :
                               individualHoldings.length >= 10 ? 10 :
                               individualHoldings.length >= 5 ? 5 : 0;
        
        // Calculate final score (out of 100)
        const calculatedScore = Math.min(
          Math.max(
            assetClassScore + sectorScore + individualScore - concentrationPenalty,
            0
          ),
          100
        );
        
        setScore(calculatedScore);
        setSectors(actualPortfolio.sectors);
        
        // Set issues and strengths
        const calculatedIssues = [];
        const calculatedStrengths = [];
        
        // Issues
        if (assetClassCount < 4) {
          calculatedIssues.push("Limited asset class diversification");
        }
        if (maxAssetClass > 40) {
          calculatedIssues.push(`Over-concentration in ${Object.keys(actualPortfolio.allocation).find(
            key => actualPortfolio.allocation[key] === maxAssetClass
          )} (${maxAssetClass}%)`);
        }
        if (sectorCount < 8) {
          calculatedIssues.push("Limited sector diversification");
        }
        if (individualHoldings.length < 10) {
          calculatedIssues.push("Limited number of individual holdings");
        }
        
        const techConcentration = actualPortfolio.sectors['Technology'] || 0;
        if (techConcentration > 25) {
          calculatedIssues.push(`High technology sector concentration (${techConcentration}%)`);
        }
        
        // Strengths
        if (assetClassCount >= 5) {
          calculatedStrengths.push("Good asset class diversification");
        }
        if (maxAssetClass < 35) {
          calculatedStrengths.push("Well-balanced asset allocation");
        }
        if (sectorCount >= 8) {
          calculatedStrengths.push("Strong sector diversification");
        }
        if (individualHoldings.length >= 15) {
          calculatedStrengths.push("Good number of individual holdings");
        }
        
        setIssues(calculatedIssues);
        setStrengths(calculatedStrengths);
        
        // Call the callback if provided
        if (onAnalyzeComplete) {
          onAnalyzeComplete(calculatedScore, calculatedIssues, calculatedStrengths);
        }
      } catch (error) {
        console.error('Error analyzing portfolio:', error);
      } finally {
        setLoading(false);
      }
    }, 1500);
  };
  
  useEffect(() => {
    if (standalone) {
      analyzePortfolio();
    }
  }, [standalone, portfolioData]);
  
  const getSeverity = (score: number) => {
    if (score >= 80) return "success";
    if (score >= 60) return "info";
    if (score >= 40) return "warning";
    return "error";
  };
  
  const getScoreMessage = (score: number) => {
    if (score >= 80) return "Excellent diversification";
    if (score >= 60) return "Good diversification";
    if (score >= 40) return "Moderate diversification";
    return "Poor diversification";
  };
  
  // Convert asset allocation to chart data
  const assetData = Object.keys(actualPortfolio.allocation).map(key => ({
    name: key,
    value: actualPortfolio.allocation[key],
  }));
  
  // Convert sector allocation to chart data
  const sectorData = Object.keys(actualPortfolio.sectors).map(key => ({
    name: key,
    value: actualPortfolio.sectors[key],
  }));
  
  // Color generator for charts
  const COLORS = [
    '#3f51b5', '#2196f3', '#4caf50', '#ff9800', '#f44336', 
    '#9c27b0', '#673ab7', '#00bcd4', '#009688', '#cddc39'
  ];
  
  return (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <AssessmentOutlined sx={{ mr: 1.5, color: 'primary.main' }} />
          Portfolio Diversification Analysis
          <EducationalTooltip
            term="Diversification"
            definition="Spreading investments across various asset types to reduce risk by ensuring that a single event doesn't significantly impact your entire portfolio."
            placement="right"
          />
        </Typography>
        
        {loading ? (
          <Box sx={{ mt: 3, mb: 3 }}>
            <Typography variant="body1" align="center" gutterBottom>
              Analyzing portfolio diversification...
            </Typography>
            <LinearProgress sx={{ mt: 2 }} />
          </Box>
        ) : score !== null ? (
          <>
            {/* Diversification Score */}
            <Box sx={{ mt: 3, mb: 4, textAlign: 'center' }}>
              <Typography variant="h4" sx={{ mb: 1 }}>
                {getScoreMessage(score)}
              </Typography>
              
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Box sx={{ position: 'relative', display: 'inline-flex', mr: 3 }}>
                  <Box
                    sx={{
                      width: 120,
                      height: 120,
                      borderRadius: '50%',
                      border: '12px solid',
                      borderColor: getSeverity(score) === 'success' ? 'success.main' :
                                 getSeverity(score) === 'info' ? 'info.main' :
                                 getSeverity(score) === 'warning' ? 'warning.main' : 'error.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <Typography variant="h3" component="div" color="text.primary">
                      {score}
                    </Typography>
                  </Box>
                </Box>
                
                <Box sx={{ textAlign: 'left' }}>
                  <Typography variant="body1" gutterBottom>
                    Diversification Score (out of 100)
                  </Typography>
                  <Chip 
                    icon={
                      getSeverity(score) === 'success' ? <CheckCircle /> :
                      getSeverity(score) === 'info' ? <Info /> :
                      getSeverity(score) === 'warning' ? <WarningAmber /> : <WarningAmber />
                    } 
                    label={getScoreMessage(score)} 
                    color={
                      getSeverity(score) === 'success' ? 'success' :
                      getSeverity(score) === 'info' ? 'info' :
                      getSeverity(score) === 'warning' ? 'warning' : 'error'
                    }
                    variant="outlined"
                  />
                </Box>
              </Box>
            </Box>
            
            <Divider sx={{ mb: 3 }} />
            
            {/* Issues and Strengths */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Diversification Issues
                </Typography>
                
                {issues.length > 0 ? (
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'error.light', color: 'error.contrastText' }}>
                    <List dense disablePadding>
                      {issues.map((issue, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemText 
                            primary={issue}
                            primaryTypographyProps={{ 
                              variant: 'body2',
                              sx: { display: 'flex', alignItems: 'center' }
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                ) : (
                  <Typography variant="body2" color="success.main">
                    No major diversification issues detected.
                  </Typography>
                )}
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Diversification Strengths
                </Typography>
                
                {strengths.length > 0 ? (
                  <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
                    <List dense disablePadding>
                      {strengths.map((strength, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemText 
                            primary={strength}
                            primaryTypographyProps={{ 
                              variant: 'body2',
                              sx: { display: 'flex', alignItems: 'center' }
                            }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                ) : (
                  <Typography variant="body2" color="warning.main">
                    Your portfolio needs improvement in diversification.
                  </Typography>
                )}
              </Grid>
            </Grid>
            
            {/* Asset Class and Sector Analysis */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Asset Class Allocation
                  <EducationalTooltip
                    term="Asset Class"
                    definition="A group of investments with similar characteristics and subject to the same laws and regulations. Common asset classes include stocks, bonds, cash, real estate, and commodities."
                    placement="top"
                  />
                </Typography>
                
                <Box sx={{ height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={assetData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {assetData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend />
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
                
                {assetConcentration > 40 && (
                  <Alert severity="warning" sx={{ mt: 2 }}>
                    <AlertTitle>Concentration Warning</AlertTitle>
                    You have {assetConcentration}% of your portfolio in a single asset class, which may increase risk.
                  </Alert>
                )}
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Sector Allocation
                  <EducationalTooltip
                    term="Sector"
                    definition="A segment of the economy or industry. Sectors represent different parts of the market like Technology, Healthcare, Financial, etc."
                    placement="top"
                  />
                </Typography>
                
                <Box sx={{ height: 250 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={sectorData}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {sectorData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Legend />
                      <RechartsTooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </Box>
                
                {actualPortfolio.sectors['Technology'] > 25 && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    <AlertTitle>Sector Concentration</AlertTitle>
                    Your technology sector allocation ({actualPortfolio.sectors['Technology']}%) is higher than average, consider if this aligns with your risk tolerance.
                  </Alert>
                )}
              </Grid>
            </Grid>
            
            {/* Improvement Recommendations */}
            <Box sx={{ mt: 4 }}>
              <Typography variant="subtitle1" gutterBottom>
                Recommendations to Improve Diversification
              </Typography>
              
              <Paper variant="outlined" sx={{ p: 2 }}>
                <List>
                  {issues.length > 0 ? (
                    issues.map((issue, index) => {
                      // Generate recommendation based on issue
                      let recommendation = "";
                      if (issue.includes("asset class")) {
                        recommendation = "Consider adding more asset classes to your portfolio, such as international stocks, bonds, or real estate.";
                      } else if (issue.includes("Over-concentration")) {
                        recommendation = "Reduce allocation to your largest asset class and redistribute to other classes.";
                      } else if (issue.includes("sector")) {
                        recommendation = "Expand your investments across more sectors to reduce sector-specific risks.";
                      } else if (issue.includes("holdings")) {
                        recommendation = "Increase the number of individual holdings or consider using ETFs for broader exposure.";
                      } else if (issue.includes("technology")) {
                        recommendation = "Consider reducing your technology exposure and redistributing to underrepresented sectors.";
                      }
                      
                      return (
                        <ListItem key={index} sx={{ py: 1.5 }}>
                          <ListItemText
                            primary={recommendation}
                            secondary={`Addresses: ${issue}`}
                          />
                        </ListItem>
                      );
                    })
                  ) : (
                    <ListItem>
                      <ListItemText
                        primary="Your portfolio demonstrates strong diversification practices."
                        secondary="Continue monitoring and rebalancing periodically to maintain diversification."
                      />
                    </ListItem>
                  )}
                </List>
                
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button
                    variant="contained"
                    color="primary"
                    endIcon={<ArrowForward />}
                    onClick={() => {
                      // Handle navigation to portfolio builder
                      window.location.href = '/portfolio-builder';
                    }}
                  >
                    Adjust Portfolio Allocation
                  </Button>
                </Box>
              </Paper>
            </Box>
            
            {/* Educational Section */}
            <Box sx={{ mt: 4 }}>
              <Typography variant="subtitle1" gutterBottom>
                Why Diversification Matters
              </Typography>
              
              <Paper variant="outlined" sx={{ p: 2, bgcolor: 'info.light', color: 'info.contrastText' }}>
                <Typography variant="body2" paragraph>
                  Diversification is a risk management strategy that mixes a variety of investments within a portfolio. The rationale is that a portfolio constructed of different kinds of assets will, on average, yield higher returns and pose a lower risk than any individual investment within the portfolio.
                </Typography>
                <Typography variant="body2" paragraph>
                  <strong>Key benefits of diversification:</strong>
                </Typography>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Reduces unsystematic risk without sacrificing potential returns" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Protects against market volatility and economic downturns" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Provides exposure to different growth opportunities" />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Creates a more stable portfolio performance over time" />
                  </ListItem>
                </List>
                <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                  Remember: Diversification does not guarantee profits or protect against losses in declining markets, but it is an important strategy for reaching long-term financial goals while minimizing risk.
                </Typography>
              </Paper>
            </Box>
          </>
        ) : (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={analyzePortfolio}
            >
              Analyze Portfolio Diversification
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default DiversificationScorer;