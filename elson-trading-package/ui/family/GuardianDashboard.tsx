import React, { useState, useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, Button, Divider, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { formatCurrency } from '../../utils/formatters';
import MinorAccountsList from './MinorAccountsList';
import PendingTradesList from './PendingTradesList';
import AddMinorAccountModal from './AddMinorAccountModal';

// Define interfaces for our data types
interface Minor {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  birthdate: string;
  account_id: number;
}

interface PendingTrade {
  trade_id: number;
  minor_id: number;
  minor_name: string;
  symbol: string;
  quantity: number;
  price: number;
  trade_type: string;
  created_at: string;
  status: string;
}

const GuardianDashboard: React.FC = () => {
  const [minors, setMinors] = useState<Minor[]>([]);
  const [pendingTrades, setPendingTrades] = useState<PendingTrade[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddMinorModal, setShowAddMinorModal] = useState<boolean>(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Load the guardian's data when component mounts
    const fetchGuardianData = async () => {
      try {
        setLoading(true);
        
        // Fetch minors under this guardian
        const minorsResponse = await axios.get('/api/v1/family/minors', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        // Fetch pending trades that need approval
        const pendingTradesResponse = await axios.get('/api/v1/family/trades/pending', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        setMinors(minorsResponse.data);
        setPendingTrades(pendingTradesResponse.data);
        setError(null);
      } catch (err) {
        console.error('Error fetching guardian data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchGuardianData();
  }, []);

  const handleAddMinor = () => {
    setShowAddMinorModal(true);
  };

  const handleCloseModal = () => {
    setShowAddMinorModal(false);
  };

  const handleMinorCreated = (newMinor: Minor) => {
    setMinors([...minors, newMinor]);
    setShowAddMinorModal(false);
  };

  const handleApproveTrade = async (tradeId: number, approved: boolean, rejectionReason?: string) => {
    try {
      await axios.post(
        `/api/v1/family/trade/${tradeId}/approve`,
        {
          approved,
          rejection_reason: rejectionReason || null
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      
      // Update the local state to remove the approved/rejected trade
      setPendingTrades(pendingTrades.filter(trade => trade.trade_id !== tradeId));
    } catch (err) {
      console.error('Error processing trade approval:', err);
      setError('Failed to process trade approval. Please try again.');
    }
  };

  const handleViewMinorPortfolio = (minorId: number) => {
    navigate(`/family/minor/${minorId}/portfolio`);
  };

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
        Family Dashboard
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* Summary Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Minor Accounts
              </Typography>
              <Typography variant="h3">
                {minors.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Pending Approvals
              </Typography>
              <Typography variant="h3">
                {pendingTrades.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Total Family Assets
              </Typography>
              <Typography variant="h3">
                {formatCurrency(0)} {/* This would be calculated from all portfolios */}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="text.secondary">
                Actions
              </Typography>
              <Button 
                variant="contained" 
                fullWidth 
                onClick={handleAddMinor}
                sx={{ mt: 1 }}
              >
                Add Minor Account
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Minor Accounts List */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Minor Accounts
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <MinorAccountsList 
                minors={minors} 
                onViewPortfolio={handleViewMinorPortfolio}
              />
              
              {minors.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No minor accounts found. Add your first minor account to get started.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
        
        {/* Pending Trades */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pending Trade Approvals
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              <PendingTradesList 
                pendingTrades={pendingTrades}
                onApproveTrade={handleApproveTrade}
              />
              
              {pendingTrades.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No pending trade approvals.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Add Minor Account Modal */}
      <AddMinorAccountModal
        open={showAddMinorModal}
        onClose={handleCloseModal}
        onMinorCreated={handleMinorCreated}
      />
    </Box>
  );
};

export default GuardianDashboard;