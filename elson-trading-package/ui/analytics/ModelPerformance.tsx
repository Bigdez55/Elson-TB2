import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardHeader, 
  CircularProgress,
  Paper,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
  Alert,
  Button,
  IconButton,
  Tooltip
} from '@mui/material';
import { useSelector } from 'react-redux';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import dayjs, { Dayjs } from 'dayjs';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  Legend, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Bar,
  BarChart
} from 'recharts';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';

import { RootState } from '../../store/store';
import { api } from '../../services/api';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`model-performance-tabpanel-${index}`}
      aria-labelledby={`model-performance-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

interface ModelPerformanceData {
  performance: {
    LOW: RegimePerformance;
    NORMAL: RegimePerformance;
    HIGH: RegimePerformance;
    EXTREME: RegimePerformance;
    summary: SummaryMetrics;
  };
  date_range: {
    start_date: string;
    end_date: string;
  };
}

interface RegimePerformance {
  win_rate: number;
  avg_return: number;
  sharpe_ratio: number;
  sample_count: number;
  best_parameters: any | null;
}

interface SummaryMetrics {
  overall_win_rate: number;
  overall_return: number;
  overall_sharpe: number;
  volatility_robustness: number;
  total_samples: number;
}

interface ModelStatusData {
  status: string;
  volatility_regime: string | null;
  circuit_breaker_status: string;
  current_parameters: any | null;
  timestamp: string;
}

interface ParameterHistoryItem {
  timestamp: string;
  regime: string;
  parameters: {
    lookback_periods: number;
    prediction_horizon: number;
    confidence_threshold: number;
    [key: string]: any;
  };
  performance: {
    win_rate: number;
    avg_return: number;
    sharpe_ratio: number;
  };
}

const VolatilityDashboard: React.FC = () => {
  const [tabIndex, setTabIndex] = useState(0);
  const [startDate, setStartDate] = useState<Dayjs | null>(dayjs().subtract(30, 'day'));
  const [endDate, setEndDate] = useState<Dayjs | null>(dayjs());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [performanceData, setPerformanceData] = useState<ModelPerformanceData | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatusData | null>(null);
  const [parameterHistory, setParameterHistory] = useState<ParameterHistoryItem[]>([]);
  
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);
  const userRole = useSelector((state: RootState) => state.auth.user?.role);
  
  // Colors for the charts
  const COLORS = {
    LOW: '#4caf50',
    NORMAL: '#2196f3',
    HIGH: '#ff9800',
    EXTREME: '#f44336',
  };

  // Load data when component mounts or date range changes
  useEffect(() => {
    if (isAuthenticated && (userRole === 'ADMIN' || userRole === 'PREMIUM')) {
      fetchModelPerformance();
      fetchModelStatus();
      fetchParameterHistory();
    }
  }, [isAuthenticated, userRole, startDate, endDate, fetchModelPerformance, fetchModelStatus, fetchParameterHistory]);

  const fetchModelPerformance = useCallback(async () => {
    if (!startDate || !endDate) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get('/analytics/model-performance/volatility-regimes', {
        params: {
          start_date: startDate.toISOString(),
          end_date: endDate.toISOString()
        }
      });
      
      setPerformanceData(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to load performance data');
      console.error('Error fetching performance data:', err);
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate]);

  const fetchModelStatus = useCallback(async () => {
    try {
      const response = await api.get('/analytics/model-performance/current-status');
      setModelStatus(response.data);
    } catch (err: any) {
      console.error('Error fetching model status:', err);
      // Don't set error state to avoid blocking the main performance data
    }
  }, []);

  const fetchParameterHistory = useCallback(async () => {
    try {
      const response = await api.get('/analytics/model-performance/parameters-history');
      setParameterHistory(response.data);
    } catch (err: any) {
      console.error('Error fetching parameter history:', err);
      // Don't set error state to avoid blocking the main performance data
    }
  }, []);

  const handleRefresh = () => {
    fetchModelPerformance();
    fetchModelStatus();
    fetchParameterHistory();
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  // Format for chart data
  const prepareWinRateChartData = () => {
    if (!performanceData) return [];
    
    const { performance } = performanceData;
    
    // Filter out regimes with no data
    return Object.entries(performance)
      .filter(([regime, data]) => regime !== 'summary' && data.sample_count > 0)
      .map(([regime, data]) => ({
        name: regime,
        winRate: (data.win_rate * 100).toFixed(2),
        sampleCount: data.sample_count,
        avgReturn: data.avg_return.toFixed(2),
        color: COLORS[regime as keyof typeof COLORS]
      }));
  };

  const prepareVolatilityDistributionData = () => {
    if (!performanceData) return [];
    
    const { performance } = performanceData;
    
    return Object.entries(performance)
      .filter(([regime]) => regime !== 'summary')
      .map(([regime, data]) => ({
        name: regime,
        value: data.sample_count,
        color: COLORS[regime as keyof typeof COLORS]
      }));
  };

  const prepareParameterHistoryData = () => {
    return parameterHistory.map(item => ({
      timestamp: dayjs(item.timestamp).format('MM/DD HH:mm'),
      regime: item.regime,
      lookbackPeriods: item.parameters.lookback_periods,
      predictionHorizon: item.parameters.prediction_horizon,
      confidenceThreshold: item.parameters.confidence_threshold,
      winRate: (item.performance.win_rate * 100).toFixed(1),
      color: COLORS[item.regime as keyof typeof COLORS]
    }));
  };

  // Calculate if performance targets are being met
  const calculatePerformanceStatus = () => {
    if (!performanceData) return null;
    
    const { performance } = performanceData;
    const highVolWinRate = performance.HIGH.win_rate * 100;
    const extremeVolWinRate = performance.EXTREME.win_rate * 100;
    const performanceDiff = Math.max(
      performance.LOW.win_rate, 
      performance.NORMAL.win_rate
    ) * 100 - Math.min(
      performance.HIGH.win_rate,
      performance.EXTREME.win_rate
    ) * 100;
    
    const targetsMet = {
      highVolTarget: highVolWinRate >= 65,
      extremeVolTarget: extremeVolWinRate >= 60,
      performanceDiffTarget: performanceDiff <= 10
    };
    
    const overallStatus = 
      targetsMet.highVolTarget && 
      targetsMet.extremeVolTarget && 
      targetsMet.performanceDiffTarget;
    
    return {
      targetsMet,
      overallStatus
    };
  };

  // Data formatting helpers
  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatPercent1Decimal = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatDate = (dateString: string) => {
    return dayjs(dateString).format('MMM D, YYYY HH:mm');
  };

  const getChipColorForRegime = (regime: string) => {
    switch (regime) {
      case 'LOW':
        return 'success';
      case 'NORMAL':
        return 'info';
      case 'HIGH':
        return 'warning';
      case 'EXTREME':
        return 'error';
      default:
        return 'default';
    }
  };

  const getChipColorForCircuitBreaker = (status: string) => {
    switch (status) {
      case 'OPEN':
        return 'error';
      case 'RESTRICTED':
        return 'warning';
      case 'CAUTIOUS':
        return 'info';
      case 'CLOSED':
        return 'success';
      default:
        return 'default';
    }
  };

  if (!isAuthenticated || (userRole !== 'ADMIN' && userRole !== 'PREMIUM')) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="info">
          Please log in with a Premium or Admin account to access the Performance Monitoring Dashboard.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', pb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          Performance Monitoring Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <DatePicker
            label="Start Date"
            value={startDate}
            onChange={setStartDate}
            slotProps={{ textField: { size: 'small' } }}
          />
          <DatePicker
            label="End Date"
            value={endDate}
            onChange={setEndDate}
            slotProps={{ textField: { size: 'small' } }}
          />
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Current Status Card */}
          {modelStatus && (
            <Card sx={{ mb: 4 }}>
              <CardHeader title="Current Model Status" />
              <CardContent>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="subtitle2">Model Status</Typography>
                      <Chip 
                        label={modelStatus.status} 
                        color={modelStatus.status === 'Active' ? 'success' : 'default'} 
                        size="small"
                      />
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="subtitle2">Last Updated</Typography>
                      <Typography variant="body2">
                        {modelStatus.timestamp ? formatDate(modelStatus.timestamp) : 'N/A'}
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="subtitle2">Current Volatility Regime</Typography>
                      {modelStatus.volatility_regime ? (
                        <Chip 
                          label={modelStatus.volatility_regime} 
                          color={getChipColorForRegime(modelStatus.volatility_regime) as any} 
                          size="small"
                        />
                      ) : (
                        <Typography variant="body2">Not available</Typography>
                      )}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Typography variant="subtitle2">Circuit Breaker Status</Typography>
                      <Chip 
                        label={modelStatus.circuit_breaker_status} 
                        color={getChipColorForCircuitBreaker(modelStatus.circuit_breaker_status) as any} 
                        size="small"
                      />
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Performance Status */}
          {performanceData && (
            <Card sx={{ mb: 4 }}>
              <CardHeader 
                title="Performance Targets" 
                action={
                  <Tooltip title="Status of meeting Phase 2 implementation targets">
                    <IconButton>
                      <InfoIcon />
                    </IconButton>
                  </Tooltip>
                }
              />
              <CardContent>
                <Grid container spacing={2}>
                  {calculatePerformanceStatus() && (
                    <>
                      <Grid item xs={12} md={3}>
                        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', height: '100%' }}>
                          <Typography variant="subtitle2" gutterBottom>
                            High Volatility Win Rate
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" component="div">
                              {formatPercent1Decimal(performanceData.performance.HIGH.win_rate)}
                            </Typography>
                            <Chip
                              label={calculatePerformanceStatus()?.targetsMet.highVolTarget ? 'Target Met' : 'Below Target'}
                              color={calculatePerformanceStatus()?.targetsMet.highVolTarget ? 'success' : 'error'}
                              size="small"
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Target: ≥ 65%
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', height: '100%' }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Extreme Volatility Win Rate
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" component="div">
                              {formatPercent1Decimal(performanceData.performance.EXTREME.win_rate)}
                            </Typography>
                            <Chip
                              label={calculatePerformanceStatus()?.targetsMet.extremeVolTarget ? 'Target Met' : 'Below Target'}
                              color={calculatePerformanceStatus()?.targetsMet.extremeVolTarget ? 'success' : 'error'}
                              size="small"
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Target: ≥ 60%
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', height: '100%' }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Performance Differential
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Typography variant="h6" component="div">
                              {performanceData.performance.summary.volatility_robustness.toFixed(1)}%
                            </Typography>
                            <Chip
                              label={calculatePerformanceStatus()?.targetsMet.performanceDiffTarget ? 'Target Met' : 'Above Target'}
                              color={calculatePerformanceStatus()?.targetsMet.performanceDiffTarget ? 'success' : 'error'}
                              size="small"
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            Target: ≤ 10%
                          </Typography>
                        </Paper>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default', height: '100%' }}>
                          <Typography variant="subtitle2" gutterBottom>
                            Overall Status
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                            <Chip
                              label={calculatePerformanceStatus()?.overallStatus ? 'Success' : 'Needs Improvement'}
                              color={calculatePerformanceStatus()?.overallStatus ? 'success' : 'warning'}
                              sx={{ fontWeight: 'bold' }}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                            All targets must be met for success
                          </Typography>
                        </Paper>
                      </Grid>
                    </>
                  )}
                </Grid>
              </CardContent>
            </Card>
          )}

          {/* Tabs for different views */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabIndex} onChange={handleTabChange} aria-label="model performance tabs">
              <Tab label="Performance by Volatility Regime" id="model-performance-tab-0" />
              <Tab label="Volatility Distribution" id="model-performance-tab-1" />
              <Tab label="Parameter Adaptation" id="model-performance-tab-2" />
            </Tabs>
          </Box>

          {/* Performance by Volatility Regime Tab */}
          <TabPanel value={tabIndex} index={0}>
            {performanceData ? (
              <Box>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={8}>
                    <Paper sx={{ p: 2, height: '100%' }}>
                      <Typography variant="h6" gutterBottom>
                        Win Rate by Volatility Regime
                      </Typography>
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart
                          data={prepareWinRateChartData()}
                          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                        >
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis domain={[0, 100]} label={{ value: 'Win Rate (%)', angle: -90, position: 'insideLeft' }} />
                          <RechartsTooltip formatter={(value: any) => [`${value}%`, 'Win Rate']} />
                          <Legend />
                          <Bar dataKey="winRate" name="Win Rate (%)" fill="#8884d8">
                            {prepareWinRateChartData().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, height: '100%' }}>
                      <Typography variant="h6" gutterBottom>
                        Performance Metrics
                      </Typography>
                      <TableContainer>
                        <Table size="small">
                          <TableHead>
                            <TableRow>
                              <TableCell>Regime</TableCell>
                              <TableCell align="right">Win Rate</TableCell>
                              <TableCell align="right">Avg Return</TableCell>
                              <TableCell align="right">Samples</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {Object.entries(performanceData.performance)
                              .filter(([regime]) => regime !== 'summary')
                              .map(([regime, data]) => (
                                <TableRow key={regime}>
                                  <TableCell>
                                    <Chip 
                                      label={regime} 
                                      size="small" 
                                      sx={{ 
                                        bgcolor: COLORS[regime as keyof typeof COLORS], 
                                        color: '#fff' 
                                      }} 
                                    />
                                  </TableCell>
                                  <TableCell align="right">{formatPercent(data.win_rate)}</TableCell>
                                  <TableCell align="right">{data.avg_return.toFixed(2)}%</TableCell>
                                  <TableCell align="right">{data.sample_count}</TableCell>
                                </TableRow>
                              ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Overall Summary
                      </Typography>
                      <Grid container spacing={1}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Overall Win Rate:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" align="right">
                            {formatPercent(performanceData.performance.summary.overall_win_rate)}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Overall Return:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" align="right">
                            {performanceData.performance.summary.overall_return.toFixed(2)}%
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Volatility Robustness:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" align="right">
                            {performanceData.performance.summary.volatility_robustness.toFixed(2)}%
                          </Typography>
                        </Grid>
                      </Grid>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
            ) : (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body1">No performance data available.</Typography>
              </Box>
            )}
          </TabPanel>

          {/* Volatility Distribution Tab */}
          <TabPanel value={tabIndex} index={1}>
            {performanceData ? (
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, height: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      Volatility Regime Distribution
                    </Typography>
                    <ResponsiveContainer width="100%" height={300}>
                      <PieChart>
                        <Pie
                          data={prepareVolatilityDistributionData()}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                        >
                          {prepareVolatilityDistributionData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <RechartsTooltip formatter={(value: any) => [`${value} samples`, 'Count']} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </Paper>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, height: '100%' }}>
                    <Typography variant="h6" gutterBottom>
                      Market Condition Summary
                    </Typography>
                    <Box sx={{ my: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Current Market Assessment
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Predominant Volatility Regime:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" align="right">
                            {performanceData && Object.entries(performanceData.performance)
                              .filter(([regime]) => regime !== 'summary')
                              .sort((a, b) => b[1].sample_count - a[1].sample_count)[0][0]}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Total Trading Samples:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" align="right">
                            {performanceData.performance.summary.total_samples}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" color="text.secondary">
                            Date Range:
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="body2" align="right">
                            {dayjs(performanceData.date_range.start_date).format('MMM D')} - {dayjs(performanceData.date_range.end_date).format('MMM D, YYYY')}
                          </Typography>
                        </Grid>
                      </Grid>
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="subtitle2" gutterBottom>
                      Volatility Classification Reference
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Regime</TableCell>
                            <TableCell>Annualized Volatility</TableCell>
                            <TableCell>Trading Strategy</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          <TableRow>
                            <TableCell>
                              <Chip label="LOW" size="small" sx={{ bgcolor: COLORS.LOW, color: '#fff' }} />
                            </TableCell>
                            <TableCell>0-15%</TableCell>
                            <TableCell>Aggressive (100% sizing)</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>
                              <Chip label="NORMAL" size="small" sx={{ bgcolor: COLORS.NORMAL, color: '#fff' }} />
                            </TableCell>
                            <TableCell>15-25%</TableCell>
                            <TableCell>Normal (100% sizing)</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>
                              <Chip label="HIGH" size="small" sx={{ bgcolor: COLORS.HIGH, color: '#fff' }} />
                            </TableCell>
                            <TableCell>25-40%</TableCell>
                            <TableCell>Cautious (50% sizing)</TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell>
                              <Chip label="EXTREME" size="small" sx={{ bgcolor: COLORS.EXTREME, color: '#fff' }} />
                            </TableCell>
                            <TableCell>&gt;40%</TableCell>
                            <TableCell>Defensive (25% sizing)</TableCell>
                          </TableRow>
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Paper>
                </Grid>
              </Grid>
            ) : (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body1">No volatility distribution data available.</Typography>
              </Box>
            )}
          </TabPanel>

          {/* Parameter Adaptation Tab */}
          <TabPanel value={tabIndex} index={2}>
            {parameterHistory.length > 0 ? (
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Parameter Adaptation History
                    </Typography>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart
                        data={prepareParameterHistoryData()}
                        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="timestamp" />
                        <YAxis yAxisId="left" orientation="left" domain={[0, 50]} label={{ value: 'Lookback Periods', angle: -90, position: 'insideLeft' }} />
                        <YAxis yAxisId="right" orientation="right" domain={[0, 1]} label={{ value: 'Confidence Threshold', angle: 90, position: 'insideRight' }} />
                        <RechartsTooltip />
                        <Legend />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="lookbackPeriods"
                          name="Lookback Periods"
                          stroke="#8884d8"
                          activeDot={{ r: 8 }}
                        />
                        <Line
                          yAxisId="right"
                          type="monotone"
                          dataKey="confidenceThreshold"
                          name="Confidence Threshold"
                          stroke="#82ca9d"
                        />
                        <Line
                          yAxisId="left"
                          type="monotone"
                          dataKey="predictionHorizon"
                          name="Prediction Horizon"
                          stroke="#ffc658"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Paper>
                </Grid>
                <Grid item xs={12}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Recent Parameter Adaptations
                    </Typography>
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Timestamp</TableCell>
                            <TableCell>Volatility Regime</TableCell>
                            <TableCell align="right">Lookback Periods</TableCell>
                            <TableCell align="right">Prediction Horizon</TableCell>
                            <TableCell align="right">Confidence Threshold</TableCell>
                            <TableCell align="right">Win Rate</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {parameterHistory.slice(-10).reverse().map((item, index) => (
                            <TableRow key={index}>
                              <TableCell>{dayjs(item.timestamp).format('MM/DD HH:mm')}</TableCell>
                              <TableCell>
                                <Chip 
                                  label={item.regime} 
                                  size="small" 
                                  sx={{ 
                                    bgcolor: COLORS[item.regime as keyof typeof COLORS], 
                                    color: '#fff' 
                                  }} 
                                />
                              </TableCell>
                              <TableCell align="right">{item.parameters.lookback_periods}</TableCell>
                              <TableCell align="right">{item.parameters.prediction_horizon}</TableCell>
                              <TableCell align="right">{item.parameters.confidence_threshold.toFixed(2)}</TableCell>
                              <TableCell align="right">{formatPercent(item.performance.win_rate)}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Paper>
                </Grid>
              </Grid>
            ) : (
              <Box sx={{ p: 2, textAlign: 'center' }}>
                <Typography variant="body1">No parameter adaptation history available.</Typography>
              </Box>
            )}
          </TabPanel>
        </>
      )}
    </Box>
  );
};

export default VolatilityDashboard;