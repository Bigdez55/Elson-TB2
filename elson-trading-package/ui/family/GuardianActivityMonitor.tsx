import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Divider,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  IconButton,
  ButtonGroup,
  Button,
  CircularProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Tooltip,
  LinearProgress
} from '@mui/material';
import { DateRangePicker } from '@mui/x-date-pickers-pro/DateRangePicker';
import { DateRange } from '@mui/x-date-pickers-pro/internals/models';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import {
  Visibility,
  InfoOutlined,
  Search,
  FilterList,
  DownloadOutlined,
  Refresh,
  BarChart,
  ShowChart,
  Timeline,
  Person,
  AccountBalance,
  School,
  Warning,
  ErrorOutline,
  Close
} from '@mui/icons-material';
import { formatCurrency, formatDate } from '../../utils/formatters';
import axios from 'axios';

// Mock Data Interfaces
interface ActivityRecord {
  id: number;
  minor_id: number;
  minor_name: string;
  activity_type: 'login' | 'logout' | 'view_portfolio' | 'trade_request' | 'educational_content' | 'settings_change' | 'password_change';
  description: string;
  timestamp: string;
  ip_address: string;
  device_info: string;
  metadata?: any;
}

interface MinorSummary {
  id: number;
  name: string;
  age: number;
  login_count: number;
  educational_progress: number;
  trade_requests: number;
  last_activity: string;
}

// Mock data for development/demo purposes
const mockActivityRecords: ActivityRecord[] = [
  {
    id: 1,
    minor_id: 101,
    minor_name: 'Alex Johnson',
    activity_type: 'login',
    description: 'Logged in to account',
    timestamp: '2025-03-05T08:30:22Z',
    ip_address: '192.168.1.1',
    device_info: 'Chrome on Windows',
  },
  {
    id: 2,
    minor_id: 101,
    minor_name: 'Alex Johnson',
    activity_type: 'view_portfolio',
    description: 'Viewed portfolio performance',
    timestamp: '2025-03-05T08:32:45Z',
    ip_address: '192.168.1.1',
    device_info: 'Chrome on Windows',
  },
  {
    id: 3,
    minor_id: 101,
    minor_name: 'Alex Johnson',
    activity_type: 'trade_request',
    description: 'Requested to buy 2 shares of AAPL',
    timestamp: '2025-03-05T08:35:12Z',
    ip_address: '192.168.1.1',
    device_info: 'Chrome on Windows',
    metadata: {
      symbol: 'AAPL',
      quantity: 2,
      price: 182.15,
      trade_type: 'buy'
    }
  },
  {
    id: 4,
    minor_id: 102,
    minor_name: 'Sam Smith',
    activity_type: 'login',
    description: 'Logged in to account',
    timestamp: '2025-03-05T09:15:33Z',
    ip_address: '192.168.1.5',
    device_info: 'Safari on iPhone',
  },
  {
    id: 5,
    minor_id: 102,
    minor_name: 'Sam Smith',
    activity_type: 'educational_content',
    description: 'Completed "Introduction to Stock Market" module',
    timestamp: '2025-03-05T09:22:18Z',
    ip_address: '192.168.1.5',
    device_info: 'Safari on iPhone',
    metadata: {
      module_id: 'stock-market-intro',
      score: 90,
      completion_time: 15.5
    }
  },
  {
    id: 6,
    minor_id: 101,
    minor_name: 'Alex Johnson',
    activity_type: 'logout',
    description: 'Logged out of account',
    timestamp: '2025-03-05T09:30:05Z',
    ip_address: '192.168.1.1',
    device_info: 'Chrome on Windows',
  },
  {
    id: 7,
    minor_id: 103,
    minor_name: 'Jamie Williams',
    activity_type: 'settings_change',
    description: 'Updated notification preferences',
    timestamp: '2025-03-05T10:05:22Z',
    ip_address: '192.168.1.10',
    device_info: 'Firefox on MacOS',
    metadata: {
      field_changed: 'notification_preferences',
      old_value: { email: true, push: false },
      new_value: { email: true, push: true }
    }
  },
  {
    id: 8,
    minor_id: 102,
    minor_name: 'Sam Smith',
    activity_type: 'trade_request',
    description: 'Requested to buy 1 share of MSFT',
    timestamp: '2025-03-05T10:45:38Z',
    ip_address: '192.168.1.5',
    device_info: 'Safari on iPhone',
    metadata: {
      symbol: 'MSFT',
      quantity: 1,
      price: 415.22,
      trade_type: 'buy'
    }
  },
  {
    id: 9,
    minor_id: 103,
    minor_name: 'Jamie Williams',
    activity_type: 'educational_content',
    description: 'Started "Types of Investments" module',
    timestamp: '2025-03-05T11:10:47Z',
    ip_address: '192.168.1.10',
    device_info: 'Firefox on MacOS',
    metadata: {
      module_id: 'types-of-investments',
      progress: 25
    }
  },
  {
    id: 10,
    minor_id: 101,
    minor_name: 'Alex Johnson',
    activity_type: 'login',
    description: 'Logged in to account',
    timestamp: '2025-03-05T13:05:12Z',
    ip_address: '192.168.1.1',
    device_info: 'Chrome on Windows',
  },
  {
    id: 11,
    minor_id: 101,
    minor_name: 'Alex Johnson',
    activity_type: 'educational_content',
    description: 'Completed "Trading Basics" quiz',
    timestamp: '2025-03-05T13:22:40Z',
    ip_address: '192.168.1.1',
    device_info: 'Chrome on Windows',
    metadata: {
      module_id: 'trading-basics-quiz',
      score: 85,
      completion_time: 8.2
    }
  },
  {
    id: 12,
    minor_id: 102,
    minor_name: 'Sam Smith',
    activity_type: 'password_change',
    description: 'Changed account password',
    timestamp: '2025-03-05T14:30:15Z',
    ip_address: '192.168.1.5',
    device_info: 'Safari on iPhone',
  }
];

const mockMinorSummaries: MinorSummary[] = [
  {
    id: 101,
    name: 'Alex Johnson',
    age: 15,
    login_count: 52,
    educational_progress: 75,
    trade_requests: 8,
    last_activity: '2025-03-05T13:22:40Z'
  },
  {
    id: 102,
    name: 'Sam Smith',
    age: 13,
    login_count: 34,
    educational_progress: 60,
    trade_requests: 4,
    last_activity: '2025-03-05T14:30:15Z'
  },
  {
    id: 103,
    name: 'Jamie Williams',
    age: 16,
    login_count: 28,
    educational_progress: 45,
    trade_requests: 2,
    last_activity: '2025-03-05T11:10:47Z'
  }
];

// Component Props
interface GuardianActivityMonitorProps {
  onViewMinorDetails?: (minorId: number) => void;
}

// Activity Icon Mapping
const getActivityIcon = (type: string) => {
  switch (type) {
    case 'login':
      return <Person color="primary" fontSize="small" />;
    case 'logout':
      return <Person color="action" fontSize="small" />;
    case 'view_portfolio':
      return <ShowChart color="info" fontSize="small" />;
    case 'trade_request':
      return <AccountBalance color="warning" fontSize="small" />;
    case 'educational_content':
      return <School color="success" fontSize="small" />;
    case 'settings_change':
      return <Timeline color="info" fontSize="small" />;
    case 'password_change':
      return <Warning color="error" fontSize="small" />;
    default:
      return <InfoOutlined fontSize="small" />;
  }
};

// Activity Type Labels
const getActivityLabel = (type: string) => {
  switch (type) {
    case 'login':
      return 'Login';
    case 'logout':
      return 'Logout';
    case 'view_portfolio':
      return 'Portfolio View';
    case 'trade_request':
      return 'Trade Request';
    case 'educational_content':
      return 'Education';
    case 'settings_change':
      return 'Settings Change';
    case 'password_change':
      return 'Password Change';
    default:
      return type.replace('_', ' ');
  }
};

// Main Component
const GuardianActivityMonitor: React.FC<GuardianActivityMonitorProps> = ({ onViewMinorDetails }) => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activityData, setActivityData] = useState<ActivityRecord[]>(mockActivityRecords);
  const [filteredActivity, setFilteredActivity] = useState<ActivityRecord[]>(mockActivityRecords);
  const [minorSummaries, setMinorSummaries] = useState<MinorSummary[]>(mockMinorSummaries);
  const [detailDialogOpen, setDetailDialogOpen] = useState(false);
  const [selectedActivity, setSelectedActivity] = useState<ActivityRecord | null>(null);
  const [activityTypeFilter, setActivityTypeFilter] = useState<string>('all');
  const [minorFilter, setMinorFilter] = useState<number | string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [dateRange, setDateRange] = useState<DateRange<Date>>([null, null]);
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  // Fetch activity data
  useEffect(() => {
    const fetchActivityData = async () => {
      try {
        setLoading(true);
        // In a real app, this would fetch from API
        // const response = await axios.get('/api/v1/family/activity-logs');
        // setActivityData(response.data);
        
        // For now, we'll use mock data after a short delay
        setTimeout(() => {
          setActivityData(mockActivityRecords);
          setFilteredActivity(mockActivityRecords);
          setMinorSummaries(mockMinorSummaries);
          setLoading(false);
        }, 500);
      } catch (err) {
        console.error('Error fetching activity data:', err);
        setError('Failed to load activity data. Please try again.');
        setLoading(false);
      }
    };

    fetchActivityData();
  }, []);

  // Apply filters when filter values change
  useEffect(() => {
    let filtered = [...activityData];
    
    // Filter by activity type
    if (activityTypeFilter !== 'all') {
      filtered = filtered.filter(item => item.activity_type === activityTypeFilter);
    }
    
    // Filter by minor
    if (minorFilter !== 'all') {
      filtered = filtered.filter(item => item.minor_id === minorFilter);
    }
    
    // Filter by search query
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item => 
        item.description.toLowerCase().includes(query) ||
        item.minor_name.toLowerCase().includes(query) ||
        (item.metadata && JSON.stringify(item.metadata).toLowerCase().includes(query))
      );
    }
    
    // Filter by date range
    if (dateRange[0] && dateRange[1]) {
      const startDate = dateRange[0].setHours(0, 0, 0, 0);
      const endDate = dateRange[1].setHours(23, 59, 59, 999);
      
      filtered = filtered.filter(item => {
        const itemDate = new Date(item.timestamp).getTime();
        return itemDate >= startDate && itemDate <= endDate;
      });
    }
    
    // Sort by timestamp (most recent first)
    filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    setFilteredActivity(filtered);
  }, [activityTypeFilter, minorFilter, searchQuery, dateRange, activityData]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleRefresh = () => {
    setLoading(true);
    // In a real app, this would refetch the data
    setTimeout(() => {
      setLoading(false);
    }, 500);
  };

  const handleViewDetails = (activity: ActivityRecord) => {
    setSelectedActivity(activity);
    setDetailDialogOpen(true);
  };

  const handleCloseDetail = () => {
    setDetailDialogOpen(false);
    setSelectedActivity(null);
  };

  const handleExportData = () => {
    // In a real app, this would generate a CSV or PDF
    alert('Export functionality would be implemented here');
  };

  const handleClearFilters = () => {
    setActivityTypeFilter('all');
    setMinorFilter('all');
    setSearchQuery('');
    setDateRange([null, null]);
  };

  const handleToggleFilters = () => {
    setShowFilterPanel(!showFilterPanel);
  };

  // Render activity log list
  const renderActivityLog = () => {
    if (loading) {
      return (
        <Box sx={{ py: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Loading activity data...
          </Typography>
        </Box>
      );
    }

    if (error) {
      return (
        <Alert severity="error" sx={{ my: 2 }}>
          {error}
        </Alert>
      );
    }

    if (filteredActivity.length === 0) {
      return (
        <Box sx={{ py: 4, textAlign: 'center' }}>
          <ErrorOutline sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="body1" color="text.secondary">
            No activities found matching your filters.
          </Typography>
          <Button
            variant="outlined"
            color="primary"
            onClick={handleClearFilters}
            sx={{ mt: 2 }}
          >
            Clear Filters
          </Button>
        </Box>
      );
    }

    return (
      <TableContainer component={Paper} variant="outlined">
        <Table sx={{ minWidth: 650 }} size="medium">
          <TableHead>
            <TableRow>
              <TableCell>Type</TableCell>
              <TableCell>Minor</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Date & Time</TableCell>
              <TableCell>Device</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredActivity.map((activity) => (
              <TableRow
                key={activity.id}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    {getActivityIcon(activity.activity_type)}
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {getActivityLabel(activity.activity_type)}
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{activity.minor_name}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{activity.description}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{formatDate(activity.timestamp)}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(activity.timestamp).toLocaleTimeString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">{activity.device_info}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {activity.ip_address}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => handleViewDetails(activity)}
                    >
                      <Visibility fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  // Render minor account summaries
  const renderMinorSummaries = () => {
    if (loading) {
      return (
        <Box sx={{ py: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <CircularProgress size={40} sx={{ mb: 2 }} />
          <Typography variant="body2" color="text.secondary">
            Loading minor account summaries...
          </Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={3}>
        {minorSummaries.map((minor) => (
          <Grid item xs={12} md={4} key={minor.id}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h6">{minor.name}</Typography>
                    <Chip
                      label={`${minor.age} years old`}
                      size="small"
                      icon={<School fontSize="small" />}
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => onViewMinorDetails && onViewMinorDetails(minor.id)}
                  >
                    View Details
                  </Button>
                </Box>

                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Last activity: {formatDate(minor.last_activity)}
                </Typography>

                <Box sx={{ mt: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">Educational Progress</Typography>
                    <Typography variant="body2" fontWeight="bold">{minor.educational_progress}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={minor.educational_progress}
                    sx={{ height: 8, borderRadius: 4, mb: 2 }}
                  />

                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    <Grid item xs={6}>
                      <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                        <Typography variant="h6" color="primary">{minor.login_count}</Typography>
                        <Typography variant="body2" color="text.secondary">Logins</Typography>
                      </Paper>
                    </Grid>
                    <Grid item xs={6}>
                      <Paper variant="outlined" sx={{ p: 1.5, textAlign: 'center' }}>
                        <Typography variant="h6" color="primary">{minor.trade_requests}</Typography>
                        <Typography variant="body2" color="text.secondary">Trade Requests</Typography>
                      </Paper>
                    </Grid>
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Activity Monitoring
          </Typography>
          <Box>
            <ButtonGroup variant="outlined" size="small" sx={{ mr: 1 }}>
              <Tooltip title="Refresh Data">
                <Button onClick={handleRefresh}>
                  <Refresh fontSize="small" />
                </Button>
              </Tooltip>
              <Tooltip title="Export Data">
                <Button onClick={handleExportData}>
                  <DownloadOutlined fontSize="small" />
                </Button>
              </Tooltip>
              <Tooltip title="Toggle Filters">
                <Button 
                  onClick={handleToggleFilters}
                  color={showFilterPanel ? 'primary' : 'inherit'}
                >
                  <FilterList fontSize="small" />
                </Button>
              </Tooltip>
            </ButtonGroup>
          </Box>
        </Box>

        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}
        >
          <Tab label="Activity Log" />
          <Tab label="Minor Summaries" />
        </Tabs>

        {/* Filter Panel */}
        {showFilterPanel && (
          <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Filter Options
            </Typography>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel id="activity-type-label">Activity Type</InputLabel>
                  <Select
                    labelId="activity-type-label"
                    value={activityTypeFilter}
                    label="Activity Type"
                    onChange={(e) => setActivityTypeFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Activities</MenuItem>
                    <MenuItem value="login">Logins</MenuItem>
                    <MenuItem value="logout">Logouts</MenuItem>
                    <MenuItem value="view_portfolio">Portfolio Views</MenuItem>
                    <MenuItem value="trade_request">Trade Requests</MenuItem>
                    <MenuItem value="educational_content">Educational Content</MenuItem>
                    <MenuItem value="settings_change">Settings Changes</MenuItem>
                    <MenuItem value="password_change">Password Changes</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <FormControl fullWidth size="small">
                  <InputLabel id="minor-filter-label">Minor Account</InputLabel>
                  <Select
                    labelId="minor-filter-label"
                    value={minorFilter}
                    label="Minor Account"
                    onChange={(e) => setMinorFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Minors</MenuItem>
                    {minorSummaries.map((minor) => (
                      <MenuItem key={minor.id} value={minor.id}>
                        {minor.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <LocalizationProvider dateAdapter={AdapterDateFns}>
                  <DateRangePicker
                    value={dateRange}
                    onChange={(newValue) => {
                      setDateRange(newValue);
                    }}
                    slotProps={{
                      textField: { 
                        size: 'small',
                        fullWidth: true,
                        placeholder: 'Filter by date range'
                      },
                    }}
                  />
                </LocalizationProvider>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  fullWidth
                  size="small"
                  placeholder="Search activities..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  InputProps={{
                    startAdornment: <Search fontSize="small" color="action" sx={{ mr: 1 }} />,
                  }}
                />
              </Grid>
              <Grid item xs={12} sx={{ textAlign: 'right' }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleClearFilters}
                  sx={{ mr: 1 }}
                >
                  Clear Filters
                </Button>
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => setShowFilterPanel(false)}
                >
                  Apply
                </Button>
              </Grid>
            </Grid>
          </Paper>
        )}

        <Divider sx={{ mb: 2 }} />

        {/* Tab Content */}
        <Box sx={{ mt: 2 }}>
          {tabValue === 0 ? renderActivityLog() : renderMinorSummaries()}
        </Box>

        {/* Activity Detail Dialog */}
        <Dialog
          open={detailDialogOpen}
          onClose={handleCloseDetail}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>
            Activity Details
            <IconButton
              aria-label="close"
              onClick={handleCloseDetail}
              sx={{ position: 'absolute', right: 8, top: 8 }}
            >
              <Close />
            </IconButton>
          </DialogTitle>
          <DialogContent dividers>
            {selectedActivity && (
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {getActivityIcon(selectedActivity.activity_type)}
                    <Typography variant="subtitle1" sx={{ ml: 1 }}>
                      {getActivityLabel(selectedActivity.activity_type)}
                    </Typography>
                    <Chip
                      label={new Date(selectedActivity.timestamp).toLocaleString()}
                      size="small"
                      variant="outlined"
                      sx={{ ml: 'auto' }}
                    />
                  </Box>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Minor Account</Typography>
                  <Typography variant="body1">{selectedActivity.minor_name}</Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Minor ID</Typography>
                  <Typography variant="body1">{selectedActivity.minor_id}</Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Divider sx={{ my: 1 }} />
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="body2" color="text.secondary">Description</Typography>
                  <Typography variant="body1">{selectedActivity.description}</Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">Device</Typography>
                  <Typography variant="body1">{selectedActivity.device_info}</Typography>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">IP Address</Typography>
                  <Typography variant="body1">{selectedActivity.ip_address}</Typography>
                </Grid>
                
                {selectedActivity.metadata && (
                  <>
                    <Grid item xs={12}>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="subtitle2" gutterBottom>Additional Details</Typography>
                    </Grid>
                    
                    {selectedActivity.activity_type === 'trade_request' && (
                      <>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">Symbol</Typography>
                          <Typography variant="body1">{selectedActivity.metadata.symbol}</Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">Quantity</Typography>
                          <Typography variant="body1">{selectedActivity.metadata.quantity} shares</Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">Price</Typography>
                          <Typography variant="body1">{formatCurrency(selectedActivity.metadata.price)}</Typography>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">Total Value</Typography>
                          <Typography variant="body1">{formatCurrency(selectedActivity.metadata.price * selectedActivity.metadata.quantity)}</Typography>
                        </Grid>
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">Trade Type</Typography>
                          <Chip
                            label={selectedActivity.metadata.trade_type.toUpperCase()}
                            color={selectedActivity.metadata.trade_type === 'buy' ? 'success' : 'error'}
                            size="small"
                          />
                        </Grid>
                      </>
                    )}
                    
                    {selectedActivity.activity_type === 'educational_content' && (
                      <>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="body2" color="text.secondary">Module</Typography>
                          <Typography variant="body1">{selectedActivity.metadata.module_id}</Typography>
                        </Grid>
                        {selectedActivity.metadata.score !== undefined && (
                          <Grid item xs={12} sm={6}>
                            <Typography variant="body2" color="text.secondary">Score</Typography>
                            <Typography variant="body1">{selectedActivity.metadata.score}%</Typography>
                          </Grid>
                        )}
                        {selectedActivity.metadata.progress !== undefined && (
                          <Grid item xs={12}>
                            <Typography variant="body2" color="text.secondary" gutterBottom>Progress</Typography>
                            <LinearProgress
                              variant="determinate"
                              value={selectedActivity.metadata.progress}
                              sx={{ height: 8, borderRadius: 4 }}
                            />
                            <Typography variant="body2" align="right" sx={{ mt: 0.5 }}>
                              {selectedActivity.metadata.progress}%
                            </Typography>
                          </Grid>
                        )}
                        {selectedActivity.metadata.completion_time !== undefined && (
                          <Grid item xs={12} sm={6}>
                            <Typography variant="body2" color="text.secondary">Completion Time</Typography>
                            <Typography variant="body1">{selectedActivity.metadata.completion_time} minutes</Typography>
                          </Grid>
                        )}
                      </>
                    )}
                    
                    {selectedActivity.activity_type === 'settings_change' && (
                      <>
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">Field Changed</Typography>
                          <Typography variant="body1">{selectedActivity.metadata.field_changed}</Typography>
                        </Grid>
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">Previous Value</Typography>
                          <Paper variant="outlined" sx={{ p: 1, bgcolor: 'background.default' }}>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                              {JSON.stringify(selectedActivity.metadata.old_value, null, 2)}
                            </Typography>
                          </Paper>
                        </Grid>
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">New Value</Typography>
                          <Paper variant="outlined" sx={{ p: 1, bgcolor: 'background.default' }}>
                            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                              {JSON.stringify(selectedActivity.metadata.new_value, null, 2)}
                            </Typography>
                          </Paper>
                        </Grid>
                      </>
                    )}
                  </>
                )}
              </Grid>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDetail}>Close</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

export default GuardianActivityMonitor;