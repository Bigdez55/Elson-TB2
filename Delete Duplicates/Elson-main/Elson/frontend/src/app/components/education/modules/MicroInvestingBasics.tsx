import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Stepper,
  Step,
  StepLabel,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Alert,
  Paper,
  Grid,
  Slider,
  TextField,
  IconButton,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import {
  AttachMoney,
  CheckCircleOutline,
  School,
  ArrowForward,
  ArrowBack,
  AccountBalance,
  LocalAtm,
  Timeline,
  TrendingUp,
  Lightbulb,
  CheckCircle,
  Info,
  ShowChart,
  Done,
  CreditCard,
  Calculate,
  ArrowCircleUp,
  FavoriteBorder,
} from '@mui/icons-material';
import { EducationalQuiz } from '../EducationalQuiz';
import { EducationalInteractive } from '../EducationalInteractive';
import { api } from '../../../services/api';
import { useSnackbar } from 'notistack';
import { formatCurrency } from '../../../utils/formatters';

// Module data
const MODULE_DATA = {
  title: 'Micro-Investing: Building Wealth One Small Step at a Time',
  description: 'Learn how micro-investing and fractional shares can help you build wealth consistently even with small amounts of money.',
  steps: [
    {
      title: 'What is Micro-Investing?',
      content: 'MicroInvestingIntro',
    },
    {
      title: 'Fractional Shares Explained',
      content: 'FractionalSharesExplained',
    },
    {
      title: 'Round-Up Investing',
      content: 'RoundUpInvesting',
    },
    {
      title: 'Dollar-Cost Averaging',
      content: 'DollarCostAveraging',
    },
    {
      title: 'Getting Started',
      content: 'GettingStarted',
    },
    {
      title: 'Knowledge Check',
      content: 'KnowledgeCheck',
    },
  ],
};

// Quiz data
const QUIZ_DATA = {
  questions: [
    {
      question: 'What is micro-investing?',
      options: [
        'A type of investment that only involves small companies',
        'Investing very small amounts of money regularly',
        'Investing only in cryptocurrency',
        'A type of investment only available to minors',
      ],
      correctAnswer: 1,
      explanation: 'Micro-investing is a strategy that allows you to invest very small amounts of money regularly, often automatically, making investing more accessible.',
    },
    {
      question: 'What are fractional shares?',
      options: [
        'Shares that have been split by a company',
        'Portions of a whole share of stock that allow you to invest with less money',
        'Shares owned by multiple people at once',
        'Discounted shares offered to new investors',
      ],
      correctAnswer: 1,
      explanation: 'Fractional shares are portions of a whole share of stock. They allow you to invest in companies with high share prices by purchasing just a fraction of a share.',
    },
    {
      question: 'How do round-ups work?',
      options: [
        'The stock price is rounded up to the nearest dollar',
        'Your transaction amounts are rounded up and the difference is invested',
        'Your investment returns are automatically rounded up',
        'The broker rounds up your investment to the nearest share',
      ],
      correctAnswer: 1,
      explanation: 'Round-ups work by rounding up your everyday purchases to the nearest dollar and investing the spare change. For example, if you spend $3.50, $0.50 would be invested.',
    },
    {
      question: 'What is dollar-cost averaging?',
      options: [
        'Converting all your investments to US dollars',
        'Investing the same amount of money at regular intervals, regardless of share price',
        'Manually calculating the average cost of your investments',
        'Only buying stocks when they're at their lowest price',
      ],
      correctAnswer: 1,
      explanation: 'Dollar-cost averaging is the practice of investing a fixed amount of money at regular intervals, regardless of share price. This helps reduce the impact of volatility.',
    },
    {
      question: 'What is a potential benefit of micro-investing?',
      options: [
        'Guaranteed high returns',
        'Making investing accessible to people with limited funds',
        'Completely eliminating investment risk',
        'Avoiding market volatility entirely',
      ],
      correctAnswer: 1,
      explanation: 'A key benefit of micro-investing is making investing accessible to people with limited funds by allowing them to start with very small amounts.',
    },
  ],
};

// Educational content components
const MicroInvestingIntro: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        What is Micro-Investing?
      </Typography>
      
      <Typography paragraph>
        Micro-investing is a strategy that allows you to invest very small amounts of money regularly.
        Instead of needing hundreds or thousands of dollars to start investing, you can begin with just a few dollars—or even pocket change.
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2, height: '100%', bgcolor: 'background.paperLight' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
              <Lightbulb color="primary" sx={{ mr: 1, mt: 0.5 }} />
              <Typography variant="subtitle1" fontWeight="bold">
                Key Benefits of Micro-Investing
              </Typography>
            </Box>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText primary="Low barrier to entry — start with as little as $1" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText primary="Build healthy financial habits through regular investing" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText primary="Learn about investing with minimal financial risk" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText primary="Take advantage of compound growth over time" />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <CheckCircle fontSize="small" color="success" />
                </ListItemIcon>
                <ListItemText primary="Automate your investing to make it effortless" />
              </ListItem>
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper elevation={2} sx={{ p: 2, height: '100%', bgcolor: 'background.paperLight' }}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
              <Info color="primary" sx={{ mr: 1, mt: 0.5 }} />
              <Typography variant="subtitle1" fontWeight="bold">
                Common Micro-Investing Methods
              </Typography>
            </Box>
            <List dense>
              <ListItem>
                <ListItemIcon>
                  <CreditCard fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Round-ups" 
                  secondary="Automatically invest the spare change from your everyday purchases" 
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <AttachMoney fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Fractional shares" 
                  secondary="Buy a portion of a stock instead of a whole share" 
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <Timeline fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="Recurring investments" 
                  secondary="Set up automatic investments on a daily, weekly, or monthly schedule" 
                />
              </ListItem>
              <ListItem>
                <ListItemIcon>
                  <LocalAtm fontSize="small" color="primary" />
                </ListItemIcon>
                <ListItemText 
                  primary="One-time micro-deposits" 
                  secondary="Manually invest small amounts whenever you want" 
                />
              </ListItem>
            </List>
          </Paper>
        </Grid>
      </Grid>
      
      <Typography variant="body1" sx={{ mt: 3 }}>
        The power of micro-investing comes from consistency and time. Even small amounts can grow significantly 
        through the power of compound interest if you start early and invest regularly.
      </Typography>
      
      <Alert severity="info" sx={{ mt: 2 }}>
        <AlertTitle>Did you know?</AlertTitle>
        If you invest just $5 per week over 30 years with an average annual return of 7%, 
        you would accumulate over $40,000, despite only contributing $7,800 directly!
      </Alert>
    </Box>
  );
};

const FractionalSharesExplained: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const [amount, setAmount] = useState<number>(10);
  const [stockPrice, setStockPrice] = useState<number>(150);

  // Calculate shares that can be purchased
  const calculateShares = () => {
    return amount / stockPrice;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Fractional Shares Explained
      </Typography>
      
      <Typography paragraph>
        Fractional shares allow you to buy a portion of a stock instead of a whole share. 
        This makes it possible to invest in companies with high share prices, even if you only have a small amount to invest.
      </Typography>
      
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>Example</AlertTitle>
        If a stock costs $3,500 per share (like some high-priced tech stocks), you can invest $100 and own approximately 0.0286 shares.
      </Alert>
      
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Benefits of Fractional Shares
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="primary">Accessibility</Typography>
              <Typography variant="body2">
                Invest in expensive stocks with small amounts of money, making premium companies available to all investors.
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="primary">Diversification</Typography>
              <Typography variant="body2">
                Spread a small investment across multiple companies instead of being limited to affordable stocks.
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="primary">Dollar-Based Investing</Typography>
              <Typography variant="body2">
                Invest exact dollar amounts instead of having to calculate how many shares you can afford.
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="subtitle2" color="primary">Regular Investing</Typography>
              <Typography variant="body2">
                Easily set up recurring investments with any amount, regardless of share prices.
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Box>
      
      <Typography variant="subtitle1" gutterBottom fontWeight="bold">
        Try it Yourself: Fractional Share Calculator
      </Typography>
      
      <Paper elevation={3} sx={{ p: 3, bgcolor: 'background.paperLight', mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              Investment Amount ($)
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Slider
                value={amount}
                onChange={(_, newValue) => setAmount(newValue as number)}
                min={1}
                max={1000}
                step={1}
                marks={[
                  { value: 1, label: '$1' },
                  { value: 500, label: '$500' },
                  { value: 1000, label: '$1000' },
                ]}
                sx={{ mr: 2, flexGrow: 1 }}
              />
              <TextField
                value={amount}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (!isNaN(value) && value >= 0) {
                    setAmount(value);
                  }
                }}
                InputProps={{ startAdornment: '$' }}
                variant="outlined"
                size="small"
                sx={{ width: 100 }}
              />
            </Box>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" gutterBottom>
              Stock Price ($)
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Slider
                value={stockPrice}
                onChange={(_, newValue) => setStockPrice(newValue as number)}
                min={10}
                max={3500}
                step={10}
                marks={[
                  { value: 10, label: '$10' },
                  { value: 1750, label: '$1750' },
                  { value: 3500, label: '$3500' },
                ]}
                sx={{ mr: 2, flexGrow: 1 }}
              />
              <TextField
                value={stockPrice}
                onChange={(e) => {
                  const value = Number(e.target.value);
                  if (!isNaN(value) && value >= 0) {
                    setStockPrice(value);
                  }
                }}
                InputProps={{ startAdornment: '$' }}
                variant="outlined"
                size="small"
                sx={{ width: 100 }}
              />
            </Box>
          </Grid>
          
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Typography variant="h6" align="center">
              You can buy {calculateShares().toFixed(6)} shares
            </Typography>
            <Typography variant="body2" color="textSecondary" align="center">
              (With fractional shares, you don't need to buy a whole share!)
            </Typography>
          </Grid>
        </Grid>
      </Paper>
      
      <Alert severity="warning">
        <AlertTitle>Important to Know</AlertTitle>
        <Typography variant="body2">
          • Not all brokerages offer fractional shares. Make sure your investment platform supports them.<br />
          • Some brokerages may have minimum investment amounts (often $1 or $5).<br />
          • Fractional shares typically cannot be transferred between brokerages.<br />
          • All the rights of stock ownership apply proportionally to your fractional shares.
        </Typography>
      </Alert>
    </Box>
  );
};

const RoundUpInvesting: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [purchaseAmount, setPurchaseAmount] = useState<number>(3.5);
  const [multiplier, setMultiplier] = useState<number>(1);
  const [roundupAmount, setRoundupAmount] = useState<number>(0.5);
  const [transactions, setTransactions] = useState<{amount: number, roundup: number}[]>([
    {amount: 3.50, roundup: 0.50},
    {amount: 12.25, roundup: 0.75},
    {amount: 8.99, roundup: 0.01},
    {amount: 4.35, roundup: 0.65},
    {amount: 25.10, roundup: 0.90},
  ]);

  // Calculate roundup
  const calculateRoundup = (amount: number, mult: number = 1) => {
    const nextDollar = Math.ceil(amount);
    return (nextDollar - amount) * mult;
  };

  // Update roundup when purchase amount changes
  React.useEffect(() => {
    setRoundupAmount(calculateRoundup(purchaseAmount, multiplier));
  }, [purchaseAmount, multiplier]);

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Round-Up Investing
      </Typography>
      
      <Typography paragraph>
        Round-up investing is a micro-investing method that automatically invests the "spare change" from your everyday purchases.
        When you make a purchase, the amount is rounded up to the nearest dollar, and the difference is invested.
      </Typography>
      
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          How Round-Ups Work
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <Paper elevation={3} sx={{ p: 2, mb: 3, bgcolor: 'background.paperLight' }}>
              <Typography variant="subtitle2" gutterBottom>
                Try the Round-Up Calculator
              </Typography>
              
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" gutterBottom>
                    Purchase Amount ($)
                  </Typography>
                  <TextField
                    value={purchaseAmount}
                    onChange={(e) => {
                      const value = parseFloat(e.target.value);
                      if (!isNaN(value) && value >= 0) {
                        setPurchaseAmount(value);
                      }
                    }}
                    InputProps={{ startAdornment: '$' }}
                    variant="outlined"
                    size="small"
                    fullWidth
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" gutterBottom>
                    Multiplier
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Slider
                      value={multiplier}
                      onChange={(_, newValue) => setMultiplier(newValue as number)}
                      min={1}
                      max={5}
                      step={1}
                      marks={[
                        { value: 1, label: '1x' },
                        { value: 2, label: '2x' },
                        { value: 3, label: '3x' },
                        { value: 4, label: '4x' },
                        { value: 5, label: '5x' },
                      ]}
                      sx={{ flexGrow: 1 }}
                    />
                  </Box>
                </Grid>
                
                <Grid item xs={12}>
                  <Box sx={{ 
                    p: 2, 
                    bgcolor: theme.palette.background.default,
                    borderRadius: 1,
                    textAlign: 'center',
                    mt: 1
                  }}>
                    <Typography variant="body2">
                      Round-up Amount: <strong>${roundupAmount.toFixed(2)}</strong>
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      ${purchaseAmount.toFixed(2)} rounded up to ${Math.ceil(purchaseAmount).toFixed(2)} 
                      {multiplier > 1 ? ` × ${multiplier}` : ''}
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={5}>
            <Paper elevation={3} sx={{ p: 2, mb: 3, bgcolor: 'background.paperLight' }}>
              <Typography variant="subtitle2" gutterBottom>
                Sample Transactions
              </Typography>
              
              <List dense>
                {transactions.map((t, idx) => (
                  <ListItem key={idx} divider={idx < transactions.length - 1}>
                    <ListItemIcon>
                      <CreditCard fontSize="small" />
                    </ListItemIcon>
                    <ListItemText
                      primary={`$${t.amount.toFixed(2)} Purchase`}
                      secondary={`$${t.roundup.toFixed(2)} Round-up`}
                    />
                    <ArrowCircleUp color="primary" />
                  </ListItem>
                ))}
              </List>
              
              <Box sx={{ mt: 2, p: 1, bgcolor: theme.palette.grey[100], borderRadius: 1 }}>
                <Typography variant="body2" align="center">
                  Total Round-ups: <strong>${transactions.reduce((sum, t) => sum + t.roundup, 0).toFixed(2)}</strong>
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Box>
      
      <Typography variant="subtitle1" gutterBottom fontWeight="bold">
        Key Benefits of Round-Up Investing
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper 
            elevation={1} 
            sx={{ 
              p: 2, 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center'
            }}
          >
            <FavoriteBorder color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Painless Saving
            </Typography>
            <Typography variant="body2">
              You won't feel the impact of the small amounts being invested from each transaction.
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper 
            elevation={1} 
            sx={{ 
              p: 2, 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center'
            }}
          >
            <ShowChart color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Automatic Investing
            </Typography>
            <Typography variant="body2">
              Your spare change is invested automatically without you having to think about it.
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper 
            elevation={1} 
            sx={{ 
              p: 2, 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center'
            }}
          >
            <Calculate color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Customizable Multipliers
            </Typography>
            <Typography variant="body2">
              Increase your investing by using multipliers (2x, 3x, etc.) on your round-ups.
            </Typography>
          </Paper>
        </Grid>
        
        <Grid item xs={12} sm={6} md={3}>
          <Paper 
            elevation={1} 
            sx={{ 
              p: 2, 
              height: '100%', 
              display: 'flex', 
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center'
            }}
          >
            <School color="primary" sx={{ fontSize: 40, mb: 1 }} />
            <Typography variant="subtitle2" gutterBottom>
              Builds Good Habits
            </Typography>
            <Typography variant="body2">
              Helps develop consistent investing habits without requiring discipline.
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      
      <Alert severity="info">
        <AlertTitle>How It Adds Up</AlertTitle>
        <Typography variant="body2">
          The average person makes 70-100 transactions per month. If the average round-up is 50 cents,
          that's $35-$50 invested monthly without even thinking about it—or $420-$600 per year!
        </Typography>
      </Alert>
    </Box>
  );
};

const DollarCostAveraging: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  const [activeTab, setActiveTab] = useState(0);
  
  // Sample DCA vs. lump sum data
  const dcaData = [
    { month: 'January', price: 100, invested: 100, shares: 1, totalShares: 1, value: 100 },
    { month: 'February', price: 80, invested: 100, shares: 1.25, totalShares: 2.25, value: 180 },
    { month: 'March', price: 90, invested: 100, shares: 1.11, totalShares: 3.36, value: 302.40 },
    { month: 'April', price: 70, invested: 100, shares: 1.43, totalShares: 4.79, value: 335.30 },
    { month: 'May', price: 110, invested: 100, shares: 0.91, totalShares: 5.70, value: 627 },
    { month: 'June', price: 120, invested: 100, shares: 0.83, totalShares: 6.53, value: 783.60 },
  ];
  
  // Calculate totals
  const totalInvested = dcaData.reduce((sum, month) => sum + month.invested, 0);
  const finalValue = dcaData[dcaData.length - 1].value;
  const profit = finalValue - totalInvested;
  const roi = (profit / totalInvested) * 100;
  
  // Calculate lump sum (investing all at once in January)
  const lumpSumShares = totalInvested / dcaData[0].price;
  const lumpSumValue = lumpSumShares * dcaData[dcaData.length - 1].price;
  const lumpSumProfit = lumpSumValue - totalInvested;
  const lumpSumRoi = (lumpSumProfit / totalInvested) * 100;
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Dollar-Cost Averaging (DCA)
      </Typography>
      
      <Typography paragraph>
        Dollar-cost averaging is an investment strategy where you invest a fixed amount of money at 
        regular intervals, regardless of the share price. This strategy is perfectly suited to 
        micro-investing and can help reduce the impact of market volatility on your investments.
      </Typography>
      
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          How Dollar-Cost Averaging Works
        </Typography>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body2" paragraph>
                <strong>1. Choose an investment amount</strong> — It could be $1, $5, $10, or $20 per week or month.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>2. Set a regular schedule</strong> — Daily, weekly, biweekly, or monthly.
              </Typography>
              <Typography variant="body2" paragraph>
                <strong>3. Invest consistently</strong> — No matter what the market is doing.
              </Typography>
              <Typography variant="body2">
                <strong>4. Let time work for you</strong> — As you accumulate more shares over time, your investment can grow through compound returns.
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper elevation={1} sx={{ p: 2, height: '100%' }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                Key Benefits of Dollar-Cost Averaging
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Reduces the impact of market volatility" 
                    secondary="You buy more shares when prices are low and fewer when prices are high" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Removes emotion from investing" 
                    secondary="No need to time the market or worry about buying at the wrong time" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Perfect for beginners" 
                    secondary="Simple strategy that requires minimal knowledge or effort" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="success" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Works well with micro-investing" 
                    secondary="Even small regular investments can add up significantly over time" 
                  />
                </ListItem>
              </List>
            </Paper>
          </Grid>
        </Grid>
      </Box>
      
      <Typography variant="subtitle1" gutterBottom fontWeight="bold">
        Real-World Example
      </Typography>
      
      <Paper elevation={3} sx={{ p: { xs: 1, sm: 2 }, mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant={isMobile ? "fullWidth" : "standard"}
          sx={{ mb: 2 }}
        >
          <Tab label="DCA in Action" />
          <Tab label="DCA vs. Lump Sum" />
        </Tabs>
        
        {activeTab === 0 && (
          <Box sx={{ overflowX: 'auto' }}>
            <Typography variant="subtitle2" gutterBottom>
              Investing $100 monthly in a stock with changing prices
            </Typography>
            
            <Box sx={{ minWidth: 600 }}>
              <Box sx={{ display: 'table', width: '100%' }}>
                <Box sx={{ display: 'table-header-group', bgcolor: theme.palette.grey[100] }}>
                  <Box sx={{ display: 'table-row' }}>
                    <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Month</Box>
                    <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Share Price</Box>
                    <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Amount Invested</Box>
                    <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Shares Purchased</Box>
                    <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Total Shares</Box>
                    <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Portfolio Value</Box>
                  </Box>
                </Box>
                
                <Box sx={{ display: 'table-row-group' }}>
                  {dcaData.map((row, index) => (
                    <Box 
                      key={index}
                      sx={{ 
                        display: 'table-row', 
                        bgcolor: index % 2 === 0 ? 'inherit' : theme.palette.grey[50]
                      }}
                    >
                      <Box sx={{ display: 'table-cell', p: 1 }}>{row.month}</Box>
                      <Box sx={{ display: 'table-cell', p: 1 }}>${row.price}</Box>
                      <Box sx={{ display: 'table-cell', p: 1 }}>${row.invested}</Box>
                      <Box sx={{ display: 'table-cell', p: 1 }}>{row.shares.toFixed(2)}</Box>
                      <Box sx={{ display: 'table-cell', p: 1 }}>{row.totalShares.toFixed(2)}</Box>
                      <Box sx={{ display: 'table-cell', p: 1 }}>${row.value.toFixed(2)}</Box>
                    </Box>
                  ))}
                </Box>
              </Box>
            </Box>
            
            <Box sx={{ mt: 2, p: 2, bgcolor: theme.palette.grey[50], borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom color="primary">
                Results after 6 months:
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2">Total Invested:</Typography>
                  <Typography variant="body1" fontWeight="bold">${totalInvested}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2">Final Value:</Typography>
                  <Typography variant="body1" fontWeight="bold">${finalValue.toFixed(2)}</Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2">Profit:</Typography>
                  <Typography variant="body1" fontWeight="bold" color={profit >= 0 ? 'success.main' : 'error.main'}>
                    ${profit.toFixed(2)}
                  </Typography>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Typography variant="body2">Return:</Typography>
                  <Typography variant="body1" fontWeight="bold" color={roi >= 0 ? 'success.main' : 'error.main'}>
                    {roi.toFixed(2)}%
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Box>
        )}
        
        {activeTab === 1 && (
          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Dollar-Cost Averaging vs. Lump Sum Investment
            </Typography>
            
            <Typography variant="body2" paragraph>
              Let's compare investing $600 all at once in January versus investing $100 each month for 6 months.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Paper elevation={2} sx={{ p: 2, bgcolor: theme.palette.primary.light, color: theme.palette.primary.contrastText }}>
                  <Typography variant="subtitle2" align="center" gutterBottom>
                    Dollar-Cost Averaging
                  </Typography>
                  <Box sx={{ textAlign: 'center', mb: 1 }}>
                    <Typography variant="body2">Invested $100/month for 6 months</Typography>
                    <Typography variant="h6">${totalInvested}</Typography>
                  </Box>
                  <Divider sx={{ my: 1, bgcolor: 'rgba(255,255,255,0.2)' }} />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Box>
                      <Typography variant="body2">Shares Accumulated:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {dcaData[dcaData.length - 1].totalShares.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2">Final Value:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        ${finalValue.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="body2">Profit:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        ${profit.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2">Return:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {roi.toFixed(2)}%
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Paper elevation={2} sx={{ p: 2, bgcolor: theme.palette.secondary.light, color: theme.palette.secondary.contrastText }}>
                  <Typography variant="subtitle2" align="center" gutterBottom>
                    Lump Sum Investment
                  </Typography>
                  <Box sx={{ textAlign: 'center', mb: 1 }}>
                    <Typography variant="body2">Invested $600 in January</Typography>
                    <Typography variant="h6">${totalInvested}</Typography>
                  </Box>
                  <Divider sx={{ my: 1, bgcolor: 'rgba(255,255,255,0.2)' }} />
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Box>
                      <Typography variant="body2">Shares Purchased:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {lumpSumShares.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2">Final Value:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        ${lumpSumValue.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Box>
                      <Typography variant="body2">Profit:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        ${lumpSumProfit.toFixed(2)}
                      </Typography>
                    </Box>
                    <Box>
                      <Typography variant="body2">Return:</Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {lumpSumRoi.toFixed(2)}%
                      </Typography>
                    </Box>
                  </Box>
                </Paper>
              </Grid>
            </Grid>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              <AlertTitle>Key Takeaway</AlertTitle>
              In this example, DCA performed better than a lump sum investment because the stock price was volatile. 
              However, results will vary depending on market conditions. DCA's main advantage is reducing the risk of investing 
              all your money at a market peak, not necessarily maximizing returns.
            </Alert>
          </Box>
        )}
      </Paper>
      
      <Alert severity="success">
        <AlertTitle>Perfect for Micro-Investing</AlertTitle>
        <Typography variant="body2">
          Dollar-cost averaging works perfectly with micro-investing because it encourages small, regular investments.
          Even $5 per week can add up significantly over time, and the strategy helps manage risk regardless of the amount invested.
        </Typography>
      </Alert>
    </Box>
  );
};

const GettingStarted: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { enqueueSnackbar } = useSnackbar();
  
  const [isSettingsDialogOpen, setIsSettingsDialogOpen] = useState(false);
  const [isFormDialogOpen, setIsFormDialogOpen] = useState(false);
  
  // Mock ETF data
  const recommendedEtfs = [
    { symbol: 'VTI', name: 'Vanguard Total Stock Market ETF', price: 247.12, expense: 0.03, type: 'Stocks (US)' },
    { symbol: 'VXUS', name: 'Vanguard Total International Stock ETF', price: 58.95, expense: 0.08, type: 'Stocks (International)' },
    { symbol: 'BND', name: 'Vanguard Total Bond Market ETF', price: 72.46, expense: 0.03, type: 'Bonds' },
    { symbol: 'VT', name: 'Vanguard Total World Stock ETF', price: 102.38, expense: 0.07, type: 'Stocks (Global)' },
  ];
  
  const handleCompleteEducation = async () => {
    try {
      // This would be a real API call in production
      // await api.post('/micro-invest/complete-education');
      enqueueSnackbar('Educational module marked as completed!', { variant: 'success' });
    } catch (error) {
      console.error('Error marking module as completed:', error);
      enqueueSnackbar('Failed to mark module as completed.', { variant: 'error' });
    }
  };
  
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Getting Started with Micro-Investing
      </Typography>
      
      <Typography paragraph>
        Now that you understand the basics of micro-investing, fractional shares, round-ups, and 
        dollar-cost averaging, it's time to put your knowledge into action! 
        Here's how to get started with micro-investing on our platform.
      </Typography>
      
      <Box sx={{ mb: 4 }}>
        <Stepper orientation={isMobile ? "vertical" : "horizontal"} sx={{ mb: 4 }}>
          <Step active>
            <StepLabel>Enable Micro-Investing</StepLabel>
          </Step>
          <Step active>
            <StepLabel>Choose Your Strategy</StepLabel>
          </Step>
          <Step active>
            <StepLabel>Set Investment Target</StepLabel>
          </Step>
          <Step active>
            <StepLabel>Start Investing</StepLabel>
          </Step>
        </Stepper>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                Step 1: Enable Micro-Investing
              </Typography>
              <Typography paragraph variant="body2">
                Visit your account settings and enable micro-investing features:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Enable fractional share trading" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Enable round-ups (optional)" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <CheckCircleOutline color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary="Link a bank account or card if using round-ups" />
                </ListItem>
              </List>
              <Button 
                variant="outlined" 
                color="primary" 
                size="small"
                onClick={() => setIsSettingsDialogOpen(true)}
                sx={{ mt: 1 }}
              >
                Settings Example
              </Button>
            </Box>
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                Step 2: Choose Your Strategy
              </Typography>
              <Typography paragraph variant="body2">
                Select the micro-investing strategy that works best for you:
              </Typography>
              <Grid container spacing={1}>
                <Grid item xs={6}>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 1.5, 
                      height: '100%',
                      bgcolor: theme.palette.primary.light,
                      color: theme.palette.primary.contrastText
                    }}
                  >
                    <Typography variant="subtitle2" gutterBottom>
                      Round-ups
                    </Typography>
                    <Typography variant="body2">
                      Automatically invest spare change from everyday purchases
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 1.5, 
                      height: '100%',
                      bgcolor: theme.palette.secondary.light,
                      color: theme.palette.secondary.contrastText
                    }}
                  >
                    <Typography variant="subtitle2" gutterBottom>
                      Regular Deposits
                    </Typography>
                    <Typography variant="body2">
                      Set up automatic weekly or monthly investments
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 1.5, 
                      height: '100%',
                      bgcolor: theme.palette.success.light,
                      color: theme.palette.success.contrastText
                    }}
                  >
                    <Typography variant="subtitle2" gutterBottom>
                      One-time Investments
                    </Typography>
                    <Typography variant="body2">
                      Make small investments whenever you have extra cash
                    </Typography>
                  </Paper>
                </Grid>
                <Grid item xs={6}>
                  <Paper 
                    elevation={1} 
                    sx={{ 
                      p: 1.5, 
                      height: '100%',
                      bgcolor: theme.palette.info.light,
                      color: theme.palette.info.contrastText
                    }}
                  >
                    <Typography variant="subtitle2" gutterBottom>
                      Hybrid Approach
                    </Typography>
                    <Typography variant="body2">
                      Combine multiple strategies for maximum benefit
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Box>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                Step 3: Set Investment Target
              </Typography>
              <Typography paragraph variant="body2">
                Choose where your micro-investments will go:
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Recommended ETFs for Micro-Investing
                </Typography>
                <Box sx={{ maxHeight: 200, overflow: 'auto', bgcolor: theme.palette.grey[50], borderRadius: 1, p: 1 }}>
                  <Box sx={{ minWidth: 400 }}>
                    <Box sx={{ display: 'table', width: '100%' }}>
                      <Box sx={{ display: 'table-header-group', bgcolor: theme.palette.grey[200] }}>
                        <Box sx={{ display: 'table-row' }}>
                          <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Symbol</Box>
                          <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Name</Box>
                          <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Type</Box>
                          <Box sx={{ display: 'table-cell', p: 1, fontWeight: 'bold' }}>Price</Box>
                        </Box>
                      </Box>
                      
                      <Box sx={{ display: 'table-row-group' }}>
                        {recommendedEtfs.map((etf, index) => (
                          <Box 
                            key={index}
                            sx={{ 
                              display: 'table-row', 
                              bgcolor: index % 2 === 0 ? 'inherit' : theme.palette.grey[100]
                            }}
                          >
                            <Box sx={{ display: 'table-cell', p: 1 }}>{etf.symbol}</Box>
                            <Box sx={{ display: 'table-cell', p: 1 }}>{etf.name}</Box>
                            <Box sx={{ display: 'table-cell', p: 1 }}>{etf.type}</Box>
                            <Box sx={{ display: 'table-cell', p: 1 }}>${etf.price}</Box>
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  </Box>
                </Box>
              </Box>
              <Typography variant="body2" gutterBottom>
                Investment target options:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <AttachMoney fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Specific ETF or stock" 
                    secondary="Choose a specific investment (like VTI or AAPL)" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <AccountBalance fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Default portfolio" 
                    secondary="Invest in your primary portfolio" 
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <TrendingUp fontSize="small" color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Recommended ETF" 
                    secondary="Based on your risk profile and goals" 
                  />
                </ListItem>
              </List>
            </Box>
            
            <Box sx={{ mt: 3 }}>
              <Typography variant="subtitle1" gutterBottom fontWeight="bold">
                Step 4: Start Investing
              </Typography>
              <Typography paragraph variant="body2">
                Once your settings are configured, your micro-investing journey begins! You can:
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemIcon>
                    <Done fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Monitor your micro-investments in your portfolio dashboard" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Done fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="View pending round-ups before they're invested" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Done fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Make manual micro-investments as small as $1" />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Done fontSize="small" color="success" />
                  </ListItemIcon>
                  <ListItemText primary="Track your progress over time with detailed statistics" />
                </ListItem>
              </List>
              <Button 
                variant="contained" 
                color="primary"
                size="small"
                onClick={() => setIsFormDialogOpen(true)}
                sx={{ mt: 1 }}
              >
                Investment Form Example
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
      
      <Divider sx={{ my: 2 }} />
      
      <Box sx={{ textAlign: 'center', mt: 3 }}>
        <Typography variant="subtitle1" gutterBottom fontWeight="bold">
          Ready to Start Your Micro-Investing Journey?
        </Typography>
        <Typography variant="body2" paragraph>
          Now that you've completed this module, you're ready to start building wealth with micro-investing!
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={handleCompleteEducation}
          startIcon={<School />}
        >
          Complete This Module
        </Button>
      </Box>
    </Box>
  );
};

const KnowledgeCheck: React.FC = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Test Your Knowledge
      </Typography>
      
      <Typography paragraph>
        Let's see how much you've learned about micro-investing! Answer the following questions 
        to test your understanding of the key concepts covered in this module.
      </Typography>
      
      <EducationalQuiz questions={QUIZ_DATA.questions} />
    </Box>
  );
};

// Main module component
export const MicroInvestingBasics: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<Record<number, boolean>>({});
  
  // Calculate steps
  const steps = MODULE_DATA.steps;
  const totalSteps = steps.length;
  const isLastStep = activeStep === totalSteps - 1;
  const isFirstStep = activeStep === 0;
  
  // Handle step changes
  const handleNext = () => {
    const newCompleted = { ...completed, [activeStep]: true };
    setCompleted(newCompleted);
    setActiveStep((prev) => prev + 1);
  };
  
  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
  };
  
  // Render current step content
  const getStepContent = (stepIndex: number) => {
    switch (steps[stepIndex].content) {
      case 'MicroInvestingIntro':
        return <MicroInvestingIntro />;
      case 'FractionalSharesExplained':
        return <FractionalSharesExplained />;
      case 'RoundUpInvesting':
        return <RoundUpInvesting />;
      case 'DollarCostAveraging':
        return <DollarCostAveraging />;
      case 'GettingStarted':
        return <GettingStarted />;
      case 'KnowledgeCheck':
        return <KnowledgeCheck />;
      default:
        return <div>Content not found</div>;
    }
  };

  return (
    <Card sx={{ mb: 4 }}>
      <CardContent>
        <Typography variant="h5" component="div" gutterBottom>
          {MODULE_DATA.title}
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          {MODULE_DATA.description}
        </Typography>
        
        <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 3 }}>
          {steps.map((step, index) => (
            <Step key={step.title} completed={completed[index]}>
              <StepLabel>{step.title}</StepLabel>
            </Step>
          ))}
        </Stepper>
        
        <Divider sx={{ mb: 3 }} />
        
        <Box sx={{ mb: 3 }}>
          {getStepContent(activeStep)}
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
          <Button
            variant="outlined"
            disabled={isFirstStep}
            onClick={handleBack}
            startIcon={<ArrowBack />}
          >
            Back
          </Button>
          
          <Button
            variant="contained"
            onClick={handleNext}
            endIcon={isLastStep ? <CheckCircleOutline /> : <ArrowForward />}
            color={isLastStep ? "success" : "primary"}
          >
            {isLastStep ? 'Complete Module' : 'Next'}
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MicroInvestingBasics;