import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Button,
  Divider,
  Card,
  CardContent,
  CardMedia,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Alert,
  Chip,
  Stack,
  useTheme,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  TrendingUp,
  BusinessCenter,
  AccessTime,
  SettingsApplications,
  Check,
  Info,
  Warning,
  MenuBook,
  ShowChart,
  AttachMoney,
  ArrowUpward,
  ArrowDownward,
  ExpandMore,
  Savings,
  Gavel,
  Timeline,
  Report
} from '@mui/icons-material';
import EducationalTooltip from '../../common/EducationalTooltip';

interface TradingBasicsProps {
  onComplete?: () => void;
  onProgress?: (progress: number) => void;
}

// Define trading concepts data
const tradingConcepts = [
  {
    title: 'Market Orders & Limit Orders',
    icon: <Gavel fontSize="large" color="primary" />,
    description: 'Learn about the two most common order types and how to use them effectively.',
    concepts: [
      {
        name: 'Market Order',
        description: 'A market order is an instruction to buy or sell a security immediately at the best available price.',
        pros: ['Executes immediately', 'Guaranteed execution (as long as there are buyers/sellers)', 'Simple to use'],
        cons: ['No control over execution price', 'Can result in slippage during volatile markets', 'May pay more than expected'],
        example: 'If Apple stock is trading around $150, placing a market order to buy will execute immediately at the current asking price, which might be $150.05.',
        when: 'Use when getting the trade executed is more important than the exact price.',
        visual: 'https://images.unsplash.com/photo-1535320903710-d993d3d77d29?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      },
      {
        name: 'Limit Order',
        description: 'A limit order is an instruction to buy or sell a security at a specific price or better.',
        pros: ['Control over execution price', 'Protects from unexpected price movements', 'Can "set it and forget it"'],
        cons: ['Not guaranteed to execute', 'May miss opportunity if price doesn\'t reach limit', 'May be partially filled'],
        example: 'If Apple stock is trading at $150, placing a limit buy order at $148 means your order will only execute if the price falls to $148 or lower.',
        when: 'Use when the price is more important than immediate execution.',
        visual: 'https://images.unsplash.com/photo-1633158829585-23ba8f7c8caf?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      }
    ]
  },
  {
    title: 'Understanding Stock Prices',
    icon: <ShowChart fontSize="large" color="primary" />,
    description: 'Learn how stock prices are determined and the factors that affect them.',
    concepts: [
      {
        name: 'Bid and Ask Prices',
        description: 'The bid price is the highest price a buyer is willing to pay, while the ask price is the lowest price a seller is willing to accept.',
        pros: ['Provides transparency', 'Shows market demand/supply at a glance', 'Helps determine fair pricing'],
        cons: ['Spread can be wide for less liquid stocks', 'May change rapidly during market volatility', 'Can be manipulated in thinly traded securities'],
        example: 'If a stock has a bid of $25.00 and an ask of $25.05, the spread is $0.05. As a buyer, you'll pay $25.05; as a seller, you'll receive $25.00.',
        when: 'Always be aware of the bid-ask spread, especially for less liquid stocks or during volatile markets.',
        visual: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      },
      {
        name: 'Price Movement Factors',
        description: 'Stock prices move based on supply and demand, which are influenced by company performance, economic conditions, and market sentiment.',
        pros: ['Understanding these factors helps predict potential movements', 'Allows for more informed investment decisions', 'Reduces emotional reactions to price changes'],
        cons: ['Multiple factors often work simultaneously', 'Short-term movements can be unpredictable', 'Requires ongoing learning and analysis'],
        example: 'A company reports earnings that exceed analyst expectations, causing more investors to want to buy the stock (increasing demand), which drives the price up.',
        when: 'Always consider these factors when evaluating whether a stock price seems fair or when trying to understand why a price is moving.',
        visual: 'https://images.unsplash.com/photo-1569025743873-ea3a9ade89f9?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      }
    ]
  },
  {
    title: 'Trading vs. Investing',
    icon: <Timeline fontSize="large" color="primary" />,
    description: 'Understand the key differences between short-term trading and long-term investing.',
    concepts: [
      {
        name: 'Trading Strategy',
        description: 'Trading involves buying and selling securities over short time periods, with the goal of generating returns from market price movements.',
        pros: ['Potential for quick returns', 'Can profit in both rising and falling markets', 'More active engagement'],
        cons: ['Higher risk', 'Requires significant time commitment', 'Higher transaction costs and taxes', 'More emotional stress'],
        example: 'A trader might buy a stock in the morning after positive news and sell it the same day after it rises 2%.',
        when: 'Trading is typically more suitable for experienced investors with time for research and monitoring, and higher risk tolerance.',
        visual: 'https://images.unsplash.com/photo-1642543348745-790326d9f570?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      },
      {
        name: 'Investing Strategy',
        description: 'Investing involves buying securities with the intention of holding them for a longer period (years or decades) to achieve long-term goals.',
        pros: ['Lower stress', 'Benefits from compound returns', 'Lower transaction costs and taxes', 'Less time-intensive'],
        cons: ['Slower growth', 'Longer time to recover from downturns', 'Less exciting'],
        example: 'An investor might buy shares of quality companies or index ETFs and hold them for many years, reinvesting dividends to compound growth.',
        when: 'Investing is generally more appropriate for most people, especially younger individuals with long time horizons.',
        visual: 'https://images.unsplash.com/photo-1579532536935-619928decd08?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      }
    ]
  },
  {
    title: 'Risk Management',
    icon: <Report fontSize="large" color="primary" />,
    description: 'Learn essential risk management techniques to protect your portfolio.',
    concepts: [
      {
        name: 'Diversification',
        description: 'Spreading your investments across different assets, sectors, and geographies to reduce the impact of any single investment performing poorly.',
        pros: ['Reduces portfolio volatility', 'Protects from single-company risks', 'Provides more consistent returns'],
        cons: ['May limit upside potential', 'Requires more research', 'Can be complex to maintain proper balance'],
        example: 'Instead of investing all your money in a single tech stock, you invest across multiple companies in different sectors like technology, healthcare, finance, and consumer goods.',
        when: 'Always diversify your investments, regardless of your age or investment goals.',
        visual: 'https://images.unsplash.com/photo-1559526324-593bc073d938?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      },
      {
        name: 'Position Sizing',
        description: 'Determining how much of your portfolio to allocate to each investment based on risk factors and your overall strategy.',
        pros: ['Prevents overexposure to any single investment', 'Allows for appropriate risk levels', 'Creates discipline in decision-making'],
        cons: ['Requires regular monitoring and adjustment', 'May miss out on large gains from concentrated positions', 'Requires mathematical analysis'],
        example: 'Using the 5% rule where no single stock position exceeds 5% of your total portfolio value, so a $10,000 portfolio would have maximum $500 in any single stock.',
        when: 'Apply position sizing to every investment you make to manage risk effectively.',
        visual: 'https://images.unsplash.com/photo-1553729459-efe14ef6055d?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      }
    ]
  },
  {
    title: 'Understanding Trading Costs',
    icon: <AttachMoney fontSize="large" color="primary" />,
    description: 'Learn about the various costs involved in trading and how they impact your returns.',
    concepts: [
      {
        name: 'Trading Commissions',
        description: 'Fees charged by brokers for executing trades, which can be a flat fee per trade or based on trade value.',
        pros: ['Many brokers now offer commission-free trading', 'Known cost that can be factored into decisions', 'Often negotiable for larger accounts'],
        cons: ['Can significantly impact returns for frequent traders', 'May influence trading behavior', 'Sometimes hidden in other costs'],
        example: 'While many brokers now offer zero-commission trades on stocks and ETFs, options trades might still incur a fee like $0.65 per contract.',
        when: 'Always understand the commission structure of your broker and factor it into your trading decisions.',
        visual: 'https://images.unsplash.com/photo-1518458028785-8fbcd101ebb9?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      },
      {
        name: 'Bid-Ask Spread Cost',
        description: 'The implicit cost paid due to the difference between the buying price (ask) and selling price (bid).',
        pros: ['More visible in modern trading platforms', 'Typically lower for high-volume securities', 'Can be minimized with limit orders'],
        cons: ['Often overlooked cost', 'Can be substantial for less liquid stocks', 'Widens during market volatility'],
        example: 'If you buy a stock at the ask price of $20.05 and immediately sell at the bid price of $20.00, you've lost $0.05 per share just from the spread.',
        when: 'Consider the spread cost particularly when trading less liquid securities or making frequent trades.',
        visual: 'https://images.unsplash.com/photo-1563986768494-4dee2763ff3f?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=300&q=80'
      }
    ]
  }
];

const TradingBasics: React.FC<TradingBasicsProps> = ({ onComplete, onProgress }) => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<{ [k: number]: boolean }>({});
  const [selectedTab, setSelectedTab] = useState(0);

  const totalSteps = () => tradingConcepts.length + 1; // +1 for intro and summary
  
  const completedSteps = () => Object.keys(completed).length;
  
  const isLastStep = () => activeStep === totalSteps() - 1;
  
  const handleNext = () => {
    const newActiveStep = activeStep + 1;
    setActiveStep(newActiveStep);
    setSelectedTab(0);
    
    // Update progress for parent component
    if (onProgress) {
      onProgress((newActiveStep / totalSteps()) * 100);
    }
    
    // Mark step as completed
    const newCompleted = { ...completed };
    newCompleted[activeStep] = true;
    setCompleted(newCompleted);
    
    // If we've reached the end, call onComplete
    if (isLastStep() && onComplete) {
      onComplete();
    }
  };
  
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
    setSelectedTab(0);
  };
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  // Render introduction step
  const renderIntroduction = () => (
    <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
      <Typography variant="h4" gutterBottom color="primary" sx={{ fontWeight: 'bold' }}>
        Trading Basics
      </Typography>
      
      <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
        This module introduces you to the fundamental concepts of trading, helping you understand
        how markets work and how to make informed trading decisions. Whether you're interested in
        active trading or long-term investing, these basics will provide a solid foundation.
      </Typography>
      
      <Alert severity="info" sx={{ my: 3 }}>
        <Typography variant="body1">
          Before making any real trades, it's important to understand the basics of how trading works,
          the different types of orders, and how to manage risk effectively.
        </Typography>
      </Alert>
      
      <Box sx={{ my: 4 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 'bold' }}>
          In this module, you'll learn about:
        </Typography>
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          {tradingConcepts.map((concept, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    {concept.icon}
                    <Typography variant="h6" sx={{ ml: 1, fontWeight: 'medium' }}>
                      {concept.title}
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {concept.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
      
      <Box sx={{ bgcolor: theme.palette.background.default, p: 3, borderRadius: 2, my: 4 }}>
        <Typography variant="h6" color="primary" gutterBottom>
          <MenuBook sx={{ mr: 1, verticalAlign: 'middle' }} />
          How to Use This Module
        </Typography>
        
        <List dense>
          <ListItem>
            <ListItemIcon><Check color="primary" /></ListItemIcon>
            <ListItemText 
              primary="Read through each section carefully" 
              secondary="Each concept builds on previous ones"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="primary" /></ListItemIcon>
            <ListItemText 
              primary="Pay attention to the examples" 
              secondary="They illustrate how concepts work in real situations"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="primary" /></ListItemIcon>
            <ListItemText 
              primary="Consider which strategies align with your goals" 
              secondary="Different approaches work for different investors"
            />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="primary" /></ListItemIcon>
            <ListItemText 
              primary="Complete the quiz after finishing" 
              secondary="Test your understanding of key concepts"
            />
          </ListItem>
        </List>
      </Box>
      
      <Button
        variant="contained"
        color="primary"
        onClick={handleNext}
        sx={{ mt: 2 }}
        startIcon={<TrendingUp />}
      >
        Begin Learning
      </Button>
    </Paper>
  );

  // Render trading concept step
  const renderTradingConcept = (index: number) => {
    const concept = tradingConcepts[index - 1];
    const selectedConcept = concept.concepts[selectedTab];
    
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          {concept.icon}
          <Typography variant="h4" color="primary" sx={{ ml: 2, fontWeight: 'bold' }}>
            {concept.title}
          </Typography>
        </Box>
        
        <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
          {concept.description}
        </Typography>
        
        <Tabs 
          value={selectedTab} 
          onChange={handleTabChange} 
          variant="fullWidth" 
          sx={{ mb: 3, borderBottom: 1, borderColor: 'divider' }}
        >
          {concept.concepts.map((subconcept, idx) => (
            <Tab 
              key={idx} 
              label={subconcept.name} 
              id={`concept-tab-${idx}`}
              aria-controls={`concept-tabpanel-${idx}`}
            />
          ))}
        </Tabs>
        
        <Box role="tabpanel" id={`concept-tabpanel-${selectedTab}`} aria-labelledby={`concept-tab-${selectedTab}`}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={7}>
              <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium', color: 'primary.main' }}>
                {selectedConcept.name}
              </Typography>
              
              <Typography variant="body1" paragraph>
                {selectedConcept.description}
              </Typography>
              
              <Box sx={{ my: 3 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  Example:
                </Typography>
                <Alert severity="info" sx={{ my: 1 }}>
                  {selectedConcept.example}
                </Alert>
              </Box>
              
              <Typography variant="subtitle1" sx={{ fontWeight: 'bold', mt: 3 }}>
                When to use:
              </Typography>
              <Alert severity="success" sx={{ my: 1 }}>
                {selectedConcept.when}
              </Alert>
            </Grid>
            
            <Grid item xs={12} md={5}>
              <CardMedia
                component="img"
                height="200"
                image={selectedConcept.visual}
                alt={selectedConcept.name}
                sx={{ borderRadius: 1, mb: 3 }}
              />
              
              <Box sx={{ bgcolor: theme.palette.background.default, p: 2, borderRadius: 2 }}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', color: 'success.main' }}>
                  <ArrowUpward fontSize="small" sx={{ mr: 1 }} /> Advantages
                </Typography>
                <List dense>
                  {selectedConcept.pros.map((pro, idx) => (
                    <ListItem key={idx} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <Check color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={pro} />
                    </ListItem>
                  ))}
                </List>
                
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', mt: 2, color: 'error.main' }}>
                  <ArrowDownward fontSize="small" sx={{ mr: 1 }} /> Limitations
                </Typography>
                <List dense>
                  {selectedConcept.cons.map((con, idx) => (
                    <ListItem key={idx} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <Warning color="error" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={con} />
                    </ListItem>
                  ))}
                </List>
              </Box>
            </Grid>
          </Grid>
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button onClick={handleBack} startIcon={<Info />}>
            Back
          </Button>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleNext}
            endIcon={<TrendingUp />}
          >
            {index === tradingConcepts.length ? 'Continue to Summary' : 'Next Concept'}
          </Button>
        </Box>
      </Paper>
    );
  };

  // Render summary step
  const renderSummary = () => (
    <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
      <Typography variant="h4" gutterBottom color="primary" sx={{ fontWeight: 'bold' }}>
        Trading Basics: Summary
      </Typography>
      
      <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
        You've now learned the fundamental concepts of trading. Let's review the key points from each section.
      </Typography>
      
      <Box sx={{ my: 3 }}>
        {tradingConcepts.map((concept, index) => (
          <Accordion key={index} defaultExpanded={index === 0}>
            <AccordionSummary
              expandIcon={<ExpandMore />}
              aria-controls={`panel${index}-content`}
              id={`panel${index}-header`}
            >
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                {concept.icon}
                <Typography variant="h6" sx={{ ml: 2, fontWeight: 'medium' }}>
                  {concept.title}
                </Typography>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {concept.concepts.map((subconcept, idx) => (
                  <Grid item xs={12} md={6} key={idx}>
                    <Card variant="outlined" sx={{ height: '100%' }}>
                      <CardContent>
                        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold', color: 'primary.main' }}>
                          {subconcept.name}
                        </Typography>
                        <Typography variant="body2" paragraph>
                          {subconcept.description}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                          <Chip 
                            size="small" 
                            label="Example" 
                            color="primary" 
                            variant="outlined" 
                            onClick={() => {}}
                            icon={<Info fontSize="small" />}
                            sx={{ cursor: 'default' }}
                          />
                          <EducationalTooltip title={subconcept.example} placement="top">
                            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', cursor: 'help' }}>
                              (Hover to see example)
                            </Typography>
                          </EducationalTooltip>
                        </Box>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>
      
      <Alert severity="success" sx={{ my: 4 }}>
        <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
          Key Takeaways:
        </Typography>
        <List dense>
          <ListItem>
            <ListItemIcon><Check color="success" /></ListItemIcon>
            <ListItemText primary="Understand the difference between market orders (immediate execution) and limit orders (price control)" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="success" /></ListItemIcon>
            <ListItemText primary="Stock prices are determined by supply and demand, affected by multiple factors" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="success" /></ListItemIcon>
            <ListItemText primary="Long-term investing typically has lower risk than short-term trading" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="success" /></ListItemIcon>
            <ListItemText primary="Diversification and position sizing are essential risk management techniques" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Check color="success" /></ListItemIcon>
            <ListItemText primary="Trading costs including commissions and spreads can significantly impact returns" />
          </ListItem>
        </List>
      </Alert>
      
      <Box sx={{ bgcolor: theme.palette.background.default, p: 3, borderRadius: 2, mb: 4 }}>
        <Typography variant="h6" color="primary" gutterBottom>
          Next Steps
        </Typography>
        <Typography variant="body1" paragraph>
          Now that you understand the basics of trading, you can:
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <BusinessCenter color="primary" sx={{ mr: 1 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    Practice Trading
                  </Typography>
                </Box>
                <Typography variant="body2">
                  Try our paper trading simulator to practice making trades without risking real money.
                </Typography>
                <Button 
                  variant="outlined" 
                  size="small" 
                  sx={{ mt: 2 }}
                  onClick={() => window.location.href = '/trading'}
                >
                  Open Paper Trading
                </Button>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Savings color="primary" sx={{ mr: 1 }} />
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    Build a Portfolio
                  </Typography>
                </Box>
                <Typography variant="body2">
                  Use our portfolio builder to create a diversified investment portfolio aligned with your goals.
                </Typography>
                <Button 
                  variant="outlined" 
                  size="small" 
                  sx={{ mt: 2 }}
                  onClick={() => window.location.href = '/portfolio'}
                >
                  Open Portfolio Builder
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <Button onClick={handleBack}>
          Back
        </Button>
        <EducationalTooltip 
          title="Completing this module will unlock the Trading Basics Quiz!"
          placement="top"
        >
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleNext}
          >
            Complete Module
          </Button>
        </EducationalTooltip>
      </Box>
    </Paper>
  );

  return (
    <Box>
      {/* Progress stepper */}
      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
        <Step key="intro">
          <StepLabel>Introduction</StepLabel>
        </Step>
        {tradingConcepts.map((concept, index) => (
          <Step key={concept.title}>
            <StepLabel>{concept.title}</StepLabel>
          </Step>
        ))}
        <Step key="summary">
          <StepLabel>Summary</StepLabel>
        </Step>
      </Stepper>
      
      {/* Content area */}
      <Box>
        {activeStep === 0 ? (
          renderIntroduction()
        ) : activeStep === totalSteps() - 1 ? (
          renderSummary()
        ) : (
          renderTradingConcept(activeStep)
        )}
      </Box>
    </Box>
  );
};

export default TradingBasics;