import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Grid,
  Typography,
  Paper,
  Tabs,
  Tab,
  Divider,
  Alert,
  Button,
  Chip
} from '@mui/material';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { subscriptionService, SubscriptionPlan } from '../../services/subscriptionService';
import api from '../../services/api';

// Interface for dashboard metrics
interface SubscriptionDashboardData {
  current_mrr: number;
  current_arr: number;
  mrr_growth_percent: number;
  subscribers_by_plan: Record<string, number>;
  total_subscribers: number;
  churn_rate: {
    period_days: number;
    subscriptions_at_start: number;
    canceled_subscriptions: number;
    churn_rate_percent: number;
  };
  conversion_rate: {
    period_days: number;
    new_users: number;
    new_subscribers: number;
    conversion_rate_percent: number;
  };
  mrr_history: Array<{
    date: string;
    mrr: number;
  }>;
  ltv_estimates: Record<string, number>;
}

// Colors for the charts
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];
const PLAN_COLORS = {
  free: '#8884d8',
  premium: '#00C49F',
  family: '#0088FE',
};

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
};

/**
 * Subscription Metrics Dashboard Component
 * Displays key subscription metrics for admins
 */
const SubscriptionMetricsDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<SubscriptionDashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);

  // Load dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const response = await api.get('/api/v1/subscriptions/metrics/dashboard');
        setDashboardData(response.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching subscription metrics:', err);
        setError('Failed to load subscription metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={() => window.location.reload()}>
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  if (!dashboardData) {
    return (
      <Alert severity="info">
        No subscription data available
      </Alert>
    );
  }

  // Prepare data for the plan distribution pie chart
  const planDistributionData = Object.entries(dashboardData.subscribers_by_plan).map(([plan, count]) => ({
    name: plan.charAt(0).toUpperCase() + plan.slice(1),
    value: count,
  }));

  // Prepare data for MRR history chart
  const mrrHistoryData = dashboardData.mrr_history.map(item => ({
    date: new Date(item.date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }),
    mrr: item.mrr,
  }));

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Subscription Metrics Dashboard
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="dashboard tabs">
          <Tab label="Overview" />
          <Tab label="Growth" />
          <Tab label="Revenue" />
        </Tabs>
      </Box>

      {activeTab === 0 && (
        <Box>
          {/* Key Metrics Section */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Monthly Recurring Revenue
                  </Typography>
                  <Typography variant="h4">
                    {formatCurrency(dashboardData.current_mrr)}
                  </Typography>
                  <Chip 
                    label={`${dashboardData.mrr_growth_percent >= 0 ? '+' : ''}${dashboardData.mrr_growth_percent.toFixed(1)}%`} 
                    color={dashboardData.mrr_growth_percent >= 0 ? 'success' : 'error'} 
                    size="small" 
                    sx={{ mt: 1 }} 
                  />
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Annual Recurring Revenue
                  </Typography>
                  <Typography variant="h4">
                    {formatCurrency(dashboardData.current_arr)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Subscribers
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.total_subscribers}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Churn Rate (Monthly)
                  </Typography>
                  <Typography variant="h4">
                    {dashboardData.churn_rate.churn_rate_percent.toFixed(1)}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Charts Section */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Subscribers by Plan" />
                <CardContent>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={planDistributionData}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {planDistributionData.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={PLAN_COLORS[entry.name.toLowerCase() as keyof typeof PLAN_COLORS] || COLORS[index % COLORS.length]} 
                            />
                          ))}
                        </Pie>
                        <Tooltip formatter={(value) => [value, 'Subscribers']} />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="MRR History" />
                <CardContent>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart
                        data={mrrHistoryData}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis 
                          tickFormatter={(value) => `$${value}`}
                        />
                        <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'MRR']} />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="mrr"
                          stroke="#8884d8"
                          activeDot={{ r: 8 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {activeTab === 1 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Conversion Rate" />
                <CardContent>
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      {dashboardData.conversion_rate.conversion_rate_percent.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      of new users subscribe within {dashboardData.conversion_rate.period_days} days
                    </Typography>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        New Users:
                      </Typography>
                      <Typography variant="body1">
                        {dashboardData.conversion_rate.new_users}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        New Subscribers:
                      </Typography>
                      <Typography variant="body1">
                        {dashboardData.conversion_rate.new_subscribers}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Churn Analysis" />
                <CardContent>
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h6">
                      {dashboardData.churn_rate.churn_rate_percent.toFixed(1)}%
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      monthly churn rate
                    </Typography>
                  </Box>
                  <Divider sx={{ my: 2 }} />
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Subscriptions at start:
                      </Typography>
                      <Typography variant="body1">
                        {dashboardData.churn_rate.subscriptions_at_start}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Canceled subscriptions:
                      </Typography>
                      <Typography variant="body1">
                        {dashboardData.churn_rate.canceled_subscriptions}
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12}>
              <Card>
                <CardHeader title="Lifetime Value (LTV) Estimates" />
                <CardContent>
                  <Grid container spacing={3}>
                    {Object.entries(dashboardData.ltv_estimates).map(([plan, value]) => (
                      <Grid item xs={12} sm={4} key={plan}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="subtitle1">
                            {plan.charAt(0).toUpperCase() + plan.slice(1)}
                          </Typography>
                          <Typography variant="h5" sx={{ mt: 1 }}>
                            {formatCurrency(value)}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            average lifetime value
                          </Typography>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}

      {activeTab === 2 && (
        <Box>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Current Revenue" />
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Card sx={{ p: 2, bgcolor: 'background.paper', boxShadow: 'none' }}>
                        <Typography variant="body2" color="textSecondary">
                          Monthly (MRR)
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(dashboardData.current_mrr)}
                        </Typography>
                      </Card>
                    </Grid>
                    <Grid item xs={6}>
                      <Card sx={{ p: 2, bgcolor: 'background.paper', boxShadow: 'none' }}>
                        <Typography variant="body2" color="textSecondary">
                          Annual (ARR)
                        </Typography>
                        <Typography variant="h5">
                          {formatCurrency(dashboardData.current_arr)}
                        </Typography>
                      </Card>
                    </Grid>
                  </Grid>
                  <Divider sx={{ my: 2 }} />
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="body2" color="textSecondary">
                      MRR Growth
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="body1" sx={{ mr: 1 }}>
                        {dashboardData.mrr_growth_percent.toFixed(1)}%
                      </Typography>
                      <Chip 
                        label={dashboardData.mrr_growth_percent >= 0 ? 'Growing' : 'Declining'} 
                        color={dashboardData.mrr_growth_percent >= 0 ? 'success' : 'error'} 
                        size="small" 
                      />
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card>
                <CardHeader title="Revenue by Plan" />
                <CardContent>
                  <Box sx={{ height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart
                        data={Object.entries(dashboardData.subscribers_by_plan)
                          .filter(([plan]) => plan !== 'free')
                          .map(([plan, count]) => {
                            // Get price based on plan
                            const monthlyPrice = plan === 'premium' ? 9.99 : 19.99;
                            return {
                              plan: plan.charAt(0).toUpperCase() + plan.slice(1),
                              revenue: count * monthlyPrice,
                              subscribers: count,
                            };
                          })}
                        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="plan" />
                        <YAxis 
                          tickFormatter={(value) => `$${value}`}
                        />
                        <Tooltip 
                          formatter={(value, name) => {
                            if (name === 'revenue') {
                              return [formatCurrency(Number(value)), 'Monthly Revenue'];
                            }
                            return [value, 'Subscribers'];
                          }} 
                        />
                        <Legend />
                        <Bar dataKey="revenue" fill="#8884d8" />
                        <Bar dataKey="subscribers" fill="#82ca9d" />
                      </BarChart>
                    </ResponsiveContainer>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      )}
    </Box>
  );
};

export default SubscriptionMetricsDashboard;