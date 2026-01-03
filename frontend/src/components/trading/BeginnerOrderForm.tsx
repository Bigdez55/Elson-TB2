import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Button,
  FormControl,
  FormHelperText,
  FormLabel,
  Grid,
  InputAdornment,
  Radio,
  RadioGroup,
  FormControlLabel,
  Stack,
  TextField,
  Typography,
  Alert,
  AlertTitle,
  Tooltip,
  Paper,
  CircularProgress,
  Divider,
} from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import BlurOnIcon from '@mui/icons-material/BlurOn';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import ReceiptIcon from '@mui/icons-material/Receipt';

import { useAuth } from '../../hooks/useAuth';
import { formatCurrency, formatNumber } from '../../utils/formatters';
import { calculateFees, FeeBreakdown } from '../../utils/tradingUtils';
import { SuccessAnimation } from '../common/SuccessAnimation';

// Type definitions
interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface Portfolio {
  id: number;
  name: string;
  cashBalance: number;
}

interface BeginnerOrderFormProps {
  defaultSymbol?: string;
  onOrderSubmit?: (orderData: any) => void;
  educationalMode?: boolean;
}

const BeginnerOrderForm: React.FC<BeginnerOrderFormProps> = ({ 
  defaultSymbol = '', 
  onOrderSubmit,
  educationalMode = true
}) => {
  const { user } = useAuth();
  
  // Form state
  const [orderType, setOrderType] = useState<'buy' | 'sell'>('buy');
  const [investmentType, setInvestmentType] = useState<'dollars' | 'shares'>('dollars');
  const [symbol, setSymbol] = useState(defaultSymbol);
  const [symbolValid, setSymbolValid] = useState(true);
  const [amount, setAmount] = useState<number | ''>('');
  const [shares, setShares] = useState<number | ''>('');
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [stock, setStock] = useState<Stock | null>(null);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [requiresApproval, setRequiresApproval] = useState(false);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [lastOrderDetails, setLastOrderDetails] = useState<{
    symbol: string;
    amount: number;
    shares: number;
  } | null>(null);
  
  // Educational tooltips
  const tooltips = {
    orderType: "Choose 'Buy' to purchase stock or 'Sell' to sell stock you own.",
    investmentType: "Choose 'Dollars' to specify how much money to invest, or 'Shares' to specify the number of shares.",
    symbol: "Enter the stock symbol (e.g., AAPL for Apple, MSFT for Microsoft).",
    dollars: "Enter how much money you want to invest in this stock.",
    shares: "Enter how many shares you want to buy or sell.",
    portfolio: "Select which portfolio to use for this trade.",
    submit: "Review your order details before submitting.",
    estimatedShares: "This is approximately how many shares you'll get based on the current price.",
    estimatedCost: "This is approximately how much money you'll spend or receive based on the current price."
  };

  // Educational helpers
  const getEducationalNote = (key: string) => {
    if (!educationalMode) return null;
    return <FormHelperText><InfoIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />{tooltips[key as keyof typeof tooltips]}</FormHelperText>;
  };

  // Load user's portfolios
  useEffect(() => {
    const fetchPortfolios = async () => {
      try {
        const response = await axios.get('/api/v1/portfolio');
        setPortfolios(response.data);
        if (response.data.length > 0) {
          setPortfolio(response.data[0]);
        }
      } catch (err) {
        console.error('Error fetching portfolios', err);
        setError('Unable to load your portfolios. Please try again later.');
      }
    };

    fetchPortfolios();
  }, []);

  // Fetch stock info when symbol changes
  useEffect(() => {
    const getStockInfo = async () => {
      if (!symbol || symbol.length < 1) {
        setStock(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(`/api/v1/market/quote/${symbol}`);
        setStock(response.data);
        setSymbolValid(true);
      } catch (err) {
        console.error('Error fetching stock data', err);
        setStock(null);
        setSymbolValid(false);
        setError(`Unable to find stock with symbol "${symbol}".`);
      } finally {
        setLoading(false);
      }
    };

    // Debounce the API call
    const timeoutId = setTimeout(() => {
      if (symbol) getStockInfo();
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [symbol]);

  // Calculate estimated shares or cost with fees
  const calculateEstimatedValues = () => {
    if (!stock) return null;

    let estimatedShares: number;
    let estimatedCost: number;

    if (investmentType === 'dollars' && amount !== '') {
      estimatedShares = +(amount as number / stock.price).toFixed(4);
      estimatedCost = amount as number;
    } else if (investmentType === 'shares' && shares !== '') {
      estimatedShares = shares as number;
      estimatedCost = +(shares as number * stock.price).toFixed(2);
    } else {
      return null;
    }

    // Calculate fees (paper trading by default)
    const fees = calculateFees(estimatedCost, estimatedShares, true);
    const totalCost = orderType === 'buy'
      ? estimatedCost + fees.totalFees
      : estimatedCost - fees.totalFees;

    return {
      estimatedShares,
      estimatedCost,
      fees,
      totalCost
    };
  };

  const estimates = calculateEstimatedValues();

  // Check if user is a minor (requires approval)
  useEffect(() => {
    if (user && user.role === 'MINOR') {
      setRequiresApproval(true);
    }
  }, [user]);

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stock || !portfolio) return;

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const orderData = {
        symbol: stock.symbol,
        portfolio_id: portfolio.id,
        trade_type: orderType,
        order_type: 'market', // Simplified form only uses market orders
      };

      // Add either quantity or investment_amount based on the selected type
      if (investmentType === 'dollars' && amount !== '') {
        // @ts-ignore - Adding to the object
        orderData.investment_amount = amount;
      } else if (investmentType === 'shares' && shares !== '') {
        // @ts-ignore - Adding to the object
        orderData.quantity = shares;
      }

      const response = await axios.post('/api/v1/trades', orderData);

      // Store order details for success animation
      setLastOrderDetails({
        symbol: stock.symbol,
        amount: estimates?.estimatedCost || 0,
        shares: estimates?.estimatedShares || 0,
      });

      if (response.data.requires_approval) {
        setSuccess('Your trade has been submitted and is waiting for approval from your guardian.');
      } else {
        setSuccess(`Your ${orderType} order has been successfully submitted!`);
        // Show success animation
        setShowSuccessAnimation(true);
      }

      // Reset form fields
      setAmount('');
      setShares('');

      // Call the callback if provided
      if (onOrderSubmit) {
        onOrderSubmit(response.data);
      }
    } catch (err: any) {
      console.error('Error submitting order', err);
      if (err.response && err.response.data && err.response.data.detail) {
        setError(err.response.data.detail);
      } else {
        setError('An error occurred while submitting your order. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        Easy Trade
        {educationalMode && (
          <Tooltip title="This is a simplified trading form designed for beginners. It features helpful guides and simplified options.">
            <InfoIcon fontSize="small" sx={{ ml: 1, verticalAlign: 'middle', color: 'primary.main' }} />
          </Tooltip>
        )}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          <AlertTitle>Success</AlertTitle>
          {success}
        </Alert>
      )}

      {requiresApproval && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <AlertTitle>Guardian Approval Required</AlertTitle>
          As a minor account, your trades will require approval from your guardian before they are executed.
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Stack spacing={3}>
          {/* Order Type Selection */}
          <FormControl component="fieldset">
            <FormLabel component="legend">I want to:</FormLabel>
            <RadioGroup
              row
              value={orderType}
              onChange={(e) => setOrderType(e.target.value as 'buy' | 'sell')}
            >
              <FormControlLabel 
                value="buy" 
                control={<Radio color="success" />} 
                label={
                  <Box display="flex" alignItems="center">
                    <TrendingUpIcon color="success" sx={{ mr: 0.5 }} />
                    Buy
                  </Box>
                } 
              />
              <FormControlLabel 
                value="sell" 
                control={<Radio color="error" />} 
                label={
                  <Box display="flex" alignItems="center">
                    <TrendingDownIcon color="error" sx={{ mr: 0.5 }} />
                    Sell
                  </Box>
                } 
              />
            </RadioGroup>
            {getEducationalNote('orderType')}
          </FormControl>

          {/* Investment Type Selection */}
          <FormControl component="fieldset">
            <FormLabel component="legend">I want to use:</FormLabel>
            <RadioGroup
              row
              value={investmentType}
              onChange={(e) => setInvestmentType(e.target.value as 'dollars' | 'shares')}
            >
              <FormControlLabel 
                value="dollars" 
                control={<Radio />} 
                label={
                  <Box display="flex" alignItems="center">
                    <AttachMoneyIcon sx={{ mr: 0.5 }} />
                    Dollars
                  </Box>
                } 
              />
              <FormControlLabel 
                value="shares" 
                control={<Radio />} 
                label={
                  <Box display="flex" alignItems="center">
                    <BlurOnIcon sx={{ mr: 0.5 }} />
                    Shares
                  </Box>
                } 
              />
            </RadioGroup>
            {getEducationalNote('investmentType')}
          </FormControl>

          {/* Stock Symbol Input */}
          <FormControl error={!symbolValid}>
            <FormLabel>Stock Symbol</FormLabel>
            <TextField
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="e.g. AAPL"
              fullWidth
              variant="outlined"
              InputProps={{
                endAdornment: loading ? (
                  <InputAdornment position="end">
                    <CircularProgress size={20} />
                  </InputAdornment>
                ) : null
              }}
              error={!symbolValid && symbol !== ''}
              helperText={!symbolValid && symbol !== '' ? `Could not find symbol "${symbol}"` : ''}
            />
            {getEducationalNote('symbol')}
          </FormControl>

          {/* Stock Info Display */}
          {stock && (
            <Box sx={{ 
              p: 2, 
              backgroundColor: 'background.paper', 
              borderRadius: 1,
              border: 1,
              borderColor: 'divider'
            }}>
              <Stack direction="row" justifyContent="space-between">
                <Typography variant="body1" fontWeight="bold">
                  {stock.name} ({stock.symbol})
                </Typography>
                <Typography 
                  variant="body1" 
                  fontWeight="bold"
                  color={stock.change >= 0 ? 'success.main' : 'error.main'}
                >
                  ${formatNumber(stock.price)} ({stock.change >= 0 ? '+' : ''}{formatNumber(stock.changePercent)}%)
                </Typography>
              </Stack>
            </Box>
          )}

          {/* Amount or Shares Input */}
          {investmentType === 'dollars' ? (
            <FormControl>
              <FormLabel>Amount to Invest</FormLabel>
              <TextField
                value={amount}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '' || /^\d*\.?\d{0,2}$/.test(value)) {
                    setAmount(value === '' ? '' : parseFloat(value));
                  }
                }}
                placeholder="Enter amount"
                fullWidth
                variant="outlined"
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                }}
                disabled={!stock}
              />
              {getEducationalNote('dollars')}
              {stock && amount !== '' && (
                <FormHelperText>
                  Estimated Shares: <strong>{formatNumber(estimates?.estimatedShares || 0)}</strong>
                  <Tooltip title={tooltips.estimatedShares}>
                    <HelpOutlineIcon fontSize="small" sx={{ ml: 0.5, verticalAlign: 'middle' }} />
                  </Tooltip>
                </FormHelperText>
              )}
            </FormControl>
          ) : (
            <FormControl>
              <FormLabel>Number of Shares</FormLabel>
              <TextField
                value={shares}
                onChange={(e) => {
                  const value = e.target.value;
                  if (value === '' || /^\d*\.?\d{0,4}$/.test(value)) {
                    setShares(value === '' ? '' : parseFloat(value));
                  }
                }}
                placeholder="Enter shares"
                fullWidth
                variant="outlined"
                disabled={!stock}
              />
              {getEducationalNote('shares')}
              {stock && shares !== '' && (
                <FormHelperText>
                  Estimated Cost: <strong>{formatCurrency(estimates?.estimatedCost || 0)}</strong>
                  <Tooltip title={tooltips.estimatedCost}>
                    <HelpOutlineIcon fontSize="small" sx={{ ml: 0.5, verticalAlign: 'middle' }} />
                  </Tooltip>
                </FormHelperText>
              )}
            </FormControl>
          )}

          {/* Portfolio Selection */}
          <FormControl>
            <FormLabel>Portfolio</FormLabel>
            <TextField
              select
              value={portfolio?.id || ''}
              onChange={(e) => {
                const selectedPortfolio = portfolios.find(p => p.id === parseInt(e.target.value));
                setPortfolio(selectedPortfolio || null);
              }}
              fullWidth
              variant="outlined"
              SelectProps={{
                native: true
              }}
            >
              {portfolios.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name} (${formatCurrency(p.cashBalance)})
                </option>
              ))}
            </TextField>
            {getEducationalNote('portfolio')}
          </FormControl>

          {/* Order Summary with Fee Breakdown */}
          {stock && portfolio && (investmentType === 'dollars' ? amount !== '' : shares !== '') && estimates && (
            <Box sx={{
              p: 2,
              backgroundColor: 'background.paper',
              borderRadius: 1,
              border: 1,
              borderColor: 'divider'
            }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ReceiptIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Order Summary</Typography>
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Order Type:</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" fontWeight="medium" color={orderType === 'buy' ? 'success.main' : 'error.main'}>
                    {orderType.toUpperCase()}
                  </Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Stock:</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">{stock.symbol} @ ${formatNumber(stock.price)}</Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    {investmentType === 'dollars' ? 'Investment:' : 'Shares:'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    {investmentType === 'dollars'
                      ? formatCurrency(amount as number)
                      : formatNumber(shares as number)}
                  </Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    {investmentType === 'dollars' ? 'Est. Shares:' : 'Est. Cost:'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">
                    {investmentType === 'dollars'
                      ? formatNumber(estimates.estimatedShares)
                      : formatCurrency(estimates.estimatedCost)}
                  </Typography>
                </Grid>

                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Portfolio:</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2">{portfolio.name}</Typography>
                </Grid>
              </Grid>

              {/* Fee Breakdown */}
              <Divider sx={{ my: 2 }} />
              <Box sx={{ bgcolor: 'action.hover', borderRadius: 1, p: 1.5 }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Fee Breakdown
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={8}>
                    <Typography variant="body2" color="text.secondary">Order Value:</Typography>
                  </Grid>
                  <Grid item xs={4} sx={{ textAlign: 'right' }}>
                    <Typography variant="body2">{formatCurrency(estimates.estimatedCost)}</Typography>
                  </Grid>
                  <Grid item xs={8}>
                    <Tooltip title={estimates.fees.feeDescription}>
                      <Typography variant="body2" color="text.secondary" sx={{ cursor: 'help', textDecoration: 'underline dotted' }}>
                        Trading Fee:
                      </Typography>
                    </Tooltip>
                  </Grid>
                  <Grid item xs={4} sx={{ textAlign: 'right' }}>
                    <Typography variant="body2">{formatCurrency(estimates.fees.totalFees)}</Typography>
                  </Grid>
                  <Grid item xs={12}>
                    <Divider sx={{ my: 0.5 }} />
                  </Grid>
                  <Grid item xs={8}>
                    <Typography variant="body2" fontWeight="bold">
                      Total {orderType === 'buy' ? 'Cost' : 'Proceeds'}:
                    </Typography>
                  </Grid>
                  <Grid item xs={4} sx={{ textAlign: 'right' }}>
                    <Typography variant="body2" fontWeight="bold" color={orderType === 'buy' ? 'error.main' : 'success.main'}>
                      {formatCurrency(estimates.totalCost)}
                    </Typography>
                  </Grid>
                </Grid>
              </Box>

              {requiresApproval && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  This order will require guardian approval
                </Alert>
              )}
            </Box>
          )}

          {/* Submit Button */}
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size="large"
            disabled={
              !stock || 
              !portfolio || 
              !symbolValid || 
              (investmentType === 'dollars' ? amount === '' : shares === '') ||
              submitting
            }
            fullWidth
          >
            {submitting ? (
              <CircularProgress size={24} color="inherit" />
            ) : requiresApproval ? (
              'Submit for Approval'
            ) : (
              `Place ${orderType.toUpperCase()} Order`
            )}
          </Button>
          {getEducationalNote('submit')}
        </Stack>
      </form>

      {/* Success Animation */}
      <SuccessAnimation
        show={showSuccessAnimation}
        title="Order Placed!"
        symbol={lastOrderDetails?.symbol}
        amount={lastOrderDetails?.amount}
        shares={lastOrderDetails?.shares}
        onComplete={() => setShowSuccessAnimation(false)}
        onClose={() => setShowSuccessAnimation(false)}
      />
    </Paper>
  );
};

export default BeginnerOrderForm;