import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Grid,
  Divider,
  Chip,
  Alert,
  Link,
  InputAdornment,
  Slider,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  FormControlLabel,
  Switch,
  CircularProgress,
  Tooltip,
  IconButton,
} from '@mui/material';
import {
  AttachMoney,
  Info,
  ExpandMore,
  History,
  ArrowUpward,
  ShowChart,
  School,
  AddCircleOutline,
} from '@mui/icons-material';
import { api } from '../../services/api';
import { formatCurrency } from '../../utils/formatters';
import { useSnackbar } from 'notistack';
import { RootState } from '../../store/store';
import useFeatureAccess from '../../hooks/useFeatureAccess';
import { EducationalTooltip } from '../common/EducationalTooltip';
import { StockSymbolInput } from '../common/StockSymbolInput';

interface Portfolio {
  id: number;
  name: string;
}

interface MicroInvestFormProps {
  onSuccess?: () => void;
  onCancel?: () => void;
  initialSymbol?: string;
  initialAmount?: number;
  portfolios?: Portfolio[];
  darkMode?: boolean;
}

export const MicroInvestForm: React.FC<MicroInvestFormProps> = ({
  onSuccess,
  onCancel,
  initialSymbol = '',
  initialAmount = 1,
  portfolios = [],
  darkMode = true,
}) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  
  // State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [showEducation, setShowEducation] = useState(false);
  
  // Redux state
  const { isPremium, isFamily } = useSelector((state: any) => state.subscription);
  const { role } = useSelector((state: any) => state.user.currentUser || {});
  const { microInvestingEnabled } = useSelector((state: any) => state.user.settings || {
    microInvestingEnabled: false,
  });
  
  // Check if user has permission for fractional shares
  const { hasPermission: hasFractionalSharesPermission, isLoading: permissionLoading } = 
    useFeatureAccess('fractional_shares');
  
  // Form state
  const [formState, setFormState] = useState({
    symbol: initialSymbol,
    portfolio_id: portfolios.length > 0 ? portfolios[0].id : '',
    investment_amount: initialAmount,
    description: '',
  });
  
  // Get recommended ETFs and symbols
  const [recommendedSymbols, setRecommendedSymbols] = useState<string[]>([
    'VTI', 'VOO', 'QQQ', 'VGT', 'VXUS', 'BND'
  ]);
  
  // Get minimum investment amount
  const [minInvestmentAmount, setMinInvestmentAmount] = useState(0.01);
  
  // Check if user has completed the educational module
  const [hasCompletedEducation, setHasCompletedEducation] = useState(false);
  
  // Load user settings
  useEffect(() => {
    const fetchUserSettings = async () => {
      try {
        const response = await api.get('/micro-invest/settings');
        setHasCompletedEducation(response.data.completed_micro_invest_education);
      } catch (error) {
        console.error('Error fetching user settings:', error);
      }
    };
    
    fetchUserSettings();
  }, []);
  
  // Load trading config for min investment
  useEffect(() => {
    const fetchTradingConfig = async () => {
      try {
        const response = await api.get('/trading/config');
        setMinInvestmentAmount(response.data.minInvestmentAmount);
      } catch (error) {
        console.error('Error fetching trading config:', error);
      }
    };
    
    fetchTradingConfig();
  }, []);
  
  // Handle form input changes
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target as HTMLInputElement;
    
    if (name === 'investment_amount') {
      const numValue = parseFloat(value);
      if (!isNaN(numValue) && numValue >= 0) {
        setFormState(prev => ({ ...prev, [name]: numValue }));
      }
    } else {
      setFormState(prev => ({ ...prev, [name as string]: value }));
    }
  };
  
  // Handle symbol selection
  const handleSymbolSelect = (symbol: string) => {
    setFormState(prev => ({ ...prev, symbol }));
  };
  
  // Handle recommended symbol click
  const handleRecommendedSymbolClick = (symbol: string) => {
    setFormState(prev => ({ ...prev, symbol }));
  };
  
  // Complete educational module
  const handleCompleteEducation = async () => {
    try {
      await api.post('/micro-invest/complete-education');
      setHasCompletedEducation(true);
      setShowEducation(false);
      enqueueSnackbar('Educational module completed!', { variant: 'success' });
    } catch (error) {
      console.error('Error completing educational module:', error);
    }
  };
  
  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate subscription
    if (!isPremium && !isFamily) {
      setError('Micro-investing requires a Premium or Family subscription');
      return;
    }
    
    // Validate permissions for minors
    if (role === 'MINOR' && !hasFractionalSharesPermission) {
      setError('You need guardian permission to use micro-investing');
      return;
    }
    
    // Validate form
    if (!formState.symbol.trim()) {
      setError('Symbol is required');
      return;
    }
    
    if (formState.investment_amount < minInvestmentAmount) {
      setError(`Investment amount must be at least $${minInvestmentAmount}`);
      return;
    }
    
    setIsSubmitting(true);
    setError('');
    
    try {
      // Prepare data for submission
      const submissionData = {
        ...formState,
        portfolio_id: Number(formState.portfolio_id),
      };
      
      // Submit form
      await api.post('/micro-invest/micro-invest', submissionData);
      
      // Suggest education if not completed
      if (!hasCompletedEducation) {
        enqueueSnackbar(
          'Learn more about micro-investing by viewing the educational module',
          { 
            variant: 'info',
            action: (key) => (
              <Button 
                color="inherit" 
                size="small" 
                onClick={() => { 
                  setShowEducation(true);
                  /*closeSnackbar(key);*/ 
                }}
              >
                View
              </Button>
            )
          }
        );
      }
      
      enqueueSnackbar('Micro-investment created successfully!', { variant: 'success' });
      
      // Handle success
      if (onSuccess) {
        onSuccess();
      } else {
        navigate('/trading');
      }
    } catch (err: any) {
      console.error('Error creating micro-investment:', err);
      setError(err.response?.data?.detail || 'Failed to create micro-investment');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  // Render dark mode version
  if (darkMode) {
    return (
      <Box>
        <Paper elevation={3} sx={{ p: 3, borderRadius: 2, bgcolor: 'background.paperDark' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <AttachMoney color="primary" sx={{ mr: 1, fontSize: 28 }} />
            <Typography variant="h6" component="div">
              Micro-Invest
              <EducationalTooltip
                term="Micro-Investing"
                definition="Invest with as little as $0.01 in fractional shares of stocks and ETFs. A great way to start building wealth with small amounts."
                placement="right"
              />
            </Typography>
          </Box>
          
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}
          
          {/* Permission notice for minors */}
          {role === 'MINOR' && (
            <Alert 
              severity={hasFractionalSharesPermission ? "success" : "warning"}
              sx={{ mb: 3 }}
            >
              {hasFractionalSharesPermission 
                ? '✓ Your guardian has granted you permission to use micro-investing.' 
                : '⚠️ You need guardian permission to use micro-investing. Ask your guardian to enable this feature for you.'}
            </Alert>
          )}
          
          {/* Educational component */}
          {showEducation && (
            <Card sx={{ mb: 3, bgcolor: 'background.paperLight' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom>
                  About Micro-Investing
                </Typography>
                <Typography variant="body2" paragraph>
                  Micro-investing allows you to invest very small amounts of money regularly. Instead of needing large sums to start investing, you can begin with just cents or a few dollars.
                </Typography>
                <Typography variant="body2" paragraph>
                  With fractional shares, you can own a portion of a stock instead of a whole share, making it possible to invest in companies with high share prices, even with small amounts.
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                  <Button 
                    variant="text" 
                    onClick={() => setShowEducation(false)}
                  >
                    Close
                  </Button>
                  <Button 
                    variant="contained" 
                    color="primary" 
                    endIcon={<School />} 
                    onClick={() => navigate('/education/micro-investing')}
                  >
                    Learn More
                  </Button>
                </Box>
              </CardContent>
            </Card>
          )}
          
          <form onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <StockSymbolInput
                  label="Investment Symbol"
                  value={formState.symbol}
                  onChange={(symbol) => handleSymbolSelect(symbol)}
                  required
                  darkMode
                />
                <Typography variant="caption" color="text.secondary">
                  Enter stock or ETF symbol
                </Typography>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth variant="outlined">
                  <InputLabel id="portfolio-label">Portfolio</InputLabel>
                  <Select
                    labelId="portfolio-label"
                    name="portfolio_id"
                    value={formState.portfolio_id}
                    onChange={handleChange as any}
                    label="Portfolio"
                    required
                    sx={{ bgcolor: 'background.paperLight' }}
                  >
                    {portfolios.map(portfolio => (
                      <MenuItem key={portfolio.id} value={portfolio.id}>
                        {portfolio.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom color="text.secondary">
                  Recommended ETFs
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {recommendedSymbols.map(symbol => (
                    <Chip
                      key={symbol}
                      label={symbol}
                      color={formState.symbol === symbol ? "primary" : "default"}
                      onClick={() => handleRecommendedSymbolClick(symbol)}
                      sx={{ 
                        '&:hover': {
                          bgcolor: 'action.hover',
                        }
                      }}
                    />
                  ))}
                </Box>
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Investment Amount
                </Typography>
                <TextField
                  name="investment_amount"
                  type="number"
                  value={formState.investment_amount}
                  onChange={handleChange}
                  fullWidth
                  required
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                    inputProps: { min: minInvestmentAmount, step: 0.01 }
                  }}
                  sx={{ bgcolor: 'background.paperLight' }}
                  helperText={`Minimum investment: $${minInvestmentAmount}`}
                />
              </Grid>
              
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Description (Optional)
                </Typography>
                <TextField
                  name="description"
                  value={formState.description}
                  onChange={handleChange}
                  placeholder="E.g., First micro-investment"
                  fullWidth
                  multiline
                  rows={2}
                  sx={{ bgcolor: 'background.paperLight' }}
                />
              </Grid>
            </Grid>
            
            <Divider sx={{ my: 3 }} />
            
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Investment Summary
              </Typography>
              <Grid container spacing={2} sx={{ mb: 3 }}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Symbol:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {formState.symbol || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">Amount:</Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {formatCurrency(formState.investment_amount)}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Portfolio:</Typography>
                  <Typography variant="body1">
                    {portfolios.find(p => p.id === formState.portfolio_id)?.name || '-'}
                  </Typography>
                </Grid>
              </Grid>
            </Box>
            
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
              <Button
                type="button"
                variant="outlined"
                onClick={onCancel}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                disabled={isSubmitting || (role === 'MINOR' && !hasFractionalSharesPermission)}
              >
                {isSubmitting ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Create Micro-Investment'
                )}
              </Button>
            </Box>
          </form>
          
          <Box sx={{ mt: 3 }}>
            <Accordion sx={{ bgcolor: 'background.paperLight' }}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Learn About Micro-Investing</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" paragraph>
                  Micro-investing allows you to invest small amounts of money regularly, even just a few cents. This strategy is perfect for beginners or those with limited funds.
                </Typography>
                <Typography variant="body2" paragraph>
                  With fractional shares, you can own a piece of high-priced stocks or ETFs without having to buy a whole share. For example, if a stock costs $3,000, you can invest $10 and own 0.0033 shares.
                </Typography>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<School />}
                  onClick={() => navigate('/education/micro-investing')}
                  sx={{ mt: 1 }}
                >
                  View Full Educational Module
                </Button>
              </AccordionDetails>
            </Accordion>
          </Box>
        </Paper>
      </Box>
    );
  }
  
  // Light mode version
  return (
    <Box>
      <Paper elevation={2} sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <AttachMoney color="primary" sx={{ mr: 1, fontSize: 28 }} />
          <Typography variant="h6" component="div">
            Micro-Invest
            <EducationalTooltip
              term="Micro-Investing"
              definition="Invest with as little as $0.01 in fractional shares of stocks and ETFs. A great way to start building wealth with small amounts."
              placement="right"
            />
          </Typography>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}
        
        {/* Permission notice for minors */}
        {role === 'MINOR' && (
          <Alert 
            severity={hasFractionalSharesPermission ? "success" : "warning"}
            sx={{ mb: 3 }}
          >
            {hasFractionalSharesPermission 
              ? '✓ Your guardian has granted you permission to use micro-investing.' 
              : '⚠️ You need guardian permission to use micro-investing. Ask your guardian to enable this feature for you.'}
          </Alert>
        )}
        
        {/* Educational component */}
        {showEducation && (
          <Card sx={{ mb: 3, bgcolor: '#f5f9ff' }}>
            <CardContent>
              <Typography variant="subtitle1" gutterBottom>
                About Micro-Investing
              </Typography>
              <Typography variant="body2" paragraph>
                Micro-investing allows you to invest very small amounts of money regularly. Instead of needing large sums to start investing, you can begin with just cents or a few dollars.
              </Typography>
              <Typography variant="body2" paragraph>
                With fractional shares, you can own a portion of a stock instead of a whole share, making it possible to invest in companies with high share prices, even with small amounts.
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                <Button 
                  variant="text" 
                  onClick={() => setShowEducation(false)}
                >
                  Close
                </Button>
                <Button 
                  variant="contained" 
                  color="primary" 
                  endIcon={<School />} 
                  onClick={() => navigate('/education/micro-investing')}
                >
                  Learn More
                </Button>
              </Box>
            </CardContent>
          </Card>
        )}
        
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <StockSymbolInput
                label="Investment Symbol"
                value={formState.symbol}
                onChange={(symbol) => handleSymbolSelect(symbol)}
                required
              />
              <Typography variant="caption" color="text.secondary">
                Enter stock or ETF symbol
              </Typography>
            </Grid>
            
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth variant="outlined">
                <InputLabel id="portfolio-label">Portfolio</InputLabel>
                <Select
                  labelId="portfolio-label"
                  name="portfolio_id"
                  value={formState.portfolio_id}
                  onChange={handleChange as any}
                  label="Portfolio"
                  required
                >
                  {portfolios.map(portfolio => (
                    <MenuItem key={portfolio.id} value={portfolio.id}>
                      {portfolio.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom color="text.secondary">
                Recommended ETFs
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {recommendedSymbols.map(symbol => (
                  <Chip
                    key={symbol}
                    label={symbol}
                    color={formState.symbol === symbol ? "primary" : "default"}
                    onClick={() => handleRecommendedSymbolClick(symbol)}
                    sx={{ 
                      '&:hover': {
                        bgcolor: 'action.hover',
                      }
                    }}
                  />
                ))}
              </Box>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Investment Amount
              </Typography>
              <TextField
                name="investment_amount"
                type="number"
                value={formState.investment_amount}
                onChange={handleChange}
                fullWidth
                required
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  inputProps: { min: minInvestmentAmount, step: 0.01 }
                }}
                helperText={`Minimum investment: $${minInvestmentAmount}`}
              />
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>
                Description (Optional)
              </Typography>
              <TextField
                name="description"
                value={formState.description}
                onChange={handleChange}
                placeholder="E.g., First micro-investment"
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
          
          <Divider sx={{ my: 3 }} />
          
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Investment Summary
            </Typography>
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">Symbol:</Typography>
                <Typography variant="body1" fontWeight="bold">
                  {formState.symbol || '-'}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="body2" color="text.secondary">Amount:</Typography>
                <Typography variant="body1" fontWeight="bold">
                  {formatCurrency(formState.investment_amount)}
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography variant="body2" color="text.secondary">Portfolio:</Typography>
                <Typography variant="body1">
                  {portfolios.find(p => p.id === formState.portfolio_id)?.name || '-'}
                </Typography>
              </Grid>
            </Grid>
          </Box>
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 2 }}>
            <Button
              type="button"
              variant="outlined"
              onClick={onCancel}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={isSubmitting || (role === 'MINOR' && !hasFractionalSharesPermission)}
            >
              {isSubmitting ? (
                <CircularProgress size={24} color="inherit" />
              ) : (
                'Create Micro-Investment'
              )}
            </Button>
          </Box>
        </form>
        
        <Box sx={{ mt: 3 }}>
          <Accordion>
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Typography>Learn About Micro-Investing</Typography>
            </AccordionSummary>
            <AccordionDetails>
              <Typography variant="body2" paragraph>
                Micro-investing allows you to invest small amounts of money regularly, even just a few cents. This strategy is perfect for beginners or those with limited funds.
              </Typography>
              <Typography variant="body2" paragraph>
                With fractional shares, you can own a piece of high-priced stocks or ETFs without having to buy a whole share. For example, if a stock costs $3,000, you can invest $10 and own 0.0033 shares.
              </Typography>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<School />}
                onClick={() => navigate('/education/micro-investing')}
                sx={{ mt: 1 }}
              >
                View Full Educational Module
              </Button>
            </AccordionDetails>
          </Accordion>
        </Box>
      </Paper>
    </Box>
  );
};

export default MicroInvestForm;