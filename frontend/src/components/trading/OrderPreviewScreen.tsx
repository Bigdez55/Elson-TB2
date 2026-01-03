import React, { useState, useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Divider,
  Grid,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery,
  CircularProgress,
} from '@mui/material';
import {
  ArrowBack,
  Info,
  CheckCircle,
  Warning,
  TrendingUp,
  TrendingDown,
  SwapVert,
} from '@mui/icons-material';
import { formatCurrency, formatNumber } from '../../utils/formatters';

// Fee constants - matching backend configuration
const COMMISSION_RATE = 0.0035; // 0.35%
const MIN_COMMISSION = 0.50; // $0.50 minimum
const PAPER_TRADING_FEE = 0.005; // $0.005 per share for paper trading

interface OrderPreviewScreenProps {
  // Order details
  symbol: string;
  companyName?: string;
  orderType: 'buy' | 'sell';
  investmentType: 'dollars' | 'shares';
  amount?: number; // Dollar amount (for dollar-based)
  shares?: number; // Share quantity (for share-based)
  currentPrice: number;
  priceChange?: number;
  priceChangePercent?: number;

  // Trading mode
  isPaperTrading?: boolean;
  isLiveTrading?: boolean;

  // Portfolio info
  portfolioName?: string;
  availableBalance?: number;

  // Callbacks
  onConfirm: () => void;
  onBack: () => void;
  onEdit?: () => void;

  // State
  isSubmitting?: boolean;
  requiresApproval?: boolean;
}

// Fee calculation utility
export const calculateFees = (
  orderValue: number,
  shares: number,
  isPaperTrading: boolean = true
): { commission: number; fees: number; totalFees: number } => {
  if (isPaperTrading) {
    // Paper trading: $0.005 per share
    const fees = shares * PAPER_TRADING_FEE;
    return { commission: 0, fees, totalFees: fees };
  }

  // Live trading: 0.35% commission with $0.50 minimum
  const rawCommission = orderValue * COMMISSION_RATE;
  const commission = Math.max(rawCommission, MIN_COMMISSION);

  return { commission, fees: 0, totalFees: commission };
};

export const OrderPreviewScreen: React.FC<OrderPreviewScreenProps> = ({
  symbol,
  companyName,
  orderType,
  investmentType,
  amount,
  shares,
  currentPrice,
  priceChange = 0,
  priceChangePercent = 0,
  isPaperTrading = true,
  isLiveTrading = false,
  portfolioName,
  availableBalance,
  onConfirm,
  onBack,
  onEdit,
  isSubmitting = false,
  requiresApproval = false,
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const [swipeProgress, setSwipeProgress] = useState(0);

  // Calculate order values
  const calculatedValues = useMemo(() => {
    let estimatedShares: number;
    let estimatedCost: number;

    if (investmentType === 'dollars' && amount) {
      estimatedShares = amount / currentPrice;
      estimatedCost = amount;
    } else if (investmentType === 'shares' && shares) {
      estimatedShares = shares;
      estimatedCost = shares * currentPrice;
    } else {
      estimatedShares = 0;
      estimatedCost = 0;
    }

    const { commission, fees, totalFees } = calculateFees(
      estimatedCost,
      estimatedShares,
      isPaperTrading
    );

    const totalAmount = orderType === 'buy'
      ? estimatedCost + totalFees
      : estimatedCost - totalFees;

    return {
      estimatedShares,
      estimatedCost,
      commission,
      fees,
      totalFees,
      totalAmount,
    };
  }, [amount, shares, currentPrice, investmentType, orderType, isPaperTrading]);

  const isBuy = orderType === 'buy';
  const hasInsufficientFunds = isBuy && availableBalance !== undefined &&
    calculatedValues.totalAmount > availableBalance;

  // Mobile swipe-to-confirm handler
  const handleSwipe = (e: React.TouchEvent) => {
    // Simple swipe detection for mobile
    const touch = e.touches[0];
    const target = e.currentTarget as HTMLElement;
    const rect = target.getBoundingClientRect();
    const progress = Math.min(1, Math.max(0, (touch.clientX - rect.left) / rect.width));
    setSwipeProgress(progress);

    if (progress > 0.9) {
      onConfirm();
    }
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: { xs: 2, sm: 3 },
        borderRadius: 2,
        maxWidth: 500,
        mx: 'auto',
      }}
    >
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <IconButton onClick={onBack} sx={{ mr: 1 }}>
          <ArrowBack />
        </IconButton>
        <Typography variant="h6" component="h2" sx={{ flexGrow: 1 }}>
          Review Order
        </Typography>
        {onEdit && (
          <Button size="small" onClick={onEdit}>
            Edit
          </Button>
        )}
      </Box>

      {/* Trading Mode Warning */}
      {isLiveTrading && (
        <Alert
          severity="error"
          icon={<Warning />}
          sx={{ mb: 2 }}
        >
          <Typography variant="subtitle2" fontWeight="bold">
            LIVE TRADING - Real Money
          </Typography>
          <Typography variant="body2">
            This order will execute with real funds.
          </Typography>
        </Alert>
      )}

      {isPaperTrading && (
        <Alert
          severity="info"
          sx={{ mb: 2 }}
        >
          <Typography variant="body2">
            Paper Trading Mode - No real money involved
          </Typography>
        </Alert>
      )}

      {/* Stock Info */}
      <Box
        sx={{
          p: 2,
          bgcolor: 'background.default',
          borderRadius: 1,
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="h5" fontWeight="bold">
              {symbol}
            </Typography>
            {companyName && (
              <Typography variant="body2" color="text.secondary">
                {companyName}
              </Typography>
            )}
          </Box>
          <Box sx={{ textAlign: 'right' }}>
            <Typography variant="h6">
              {formatCurrency(currentPrice)}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end' }}>
              {priceChange >= 0 ? (
                <TrendingUp color="success" fontSize="small" />
              ) : (
                <TrendingDown color="error" fontSize="small" />
              )}
              <Typography
                variant="body2"
                color={priceChange >= 0 ? 'success.main' : 'error.main'}
              >
                {priceChange >= 0 ? '+' : ''}{formatNumber(priceChangePercent)}%
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>

      {/* Order Type Chip */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
        <Chip
          label={isBuy ? 'BUY ORDER' : 'SELL ORDER'}
          color={isBuy ? 'success' : 'error'}
          size="medium"
          sx={{ fontWeight: 'bold', px: 2 }}
        />
      </Box>

      {/* Order Details */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Order Details
        </Typography>
        <Divider sx={{ mb: 1 }} />

        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">
              {investmentType === 'dollars' ? 'Investment Amount' : 'Shares'}
            </Typography>
          </Grid>
          <Grid item xs={6} sx={{ textAlign: 'right' }}>
            <Typography variant="body2" fontWeight="medium">
              {investmentType === 'dollars'
                ? formatCurrency(amount || 0)
                : formatNumber(shares || 0)}
            </Typography>
          </Grid>

          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">
              Market Price
            </Typography>
          </Grid>
          <Grid item xs={6} sx={{ textAlign: 'right' }}>
            <Typography variant="body2" fontWeight="medium">
              {formatCurrency(currentPrice)}
            </Typography>
          </Grid>

          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">
              Est. {investmentType === 'dollars' ? 'Shares' : 'Cost'}
            </Typography>
          </Grid>
          <Grid item xs={6} sx={{ textAlign: 'right' }}>
            <Typography variant="body2" fontWeight="medium">
              {investmentType === 'dollars'
                ? formatNumber(calculatedValues.estimatedShares, 4)
                : formatCurrency(calculatedValues.estimatedCost)}
            </Typography>
          </Grid>

          {portfolioName && (
            <>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Portfolio
                </Typography>
              </Grid>
              <Grid item xs={6} sx={{ textAlign: 'right' }}>
                <Typography variant="body2" fontWeight="medium">
                  {portfolioName}
                </Typography>
              </Grid>
            </>
          )}
        </Grid>
      </Box>

      {/* Fee Breakdown */}
      <Box
        sx={{
          p: 2,
          bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
          borderRadius: 1,
          mb: 2,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
            Fee Breakdown
          </Typography>
          <Tooltip title="Fees help maintain the platform and provide secure trading services.">
            <IconButton size="small">
              <Info fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>

        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">
              Order Value
            </Typography>
          </Grid>
          <Grid item xs={6} sx={{ textAlign: 'right' }}>
            <Typography variant="body2">
              {formatCurrency(calculatedValues.estimatedCost)}
            </Typography>
          </Grid>

          {isPaperTrading ? (
            <>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Paper Trading Fee
                </Typography>
              </Grid>
              <Grid item xs={6} sx={{ textAlign: 'right' }}>
                <Typography variant="body2">
                  {formatCurrency(calculatedValues.fees)}
                </Typography>
              </Grid>
            </>
          ) : (
            <>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">
                  Commission (0.35%)
                </Typography>
              </Grid>
              <Grid item xs={6} sx={{ textAlign: 'right' }}>
                <Typography variant="body2">
                  {formatCurrency(calculatedValues.commission)}
                </Typography>
              </Grid>
            </>
          )}

          <Grid item xs={12}>
            <Divider sx={{ my: 1 }} />
          </Grid>

          <Grid item xs={6}>
            <Typography variant="body1" fontWeight="bold">
              Total {isBuy ? 'Cost' : 'Proceeds'}
            </Typography>
          </Grid>
          <Grid item xs={6} sx={{ textAlign: 'right' }}>
            <Typography variant="body1" fontWeight="bold" color={isBuy ? 'error.main' : 'success.main'}>
              {formatCurrency(calculatedValues.totalAmount)}
            </Typography>
          </Grid>
        </Grid>
      </Box>

      {/* Available Balance Warning */}
      {hasInsufficientFunds && (
        <Alert severity="error" sx={{ mb: 2 }}>
          <Typography variant="body2">
            Insufficient funds. Available: {formatCurrency(availableBalance || 0)}
          </Typography>
        </Alert>
      )}

      {/* Guardian Approval Notice */}
      {requiresApproval && (
        <Alert severity="info" sx={{ mb: 2 }}>
          <Typography variant="body2">
            This order requires guardian approval before execution.
          </Typography>
        </Alert>
      )}

      {/* Confirm Button */}
      {isMobile ? (
        <Box
          sx={{
            position: 'relative',
            height: 56,
            bgcolor: 'grey.200',
            borderRadius: 2,
            overflow: 'hidden',
            cursor: isSubmitting || hasInsufficientFunds ? 'not-allowed' : 'pointer',
          }}
          onTouchMove={!isSubmitting && !hasInsufficientFunds ? handleSwipe : undefined}
        >
          <Box
            sx={{
              position: 'absolute',
              left: 0,
              top: 0,
              height: '100%',
              width: `${swipeProgress * 100}%`,
              bgcolor: isBuy ? 'success.main' : 'error.main',
              transition: 'width 0.1s',
            }}
          />
          <Box
            sx={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SwapVert sx={{ mr: 1 }} />
            <Typography fontWeight="medium">
              {isSubmitting ? 'Submitting...' : 'Swipe to Confirm'}
            </Typography>
          </Box>
        </Box>
      ) : (
        <Button
          fullWidth
          variant="contained"
          color={isBuy ? 'success' : 'error'}
          size="large"
          onClick={onConfirm}
          disabled={isSubmitting || hasInsufficientFunds}
          startIcon={isSubmitting ? <CircularProgress size={20} color="inherit" /> : <CheckCircle />}
        >
          {isSubmitting
            ? 'Submitting Order...'
            : requiresApproval
              ? 'Submit for Approval'
              : `Confirm ${isBuy ? 'Buy' : 'Sell'} Order`
          }
        </Button>
      )}

      {/* Footer Note */}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ display: 'block', textAlign: 'center', mt: 2 }}
      >
        By confirming, you agree to execute this order at the best available market price.
        {isPaperTrading && ' This is a simulated trade.'}
      </Typography>
    </Paper>
  );
};

export default OrderPreviewScreen;
