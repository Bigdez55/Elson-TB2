import React, { useState } from 'react';
import {
  Box,
  Button,
  ButtonGroup,
  Typography,
  Paper,
  TextField,
  InputAdornment,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery,
  CircularProgress,
  Collapse,
} from '@mui/material';
import {
  Add,
  Remove,
  TrendingUp,
  AttachMoney,
  Edit,
  Close,
} from '@mui/icons-material';
import { formatCurrency } from '../../utils/formatters';
import {
  QUICK_INVEST_AMOUNTS,
  calculateDollarBasedOrder,
  formatShares,
} from '../../utils/tradingUtils';

interface QuickInvestButtonsProps {
  // Stock info
  symbol: string;
  companyName?: string;
  currentPrice: number;

  // Configuration
  presetAmounts?: number[];
  showCustomInput?: boolean;
  minAmount?: number;
  maxAmount?: number;

  // Trading mode
  isPaperTrading?: boolean;

  // Callbacks
  onInvest: (amount: number, shares: number) => void | Promise<void>;
  onPreview?: (amount: number, shares: number) => void;

  // State
  isLoading?: boolean;
  disabled?: boolean;

  // Style
  variant?: 'compact' | 'expanded';
  color?: 'primary' | 'secondary' | 'success';
}

export const QuickInvestButtons: React.FC<QuickInvestButtonsProps> = ({
  symbol,
  companyName,
  currentPrice,
  presetAmounts = [1, 5, 10, 25],
  showCustomInput = true,
  minAmount = 0.01,
  maxAmount = 10000,
  isPaperTrading = true,
  onInvest,
  onPreview,
  isLoading = false,
  disabled = false,
  variant = 'compact',
  color = 'primary',
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [showCustom, setShowCustom] = useState(false);

  // Calculate estimated shares for display
  const getEstimate = (amount: number) => {
    return calculateDollarBasedOrder(amount, currentPrice, 'buy', isPaperTrading);
  };

  // Handle preset button click
  const handlePresetClick = (amount: number) => {
    setSelectedAmount(amount);
    setShowCustom(false);
    if (onPreview) {
      const estimate = getEstimate(amount);
      onPreview(amount, estimate.shares);
    }
  };

  // Handle custom amount change
  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Allow only numbers and decimals
    if (value === '' || /^\d*\.?\d{0,2}$/.test(value)) {
      setCustomAmount(value);
      const numValue = parseFloat(value);
      if (!isNaN(numValue) && numValue >= minAmount) {
        setSelectedAmount(numValue);
        if (onPreview) {
          const estimate = getEstimate(numValue);
          onPreview(numValue, estimate.shares);
        }
      } else {
        setSelectedAmount(null);
      }
    }
  };

  // Handle invest button click
  const handleInvest = async () => {
    if (selectedAmount && selectedAmount >= minAmount) {
      const estimate = getEstimate(selectedAmount);
      await onInvest(selectedAmount, estimate.shares);
    }
  };

  // Increment/decrement for custom input
  const adjustCustomAmount = (delta: number) => {
    const current = parseFloat(customAmount) || 0;
    const newValue = Math.max(minAmount, Math.min(maxAmount, current + delta));
    setCustomAmount(newValue.toFixed(2));
    setSelectedAmount(newValue);
    if (onPreview) {
      const estimate = getEstimate(newValue);
      onPreview(newValue, estimate.shares);
    }
  };

  const estimate = selectedAmount ? getEstimate(selectedAmount) : null;

  // Compact variant (for watchlist, quick actions)
  if (variant === 'compact') {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {presetAmounts.slice(0, 4).map((amount) => (
            <Chip
              key={amount}
              label={`$${amount}`}
              onClick={() => handlePresetClick(amount)}
              color={selectedAmount === amount ? color : 'default'}
              variant={selectedAmount === amount ? 'filled' : 'outlined'}
              size={isMobile ? 'small' : 'medium'}
              sx={{
                fontWeight: selectedAmount === amount ? 'bold' : 'normal',
                transition: 'all 0.2s',
                '&:hover': {
                  transform: 'scale(1.05)',
                },
              }}
            />
          ))}
          {showCustomInput && (
            <Chip
              label="Custom"
              onClick={() => setShowCustom(!showCustom)}
              color={showCustom ? color : 'default'}
              variant={showCustom ? 'filled' : 'outlined'}
              size={isMobile ? 'small' : 'medium'}
              icon={showCustom ? <Close fontSize="small" /> : <Edit fontSize="small" />}
            />
          )}
        </Box>

        <Collapse in={showCustom}>
          <TextField
            size="small"
            value={customAmount}
            onChange={handleCustomChange}
            placeholder="Enter amount"
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
            }}
            sx={{ mt: 1 }}
            fullWidth
          />
        </Collapse>

        {estimate && selectedAmount && (
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">
              ≈ {formatShares(estimate.shares)} shares
            </Typography>
            <Button
              size="small"
              variant="contained"
              color={color}
              onClick={handleInvest}
              disabled={disabled || isLoading}
              startIcon={isLoading ? <CircularProgress size={16} /> : <TrendingUp />}
            >
              {isLoading ? 'Investing...' : 'Invest'}
            </Button>
          </Box>
        )}
      </Box>
    );
  }

  // Expanded variant (for dedicated invest page)
  return (
    <Paper
      elevation={2}
      sx={{
        p: 2,
        borderRadius: 2,
      }}
    >
      {/* Header */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Quick Invest in {symbol}
        </Typography>
        {companyName && (
          <Typography variant="body2" color="text.secondary">
            {companyName} • {formatCurrency(currentPrice)}/share
          </Typography>
        )}
      </Box>

      {/* Preset Amount Buttons */}
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Choose Amount
      </Typography>
      <ButtonGroup
        variant="outlined"
        fullWidth
        sx={{ mb: 2 }}
      >
        {presetAmounts.map((amount) => (
          <Button
            key={amount}
            onClick={() => handlePresetClick(amount)}
            variant={selectedAmount === amount ? 'contained' : 'outlined'}
            color={color}
            sx={{
              py: 1.5,
              flexDirection: 'column',
              '&.MuiButton-contained': {
                boxShadow: 'none',
              },
            }}
          >
            <Typography variant="body1" fontWeight="bold">
              ${amount}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 0.8 }}>
              ≈{formatShares(amount / currentPrice)}
            </Typography>
          </Button>
        ))}
      </ButtonGroup>

      {/* Custom Amount Input */}
      {showCustomInput && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Or Enter Custom Amount
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <IconButton
              size="small"
              onClick={() => adjustCustomAmount(-1)}
              disabled={parseFloat(customAmount) <= minAmount}
            >
              <Remove />
            </IconButton>
            <TextField
              value={customAmount}
              onChange={handleCustomChange}
              placeholder="0.00"
              size="small"
              InputProps={{
                startAdornment: <InputAdornment position="start">$</InputAdornment>,
              }}
              sx={{
                flex: 1,
                '& input': {
                  textAlign: 'center',
                  fontSize: '1.2rem',
                  fontWeight: 'bold',
                },
              }}
            />
            <IconButton
              size="small"
              onClick={() => adjustCustomAmount(1)}
              disabled={parseFloat(customAmount) >= maxAmount}
            >
              <Add />
            </IconButton>
          </Box>
        </Box>
      )}

      {/* Order Summary */}
      {estimate && selectedAmount && (
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            mb: 2,
            bgcolor: theme.palette.mode === 'dark' ? 'grey.900' : 'grey.50',
          }}
        >
          <Typography variant="subtitle2" gutterBottom>
            Order Preview
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Investment Amount
            </Typography>
            <Typography variant="body2" fontWeight="medium">
              {formatCurrency(selectedAmount)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Estimated Shares
            </Typography>
            <Typography variant="body2" fontWeight="medium">
              {formatShares(estimate.shares)}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Fees
            </Typography>
            <Typography variant="body2">
              {formatCurrency(estimate.fees.totalFees)}
            </Typography>
          </Box>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              pt: 1,
              borderTop: 1,
              borderColor: 'divider',
            }}
          >
            <Typography variant="body1" fontWeight="bold">
              Total Cost
            </Typography>
            <Typography variant="body1" fontWeight="bold" color="success.main">
              {formatCurrency(estimate.totalAmount)}
            </Typography>
          </Box>
        </Paper>
      )}

      {/* Invest Button */}
      <Button
        fullWidth
        variant="contained"
        color={color}
        size="large"
        onClick={handleInvest}
        disabled={disabled || isLoading || !selectedAmount || selectedAmount < minAmount}
        startIcon={isLoading ? <CircularProgress size={20} /> : <AttachMoney />}
        sx={{
          py: 1.5,
          fontSize: '1rem',
          fontWeight: 'bold',
        }}
      >
        {isLoading
          ? 'Processing...'
          : selectedAmount
            ? `Invest ${formatCurrency(selectedAmount)}`
            : 'Select Amount to Invest'
        }
      </Button>

      {/* Trading Mode Indicator */}
      <Box sx={{ textAlign: 'center', mt: 1 }}>
        <Chip
          size="small"
          label={isPaperTrading ? 'Paper Trading' : 'Live Trading'}
          color={isPaperTrading ? 'info' : 'error'}
          variant="outlined"
        />
      </Box>
    </Paper>
  );
};

export default QuickInvestButtons;
