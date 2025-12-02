import React, { useState, useEffect } from 'react';
import { Card, CardContent, Typography, Box, CircularProgress, Divider, Chip, LinearProgress, List, ListItem, ListItemText, Alert, useTheme, useMediaQuery } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import api from '../../services/api';
import ResponsiveContainer from '../common/ResponsiveContainer';

interface RiskMetrics {
  diversification_score: number;
  volatility: number;
  beta: number;
  sharpe_ratio: number;
  max_drawdown: number;
  value_at_risk: number;
  expected_return: number;
  risk_rating: number;
}

interface RiskProfileReport {
  user_id: number;
  risk_profile: string;
  portfolio_id: number;
  metrics: RiskMetrics;
  limits: {
    max_volatility: number;
    max_drawdown: number;
  };
  is_compliant: boolean;
  warnings: string[];
  recommendations: string[];
}

const RiskAnalysisPanel: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [riskReport, setRiskReport] = useState<RiskProfileReport | null>(null);
  
  useEffect(() => {
    const fetchRiskReport = async () => {
      try {
        setLoading(true);
        const response = await api.get('/v1/risk/portfolio-assessment');
        setRiskReport(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching risk report:', err);
        setError('Failed to load risk assessment. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchRiskReport();
  }, []);
  
  const getRiskRatingColor = (rating: number): string => {
    if (rating <= 3) return '#4caf50'; // Green - Low risk
    if (rating <= 6) return '#ff9800'; // Orange - Medium risk
    return '#f44336'; // Red - High risk
  };
  
  const formatPercentage = (value: number): string => {
    return `${(value * 100).toFixed(1)}%`;
  };
  
  if (loading) {
    return (
      <Card>
        <CardContent sx={{ p: isMobile ? 2 : 3 }}>
          <Typography variant={isMobile ? "subtitle1" : "h6"} gutterBottom>Risk Analysis</Typography>
          <Box display="flex" justifyContent="center" p={isMobile ? 1 : 2}>
            <CircularProgress size={isMobile ? 30 : 40} />
          </Box>
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card>
        <CardContent sx={{ p: isMobile ? 2 : 3 }}>
          <Typography variant={isMobile ? "subtitle1" : "h6"} gutterBottom>Risk Analysis</Typography>
          <Alert severity="error" sx={{ fontSize: isMobile ? '0.85rem' : undefined }}>{error}</Alert>
        </CardContent>
      </Card>
    );
  }
  
  if (!riskReport) {
    return (
      <Card>
        <CardContent sx={{ p: isMobile ? 2 : 3 }}>
          <Typography variant={isMobile ? "subtitle1" : "h6"} gutterBottom>Risk Analysis</Typography>
          <Alert severity="info" sx={{ fontSize: isMobile ? '0.85rem' : undefined }}>No risk data available.</Alert>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardContent sx={{ p: isMobile ? 2 : 3 }}>
        <ResponsiveContainer
          mobileClasses="flex flex-col items-start"
          desktopClasses="flex flex-row items-center justify-between"
          className="mb-4 gap-y-2"
        >
          <Typography variant={isMobile ? "subtitle1" : "h6"}>Risk Analysis</Typography>
          <Chip 
            icon={riskReport.is_compliant ? <CheckCircleOutlineIcon fontSize={isMobile ? "small" : "medium"} /> : <ErrorOutlineIcon fontSize={isMobile ? "small" : "medium"} />}
            label={riskReport.is_compliant ? "Within Limits" : "Exceeds Limits"}
            color={riskReport.is_compliant ? "success" : "error"}
            size={isMobile ? "small" : "medium"}
          />
        </ResponsiveContainer>
        
        <Typography variant={isMobile ? "body1" : "subtitle1"} gutterBottom fontWeight="medium">
          Risk Profile: <strong style={{ textTransform: 'capitalize' }}>{riskReport.risk_profile}</strong>
        </Typography>
        
        <Box mb={isMobile ? 2 : 3}>
          <Typography variant="body2" color="textSecondary" gutterBottom fontSize={isMobile ? "0.75rem" : undefined}>
            Risk Rating
          </Typography>
          <Box display="flex" alignItems="center">
            <Box width="100%" mr={1}>
              <LinearProgress 
                variant="determinate" 
                value={riskReport.metrics.risk_rating * 10} 
                sx={{ 
                  height: isMobile ? 8 : 10, 
                  borderRadius: 5,
                  backgroundColor: '#e0e0e0',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getRiskRatingColor(riskReport.metrics.risk_rating)
                  }
                }}
              />
            </Box>
            <Box minWidth={35}>
              <Typography variant="body2" color="textSecondary" fontSize={isMobile ? "0.75rem" : undefined}>
                {riskReport.metrics.risk_rating.toFixed(1)}/10
              </Typography>
            </Box>
          </Box>
        </Box>
        
        <Divider sx={{ my: isMobile ? 1.5 : 2 }} />
        
        <Typography variant={isMobile ? "body1" : "subtitle2"} gutterBottom fontWeight="medium">Key Metrics</Typography>
        <ResponsiveContainer className="mb-4">
          <ResponsiveContainer
            className="w-full space-y-2 mb-2"
            desktopClasses="grid grid-cols-2 gap-4 space-y-0"
            breakpoint="sm"
          >
            <Box className="mb-1">
              <Typography variant="body2" color="textSecondary" fontSize={isMobile ? "0.75rem" : undefined}>Volatility</Typography>
              <Typography variant={isMobile ? "body2" : "body1"}>
                {formatPercentage(riskReport.metrics.volatility)}
                {riskReport.metrics.volatility > riskReport.limits.max_volatility && 
                  <ErrorOutlineIcon fontSize="small" color="error" sx={{ ml: 0.5, verticalAlign: 'middle' }} />
                }
              </Typography>
            </Box>
            <Box className="mb-1">
              <Typography variant="body2" color="textSecondary" fontSize={isMobile ? "0.75rem" : undefined}>Max Drawdown</Typography>
              <Typography variant={isMobile ? "body2" : "body1"}>
                {formatPercentage(riskReport.metrics.max_drawdown)}
                {riskReport.metrics.max_drawdown > riskReport.limits.max_drawdown && 
                  <ErrorOutlineIcon fontSize="small" color="error" sx={{ ml: 0.5, verticalAlign: 'middle' }} />
                }
              </Typography>
            </Box>
            <Box className="mb-1">
              <Typography variant="body2" color="textSecondary" fontSize={isMobile ? "0.75rem" : undefined}>Sharpe Ratio</Typography>
              <Typography variant={isMobile ? "body2" : "body1"}>{riskReport.metrics.sharpe_ratio.toFixed(2)}</Typography>
            </Box>
            <Box className="mb-1">
              <Typography variant="body2" color="textSecondary" fontSize={isMobile ? "0.75rem" : undefined}>Diversification</Typography>
              <Typography variant={isMobile ? "body2" : "body1"}>{formatPercentage(riskReport.metrics.diversification_score)}</Typography>
            </Box>
          </ResponsiveContainer>
        </ResponsiveContainer>
        
        {riskReport.warnings.length > 0 && (
          <>
            <Divider sx={{ my: isMobile ? 1.5 : 2 }} />
            <Typography variant={isMobile ? "body1" : "subtitle2"} gutterBottom fontWeight="medium">Warnings</Typography>
            <Alert severity="warning" sx={{ mb: isMobile ? 1.5 : 2, fontSize: isMobile ? '0.85rem' : undefined }}>
              <List dense disablePadding>
                {riskReport.warnings.map((warning, index) => (
                  <ListItem key={index} disableGutters>
                    <ListItemText 
                      primary={warning} 
                      primaryTypographyProps={{ fontSize: isMobile ? '0.8rem' : undefined }}
                    />
                  </ListItem>
                ))}
              </List>
            </Alert>
          </>
        )}
        
        {riskReport.recommendations.length > 0 && (
          <>
            <Divider sx={{ my: isMobile ? 1.5 : 2 }} />
            <Typography variant={isMobile ? "body1" : "subtitle2"} gutterBottom fontWeight="medium">Recommendations</Typography>
            <List dense>
              {riskReport.recommendations.map((recommendation, index) => (
                <ListItem key={index} disableGutters sx={{ py: isMobile ? 0.5 : 1 }}>
                  <ListItemText 
                    primary={recommendation} 
                    primaryTypographyProps={{ fontSize: isMobile ? '0.8rem' : undefined }}
                  />
                </ListItem>
              ))}
            </List>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default RiskAnalysisPanel;