import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  Box,
  Typography,
  Paper,
  Grid,
  Switch,
  FormControlLabel,
  Slider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Divider,
  Alert,
  Card,
  CardContent,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Link,
  Badge,
} from '@mui/material';
import {
  Savings,
  AccountBalance,
  CreditCard,
  Info,
  Add,
  Refresh,
  DeleteOutline,
  Sync,
  BarChart,
  AddCircle,
  ArrowForward,
  School,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { useSnackbar } from 'notistack';
import { formatCurrency } from '../../utils/formatters';
import { RootState } from '../../store/store';
import { EducationalTooltip } from '../common/EducationalTooltip';

interface RoundupSettingsProps {
  onSaved?: () => void;
  darkMode?: boolean;
}

interface RoundupStats {
  total_roundups: number;
  total_amount: number;
  pending_amount: number;
  invested_amount: number;
  total_investments: number;
}

export const RoundupSettings: React.FC<RoundupSettingsProps> = ({
  onSaved,
  darkMode = true,
}) => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { enqueueSnackbar } = useSnackbar();
  
  // Redux state
  const { isPremium, isFamily } = useSelector((state: any) => state.subscription);
  const user = useSelector((state: any) => state.user.currentUser);
  const portfolios = useSelector((state: any) => state.portfolio.portfolios || []);
  
  // State
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    roundup_enabled: false,
    roundup_multiplier: 1,
    roundup_frequency: 'weekly',
    roundup_threshold: 5,
    micro_invest_target_type: 'default_portfolio',
    micro_invest_portfolio_id: null as number | null,
    micro_invest_symbol: '',
    notify_on_roundup: true,
    notify_on_investment: true,
    bank_account_linked: false,
    card_accounts_linked: false,
  });
  
  // Linked accounts state
  const [linkedAccounts, setLinkedAccounts] = useState<any[]>([]);
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  
  // Stats state
  const [stats, setStats] = useState<RoundupStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  
  // Fetch settings
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await api.get('/micro-invest/settings');
        setSettings(response.data);
        
        // If no portfolio is selected, use the first one
        if (!response.data.micro_invest_portfolio_id && portfolios.length > 0) {
          setSettings(prev => ({
            ...prev,
            micro_invest_portfolio_id: portfolios[0].id
          }));
        }
        
        // Fetch stats if roundups are enabled
        if (response.data.roundup_enabled) {
          fetchStats();
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching roundup settings:', error);
        setLoading(false);
      }
    };
    
    fetchSettings();
  }, [portfolios]);
  
  // Fetch roundup stats
  const fetchStats = async () => {
    setLoadingStats(true);
    try {
      const response = await api.get('/micro-invest/roundups/summary');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching roundup stats:', error);
    } finally {
      setLoadingStats(false);
    }
  };
  
  // Handle settings change
  const handleSettingsChange = (name: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [name]: value
    }));
  };
  
  // Handle save settings
  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      await api.patch('/micro-invest/settings', settings);
      enqueueSnackbar('Roundup settings saved successfully!', { variant: 'success' });
      
      // Refetch stats if enabled
      if (settings.roundup_enabled) {
        fetchStats();
      }
      
      if (onSaved) {
        onSaved();
      }
    } catch (error) {
      console.error('Error saving roundup settings:', error);
      enqueueSnackbar('Failed to save settings. Please try again.', { variant: 'error' });
    } finally {
      setSaving(false);
    }
  };
  
  // Handle link account
  const handleLinkAccount = async () => {
    setShowLinkDialog(false);
    enqueueSnackbar('Account linking feature will be implemented soon.', { variant: 'info' });
  };
  
  // Handle invest now
  const handleInvestNow = async () => {
    try {
      const response = await api.post('/micro-invest/roundups/invest');
      if (response.data.status === 'success') {
        enqueueSnackbar(`Successfully invested ${formatCurrency(response.data.amount)} in ${response.data.symbol}!`, { variant: 'success' });
        fetchStats();
      } else if (response.data.status === 'no_pending_roundups') {
        enqueueSnackbar('No pending roundups to invest.', { variant: 'info' });
      } else if (response.data.status === 'below_minimum') {
        enqueueSnackbar(`Pending amount (${formatCurrency(response.data.amount)}) is below the minimum investment threshold.`, { variant: 'warning' });
      }
    } catch (error) {
      console.error('Error investing roundups:', error);
      enqueueSnackbar('Failed to invest roundups. Please try again.', { variant: 'error' });
    }
  };
  
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }
  
  // Check subscription
  const canUseRoundups = isPremium || isFamily;
  
  const bgPaper = darkMode ? 'background.paperDark' : 'background.paper';
  const bgPaperLight = darkMode ? 'background.paperLight' : '#f5f9ff';
  const textColor = darkMode ? 'text.primary' : 'text.primary';
  const secondaryTextColor = darkMode ? 'text.secondary' : 'text.secondary';
  
  return (
    <Box>
      <Paper elevation={darkMode ? 3 : 1} sx={{ p: 3, bgcolor: bgPaper }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Savings color="primary" sx={{ mr: 1, fontSize: 28 }} />
          <Typography variant="h6" component="div" color={textColor}>
            Roundup Settings
            <EducationalTooltip
              term="Roundups"
              definition="Roundups automatically collect the spare change from your everyday purchases and invest it. For example, if you spend $3.50, $0.50 will be invested."
              placement="right"
            />
          </Typography>
        </Box>
        
        {!canUseRoundups && (
          <Alert severity="info" sx={{ mb: 3 }}>
            Roundups are available with Premium and Family subscriptions.{' '}
            <Link href="/pricing" color="inherit" underline="always">
              Upgrade now
            </Link>
          </Alert>
        )}
        
        <Grid container spacing={3}>
          <Grid size={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.roundup_enabled}
                  onChange={(e) => handleSettingsChange('roundup_enabled', e.target.checked)}
                  disabled={!canUseRoundups}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="subtitle1" sx={{ mr: 1 }}>
                    Enable Roundups
                  </Typography>
                  <Tooltip title="Automatically round up your purchases and invest the spare change">
                    <Info fontSize="small" color="action" />
                  </Tooltip>
                </Box>
              }
            />
          </Grid>
          
          {settings.roundup_enabled && (
            <>
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" gutterBottom color={secondaryTextColor}>
                  Roundup Multiplier
                  <Tooltip title="Multiply your roundups to invest more. For example, with 2x multiplier, a $0.50 roundup becomes $1.00">
                    <Info fontSize="small" color="action" sx={{ ml: 1 }} />
                  </Tooltip>
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Slider
                    value={settings.roundup_multiplier}
                    onChange={(_, value) => handleSettingsChange('roundup_multiplier', value)}
                    step={1}
                    marks
                    min={1}
                    max={5}
                    valueLabelDisplay="auto"
                    sx={{ flexGrow: 1, mr: 2 }}
                  />
                  <Typography variant="body1" color={textColor} sx={{ fontWeight: 'bold', minWidth: 30 }}>
                    {settings.roundup_multiplier}x
                  </Typography>
                </Box>
              </Grid>
              
              <Grid size={{ xs: 12, md: 6 }}>
                <Typography variant="subtitle2" gutterBottom color={secondaryTextColor}>
                  Investment Frequency
                  <Tooltip title="How often your collected roundups will be invested">
                    <Info fontSize="small" color="action" sx={{ ml: 1 }} />
                  </Tooltip>
                </Typography>
                <FormControl fullWidth>
                  <Select
                    value={settings.roundup_frequency}
                    onChange={(e) => handleSettingsChange('roundup_frequency', e.target.value)}
                    sx={{ bgcolor: bgPaperLight }}
                  >
                    <MenuItem value="daily">Daily</MenuItem>
                    <MenuItem value="weekly">Weekly (Every Monday)</MenuItem>
                    <MenuItem value="threshold">When Threshold Reached</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              
              {settings.roundup_frequency === 'threshold' && (
                <Grid size={{ xs: 12, md: 6 }}>
                  <Typography variant="subtitle2" gutterBottom color={secondaryTextColor}>
                    Investment Threshold ($)
                    <Tooltip title="Minimum amount to collect before investing">
                      <Info fontSize="small" color="action" sx={{ ml: 1 }} />
                    </Tooltip>
                  </Typography>
                  <TextField
                    type="number"
                    value={settings.roundup_threshold}
                    onChange={(e) => handleSettingsChange('roundup_threshold', parseFloat(e.target.value))}
                    InputProps={{
                      startAdornment: <Box component="span" sx={{ mr: 1 }}>$</Box>,
                    }}
                    fullWidth
                    sx={{ bgcolor: bgPaperLight }}
                  />
                </Grid>
              )}
              
              <Grid size={12}>
                <Typography variant="subtitle2" gutterBottom color={secondaryTextColor}>
                  Investment Target
                  <Tooltip title="Where your roundups will be invested">
                    <Info fontSize="small" color="action" sx={{ ml: 1 }} />
                  </Tooltip>
                </Typography>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <Select
                    value={settings.micro_invest_target_type}
                    onChange={(e) => handleSettingsChange('micro_invest_target_type', e.target.value)}
                    sx={{ bgcolor: bgPaperLight }}
                  >
                    <MenuItem value="default_portfolio">Default Portfolio</MenuItem>
                    <MenuItem value="specific_portfolio">Specific Portfolio</MenuItem>
                    <MenuItem value="specific_symbol">Specific Symbol/ETF</MenuItem>
                    <MenuItem value="recommended_etf">Recommended ETF</MenuItem>
                  </Select>
                </FormControl>
                
                {settings.micro_invest_target_type === 'specific_portfolio' && (
                  <FormControl fullWidth>
                    <InputLabel>Portfolio</InputLabel>
                    <Select
                      value={settings.micro_invest_portfolio_id || ''}
                      onChange={(e) => handleSettingsChange('micro_invest_portfolio_id', e.target.value)}
                      label="Portfolio"
                      sx={{ bgcolor: bgPaperLight }}
                    >
                      {portfolios.map((portfolio: any) => (
                        <MenuItem key={portfolio.id} value={portfolio.id}>
                          {portfolio.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                )}
                
                {settings.micro_invest_target_type === 'specific_symbol' && (
                  <TextField
                    label="Symbol"
                    value={settings.micro_invest_symbol}
                    onChange={(e) => handleSettingsChange('micro_invest_symbol', e.target.value.toUpperCase())}
                    placeholder="e.g., VTI"
                    fullWidth
                    sx={{ bgcolor: bgPaperLight }}
                  />
                )}
                
                {settings.micro_invest_target_type === 'recommended_etf' && (
                  <Alert severity="info">
                    Based on your risk profile, we'll automatically invest in an appropriate ETF.
                  </Alert>
                )}
              </Grid>
              
              <Grid size={12}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle1" gutterBottom color={textColor} sx={{ mt: 2 }}>
                  Linked Accounts
                  <Tooltip title="Connect bank accounts and cards to track transactions for roundups">
                    <Info fontSize="small" color="action" sx={{ ml: 1 }} />
                  </Tooltip>
                </Typography>
                
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Paper
                      elevation={darkMode ? 2 : 1}
                      sx={{
                        p: 2,
                        bgcolor: settings.bank_account_linked ? (darkMode ? 'success.dark' : 'success.light') : bgPaperLight,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <AccountBalance 
                          color={settings.bank_account_linked ? "success" : "action"} 
                          sx={{ mr: 1 }} 
                        />
                        <Typography variant="body1" color={textColor}>
                          Bank Account
                        </Typography>
                      </Box>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={settings.bank_account_linked ? <Sync /> : <Add />}
                        onClick={() => setShowLinkDialog(true)}
                      >
                        {settings.bank_account_linked ? 'Manage' : 'Link'}
                      </Button>
                    </Paper>
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <Paper
                      elevation={darkMode ? 2 : 1}
                      sx={{
                        p: 2,
                        bgcolor: settings.card_accounts_linked ? (darkMode ? 'success.dark' : 'success.light') : bgPaperLight,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                      }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <CreditCard 
                          color={settings.card_accounts_linked ? "success" : "action"} 
                          sx={{ mr: 1 }} 
                        />
                        <Typography variant="body1" color={textColor}>
                          Card Accounts
                        </Typography>
                      </Box>
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={settings.card_accounts_linked ? <Sync /> : <Add />}
                        onClick={() => setShowLinkDialog(true)}
                      >
                        {settings.card_accounts_linked ? 'Manage' : 'Link'}
                      </Button>
                    </Paper>
                  </Grid>
                </Grid>
                
                {(!settings.bank_account_linked && !settings.card_accounts_linked) && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    Link at least one account to start collecting roundups.
                  </Alert>
                )}
              </Grid>
              
              <Grid size={12}>
                <Divider sx={{ my: 1 }} />
                <Typography variant="subtitle1" gutterBottom color={textColor} sx={{ mt: 2 }}>
                  Notification Preferences
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notify_on_roundup}
                          onChange={(e) => handleSettingsChange('notify_on_roundup', e.target.checked)}
                          color="primary"
                        />
                      }
                      label="Notify on roundup collection"
                    />
                  </Grid>
                  <Grid size={{ xs: 12, sm: 6 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={settings.notify_on_investment}
                          onChange={(e) => handleSettingsChange('notify_on_investment', e.target.checked)}
                          color="primary"
                        />
                      }
                      label="Notify on investment"
                    />
                  </Grid>
                </Grid>
              </Grid>
            </>
          )}
        </Grid>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
          <Button
            variant="contained"
            color="primary"
            onClick={handleSaveSettings}
            disabled={saving || !canUseRoundups}
          >
            {saving ? <CircularProgress size={24} /> : 'Save Settings'}
          </Button>
        </Box>
      </Paper>
      
      {settings.roundup_enabled && (
        <Paper elevation={darkMode ? 3 : 1} sx={{ p: 3, mt: 3, bgcolor: bgPaper }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" color={textColor}>
              Roundup Summary
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={fetchStats}
              disabled={loadingStats}
              size="small"
            >
              Refresh
            </Button>
          </Box>
          
          {loadingStats ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
              <CircularProgress />
            </Box>
          ) : stats ? (
            <>
              <Grid container spacing={3}>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: bgPaperLight }}>
                    <Typography variant="body2" color={secondaryTextColor}>
                      Total Roundups
                    </Typography>
                    <Typography variant="h6" color={textColor}>
                      {stats.total_roundups}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: bgPaperLight }}>
                    <Typography variant="body2" color={secondaryTextColor}>
                      Total Amount
                    </Typography>
                    <Typography variant="h6" color={textColor}>
                      {formatCurrency(stats.total_amount)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: bgPaperLight }}>
                    <Typography variant="body2" color={secondaryTextColor}>
                      Pending
                    </Typography>
                    <Typography variant="h6" color="primary">
                      {formatCurrency(stats.pending_amount)}
                    </Typography>
                  </Paper>
                </Grid>
                <Grid size={{ xs: 6, sm: 3 }}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: bgPaperLight }}>
                    <Typography variant="body2" color={secondaryTextColor}>
                      Invested
                    </Typography>
                    <Typography variant="h6" color="success.main">
                      {formatCurrency(stats.invested_amount)}
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleInvestNow}
                  disabled={stats.pending_amount <= 0}
                  startIcon={<Savings />}
                  sx={{ mr: 2 }}
                >
                  Invest Now ({formatCurrency(stats.pending_amount)})
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/roundups/history')}
                  startIcon={<BarChart />}
                >
                  View History
                </Button>
              </Box>
            </>
          ) : (
            <Alert severity="info">
              No roundup data available yet. Start by linking accounts and enabling roundups.
            </Alert>
          )}
        </Paper>
      )}
      
      {/* Learn about roundups card */}
      <Card sx={{ mt: 3, bgcolor: darkMode ? 'primary.dark' : 'primary.light' }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom color={darkMode ? 'white' : 'primary.dark'}>
            Learn About Roundups & Micro-Investing
          </Typography>
          <Typography variant="body2" color={darkMode ? 'rgba(255,255,255,0.8)' : 'primary.dark'}>
            Discover how small, consistent investments can add up to significant wealth over time.
            Our educational modules explain how roundups and micro-investing work.
          </Typography>
          <Button
            variant="contained"
            color={darkMode ? "secondary" : "primary"}
            sx={{ mt: 2 }}
            endIcon={<ArrowForward />}
            onClick={() => navigate('/education/micro-investing')}
          >
            View Educational Content
          </Button>
        </CardContent>
      </Card>
      
      {/* Link Account Dialog */}
      <Dialog open={showLinkDialog} onClose={() => setShowLinkDialog(false)}>
        <DialogTitle>Link Account</DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            Linking your accounts allows us to track your transactions and round them up for investing.
          </Typography>
          <Typography variant="body2" paragraph>
            We use bank-level security to ensure your information is always protected.
          </Typography>
          <Alert severity="info" sx={{ mb: 2 }}>
            Note: This feature is simulated for the beta version. In production, this would connect to a secure financial data API like Plaid.
          </Alert>
          <FormControlLabel
            control={
              <Switch 
                checked={settings.bank_account_linked}
                onChange={(e) => handleSettingsChange('bank_account_linked', e.target.checked)}
              />
            }
            label="Simulate Bank Account Linked"
          />
          <FormControlLabel
            control={
              <Switch 
                checked={settings.card_accounts_linked}
                onChange={(e) => handleSettingsChange('card_accounts_linked', e.target.checked)}
              />
            }
            label="Simulate Card Accounts Linked"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLinkDialog(false)}>Cancel</Button>
          <Button onClick={handleLinkAccount} variant="contained" color="primary">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RoundupSettings;