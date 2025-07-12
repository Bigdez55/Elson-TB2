import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Divider,
  Grid,
  Switch,
  FormControlLabel,
  Slider,
  TextField,
  Button,
  Alert,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Stack,
  IconButton,
  Paper,
  FormHelperText,
  FormGroup,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Tooltip,
  InputAdornment
} from '@mui/material';
import {
  InfoOutlined,
  Save,
  Refresh,
  Settings,
  Block,
  Security,
  Warning,
  School,
  AttachMoney,
  AccessTime,
  ChildCare,
  Done,
  Add,
  Delete,
  Close
} from '@mui/icons-material';
import axios from 'axios';
import { formatCurrency } from '../../utils/formatters';

// Interface for Minor Account Details
interface MinorAccount {
  id: number;
  name: string;
  age: number;
  email: string;
  avatar?: string;
}

// Interface for Restriction Settings
interface RestrictionSettings {
  max_daily_trade_amount: number;
  max_single_trade_amount: number;
  max_daily_trades: number;
  trading_enabled: boolean;
  educational_requirement: boolean;
  educational_modules_required: string[];
  allowed_investment_types: string[];
  restricted_symbols: string[];
  automatic_approval_under: number;
  content_filter_level: 'low' | 'medium' | 'high';
  time_restrictions: {
    enabled: boolean;
    allowed_days: string[];
    allowed_hours: {
      start: string;
      end: string;
    };
  };
}

// Mock data for educational modules
const availableEducationalModules = [
  { id: 'stock-market-intro', name: 'Introduction to Stock Market' },
  { id: 'types-of-investments', name: 'Types of Investments' },
  { id: 'trading-basics', name: 'Trading Basics' },
  { id: 'understanding-risk', name: 'Understanding Risk' },
  { id: 'portfolio-building', name: 'Building a Portfolio' }
];

// Mock data for investment types
const availableInvestmentTypes = [
  { id: 'stock', name: 'Individual Stocks' },
  { id: 'etf', name: 'ETFs' },
  { id: 'mutual_fund', name: 'Mutual Funds' },
  { id: 'bond', name: 'Bonds' },
  { id: 'option', name: 'Options' },
  { id: 'crypto', name: 'Cryptocurrencies' }
];

// Mock data for days of the week
const daysOfWeek = [
  { id: 'monday', name: 'Monday' },
  { id: 'tuesday', name: 'Tuesday' },
  { id: 'wednesday', name: 'Wednesday' },
  { id: 'thursday', name: 'Thursday' },
  { id: 'friday', name: 'Friday' },
  { id: 'saturday', name: 'Saturday' },
  { id: 'sunday', name: 'Sunday' }
];

// Default settings (used when creating a new configuration)
const defaultSettings: RestrictionSettings = {
  max_daily_trade_amount: 500,
  max_single_trade_amount: 100,
  max_daily_trades: 5,
  trading_enabled: true,
  educational_requirement: true,
  educational_modules_required: ['stock-market-intro'],
  allowed_investment_types: ['stock', 'etf', 'mutual_fund'],
  restricted_symbols: [],
  automatic_approval_under: 25,
  content_filter_level: 'medium',
  time_restrictions: {
    enabled: false,
    allowed_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    allowed_hours: {
      start: '08:00',
      end: '20:00'
    }
  }
};

interface MinorRestrictionSettingsProps {
  minorId?: number;
  onSaved?: () => void;
  onCancel?: () => void;
}

const MinorRestrictionSettings: React.FC<MinorRestrictionSettingsProps> = ({
  minorId,
  onSaved,
  onCancel
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [settings, setSettings] = useState<RestrictionSettings>(defaultSettings);
  const [minorDetails, setMinorDetails] = useState<MinorAccount | null>(null);
  const [isAddingSymbol, setIsAddingSymbol] = useState(false);
  const [symbolToAdd, setSymbolToAdd] = useState('');
  const [symbolError, setSymbolError] = useState('');

  // Confirmation dialog state
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [confirmDialogAction, setConfirmDialogAction] = useState<'enable' | 'disable' | null>(null);

  // Fetch settings for the minor account
  useEffect(() => {
    if (!minorId) return;

    const fetchSettings = async () => {
      try {
        setLoading(true);
        // In a real app, this would be an API call
        // const response = await axios.get(`/api/v1/family/minor/${minorId}/restrictions`);
        // setSettings(response.data.settings);
        // setMinorDetails(response.data.minor);

        // Mock data for demo
        setTimeout(() => {
          // Use default settings with some random variations
          const mockSettings: RestrictionSettings = {
            ...defaultSettings,
            max_daily_trade_amount: 500,
            max_single_trade_amount: 100,
            restricted_symbols: ['GME', 'AMC', 'DOGE'],
            automatic_approval_under: 25
          };

          setSettings(mockSettings);
          setMinorDetails({
            id: minorId,
            name: 'Sam Smith',
            age: 13,
            email: 'sam.smith@example.com'
          });
          setLoading(false);
        }, 800);
      } catch (err) {
        console.error('Error fetching restriction settings:', err);
        setError('Failed to load restriction settings. Please try again.');
        setLoading(false);
      }
    };

    fetchSettings();
  }, [minorId]);

  // Handle saving settings
  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      
      // In a real app, this would be an API call
      // await axios.post(`/api/v1/family/minor/${minorId}/restrictions`, settings);
      
      // Mock successful save for demo
      setTimeout(() => {
        setSuccessMessage('Restriction settings saved successfully');
        setSaving(false);
        
        // Clear success message after 3 seconds
        setTimeout(() => {
          setSuccessMessage(null);
          if (onSaved) onSaved();
        }, 3000);
      }, 1000);
    } catch (err) {
      console.error('Error saving restriction settings:', err);
      setError('Failed to save restriction settings. Please try again.');
      setSaving(false);
    }
  };

  // Handle reset to defaults
  const handleReset = () => {
    setSettings(defaultSettings);
  };

  // Handle switch change
  const handleSwitchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = event.target;
    
    // Special handling for trading_enabled toggle
    if (name === 'trading_enabled' && !checked) {
      setConfirmDialogAction('disable');
      setConfirmDialogOpen(true);
      return;
    }
    
    // Special handling for educational_requirement toggle
    if (name === 'educational_requirement' && !checked) {
      setConfirmDialogAction('enable');
      setConfirmDialogOpen(true);
      return;
    }
    
    if (name === 'time_restrictions.enabled') {
      setSettings(prev => ({
        ...prev,
        time_restrictions: {
          ...prev.time_restrictions,
          enabled: checked
        }
      }));
    } else {
      setSettings(prev => ({
        ...prev,
        [name]: checked
      }));
    }
  };

  // Handle numeric input changes
  const handleNumericChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    const numValue = parseFloat(value);
    
    if (!isNaN(numValue)) {
      setSettings(prev => ({
        ...prev,
        [name]: numValue
      }));
    }
  };

  // Handle slider changes
  const handleSliderChange = (name: string) => (_event: Event, newValue: number | number[]) => {
    setSettings(prev => ({
      ...prev,
      [name]: newValue
    }));
  };

  // Handle select changes
  const handleSelectChange = (event: React.ChangeEvent<{ name?: string; value: unknown }>) => {
    const { name, value } = event.target;
    
    if (name) {
      setSettings(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  // Handle time changes
  const handleTimeChange = (field: 'start' | 'end') => (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSettings(prev => ({
      ...prev,
      time_restrictions: {
        ...prev.time_restrictions,
        allowed_hours: {
          ...prev.time_restrictions.allowed_hours,
          [field]: value
        }
      }
    }));
  };

  // Handle day toggle
  const handleDayToggle = (day: string) => () => {
    setSettings(prev => {
      const currentDays = prev.time_restrictions.allowed_days;
      const updatedDays = currentDays.includes(day)
        ? currentDays.filter(d => d !== day)
        : [...currentDays, day];
        
      return {
        ...prev,
        time_restrictions: {
          ...prev.time_restrictions,
          allowed_days: updatedDays
        }
      };
    });
  };

  // Handle changing educational modules
  const handleModuleToggle = (moduleId: string) => () => {
    setSettings(prev => {
      const currentModules = prev.educational_modules_required;
      const updatedModules = currentModules.includes(moduleId)
        ? currentModules.filter(m => m !== moduleId)
        : [...currentModules, moduleId];
        
      return {
        ...prev,
        educational_modules_required: updatedModules
      };
    });
  };

  // Handle investment type toggle
  const handleInvestmentTypeToggle = (typeId: string) => () => {
    setSettings(prev => {
      const currentTypes = prev.allowed_investment_types;
      const updatedTypes = currentTypes.includes(typeId)
        ? currentTypes.filter(t => t !== typeId)
        : [...currentTypes, typeId];
        
      return {
        ...prev,
        allowed_investment_types: updatedTypes
      };
    });
  };

  // Handle restricted symbol add
  const handleAddSymbol = () => {
    setIsAddingSymbol(true);
    setSymbolToAdd('');
    setSymbolError('');
  };

  // Handle symbol input change
  const handleSymbolInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSymbolToAdd(event.target.value.toUpperCase());
    setSymbolError('');
  };

  // Handle confirm add symbol
  const handleConfirmAddSymbol = () => {
    const symbol = symbolToAdd.trim();
    
    if (!symbol) {
      setSymbolError('Please enter a symbol');
      return;
    }
    
    if (settings.restricted_symbols.includes(symbol)) {
      setSymbolError('This symbol is already restricted');
      return;
    }
    
    // Add the symbol to restricted list
    setSettings(prev => ({
      ...prev,
      restricted_symbols: [...prev.restricted_symbols, symbol]
    }));
    
    setIsAddingSymbol(false);
  };

  // Handle cancel add symbol
  const handleCancelAddSymbol = () => {
    setIsAddingSymbol(false);
  };

  // Handle remove restricted symbol
  const handleRemoveSymbol = (symbol: string) => () => {
    setSettings(prev => ({
      ...prev,
      restricted_symbols: prev.restricted_symbols.filter(s => s !== symbol)
    }));
  };

  // Handle confirmation dialog
  const handleConfirmAction = () => {
    // If confirming disable trading
    if (confirmDialogAction === 'disable') {
      setSettings(prev => ({
        ...prev,
        trading_enabled: false
      }));
    }
    
    // If confirming disable educational requirements
    if (confirmDialogAction === 'enable') {
      setSettings(prev => ({
        ...prev,
        educational_requirement: false
      }));
    }
    
    setConfirmDialogOpen(false);
    setConfirmDialogAction(null);
  };

  // Handle cancel confirmation
  const handleCancelConfirm = () => {
    setConfirmDialogOpen(false);
    setConfirmDialogAction(null);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress size={40} />
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        {/* Header with minor details */}
        {minorDetails && (
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                bgcolor: 'primary.main',
                color: 'primary.contrastText',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                mr: 2
              }}
            >
              <ChildCare fontSize="large" />
            </Box>
            <Box>
              <Typography variant="h6">{minorDetails.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {minorDetails.age} years old • {minorDetails.email}
              </Typography>
            </Box>
          </Box>
        )}

        {/* Success message */}
        {successMessage && (
          <Alert severity="success" sx={{ mb: 3 }}>{successMessage}</Alert>
        )}
        
        {/* Error message */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
        )}

        {/* Trading Permissions */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <AttachMoney sx={{ mr: 1 }} />
              Trading Permissions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.trading_enabled}
                      onChange={handleSwitchChange}
                      name="trading_enabled"
                      color="primary"
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography>Enable Trading</Typography>
                      <Tooltip title="Allow the minor to place trade requests">
                        <InfoOutlined fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                      </Tooltip>
                    </Box>
                  }
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Maximum Daily Trading Amount"
                  name="max_daily_trade_amount"
                  value={settings.max_daily_trade_amount}
                  onChange={handleNumericChange}
                  disabled={!settings.trading_enabled}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  }}
                  helperText="Maximum total value of trades allowed per day"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Maximum Single Trade Amount"
                  name="max_single_trade_amount"
                  value={settings.max_single_trade_amount}
                  onChange={handleNumericChange}
                  disabled={!settings.trading_enabled}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  }}
                  helperText="Maximum value for a single trade"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Maximum Daily Trades"
                  name="max_daily_trades"
                  value={settings.max_daily_trades}
                  onChange={handleNumericChange}
                  disabled={!settings.trading_enabled}
                  helperText="Maximum number of trades allowed per day"
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Auto-Approve Trades Under"
                  name="automatic_approval_under"
                  value={settings.automatic_approval_under}
                  onChange={handleNumericChange}
                  disabled={!settings.trading_enabled}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  }}
                  helperText="Trades below this amount will be automatically approved"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Investment Types */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <Security sx={{ mr: 1 }} />
              Allowed Investment Types
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Typography variant="body2" color="text.secondary" paragraph>
              Select which investment types the minor is allowed to trade.
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {availableInvestmentTypes.map((type) => {
                const isSelected = settings.allowed_investment_types.includes(type.id);
                return (
                  <Chip
                    key={type.id}
                    label={type.name}
                    clickable
                    color={isSelected ? 'primary' : 'default'}
                    variant={isSelected ? 'filled' : 'outlined'}
                    onClick={handleInvestmentTypeToggle(type.id)}
                    disabled={!settings.trading_enabled}
                  />
                );
              })}
            </Box>
            
            <Alert severity="info" variant="outlined">
              <Typography variant="body2">
                More advanced investment types like Options and Cryptocurrencies may require additional education before enabling.
              </Typography>
            </Alert>
          </CardContent>
        </Card>

        {/* Restricted Symbols */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <Block sx={{ mr: 1 }} />
              Restricted Symbols
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Typography variant="body2" color="text.secondary" paragraph>
              Add stock symbols that the minor is not allowed to trade.
            </Typography>
            
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {settings.restricted_symbols.map((symbol) => (
                <Chip
                  key={symbol}
                  label={symbol}
                  onDelete={handleRemoveSymbol(symbol)}
                  disabled={!settings.trading_enabled}
                  color="error"
                />
              ))}
              
              {isAddingSymbol ? (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <TextField
                    size="small"
                    label="Symbol"
                    value={symbolToAdd}
                    onChange={handleSymbolInputChange}
                    error={!!symbolError}
                    helperText={symbolError}
                    autoFocus
                    disabled={!settings.trading_enabled}
                  />
                  <Button
                    variant="contained"
                    size="small"
                    onClick={handleConfirmAddSymbol}
                    disabled={!settings.trading_enabled}
                  >
                    <Done fontSize="small" />
                  </Button>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={handleCancelAddSymbol}
                    disabled={!settings.trading_enabled}
                  >
                    <Close fontSize="small" />
                  </Button>
                </Box>
              ) : (
                <Chip
                  icon={<Add />}
                  label="Add Symbol"
                  variant="outlined"
                  onClick={handleAddSymbol}
                  disabled={!settings.trading_enabled}
                />
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Educational Requirements */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <School sx={{ mr: 1 }} />
              Educational Requirements
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.educational_requirement}
                      onChange={handleSwitchChange}
                      name="educational_requirement"
                      color="primary"
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography>Require Educational Module Completion</Typography>
                      <Tooltip title="Minor must complete selected educational modules before trading">
                        <InfoOutlined fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                      </Tooltip>
                    </Box>
                  }
                />
              </Grid>
              
              {settings.educational_requirement && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Select modules that must be completed before trading is enabled:
                  </Typography>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {availableEducationalModules.map((module) => {
                      const isSelected = settings.educational_modules_required.includes(module.id);
                      return (
                        <Chip
                          key={module.id}
                          label={module.name}
                          clickable
                          color={isSelected ? 'primary' : 'default'}
                          variant={isSelected ? 'filled' : 'outlined'}
                          onClick={handleModuleToggle(module.id)}
                        />
                      );
                    })}
                  </Box>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>

        {/* Content Filtering */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <Settings sx={{ mr: 1 }} />
              Content Filtering
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="content-filter-label">Content Filter Level</InputLabel>
              <Select
                labelId="content-filter-label"
                name="content_filter_level"
                value={settings.content_filter_level}
                label="Content Filter Level"
                onChange={handleSelectChange}
              >
                <MenuItem value="low">Low (Minimal Filtering)</MenuItem>
                <MenuItem value="medium">Medium (Age-Appropriate)</MenuItem>
                <MenuItem value="high">High (Maximum Protection)</MenuItem>
              </Select>
              <FormHelperText>
                Controls the level of filtering for news and educational content
              </FormHelperText>
            </FormControl>
          </CardContent>
        </Card>

        {/* Time Restrictions */}
        <Card variant="outlined" sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <AccessTime sx={{ mr: 1 }} />
              Time Restrictions
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.time_restrictions.enabled}
                      onChange={handleSwitchChange}
                      name="time_restrictions.enabled"
                      color="primary"
                    />
                  }
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography>Enable Time Restrictions</Typography>
                      <Tooltip title="Limit when the minor can access trading features">
                        <InfoOutlined fontSize="small" sx={{ ml: 1, color: 'text.secondary' }} />
                      </Tooltip>
                    </Box>
                  }
                />
              </Grid>
              
              {settings.time_restrictions.enabled && (
                <>
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Allowed Days:
                    </Typography>
                    
                    <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 2 }}>
                      {daysOfWeek.map((day) => {
                        const isSelected = settings.time_restrictions.allowed_days.includes(day.id);
                        return (
                          <Chip
                            key={day.id}
                            label={day.name}
                            clickable
                            color={isSelected ? 'primary' : 'default'}
                            variant={isSelected ? 'filled' : 'outlined'}
                            onClick={handleDayToggle(day.id)}
                            sx={{ mt: 1 }}
                          />
                        );
                      })}
                    </Stack>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="time"
                      label="Start Time"
                      value={settings.time_restrictions.allowed_hours.start}
                      onChange={handleTimeChange('start')}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      type="time"
                      label="End Time"
                      value={settings.time_restrictions.allowed_hours.end}
                      onChange={handleTimeChange('end')}
                      InputLabelProps={{ shrink: true }}
                    />
                  </Grid>
                </>
              )}
            </Grid>
          </CardContent>
        </Card>

        {/* Action buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button 
            variant="outlined" 
            onClick={onCancel || handleReset}
            disabled={saving}
          >
            {onCancel ? 'Cancel' : 'Reset to Defaults'}
          </Button>
          
          <Box>
            <Button
              variant="outlined"
              onClick={handleReset}
              sx={{ mr: 1 }}
              disabled={saving}
            >
              <Refresh sx={{ mr: 1 }} />
              Reset
            </Button>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleSave}
              disabled={saving}
              startIcon={saving ? <CircularProgress size={20} /> : <Save />}
            >
              {saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </Box>
        </Box>

        {/* Confirmation Dialog */}
        <Dialog
          open={confirmDialogOpen}
          onClose={handleCancelConfirm}
          aria-labelledby="alert-dialog-title"
          aria-describedby="alert-dialog-description"
        >
          <DialogTitle id="alert-dialog-title">
            {confirmDialogAction === 'disable' ? 'Disable Trading?' : 'Disable Educational Requirements?'}
          </DialogTitle>
          <DialogContent>
            <DialogContentText id="alert-dialog-description">
              {confirmDialogAction === 'disable' ? (
                <>
                  <Warning color="warning" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Disabling trading will prevent the minor from placing any trades until you re-enable this feature.
                  Are you sure you want to continue?
                </>
              ) : (
                <>
                  <Warning color="warning" sx={{ verticalAlign: 'middle', mr: 1 }} />
                  Disabling educational requirements will allow the minor to trade without completing educational modules.
                  This is not recommended for younger users. Are you sure you want to continue?
                </>
              )}
            </DialogContentText>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCancelConfirm}>Cancel</Button>
            <Button onClick={handleConfirmAction} color="warning" autoFocus>
              {confirmDialogAction === 'disable' ? 'Disable Trading' : 'Disable Requirements'}
            </Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default MinorRestrictionSettings;