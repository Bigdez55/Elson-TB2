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
  Paper, 
  Grid, 
  Divider, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText,
  useTheme,
  IconButton,
  LinearProgress
} from '@mui/material';
import {
  TrendingUp,
  School,
  CheckCircle,
  PlayArrow,
  NavigateNext,
  NavigateBefore,
  InfoOutlined,
  BarChart,
  AccountBalance,
  Business,
  People,
  FactCheck
} from '@mui/icons-material';
import EducationalTooltip from '../../common/EducationalTooltip';
import { getTerm } from '../../../../utils/glossaryTerms';

// Define the module sections
const sections = [
  {
    title: "What is the Stock Market?",
    icon: <AccountBalance />,
    content: (
      <>
        <Typography variant="body1" paragraph>
          The stock market is a collection of markets where investors buy and sell shares of publicly-traded companies. These transactions take place through exchanges, such as the New York Stock Exchange (NYSE) or the Nasdaq, or over-the-counter (OTC) markets.
        </Typography>
        <Typography variant="body1" paragraph>
          Think of the stock market as a marketplace where ownership in companies is bought and sold. When you buy stock, you're actually purchasing a small piece of that company—making you a part owner or "shareholder."
        </Typography>
        <Box sx={{ my: 3, p: 2, bgcolor: 'primary.light', borderRadius: 2, color: 'white' }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Key Fact
          </Typography>
          <Typography variant="body2">
            The New York Stock Exchange was founded in 1792 and is the world's largest stock exchange by market capitalization of its listed companies.
          </Typography>
        </Box>
        <Grid container spacing={3} sx={{ mt: 2 }}>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center' }}>
                  <Business sx={{ mr: 1 }} />
                  Primary Market
                </Typography>
                <Typography variant="body2">
                  Where companies issue new securities to raise funds, like during an Initial Public Offering (IPO).
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Card variant="outlined">
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary" sx={{ display: 'flex', alignItems: 'center' }}>
                  <People sx={{ mr: 1 }} />
                  Secondary Market
                </Typography>
                <Typography variant="body2">
                  Where investors trade previously issued securities without the involvement of the issuing companies.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </>
    )
  },
  {
    title: "Why Do Companies Go Public?",
    icon: <Business />,
    content: (
      <>
        <Typography variant="body1" paragraph>
          Companies "go public" through an Initial Public Offering (IPO) to raise capital for expansion, pay off debt, fund research and development, or allow early investors to cash out their investments.
        </Typography>
        <Typography variant="body1" paragraph>
          When a company goes public, it sells shares to investors in exchange for money that the company can use. This allows companies to raise funds without taking on debt.
        </Typography>
        <Box sx={{ my: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Main Reasons Companies Go Public:
          </Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Raise Capital" 
                secondary="Access to large amounts of money for growth and expansion" 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Liquidity for Shareholders" 
                secondary="Early investors and founders can sell shares more easily" 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Enhanced Company Reputation" 
                secondary="Public companies often gain more visibility and credibility" 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="Currency for Acquisitions" 
                secondary="Companies can use stock to acquire other businesses" 
              />
            </ListItem>
          </List>
        </Box>
        <Box sx={{ mt: 3, p: 2, bgcolor: 'info.light', borderRadius: 2, color: 'white' }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <InfoOutlined sx={{ mr: 1 }} />
            Did You Know?
          </Typography>
          <Typography variant="body2">
            Facebook (now Meta) raised over $16 billion in its IPO in 2012, one of the largest technology IPOs in history.
          </Typography>
        </Box>
      </>
    )
  },
  {
    title: "How Stock Prices Work",
    icon: <TrendingUp />,
    content: (
      <>
        <Typography variant="body1" paragraph>
          Stock prices are determined by supply and demand in the market. When more people want to buy a stock (demand) than sell it (supply), the price goes up. When more people want to sell than buy, the price goes down.
        </Typography>
        <Typography variant="body1" paragraph>
          Many factors influence a stock's price, including company performance, economic conditions, industry trends, market sentiment, and global events.
        </Typography>
        <Box sx={{ my: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Factors That Affect Stock Prices:
          </Typography>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} sm={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Company Factors
                  </Typography>
                  <List dense disablePadding>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Earnings Reports" 
                        secondary="Quarterly financial performance" 
                      />
                    </ListItem>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Product Launches" 
                        secondary="New products or services" 
                      />
                    </ListItem>
                    <ListItem disablePadding>
                      <ListItemText 
                        primary="Management Changes" 
                        secondary="New CEO or executives" 
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Card variant="outlined" sx={{ height: '100%' }}>
                <CardContent>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    External Factors
                  </Typography>
                  <List dense disablePadding>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Economic Indicators" 
                        secondary="Interest rates, inflation, GDP" 
                      />
                    </ListItem>
                    <ListItem disablePadding sx={{ pb: 1 }}>
                      <ListItemText 
                        primary="Industry Trends" 
                        secondary="Changes affecting entire sectors" 
                      />
                    </ListItem>
                    <ListItem disablePadding>
                      <ListItemText 
                        primary="Global Events" 
                        secondary="Political events, natural disasters" 
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
        <Box sx={{ mt: 3, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Example: How News Affects Stock Prices
          </Typography>
          <Paper variant="outlined" sx={{ p: 2 }}>
            <Typography variant="body2" paragraph>
              <strong>Positive News:</strong> A technology company announces better-than-expected earnings and a new product line. Investors get excited about future growth potential and buy more shares, driving the price up.
            </Typography>
            <Typography variant="body2">
              <strong>Negative News:</strong> The same company announces delays in product development and lower sales forecasts. Investors become concerned about future performance and sell shares, causing the price to drop.
            </Typography>
          </Paper>
        </Box>
      </>
    )
  },
  {
    title: "Understanding Bull & Bear Markets",
    icon: <BarChart />,
    content: (
      <>
        <Typography variant="body1" paragraph>
          The terms "bull market" and "bear market" describe the general trend of stock prices over time.
        </Typography>
        <Grid container spacing={3} sx={{ my: 2 }}>
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
              <Box sx={{ position: 'absolute', top: 0, right: 0, width: '100%', height: '4px', bgcolor: 'success.main' }} />
              <CardContent>
                <Typography variant="h6" color="success.main" gutterBottom>
                  Bull Market
                </Typography>
                <Typography variant="body2" paragraph>
                  A bull market is when stock prices are rising or expected to rise. It's typically associated with:
                </Typography>
                <List dense>
                  <ListItem disablePadding sx={{ pb: 1 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText primary="Increasing stock prices" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 1 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText primary="Economic growth" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 1 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText primary="Investor optimism" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText primary="Low unemployment" />
                  </ListItem>
                </List>
                <Box sx={{ mt: 2, p: 1, bgcolor: 'success.light', borderRadius: 1, color: 'white' }}>
                  <Typography variant="body2">
                    The longest bull market in history lasted 11 years, from 2009 to 2020.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card variant="outlined" sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
              <Box sx={{ position: 'absolute', top: 0, right: 0, width: '100%', height: '4px', bgcolor: 'error.main' }} />
              <CardContent>
                <Typography variant="h6" color="error.main" gutterBottom>
                  Bear Market
                </Typography>
                <Typography variant="body2" paragraph>
                  A bear market is when stock prices are falling or expected to fall. It's typically associated with:
                </Typography>
                <List dense>
                  <ListItem disablePadding sx={{ pb: 1 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Declining stock prices" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 1 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Economic recession" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 1 }}>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Investor pessimism" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemIcon sx={{ minWidth: 30 }}>
                      <CheckCircle fontSize="small" color="error" />
                    </ListItemIcon>
                    <ListItemText primary="Rising unemployment" />
                  </ListItem>
                </List>
                <Box sx={{ mt: 2, p: 1, bgcolor: 'error.light', borderRadius: 1, color: 'white' }}>
                  <Typography variant="body2">
                    Bear markets typically last 9-10 months on average but can be longer.
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        <Typography variant="body1" paragraph>
          It's important to remember that both bull and bear markets are normal parts of market cycles. As an investor, understanding which type of market you're in can help inform your investment strategy.
        </Typography>
        <Box sx={{ p: 2, bgcolor: 'background.paper', borderRadius: 2, border: '1px dashed', borderColor: 'divider' }}>
          <Typography variant="subtitle1" gutterBottom>
            Investment Tip
          </Typography>
          <Typography variant="body2">
            Markets can be unpredictable in the short term, but historically, the stock market has trended upward over long periods. This is why many financial advisors recommend a long-term investment strategy, especially for younger investors.
          </Typography>
        </Box>
      </>
    )
  },
  {
    title: "Key Stock Market Participants",
    icon: <People />,
    content: (
      <>
        <Typography variant="body1" paragraph>
          The stock market includes various participants who play different roles in the buying and selling of securities.
        </Typography>
        <Grid container spacing={2} sx={{ my: 2 }}>
          <Grid item xs={12} sm={6} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary">
                  Individual Investors
                </Typography>
                <Typography variant="body2" paragraph>
                  Regular people who buy and sell stocks for their personal portfolios. They typically invest for:
                </Typography>
                <List dense disablePadding>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Retirement savings" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="College funds" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemText primary="Personal wealth growth" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary">
                  Institutional Investors
                </Typography>
                <Typography variant="body2" paragraph>
                  Organizations that invest on behalf of others:
                </Typography>
                <List dense disablePadding>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Pension funds" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Mutual funds" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemText primary="Insurance companies" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary">
                  Market Makers
                </Typography>
                <Typography variant="body2" paragraph>
                  Firms that facilitate trading by:
                </Typography>
                <List dense disablePadding>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Always being ready to buy or sell" />
                  </ListItem>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Providing market liquidity" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemText primary="Maintaining orderly markets" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary">
                  Brokers
                </Typography>
                <Typography variant="body2" paragraph>
                  Intermediaries who execute trades for clients:
                </Typography>
                <List dense disablePadding>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Full-service brokers (advice + execution)" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemText primary="Discount brokers (mainly execution)" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary">
                  Regulators
                </Typography>
                <Typography variant="body2" paragraph>
                  Organizations that oversee markets:
                </Typography>
                <List dense disablePadding>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="SEC (Securities and Exchange Commission)" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemText primary="FINRA (Financial Industry Regulatory Authority)" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <Card variant="outlined" sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom color="primary">
                  Companies
                </Typography>
                <Typography variant="body2" paragraph>
                  Businesses that issue stock to:
                </Typography>
                <List dense disablePadding>
                  <ListItem disablePadding sx={{ pb: 0.5 }}>
                    <ListItemText primary="Raise capital" />
                  </ListItem>
                  <ListItem disablePadding>
                    <ListItemText primary="Fund operations and expansion" />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        <Box sx={{ mt: 2, p: 2, bgcolor: 'background.paper', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
          <Typography variant="subtitle1" gutterBottom>
            Understanding the Role of Brokers
          </Typography>
          <Typography variant="body2" paragraph>
            When you decide to buy or sell stock, you don't directly interact with the stock exchange. Instead, you place your order through a broker who executes the transaction on your behalf.
          </Typography>
          <Typography variant="body2">
            In the past, this meant calling a broker on the phone, but today most investors use online brokerages that charge low fees for each transaction. Some modern brokerages even offer commission-free trading.
          </Typography>
        </Box>
      </>
    )
  },
  {
    title: "Wrap-Up and Knowledge Check",
    icon: <FactCheck />,
    content: (
      <>
        <Typography variant="body1" paragraph>
          Congratulations on completing this introduction to the stock market! Let's review the key points we've covered:
        </Typography>
        <Box sx={{ my: 3 }}>
          <List>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="The stock market is where shares of publicly-traded companies are bought and sold"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Companies go public through IPOs to raise capital and provide liquidity to early investors"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Stock prices are determined by supply and demand and affected by various factors"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="Bull markets indicate rising prices and optimism, while bear markets indicate falling prices and pessimism"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <CheckCircle color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary="The stock market includes various participants like individual investors, institutions, brokers, and regulators"
              />
            </ListItem>
          </List>
        </Box>
        <Box sx={{ mt: 3, p: 2, bgcolor: 'primary.light', borderRadius: 2, color: 'white' }}>
          <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
            Ready to test your knowledge?
          </Typography>
          <Typography variant="body2" paragraph>
            Try the quiz below to see how much you've learned about the stock market. You'll need to answer 4 out of 5 questions correctly to mark this module as complete.
          </Typography>
          <Button variant="contained" color="secondary" onClick={() => window.location.href="/learning?quiz=stock-market-intro"}>
            Take the Quiz
          </Button>
        </Box>
        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle1" gutterBottom>
            Next Steps in Your Learning Journey
          </Typography>
          <Typography variant="body2" paragraph>
            Now that you understand the basics of the stock market, you might want to explore:
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <Button 
                fullWidth 
                variant="outlined"
                startIcon={<School />}
                onClick={() => window.location.href="/learning?module=stock-types"}
                sx={{ justifyContent: "flex-start", textAlign: "left", py: 1.5 }}
              >
                Types of Stocks and Investments
              </Button>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Button 
                fullWidth 
                variant="outlined"
                startIcon={<TrendingUp />}
                onClick={() => window.location.href="/learning?module=trading-basics"}
                sx={{ justifyContent: "flex-start", textAlign: "left", py: 1.5 }}
              >
                Trading 101: How to Buy and Sell
              </Button>
            </Grid>
          </Grid>
        </Box>
      </>
    )
  }
];

interface StockMarketIntroductionProps {
  onComplete?: () => void;
  onProgress?: (progress: number) => void;
}

const StockMarketIntroduction: React.FC<StockMarketIntroductionProps> = ({ 
  onComplete,
  onProgress 
}) => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<{[k: number]: boolean}>({});

  // Handle next button click
  const handleNext = () => {
    const newActiveStep = activeStep + 1;
    setActiveStep(newActiveStep);
    
    // Mark step as completed
    const newCompleted = { ...completed };
    newCompleted[activeStep] = true;
    setCompleted(newCompleted);
    
    // Calculate progress percentage
    const progress = (Object.keys(newCompleted).length / sections.length) * 100;
    if (onProgress) {
      onProgress(progress);
    }
    
    // Check if all steps are completed
    if (newActiveStep === sections.length - 1) {
      // We're on the last section
      if (!completed[newActiveStep]) {
        newCompleted[newActiveStep] = true;
        setCompleted(newCompleted);
        const finalProgress = (Object.keys(newCompleted).length / sections.length) * 100;
        if (onProgress) {
          onProgress(finalProgress);
        }
      }
    }
  };

  // Handle back button click
  const handleBack = () => {
    setActiveStep((prevActiveStep) => prevActiveStep - 1);
  };

  // Handle step click
  const handleStep = (step: number) => () => {
    setActiveStep(step);
  };

  // Handle module completion
  const handleComplete = () => {
    const newCompleted = { ...completed };
    newCompleted[activeStep] = true;
    setCompleted(newCompleted);
    
    if (onComplete) {
      onComplete();
    }
  };

  // Calculate overall progress
  const totalProgress = (Object.keys(completed).length / sections.length) * 100;

  return (
    <Box>
      {/* Module Header */}
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <School sx={{ mr: 1.5, color: 'primary.main' }} />
          Introduction to the Stock Market
          <EducationalTooltip
            term="Stock Market"
            definition={getTerm('Stock Market')?.definition || "A place where people buy and sell shares of companies."}
            placement="right"
          />
        </Typography>
        
        {/* Progress bar */}
        <Box sx={{ mt: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">Progress</Typography>
            <Typography variant="body2" color="text.secondary">{Math.round(totalProgress)}%</Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={totalProgress} 
            sx={{ height: 8, borderRadius: 4 }} 
          />
        </Box>
      </Box>
      
      {/* Stepper navigation */}
      <Stepper 
        nonLinear 
        activeStep={activeStep} 
        sx={{ 
          mb: 4, 
          overflowX: 'auto',
          flexWrap: 'nowrap'
        }}
      >
        {sections.map((section, index) => (
          <Step key={section.title} completed={completed[index]}>
            <StepLabel 
              StepIconProps={{ 
                icon: section.icon,
                active: activeStep === index,
                completed: completed[index]
              }}
              onClick={handleStep(index)}
              sx={{ cursor: 'pointer' }}
            >
              <Typography 
                variant="body2" 
                sx={{ 
                  display: { xs: 'none', md: 'block' } 
                }}
              >
                {section.title}
              </Typography>
            </StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {/* Content Section */}
      <Paper 
        elevation={0} 
        variant="outlined" 
        sx={{ 
          p: 3, 
          borderRadius: 2,
          mb: 3,
          minHeight: '50vh'
        }}
      >
        {/* Section Title */}
        <Typography 
          variant="h5" 
          gutterBottom 
          sx={{ 
            display: 'flex', 
            alignItems: 'center',
            mb: 3,
            color: 'primary.main'
          }}
        >
          {sections[activeStep].icon}
          <Box component="span" sx={{ ml: 1.5 }}>
            {sections[activeStep].title}
          </Box>
        </Typography>
        
        <Divider sx={{ mb: 3 }} />
        
        {/* Section Content */}
        {sections[activeStep].content}
      </Paper>
      
      {/* Navigation buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Button
          startIcon={<NavigateBefore />}
          onClick={handleBack}
          disabled={activeStep === 0}
          variant="outlined"
        >
          Previous
        </Button>
        
        <Box>
          {activeStep === sections.length - 1 ? (
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleComplete}
              startIcon={<CheckCircle />}
            >
              Complete Module
            </Button>
          ) : (
            <Button
              variant="contained"
              color="primary"
              onClick={handleNext}
              endIcon={<NavigateNext />}
            >
              Continue
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default StockMarketIntroduction;