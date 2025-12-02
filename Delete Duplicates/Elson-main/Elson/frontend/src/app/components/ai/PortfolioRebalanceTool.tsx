import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Divider,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  Chip,
  LinearProgress
} from '@mui/material';
import {
  Balance,
  AutoFixHigh,
  BarChart,
  CheckCircleOutline,
  TrendingUp,
  TrendingDown
} from '@mui/icons-material';
import axios from 'axios';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface TradeRebalance {
  id: number;
  symbol: string;
  quantity: number;
  price: number;
  trade_type: string;
  order_type: string;
  status: string;
  total_amount: number;
  created_at: string;
}

interface RebalanceResponse {
  trades: TradeRebalance[];
  trade_count: number;
  message: string;
}

const PortfolioRebalanceTool: React.FC = () => {
  const [activeStep, setActiveStep] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [rebalanceResult, setRebalanceResult] = useState<RebalanceResponse | null>(null);
  const [openDialog, setOpenDialog] = useState<boolean>(false);
  const [executing, setExecuting] = useState<boolean>(false);
  const [completed, setCompleted] = useState<boolean>(false);

  const steps = [
    'Analyze Portfolio',
    'Generate Rebalance Plan',
    'Review & Execute'
  ];

  const handleAnalyze = async () => {
    setLoading(true);
    setError(null);

    try {
      // This is just a simulation - in a real app you would fetch portfolio data
      // and analyze target vs. current allocations
      await new Promise(resolve => setTimeout(resolve, 1500));
      setActiveStep(1);
    } catch (err) {
      console.error('Error analyzing portfolio:', err);
      setError('Failed to analyze portfolio. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async () => {
    setLoading(true);
    setError(null);

    try {
      // Call the AI rebalance endpoint
      const response = await axios.post('/api/v1/ai/rebalance', {}, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setRebalanceResult(response.data);
      setActiveStep(2);
    } catch (err) {
      console.error('Error generating rebalance plan:', err);
      setError('Failed to generate rebalance plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
  };

  const handleExecute = async () => {
    setExecuting(true);
    
    try {
      // In a real app, you would execute the trades here
      // This is a simulation
      await new Promise(resolve => setTimeout(resolve, 2000));
      setCompleted(true);
      setOpenDialog(false);
    } catch (err) {
      console.error('Error executing rebalance:', err);
      setError('Failed to execute trades. Please try again.');
    } finally {
      setExecuting(false);
    }
  };

  const handleReset = () => {
    setActiveStep(0);
    setRebalanceResult(null);
    setCompleted(false);
    setError(null);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Balance color="primary" sx={{ mr: 1 }} />
          AI Portfolio Rebalancer
        </Typography>
        
        <Divider sx={{ mb: 3 }} />
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {completed && (
          <Alert severity="success" sx={{ mb: 3 }}>
            Portfolio rebalancing complete! Your trades have been executed successfully.
          </Alert>
        )}
        
        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        <Box sx={{ mt: 2, mb: 4 }}>
          {activeStep === 0 && (
            <Box>
              <Typography variant="body1" gutterBottom>
                The AI Portfolio Rebalancer will analyze your current portfolio against your target allocation based on your risk profile, and generate trades to bring your portfolio back in balance.
              </Typography>
              
              <Box sx={{ mt: 3, mb: 3, display: 'flex', justifyContent: 'center' }}>
                <AutoFixHigh sx={{ fontSize: 80, color: 'primary.light', opacity: 0.7 }} />
              </Box>
              
              <Typography variant="body2" color="text.secondary" paragraph>
                This tool will:
              </Typography>
              
              <ul>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Analyze your current asset allocation vs. your target allocation
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Generate optimal trades to rebalance your portfolio
                  </Typography>
                </li>
                <li>
                  <Typography variant="body2" color="text.secondary">
                    Minimize transaction costs and tax implications
                  </Typography>
                </li>
              </ul>
              
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleAnalyze}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={24} /> : null}
                  size="large"
                >
                  {loading ? 'Analyzing...' : 'Analyze My Portfolio'}
                </Button>
              </Box>
            </Box>
          )}
          
          {activeStep === 1 && (
            <Box>
              <Typography variant="body1" gutterBottom>
                Your portfolio analysis is complete. The AI will now generate a rebalancing plan based on your target allocation.
              </Typography>
              
              <Box sx={{ mt: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Current Allocation</Typography>
                  <Typography variant="body2">Target Allocation</Typography>
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>US Stocks: 45% → 40%</Typography>
                  <LinearProgress 
                    variant="buffer" 
                    value={40} 
                    valueBuffer={45} 
                    color="primary"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>International Stocks: 20% → 25%</Typography>
                  <LinearProgress 
                    variant="buffer" 
                    value={25} 
                    valueBuffer={20} 
                    color="secondary"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>Bonds: 25% → 30%</Typography>
                  <LinearProgress 
                    variant="buffer" 
                    value={30} 
                    valueBuffer={25} 
                    color="success"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
                
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" gutterBottom>Cash: 10% → 5%</Typography>
                  <LinearProgress 
                    variant="buffer" 
                    value={5} 
                    valueBuffer={10} 
                    color="warning"
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>
              </Box>
              
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                <BarChart sx={{ fontSize: 80, color: 'primary.light', opacity: 0.7 }} />
              </Box>
              
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleGeneratePlan}
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={24} /> : null}
                  size="large"
                >
                  {loading ? 'Generating...' : 'Generate Rebalance Plan'}
                </Button>
              </Box>
            </Box>
          )}
          
          {activeStep === 2 && rebalanceResult && (
            <Box>
              <Typography variant="body1" gutterBottom>
                Review the AI-generated rebalance plan below. These trades will help bring your portfolio back to your target allocation.
              </Typography>
              
              <Alert severity="info" sx={{ my: 2 }}>
                {rebalanceResult.message}
              </Alert>
              
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 3 }}>
                Proposed Trades:
              </Typography>
              
              <List sx={{ mb: 3 }}>
                {rebalanceResult.trades.map((trade) => (
                  <ListItem
                    key={trade.id}
                    sx={{ 
                      mb: 2, 
                      p: 2, 
                      border: '1px solid', 
                      borderColor: 'divider',
                      borderRadius: 1
                    }}
                  >
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="subtitle2">
                            {trade.symbol}
                          </Typography>
                          <Chip 
                            icon={trade.trade_type === 'buy' ? <TrendingUp /> : <TrendingDown />}
                            label={trade.trade_type.toUpperCase()}
                            color={trade.trade_type === 'buy' ? 'success' : 'error'}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <>
                          <Typography variant="body2" component="span" display="block">
                            Quantity: {trade.quantity} shares @ {formatCurrency(trade.price)}
                          </Typography>
                          <Typography variant="body2" component="span" display="block">
                            Total: {formatCurrency(trade.total_amount)}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" display="block">
                            Order Type: {trade.order_type.toUpperCase()}
                          </Typography>
                        </>
                      }
                    />
                  </ListItem>
                ))}
              </List>
              
              {rebalanceResult.trades.length === 0 && (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 3 }}>
                  No trades needed! Your portfolio is already well-balanced according to your target allocation.
                </Typography>
              )}
              
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleOpenDialog}
                  disabled={rebalanceResult.trades.length === 0 || completed}
                  startIcon={completed ? <CheckCircleOutline /> : null}
                  size="large"
                >
                  {completed ? 'Rebalancing Completed' : 'Execute Rebalance Plan'}
                </Button>
                
                <Button
                  variant="text"
                  onClick={handleReset}
                  sx={{ ml: 2 }}
                >
                  Start Over
                </Button>
              </Box>
            </Box>
          )}
        </Box>
        
        {/* Confirmation Dialog */}
        <Dialog
          open={openDialog}
          onClose={handleCloseDialog}
        >
          <DialogTitle>Confirm Portfolio Rebalance</DialogTitle>
          <DialogContent>
            <DialogContentText>
              Are you sure you want to execute the rebalance plan? This will create {rebalanceResult?.trade_count} trades in your account.
            </DialogContentText>
            {executing && (
              <Box sx={{ mt: 3 }}>
                <CircularProgress sx={{ display: 'block', mx: 'auto', mb: 2 }} />
                <Typography variant="body2" align="center">
                  Executing trades...
                </Typography>
              </Box>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog} disabled={executing}>
              Cancel
            </Button>
            <Button 
              onClick={handleExecute} 
              color="primary" 
              variant="contained"
              disabled={executing}
            >
              Confirm Rebalance
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default PortfolioRebalanceTool;