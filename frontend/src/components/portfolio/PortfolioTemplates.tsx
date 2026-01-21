import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  Button,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tab,
  Tabs,
  useTheme,
} from '@mui/material';
import {
  AccountBalance,
  School,
  TrendingUp,
  Star,
  Whatshot,
  LocalAtm,
  VerifiedUser,
  PieChart,
  ArrowForward,
  FilterList,
  Check,
  Info,
  NavigateNext,
} from '@mui/icons-material';
import EducationalTooltip from '../common/EducationalTooltip';

// Template categories
type TemplateCategory = 'age' | 'goal' | 'all';

// Template data structure
interface PortfolioTemplate {
  id: string;
  name: string;
  description: string;
  riskLevel: 'conservative' | 'moderate' | 'growth' | 'aggressive';
  suitableFor: {
    ages: string;
    goals: string[];
    timeHorizon: string;
  };
  allocation: {
    [key: string]: number;
  };
  expectedReturn: {
    low: number;
    average: number;
    high: number;
  };
  volatility: number; // 1-10 scale
  diversification: number; // 1-10 scale
  popularity: number; // 1-5 scale
  featured?: boolean;
}

// Define portfolio templates
const PORTFOLIO_TEMPLATES: PortfolioTemplate[] = [
  {
    id: 'starter-conservative',
    name: 'Starter Conservative',
    description: 'A low-risk portfolio for beginners or those with a short time horizon.',
    riskLevel: 'conservative',
    suitableFor: {
      ages: '8-12, 60+',
      goals: ['Capital Preservation', 'Income', 'Education Savings'],
      timeHorizon: '1-3 years',
    },
    allocation: {
      'US Stocks': 20,
      'International Stocks': 10,
      'Bonds': 50,
      'Real Estate': 5,
      'Cash': 15,
    },
    expectedReturn: {
      low: 2,
      average: 4,
      high: 6,
    },
    volatility: 3,
    diversification: 7,
    popularity: 4,
  },
  {
    id: 'balanced-growth',
    name: 'Balanced Growth',
    description: 'A balanced portfolio for moderate growth with reduced volatility.',
    riskLevel: 'moderate',
    suitableFor: {
      ages: '13-17, 45-59',
      goals: ['Growth', 'Income', 'College Savings'],
      timeHorizon: '3-5 years',
    },
    allocation: {
      'US Stocks': 40,
      'International Stocks': 15,
      'Bonds': 30,
      'Real Estate': 10,
      'Cash': 5,
    },
    expectedReturn: {
      low: 4,
      average: 6,
      high: 8,
    },
    volatility: 5,
    diversification: 8,
    popularity: 5,
    featured: true,
  },
  {
    id: 'growth-portfolio',
    name: 'Long-Term Growth',
    description: 'A growth-oriented portfolio for long-term investors.',
    riskLevel: 'growth',
    suitableFor: {
      ages: '18-44',
      goals: ['Growth', 'Retirement', 'Wealth Building'],
      timeHorizon: '5-10 years',
    },
    allocation: {
      'US Stocks': 55,
      'International Stocks': 25,
      'Bonds': 10,
      'Real Estate': 5,
      'Commodities': 5,
    },
    expectedReturn: {
      low: 6,
      average: 8,
      high: 10,
    },
    volatility: 7,
    diversification: 9,
    popularity: 4,
  },
  {
    id: 'aggressive-growth',
    name: 'Aggressive Growth',
    description: 'A high-risk, high-reward portfolio for long-term growth.',
    riskLevel: 'aggressive',
    suitableFor: {
      ages: '18-30',
      goals: ['Maximum Growth', 'Wealth Building'],
      timeHorizon: '10+ years',
    },
    allocation: {
      'US Stocks': 60,
      'International Stocks': 30,
      'Real Estate': 5,
      'Commodities': 5,
    },
    expectedReturn: {
      low: 7,
      average: 10,
      high: 13,
    },
    volatility: 9,
    diversification: 6,
    popularity: 3,
  },
  {
    id: 'education-savings',
    name: 'Education Fund',
    description: 'Designed for parents saving for their children\'s education.',
    riskLevel: 'moderate',
    suitableFor: {
      ages: 'Parents of children 5-15',
      goals: ['Education Savings', 'College Fund'],
      timeHorizon: '3-15 years',
    },
    allocation: {
      'US Stocks': 45,
      'International Stocks': 15,
      'Bonds': 30,
      'Real Estate': 5,
      'Cash': 5,
    },
    expectedReturn: {
      low: 4,
      average: 6,
      high: 8,
    },
    volatility: 5,
    diversification: 8,
    popularity: 4,
  },
  {
    id: 'tech-growth',
    name: 'Tech-Focused Growth',
    description: 'A growth portfolio with emphasis on technology and innovation.',
    riskLevel: 'aggressive',
    suitableFor: {
      ages: '18-40',
      goals: ['Growth', 'Innovation Exposure'],
      timeHorizon: '7+ years',
    },
    allocation: {
      'US Stocks': 70,
      'International Stocks': 20,
      'Bonds': 5,
      'Cash': 5,
    },
    expectedReturn: {
      low: 8,
      average: 12,
      high: 16,
    },
    volatility: 10,
    diversification: 5,
    popularity: 4,
  },
  {
    id: 'first-investment',
    name: 'First Investment',
    description: 'Perfect for beginners making their first investment.',
    riskLevel: 'conservative',
    suitableFor: {
      ages: '8-16',
      goals: ['Learning', 'Saving'],
      timeHorizon: '1-5 years',
    },
    allocation: {
      'US Stocks': 25,
      'International Stocks': 5,
      'Bonds': 50,
      'Cash': 20,
    },
    expectedReturn: {
      low: 3,
      average: 5,
      high: 7,
    },
    volatility: 3,
    diversification: 6,
    popularity: 5,
    featured: true,
  },
  {
    id: 'income-portfolio',
    name: 'Income Portfolio',
    description: 'Focused on generating stable income rather than growth.',
    riskLevel: 'conservative',
    suitableFor: {
      ages: '50+',
      goals: ['Income', 'Capital Preservation'],
      timeHorizon: '1-3 years',
    },
    allocation: {
      'US Stocks': 20,
      'International Stocks': 5,
      'Bonds': 60,
      'Real Estate': 10,
      'Cash': 5,
    },
    expectedReturn: {
      low: 3,
      average: 5,
      high: 7,
    },
    volatility: 3,
    diversification: 7,
    popularity: 3,
  },
];

// Define color mapping for risk levels
const RISK_COLORS = {
  conservative: '#4caf50', // green
  moderate: '#2196f3', // blue
  growth: '#ff9800', // orange
  aggressive: '#f44336', // red
};

interface PortfolioTemplatesProps {
  onSelectTemplate?: (template: PortfolioTemplate) => void;
  userAge?: number;
  currentGoal?: string;
}

const PortfolioTemplates: React.FC<PortfolioTemplatesProps> = ({
  onSelectTemplate,
  userAge,
  currentGoal
}) => {
  const theme = useTheme();
  const [selectedCategory, setSelectedCategory] = useState<TemplateCategory>('all');
  const [selectedTemplate, setSelectedTemplate] = useState<PortfolioTemplate | null>(null);
  const [detailsOpen, setDetailsOpen] = useState<boolean>(false);
  
  // Color generation for allocation pie chart
  const getColorForAsset = (assetName: string) => {
    const colorMap: { [key: string]: string } = {
      'US Stocks': '#3f51b5',
      'International Stocks': '#2196f3',
      'Bonds': '#4caf50',
      'Real Estate': '#ff9800',
      'Commodities': '#f44336',
      'Cash': '#9e9e9e',
    };
    
    return colorMap[assetName] || '#9c27b0';
  };
  
  // Filter templates based on category
  const getFilteredTemplates = () => {
    if (selectedCategory === 'all') return PORTFOLIO_TEMPLATES;
    
    if (selectedCategory === 'age' && userAge) {
      return PORTFOLIO_TEMPLATES.filter(template => {
        const ageRanges = template.suitableFor.ages
          .split(',')
          .map(range => range.trim())
          .filter(range => range.includes('-'));
          
        return ageRanges.some(range => {
          const [min, max] = range.split('-').map(Number);
          return userAge >= min && userAge <= max;
        });
      });
    }
    
    if (selectedCategory === 'goal' && currentGoal) {
      return PORTFOLIO_TEMPLATES.filter(template => 
        template.suitableFor.goals.some(goal => 
          goal.toLowerCase().includes(currentGoal.toLowerCase())
        )
      );
    }
    
    return PORTFOLIO_TEMPLATES;
  };
  
  // Handle template selection
  const handleSelectTemplate = (template: PortfolioTemplate) => {
    setSelectedTemplate(template);
    setDetailsOpen(true);
  };
  
  // Handle details close
  const handleCloseDetails = () => {
    setDetailsOpen(false);
  };
  
  // Handle use template action
  const handleUseTemplate = () => {
    if (selectedTemplate && onSelectTemplate) {
      onSelectTemplate(selectedTemplate);
    }
    setDetailsOpen(false);
  };
  
  // Handle category change
  const handleCategoryChange = (_event: React.SyntheticEvent, newValue: TemplateCategory) => {
    setSelectedCategory(newValue);
  };
  
  // Featured templates
  const featuredTemplates = PORTFOLIO_TEMPLATES.filter(template => template.featured);
  
  return (
    <Box>
      <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <AccountBalance sx={{ mr: 1.5, color: 'primary.main' }} />
        Starter Portfolio Templates
        <EducationalTooltip
          term="Portfolio Templates"
          definition="Pre-built investment portfolios designed for different investors based on age, goals, and risk tolerance."
          placement="right"
        />
      </Typography>
      
      {/* Category Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={selectedCategory} 
          onChange={handleCategoryChange}
          aria-label="portfolio template categories"
        >
          <Tab 
            icon={<FilterList />} 
            iconPosition="start" 
            label="All Templates" 
            value="all" 
          />
          <Tab 
            icon={<School />} 
            iconPosition="start" 
            label="By Age" 
            value="age" 
            disabled={!userAge}
          />
          <Tab 
            icon={<Star />} 
            iconPosition="start" 
            label="By Goal" 
            value="goal" 
            disabled={!currentGoal}
          />
        </Tabs>
      </Box>
      
      {/* Featured Templates */}
      {selectedCategory === 'all' && featuredTemplates.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Featured Templates
          </Typography>
          
          <Grid container spacing={2}>
            {featuredTemplates.map((template) => (
              <Grid size={{ xs: 12, sm: 6 }} key={template.id}>
                <Paper 
                  elevation={3}
                  sx={{ 
                    p: 2, 
                    borderTop: `4px solid ${RISK_COLORS[template.riskLevel]}`,
                    height: '100%',
                    display: 'flex',
                    flexDirection: 'column',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <Box 
                    sx={{ 
                      position: 'absolute', 
                      top: 0, 
                      right: 0, 
                      bgcolor: 'primary.main',
                      color: 'primary.contrastText',
                      px: 1,
                      py: 0.5,
                      fontSize: '0.75rem',
                      fontWeight: 'bold',
                      borderRadius: '0 0 0 8px'
                    }}
                  >
                    FEATURED
                  </Box>
                  
                  <Typography variant="h6" gutterBottom>
                    {template.name}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {template.description}
                  </Typography>
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Chip 
                      size="small" 
                      label={template.riskLevel.charAt(0).toUpperCase() + template.riskLevel.slice(1)} 
                      sx={{ bgcolor: RISK_COLORS[template.riskLevel], color: 'white' }}
                    />
                    <Chip 
                      size="small" 
                      label={`${template.expectedReturn.average}% Avg. Return`}
                      color="primary"
                      variant="outlined"
                    />
                  </Box>
                  
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                    Suitable for: {template.suitableFor.ages} • {template.suitableFor.timeHorizon}
                  </Typography>
                  
                  <Box sx={{ mt: 'auto', pt: 2 }}>
                    <Button 
                      fullWidth 
                      variant="contained" 
                      color="primary"
                      endIcon={<ArrowForward />}
                      onClick={() => handleSelectTemplate(template)}
                    >
                      View Details
                    </Button>
                  </Box>
                </Paper>
              </Grid>
            ))}
          </Grid>
        </Box>
      )}
      
      {/* All Templates */}
      <Box>
        <Typography 
          variant="h6" 
          gutterBottom 
          sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'space-between' 
          }}
        >
          <span>
            {selectedCategory === 'all' ? 'All Templates' : 
             selectedCategory === 'age' ? 'Templates for Your Age' : 'Templates for Your Goal'}
          </span>
          <Typography variant="body2" color="text.secondary">
            {getFilteredTemplates().length} templates
          </Typography>
        </Typography>
        
        <Grid container spacing={2}>
          {getFilteredTemplates().map((template) => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={template.id}>
              <Card 
                variant="outlined" 
                sx={{ 
                  height: '100%', 
                  display: 'flex', 
                  flexDirection: 'column',
                  transition: 'all 0.2s',
                  '&:hover': {
                    boxShadow: 3,
                    borderColor: 'primary.main',
                  },
                }}
              >
                <Box 
                  sx={{ 
                    height: 8, 
                    bgcolor: RISK_COLORS[template.riskLevel],
                    width: '100%'
                  }} 
                />
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="h6" gutterBottom>
                    {template.name}
                  </Typography>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {template.description}
                  </Typography>
                  
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Expected annual return
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <Typography variant="h6" color="primary.main" sx={{ mr: 1 }}>
                        {template.expectedReturn.average}%
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        ({template.expectedReturn.low}%-{template.expectedReturn.high}%)
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', mb: 2 }}>
                    <Box sx={{ mr: 3 }}>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Volatility
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {[...Array(10)].map((_, i) => (
                          <Box
                            key={i}
                            sx={{
                              width: 4,
                              height: 12,
                              mx: '1px',
                              borderRadius: 1,
                              bgcolor: i < template.volatility ? 'error.main' : 'divider',
                            }}
                          />
                        ))}
                      </Box>
                    </Box>
                    
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        Diversification
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        {[...Array(10)].map((_, i) => (
                          <Box
                            key={i}
                            sx={{
                              width: 4,
                              height: 12,
                              mx: '1px',
                              borderRadius: 1,
                              bgcolor: i < template.diversification ? 'success.main' : 'divider',
                            }}
                          />
                        ))}
                      </Box>
                    </Box>
                  </Box>
                  
                  <Box sx={{ mt: 'auto' }}>
                    <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                      Top allocations
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {Object.entries(template.allocation)
                        .sort(([, a], [, b]) => b - a)
                        .slice(0, 3)
                        .map(([asset, value]) => (
                          <Chip
                            key={asset}
                            size="small"
                            label={`${asset} ${value}%`}
                            sx={{ 
                              bgcolor: getColorForAsset(asset) + '20',
                              color: getColorForAsset(asset),
                              borderColor: getColorForAsset(asset)
                            }}
                            variant="outlined"
                          />
                        ))
                      }
                    </Box>
                  </Box>
                </CardContent>
                
                <Divider />
                
                <Box sx={{ p: 2, pt: 1 }}>
                  <Button 
                    fullWidth 
                    variant="contained" 
                    color="primary"
                    onClick={() => handleSelectTemplate(template)}
                    endIcon={<NavigateNext />}
                    size="small"
                  >
                    View Details
                  </Button>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
        
        {getFilteredTemplates().length === 0 && (
          <Paper sx={{ p: 3, textAlign: 'center', bgcolor: 'background.paper' }}>
            <Typography variant="body1" color="text.secondary">
              No templates found for your current filters.
            </Typography>
            <Button 
              variant="outlined" 
              color="primary" 
              sx={{ mt: 2 }}
              onClick={() => setSelectedCategory('all')}
            >
              View All Templates
            </Button>
          </Paper>
        )}
      </Box>
      
      {/* Template Details Dialog */}
      {selectedTemplate && (
        <Dialog
          open={detailsOpen}
          onClose={handleCloseDetails}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle sx={{ borderBottom: `4px solid ${RISK_COLORS[selectedTemplate.riskLevel]}` }}>
            {selectedTemplate.name}
          </DialogTitle>
          
          <DialogContent>
            <Box sx={{ py: 2 }}>
              <Typography variant="body1" paragraph>
                {selectedTemplate.description}
              </Typography>
              
              <Box sx={{ mb: 3 }}>
                <Grid container spacing={3}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Risk Level
                      </Typography>
                      <Chip 
                        label={selectedTemplate.riskLevel.charAt(0).toUpperCase() + selectedTemplate.riskLevel.slice(1)}
                        sx={{ 
                          bgcolor: RISK_COLORS[selectedTemplate.riskLevel], 
                          color: 'white' 
                        }}
                      />
                      
                      <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                        Time Horizon
                      </Typography>
                      <Typography variant="body2">
                        {selectedTemplate.suitableFor.timeHorizon}
                      </Typography>
                      
                      <Typography variant="subtitle2" sx={{ mt: 2 }} gutterBottom>
                        Suitable For
                      </Typography>
                      <Typography variant="body2">
                        Ages: {selectedTemplate.suitableFor.ages}
                      </Typography>
                    </Paper>
                  </Grid>
                  
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Expected Annual Return
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'baseline', mb: 2 }}>
                        <Typography variant="h4" color="primary">
                          {selectedTemplate.expectedReturn.average}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                          expected
                        </Typography>
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        Potential range:
                      </Typography>
                      
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="body2" fontWeight="bold" color="error.main">
                          {selectedTemplate.expectedReturn.low}%
                        </Typography>
                        <Box sx={{ 
                          height: 4, 
                          flexGrow: 1, 
                          mx: 1, 
                          borderRadius: 2,
                          background: `linear-gradient(to right, ${theme.palette.error.main}, ${theme.palette.success.main})` 
                        }} />
                        <Typography variant="body2" fontWeight="bold" color="success.main">
                          {selectedTemplate.expectedReturn.high}%
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Paper variant="outlined" sx={{ p: 2, height: '100%' }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Suitable Goals
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selectedTemplate.suitableFor.goals.map((goal) => (
                          <Chip 
                            key={goal} 
                            label={goal} 
                            size="small" 
                            color="primary" 
                            variant="outlined"
                          />
                        ))}
                      </Box>
                      
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Portfolio Metrics
                        </Typography>
                        <Grid container spacing={1}>
                          <Grid size={6}>
                            <Typography variant="caption" color="text.secondary">
                              Volatility:
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Box sx={{ width: 50 }}>
                                <Typography variant="body2" fontWeight="bold">
                                  {selectedTemplate.volatility}/10
                                </Typography>
                              </Box>
                              <Box 
                                sx={{ 
                                  height: 8, 
                                  width: 80, 
                                  borderRadius: 4,
                                  bgcolor: 'grey.200',
                                  overflow: 'hidden'
                                }}
                              >
                                <Box 
                                  sx={{ 
                                    height: '100%', 
                                    width: `${selectedTemplate.volatility * 10}%`,
                                    bgcolor: 'error.main' 
                                  }} 
                                />
                              </Box>
                            </Box>
                          </Grid>
                          <Grid size={6}>
                            <Typography variant="caption" color="text.secondary">
                              Diversification:
                            </Typography>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Box sx={{ width: 50 }}>
                                <Typography variant="body2" fontWeight="bold">
                                  {selectedTemplate.diversification}/10
                                </Typography>
                              </Box>
                              <Box 
                                sx={{ 
                                  height: 8, 
                                  width: 80, 
                                  borderRadius: 4,
                                  bgcolor: 'grey.200',
                                  overflow: 'hidden'
                                }}
                              >
                                <Box 
                                  sx={{ 
                                    height: '100%', 
                                    width: `${selectedTemplate.diversification * 10}%`,
                                    bgcolor: 'success.main' 
                                  }} 
                                />
                              </Box>
                            </Box>
                          </Grid>
                        </Grid>
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>
              </Box>
              
              <Divider sx={{ my: 3 }} />
              
              {/* Asset Allocation */}
              <Typography variant="h6" gutterBottom>
                Asset Allocation
              </Typography>
              
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 7 }}>
                  <Box sx={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Box sx={{ position: 'relative', width: 250, height: 250 }}>
                      {/* This is a simplified visualization - in a real app you would use a charting library */}
                      {Object.entries(selectedTemplate.allocation).map(([asset, percentage], index, arr) => {
                        const prevSizes = arr.slice(0, index).reduce((sum, [, size]) => sum + size, 0);
                        const startAngle = (prevSizes / 100) * 360;
                        const angle = (percentage / 100) * 360;
                        
                        return (
                          <Box
                            key={asset}
                            sx={{
                              position: 'absolute',
                              width: '100%',
                              height: '100%',
                              borderRadius: '50%',
                              clipPath: `polygon(50% 50%, 50% 0, ${
                                50 + 50 * Math.sin((startAngle + angle) * (Math.PI / 180))
                              }% ${
                                50 - 50 * Math.cos((startAngle + angle) * (Math.PI / 180))
                              }%, ${
                                50 + 50 * Math.sin(startAngle * (Math.PI / 180))
                              }% ${
                                50 - 50 * Math.cos(startAngle * (Math.PI / 180))
                              }%, 50% 0)`,
                              backgroundColor: getColorForAsset(asset),
                              transform: 'rotate(-90deg)',
                            }}
                          />
                        );
                      })}
                      
                      <Box
                        sx={{
                          position: 'absolute',
                          top: '50%',
                          left: '50%',
                          transform: 'translate(-50%, -50%)',
                          width: '60%',
                          height: '60%',
                          borderRadius: '50%',
                          bgcolor: 'background.paper',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexDirection: 'column',
                          boxShadow: 'inset 0 0 10px rgba(0,0,0,0.1)'
                        }}
                      >
                        <PieChart sx={{ color: 'primary.main', fontSize: 32 }} />
                        <Typography variant="caption" color="text.secondary" align="center">
                          Asset<br />Allocation
                        </Typography>
                      </Box>
                    </Box>
                  </Box>
                </Grid>
                
                <Grid size={{ xs: 12, md: 5 }}>
                  <List>
                    {Object.entries(selectedTemplate.allocation)
                      .sort(([, a], [, b]) => b - a)
                      .map(([asset, percentage]) => (
                        <ListItem key={asset} sx={{ py: 1 }}>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <Box
                              sx={{
                                width: 16,
                                height: 16,
                                bgcolor: getColorForAsset(asset),
                                borderRadius: '50%'
                              }}
                            />
                          </ListItemIcon>
                          <ListItemText 
                            primary={asset} 
                            secondary={`${percentage}%`}
                          />
                          <Box 
                            sx={{ 
                              width: 60, 
                              height: 8, 
                              borderRadius: 4,
                              bgcolor: 'grey.200',
                              overflow: 'hidden'
                            }}
                          >
                            <Box 
                              sx={{ 
                                height: '100%', 
                                width: `${percentage}%`,
                                bgcolor: getColorForAsset(asset) 
                              }} 
                            />
                          </Box>
                        </ListItem>
                      ))
                    }
                  </List>
                </Grid>
              </Grid>
              
              <Divider sx={{ my: 3 }} />
              
              {/* Educational Section */}
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2, 
                  bgcolor: 'info.light', 
                  color: 'info.contrastText',
                  borderRadius: 2
                }}
              >
                <Typography variant="subtitle1" sx={{ display: 'flex', alignItems: 'center' }}>
                  <Info sx={{ mr: 1 }} />
                  Why This Portfolio Works
                </Typography>
                <Typography variant="body2" paragraph sx={{ mt: 1 }}>
                  {selectedTemplate.riskLevel === 'conservative' && 
                    'This conservative portfolio focuses on capital preservation while still allowing for modest growth. The higher allocation to bonds and cash provides stability, while the stock components offer potential for growth.'
                  }
                  {selectedTemplate.riskLevel === 'moderate' && 
                    'This balanced portfolio aims to provide steady growth with moderate risk. The mix of stocks and bonds helps reduce volatility while still giving you good potential for long-term returns.'
                  }
                  {selectedTemplate.riskLevel === 'growth' && 
                    'This growth-oriented portfolio is designed for investors with a longer time horizon who can tolerate higher short-term volatility. The higher allocation to stocks helps maximize growth potential over time.'
                  }
                  {selectedTemplate.riskLevel === 'aggressive' && 
                    'This aggressive portfolio maximizes growth potential but comes with higher volatility. The heavy allocation to stocks, particularly international stocks, provides strong growth opportunities but requires a long time horizon to ride out market fluctuations.'
                  }
                </Typography>
                <Typography variant="body2">
                  <strong>Best suited for:</strong> {selectedTemplate.suitableFor.ages} year olds with {selectedTemplate.suitableFor.timeHorizon} investment horizon, focusing on {selectedTemplate.suitableFor.goals.join(', ')}.
                </Typography>
              </Paper>
            </Box>
          </DialogContent>
          
          <DialogActions>
            <Button onClick={handleCloseDetails}>Cancel</Button>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleUseTemplate}
              startIcon={<Check />}
            >
              Use This Template
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Box>
  );
};

export default PortfolioTemplates;