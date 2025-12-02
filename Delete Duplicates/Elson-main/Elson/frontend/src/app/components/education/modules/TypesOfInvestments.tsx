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
  Chip,
  Tooltip,
  useTheme,
  Alert
} from '@mui/material';
import {
  TrendingUp,
  Business,
  Assessment,
  AccountBalance,
  Home,
  AttachMoney,
  ShowChart,
  EmojiObjects,
  Check,
  HelpOutline
} from '@mui/icons-material';
import EducationalTooltip from '../../common/EducationalTooltip';

interface TypesOfInvestmentsProps {
  onComplete?: () => void;
  onProgress?: (progress: number) => void;
}

// Define investment types with descriptions
const investmentTypes = [
  {
    title: 'Stocks',
    icon: <Business fontSize="large" color="primary" />,
    description: 'Ownership shares in a company. When you buy a stock, you own a small piece of that company.',
    pros: ['Potential for high returns', 'Ownership in companies', 'Liquidity (easy to buy/sell)'],
    cons: ['Higher volatility', 'Requires research', 'No guaranteed returns'],
    ageAppropriate: 'Teens and up',
    riskLevel: 'Moderate to High',
    example: 'Buying shares of Apple (AAPL) means you own a tiny piece of Apple Inc.',
    image: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=280&q=80'
  },
  {
    title: 'Bonds',
    icon: <AccountBalance fontSize="large" color="primary" />,
    description: 'Loans to a company or government that pays you interest over time and returns your principal at maturity.',
    pros: ['More stable than stocks', 'Regular income payments', 'Lower risk than stocks'],
    cons: ['Lower returns than stocks', 'Interest rate risk', 'Some bonds have low liquidity'],
    ageAppropriate: 'All ages',
    riskLevel: 'Low to Moderate',
    example: 'A 10-year Treasury bond is lending money to the U.S. government for 10 years.',
    image: 'https://images.unsplash.com/photo-1607026151739-e7ce1ee93929?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=280&q=80'
  },
  {
    title: 'ETFs (Exchange-Traded Funds)',
    icon: <Assessment fontSize="large" color="primary" />,
    description: 'Baskets of many investments (like stocks or bonds) that trade like a single stock.',
    pros: ['Instant diversification', 'Low cost', 'Trade throughout the day'],
    cons: ['Some have trading fees', 'Some may track indexes poorly', 'Potential tax complications'],
    ageAppropriate: 'All ages',
    riskLevel: 'Varies by ETF type',
    example: 'VOO tracks the S&P 500 index, giving you exposure to 500 large U.S. companies with one purchase.',
    image: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=280&q=80'
  },
  {
    title: 'Mutual Funds',
    icon: <ShowChart fontSize="large" color="primary" />,
    description: 'Professionally managed pools of money from many investors used to buy a collection of stocks, bonds, or other securities.',
    pros: ['Professional management', 'Diversification', 'Many investment options'],
    cons: ['Higher fees than ETFs', 'Trade only once per day', 'May have minimum investments'],
    ageAppropriate: 'All ages',
    riskLevel: 'Varies by fund type',
    example: 'Vanguard Total Stock Market Index Fund invests in thousands of U.S. stocks.',
    image: 'https://images.unsplash.com/photo-1579532537598-459ecdaf39cc?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=280&q=80'
  },
  {
    title: 'Real Estate',
    icon: <Home fontSize="large" color="primary" />,
    description: 'Investments in physical property or through real estate investment trusts (REITs).',
    pros: ['Tangible asset', 'Potential income and appreciation', 'Hedge against inflation'],
    cons: ['Less liquid', 'Maintenance costs', 'Requires larger initial investment'],
    ageAppropriate: 'Adults (REITs for teens)',
    riskLevel: 'Moderate to High',
    example: 'Buying rental property or investing in Vanguard Real Estate ETF (VNQ).',
    image: 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=280&q=80'
  },
  {
    title: 'Certificates of Deposit (CDs)',
    icon: <AttachMoney fontSize="large" color="primary" />,
    description: 'Time deposits at banks that pay fixed interest rates for specific time periods.',
    pros: ['Safe and FDIC insured', 'Fixed, guaranteed returns', 'No investment knowledge needed'],
    cons: ['Low returns', 'Penalties for early withdrawal', 'Interest may not beat inflation'],
    ageAppropriate: 'All ages',
    riskLevel: 'Very Low',
    example: 'A 12-month CD at your local bank paying 3% interest annually.',
    image: 'https://images.unsplash.com/photo-1565514020179-026b62cabfe3?ixlib=rb-1.2.1&auto=format&fit=crop&w=500&h=280&q=80'
  }
];

const TypesOfInvestments: React.FC<TypesOfInvestmentsProps> = ({ onComplete, onProgress }) => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<{ [k: number]: boolean }>({});
  const [showComparisonTable, setShowComparisonTable] = useState(false);

  const totalSteps = () => investmentTypes.length + 1; // +1 for intro and summary
  
  const completedSteps = () => Object.keys(completed).length;
  
  const isLastStep = () => activeStep === totalSteps() - 1;
  
  const handleNext = () => {
    const newActiveStep = activeStep + 1;
    setActiveStep(newActiveStep);
    
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
  };
  
  const handleShowComparison = () => {
    setShowComparisonTable(!showComparisonTable);
  };

  // Render introduction step
  const renderIntroduction = () => (
    <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
      <Typography variant="h4" gutterBottom color="primary" sx={{ fontWeight: 'bold' }}>
        Types of Investments
      </Typography>
      
      <Typography variant="body1" paragraph>
        This module introduces you to the most common types of investments available to investors
        of all ages. You'll learn about the key features, benefits, and risks of each investment type.
      </Typography>
      
      <Alert severity="info" sx={{ my: 2 }}>
        <Typography variant="body1">
          Learning about different investment types is an important step in building a diversified portfolio.
          Each type has unique characteristics that make it suitable for different goals and risk tolerances.
        </Typography>
      </Alert>
      
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, my: 3 }}>
        {investmentTypes.map((type) => (
          <Chip 
            key={type.title}
            label={type.title} 
            color="primary" 
            variant="outlined" 
            icon={type.icon} 
          />
        ))}
      </Box>
      
      <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
        In this module, you'll learn:
      </Typography>
      
      <List>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText primary="The basic characteristics of each investment type" />
        </ListItem>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText primary="The pros and cons of each investment option" />
        </ListItem>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText primary="Which investments are appropriate for different age groups" />
        </ListItem>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText primary="How to think about building a portfolio with different investment types" />
        </ListItem>
      </List>
      
      <Button
        variant="contained"
        color="primary"
        onClick={handleNext}
        sx={{ mt: 2 }}
      >
        Begin Learning
      </Button>
    </Paper>
  );

  // Render investment type step
  const renderInvestmentType = (index: number) => {
    const investment = investmentTypes[index - 1];
    
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              {investment.icon}
              <Typography variant="h4" color="primary" sx={{ ml: 2, fontWeight: 'bold' }}>
                {investment.title}
              </Typography>
            </Box>
            
            <Typography variant="body1" paragraph sx={{ fontSize: '1.1rem' }}>
              {investment.description}
            </Typography>
            
            <Box sx={{ my: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Typography variant="subtitle1" sx={{ mr: 1, fontWeight: 'bold' }}>
                  Risk Level:
                </Typography>
                <Chip 
                  label={investment.riskLevel} 
                  color={
                    investment.riskLevel.includes('Low') ? 'success' : 
                    investment.riskLevel.includes('Moderate') ? 'warning' : 'error'
                  }
                  size="small"
                />
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Typography variant="subtitle1" sx={{ mr: 1, fontWeight: 'bold' }}>
                  Age Appropriate:
                </Typography>
                <Chip 
                  label={investment.ageAppropriate} 
                  color="primary"
                  size="small"
                />
              </Box>
            </Box>
            
            <Typography variant="subtitle1" sx={{ mt: 2, fontWeight: 'bold' }}>Example:</Typography>
            <Alert severity="info" sx={{ mt: 1, mb: 3 }}>
              {investment.example}
            </Alert>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <CardMedia
              component="img"
              height="200"
              image={investment.image}
              alt={investment.title}
              sx={{ borderRadius: 1, mb: 2 }}
            />
            
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: 'success.main', display: 'flex', alignItems: 'center' }}>
                  <TrendingUp sx={{ mr: 1 }} /> Pros
                </Typography>
                <List dense>
                  {investment.pros.map((pro, idx) => (
                    <ListItem key={idx} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <Check color="success" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={pro} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold', color: 'error.main', display: 'flex', alignItems: 'center' }}>
                  <ShowChart sx={{ mr: 1 }} /> Cons
                </Typography>
                <List dense>
                  {investment.cons.map((con, idx) => (
                    <ListItem key={idx} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <HelpOutline color="error" fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={con} />
                    </ListItem>
                  ))}
                </List>
              </Grid>
            </Grid>
          </Grid>
        </Grid>
        
        <Divider sx={{ my: 3 }} />
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button onClick={handleBack}>
            Back
          </Button>
          <Button variant="contained" color="primary" onClick={handleNext}>
            {index === investmentTypes.length ? 'Continue to Summary' : 'Next Investment Type'}
          </Button>
        </Box>
      </Paper>
    );
  };

  // Render summary step
  const renderSummary = () => (
    <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
      <Typography variant="h4" gutterBottom color="primary" sx={{ fontWeight: 'bold' }}>
        Summary: Building a Balanced Portfolio
      </Typography>
      
      <Typography variant="body1" paragraph>
        Now that you've learned about different investment types, let's talk about how they work together
        in a well-balanced portfolio.
      </Typography>
      
      <Alert severity="success" sx={{ my: 3 }}>
        <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
          Key Takeaway: Diversification across different investment types can help manage risk while pursuing growth.
        </Typography>
      </Alert>
      
      <Button
        variant="outlined"
        color="primary"
        onClick={handleShowComparison}
        sx={{ my: 2 }}
      >
        {showComparisonTable ? 'Hide Comparison Table' : 'Show Comparison Table'}
      </Button>
      
      {showComparisonTable && (
        <Box sx={{ overflowX: 'auto', my: 3 }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', borderSpacing: 0 }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f5f5f5', textAlign: 'left' }}>Investment Type</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f5f5f5', textAlign: 'left' }}>Risk Level</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f5f5f5', textAlign: 'left' }}>Potential Return</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f5f5f5', textAlign: 'left' }}>Time Horizon</th>
                <th style={{ border: '1px solid #ddd', padding: '8px', backgroundColor: '#f5f5f5', textAlign: 'left' }}>Best For</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Stocks</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Higher</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Higher</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>5+ years</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Growth</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Bonds</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Lower</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Lower</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>2-10 years</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Income & Stability</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>ETFs</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Varies</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Varies</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Varies</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Diversification</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Mutual Funds</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Varies</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Varies</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Varies</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Managed Diversification</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Real Estate</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Moderate-High</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Moderate-High</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>5+ years</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Growth & Income</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>CDs</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Very Low</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Very Low</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>0.5-5 years</td>
                <td style={{ border: '1px solid #ddd', padding: '8px' }}>Capital Preservation</td>
              </tr>
            </tbody>
          </table>
        </Box>
      )}
      
      <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
        Creating Your First Investment Portfolio
      </Typography>
      
      <Typography variant="body1" paragraph>
        As a young investor, consider starting with a simple portfolio that includes:
      </Typography>
      
      <List>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText 
            primary="A broad market ETF (like VOO or VTI)" 
            secondary="This gives you instant diversification across many stocks" 
          />
        </ListItem>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText 
            primary="A bond ETF (like BND or AGG)" 
            secondary="This adds stability to your portfolio" 
          />
        </ListItem>
        <ListItem>
          <ListItemIcon><Check color="primary" /></ListItemIcon>
          <ListItemText 
            primary="A small amount in individual stocks that interest you" 
            secondary="This helps you learn about company analysis and stock movements" 
          />
        </ListItem>
      </List>
      
      <Box sx={{ bgcolor: theme.palette.background.default, p: 3, borderRadius: 2, mt: 3 }}>
        <Typography variant="h6" gutterBottom color="primary">
          Next Steps
        </Typography>
        <Typography variant="body1">
          Use our Portfolio Builder tool to create your own portfolio with these different investment types.
          The Portfolio Builder will help you understand how to balance risk and potential returns.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => window.location.href = '/portfolio'}
          sx={{ mt: 2 }}
        >
          Try Portfolio Builder
        </Button>
      </Box>
      
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
        <Button onClick={handleBack}>
          Back
        </Button>
        <EducationalTooltip 
          title="Completing this module will unlock the Types of Investments Quiz!"
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
        {investmentTypes.map((type, index) => (
          <Step key={type.title}>
            <StepLabel>{type.title}</StepLabel>
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
          renderInvestmentType(activeStep)
        )}
      </Box>
    </Box>
  );
};

export default TypesOfInvestments;