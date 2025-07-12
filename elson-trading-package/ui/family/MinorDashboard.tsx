import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Alert, 
  Chip, 
  Divider,
  CircularProgress,
  Button,
  Paper
} from '@mui/material';
import { Person, School, Badge } from '@mui/icons-material';
import axios from 'axios';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface Guardian {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
}

interface TradeRequest {
  id: number;
  symbol: string;
  quantity: number;
  price: number;
  trade_type: string;
  status: string;
  created_at: string;
  approved_at?: string;
  executed_at?: string;
  rejection_reason?: string;
}

const MinorDashboard: React.FC = () => {
  const [guardian, setGuardian] = useState<Guardian | null>(null);
  const [pendingTrades, setPendingTrades] = useState<TradeRequest[]>([]);
  const [recentlyApproved, setRecentlyApproved] = useState<TradeRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load the minor's data when component mounts
    const fetchMinorData = async () => {
      try {
        setLoading(true);
        
        // Fetch the minor's guardian info
        const guardianResponse = await axios.get('/api/v1/family/guardian', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Fetch the minor's trade requests (would need an API endpoint for this)
        const tradesResponse = await axios.get('/api/v1/trading/my-trades', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        setGuardian(guardianResponse.data);
        
        // Filter trades by status
        const trades = tradesResponse.data || [];
        setPendingTrades(trades.filter((t: TradeRequest) => t.status === 'pending_approval'));
        setRecentlyApproved(trades.filter((t: TradeRequest) => 
          ['pending', 'filled', 'rejected'].includes(t.status)
        ).slice(0, 5)); // Just show the 5 most recent
        
        setError(null);
      } catch (err) {
        console.error('Error fetching minor data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMinorData();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '80vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        My Dashboard
        <Chip 
          icon={<School />} 
          label="Minor Account" 
          color="primary" 
          variant="outlined" 
          sx={{ ml: 2 }}
        />
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      {/* Guardian Info */}
      {guardian && (
        <Paper sx={{ p: 2, mb: 3, bgcolor: 'background.paper' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Person color="primary" sx={{ fontSize: 40, mr: 2 }} />
            <Box>
              <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
                <Badge fontSize="small" sx={{ mr: 1 }} />
                My Guardian
              </Typography>
              <Typography variant="h6">
                {guardian.first_name} {guardian.last_name}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {guardian.email}
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}
      
      <Grid container spacing={3}>
        {/* Pending Trade Requests */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pending Trade Requests
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {pendingTrades.length > 0 ? (
                pendingTrades.map((trade) => (
                  <Box 
                    key={trade.id} 
                    sx={{ 
                      mb: 2, 
                      p: 2, 
                      border: '1px solid', 
                      borderColor: 'divider',
                      borderRadius: 1,
                      '&:last-child': { mb: 0 }
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1">
                        {trade.symbol} - {trade.quantity} shares
                      </Typography>
                      <Chip 
                        label="Pending Approval" 
                        color="warning" 
                        size="small"
                      />
                    </Box>
                    
                    <Typography variant="body2">
                      {trade.trade_type.toUpperCase()} @ {formatCurrency(trade.price)} per share
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total: {formatCurrency(trade.quantity * trade.price)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Requested: {formatDate(trade.created_at)}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No pending trade requests.
                </Typography>
              )}
              
              <Box sx={{ mt: 2, textAlign: 'center' }}>
                <Button 
                  variant="contained" 
                  color="primary"
                  href="/trading/new"
                >
                  Create New Trade Request
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Recently Processed Trades */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recently Processed Trades
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {recentlyApproved.length > 0 ? (
                recentlyApproved.map((trade) => (
                  <Box 
                    key={trade.id} 
                    sx={{ 
                      mb: 2, 
                      p: 2, 
                      border: '1px solid', 
                      borderColor: 'divider',
                      borderRadius: 1,
                      '&:last-child': { mb: 0 }
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="subtitle1">
                        {trade.symbol} - {trade.quantity} shares
                      </Typography>
                      <Chip 
                        label={trade.status.replace('_', ' ').toUpperCase()} 
                        color={
                          trade.status === 'filled' ? 'success' : 
                          trade.status === 'pending' ? 'info' : 
                          trade.status === 'rejected' ? 'error' : 
                          'default'
                        }
                        size="small"
                      />
                    </Box>
                    
                    <Typography variant="body2">
                      {trade.trade_type.toUpperCase()} @ {formatCurrency(trade.price)} per share
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total: {formatCurrency(trade.quantity * trade.price)}
                    </Typography>
                    
                    {trade.status === 'rejected' && trade.rejection_reason && (
                      <Alert severity="info" sx={{ mt: 1 }}>
                        <Typography variant="body2">
                          Rejection reason: {trade.rejection_reason}
                        </Typography>
                      </Alert>
                    )}
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      {trade.status === 'filled' && trade.executed_at && `Executed: ${formatDate(trade.executed_at)}`}
                      {trade.status === 'pending' && trade.approved_at && `Approved: ${formatDate(trade.approved_at)}`}
                      {trade.status === 'rejected' && `Rejected: ${formatDate(trade.approved_at || trade.created_at)}`}
                    </Typography>
                  </Box>
                ))
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No recent trades.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Educational Content */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Financial Education
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <Typography variant="body1" gutterBottom>
                Learning about investing is an important step to building your financial future!
              </Typography>
              
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        Stock Market Basics
                      </Typography>
                      <Typography variant="body2">
                        Learn about how the stock market works and why companies go public.
                      </Typography>
                      <Button size="small" sx={{ mt: 2 }}>Read More</Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        Smart Investing Tips
                      </Typography>
                      <Typography variant="body2">
                        Discover how to make informed investment decisions for your future.
                      </Typography>
                      <Button size="small" sx={{ mt: 2 }}>Read More</Button>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} sm={4}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary">
                        Saving for College
                      </Typography>
                      <Typography variant="body2">
                        Tips and strategies for building your education fund through smart investing.
                      </Typography>
                      <Button size="small" sx={{ mt: 2 }}>Read More</Button>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MinorDashboard;