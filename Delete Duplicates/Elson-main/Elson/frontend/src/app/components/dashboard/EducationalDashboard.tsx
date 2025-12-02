import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  CardActions, 
  CardMedia,
  Tabs,
  Tab,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip,
  LinearProgress,
  useTheme,
  alpha,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  School,
  TrendingUp,
  AccountBalance,
  BarChart,
  Timeline,
  MenuBook,
  Star,
  StarBorder,
  ArrowForward,
  CheckCircle,
  PlayCircle
} from '@mui/icons-material';
import BeginnerOrderForm from '../trading/BeginnerOrderForm';
import FinancialGlossary from '../common/FinancialGlossary';
import EducationalTooltip from '../common/EducationalTooltip';
import { useAuth } from '../../hooks/useAuth';

// Interface for learning modules
interface LearningModule {
  id: string;
  title: string;
  description: string;
  level: 'beginner' | 'intermediate' | 'advanced';
  duration: number; // in minutes
  icon: React.ReactNode;
  completed: boolean;
  progress: number;
  image?: string;
}

// Demo progress data for learning modules
const demoLearningModules: LearningModule[] = [
  {
    id: 'stock-market-intro',
    title: 'Introduction to the Stock Market',
    description: 'Learn the fundamentals of how the stock market works and why companies go public.',
    level: 'beginner',
    duration: 15,
    icon: <School />,
    completed: false,
    progress: 100,
    image: 'https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80'
  },
  {
    id: 'types-of-investments',
    title: 'Types of Investments',
    description: 'Explore different investment types including stocks, bonds, ETFs, and more.',
    level: 'beginner',
    duration: 25,
    icon: <AccountBalance />,
    completed: false,
    progress: 40,
    image: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=600&q=80'
  },
  {
    id: 'trading-basics',
    title: 'Trading Basics',
    description: 'Learn essential trading concepts including order types, bid-ask spreads, and risk management.',
    level: 'beginner',
    duration: 30,
    icon: <TrendingUp />,
    completed: false,
    progress: 0,
    image: 'https://images.unsplash.com/photo-1535320903710-d993d3d77d29?auto=format&fit=crop&w=600&q=80'
  },
  {
    id: 'understanding-risk',
    title: 'Understanding Investment Risk',
    description: 'Learn how to assess risk in your investments and make informed decisions.',
    level: 'intermediate',
    duration: 25,
    icon: <BarChart />,
    completed: false,
    progress: 0,
    image: 'https://images.unsplash.com/photo-1460472178825-e5240623afd5?auto=format&fit=crop&w=600&q=80'
  },
  {
    id: 'building-portfolio',
    title: 'Building Your First Portfolio',
    description: 'Discover how to create a balanced and diversified investment portfolio.',
    level: 'intermediate',
    duration: 30,
    icon: <AccountBalance />,
    completed: false,
    progress: 0,
    image: 'https://images.unsplash.com/photo-1579532537598-459ecdaf39cc?auto=format&fit=crop&w=600&q=80'
  }
];

// Investment quiz questions for the educational component
const investmentQuiz = [
  {
    question: 'What does "diversification" mean in investing?',
    options: [
      'Buying only tech stocks',
      'Investing in different types of assets to reduce risk',
      'Investing all your money in one company',
      'Only investing in foreign markets'
    ],
    correctAnswer: 1
  },
  {
    question: 'What is a stock?',
    options: [
      'A loan you give to a company',
      'A piece of ownership in a company',
      'A guarantee of profits',
      'A type of cryptocurrency'
    ],
    correctAnswer: 1
  },
  {
    question: 'What is a dividend?',
    options: [
      'The total value of your portfolio',
      'A fee paid to your broker',
      'A payment made by a company to its shareholders',
      'The profit made when selling a stock'
    ],
    correctAnswer: 2
  }
];

const EducationalDashboard: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuth();
  const [tab, setTab] = useState(0);
  const [modules, setModules] = useState<LearningModule[]>(demoLearningModules);
  const [quizOpen, setQuizOpen] = useState(false);
  const [currentQuizIndex, setCurrentQuizIndex] = useState(0);

  // Handle tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };

  // Handle module start
  const handleStartModule = (moduleId: string) => {
    // Navigate to the module content
    window.location.href = `/learning?module=${moduleId}`;
  };

  // Handle module completion
  const handleCompleteModule = (moduleId: string) => {
    setModules(prevModules => 
      prevModules.map(module => 
        module.id === moduleId 
          ? { ...module, completed: true, progress: 100 } 
          : module
      )
    );
  };

  // Get recommended modules based on user level
  const getRecommendedModules = () => {
    // For demo, we'll just return modules with progress > 0 or the first module if none started
    const inProgressModules = modules.filter(m => m.progress > 0 && m.progress < 100);
    if (inProgressModules.length > 0) {
      return inProgressModules;
    }
    return [modules[0]];
  };
  
  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1" display="flex" alignItems="center">
          <School sx={{ mr: 1.5, color: 'primary.main' }} />
          Learning Center
          <EducationalTooltip
            term="Learning Center"
            definition="Your personalized dashboard for financial education. Start with the beginner modules and track your progress."
            placement="right"
          />
        </Typography>
        <Chip 
          icon={<Star />} 
          label={`Level: ${user?.role === 'MINOR' ? 'Beginner' : 'Intermediate'}`}
          color="primary" 
          variant="outlined" 
        />
      </Box>

      {/* Welcome card with progress summary */}
      <Card variant="outlined" sx={{ mb: 4, borderRadius: 2, overflow: 'hidden' }}>
        <Box sx={{ 
          p: 3, 
          background: `linear-gradient(45deg, ${theme.palette.primary.main} 30%, ${theme.palette.primary.light} 90%)`,
          color: 'white'
        }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={7}>
              <Typography variant="h5" gutterBottom>
                Welcome back, {user?.first_name || 'Learner'}!
              </Typography>
              <Typography variant="body1" sx={{ mb: 2, opacity: 0.9 }}>
                Continue your investing journey and build your financial knowledge.
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
                <Button 
                  variant="contained" 
                  color="secondary" 
                  startIcon={<PlayCircle />}
                  onClick={() => handleStartModule(getRecommendedModules()[0].id)}
                  sx={{ 
                    color: 'primary.main', 
                    bgcolor: 'white',
                    '&:hover': {
                      bgcolor: alpha(theme.palette.common.white, 0.9),
                    }
                  }}
                >
                  Continue Learning
                </Button>
                <Button 
                  variant="outlined" 
                  onClick={() => setTab(2)}
                  sx={{ 
                    color: 'white', 
                    borderColor: 'white',
                    '&:hover': {
                      borderColor: 'white',
                      bgcolor: alpha(theme.palette.common.white, 0.1),
                    }
                  }}
                >
                  View All Modules
                </Button>
              </Box>
            </Grid>
            <Grid item xs={12} md={5}>
              <Box sx={{ 
                bgcolor: alpha(theme.palette.common.white, 0.1), 
                p: 2, 
                borderRadius: 2
              }}>
                <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                  <CheckCircle fontSize="small" sx={{ mr: 1 }} />
                  Your Learning Progress
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="body2">Overall Completion</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {Math.round(modules.reduce((acc, m) => acc + m.progress, 0) / modules.length)}%
                  </Typography>
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={modules.reduce((acc, m) => acc + m.progress, 0) / modules.length} 
                  sx={{ 
                    height: 8, 
                    borderRadius: 4,
                    mb: 1.5,
                    bgcolor: alpha(theme.palette.common.white, 0.2),
                    '& .MuiLinearProgress-bar': {
                      bgcolor: 'white'
                    }
                  }}
                />
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  {modules.filter(m => m.completed).length} of {modules.length} modules completed
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Box>
      </Card>

      {/* Main content tabs */}
      <Paper sx={{ mb: 4 }}>
        <Tabs 
          value={tab} 
          onChange={handleTabChange} 
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="Overview" icon={<School />} iconPosition="start" />
          <Tab label="Practice Trading" icon={<TrendingUp />} iconPosition="start" />
          <Tab label="Learning Modules" icon={<MenuBook />} iconPosition="start" />
          <Tab label="Financial Terms" icon={<AccountBalance />} iconPosition="start" />
        </Tabs>

        {/* Overview Tab */}
        {tab === 0 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>Learning Path</Typography>
            
            <Grid container spacing={3} mb={4}>
              {/* Recommended modules */}
              <Grid item xs={12} md={8}>
                <Typography variant="subtitle1" gutterBottom>
                  Recommended For You
                </Typography>
                <Grid container spacing={2}>
                  {getRecommendedModules().map(module => (
                    <Grid item xs={12} sm={6} key={module.id}>
                      <Card variant="outlined">
                        <CardMedia
                          component="img"
                          height="140"
                          image={module.image}
                          alt={module.title}
                        />
                        <CardContent>
                          <Typography variant="h6">{module.title}</Typography>
                          <Box display="flex" alignItems="center" mt={1} mb={2}>
                            <Chip 
                              label={module.level.charAt(0).toUpperCase() + module.level.slice(1)} 
                              size="small" 
                              color="primary" 
                              sx={{ mr: 1 }} 
                            />
                            <Typography variant="body2" color="text.secondary">
                              {module.duration} min
                            </Typography>
                          </Box>
                          <Box sx={{ width: '100%', mb: 2 }}>
                            <Box display="flex" justifyContent="space-between" mb={0.5}>
                              <Typography variant="body2" color="text.secondary">Progress</Typography>
                              <Typography variant="body2" color="text.secondary">{module.progress}%</Typography>
                            </Box>
                            <LinearProgress 
                              variant="determinate" 
                              value={module.progress} 
                              sx={{ height: 6, borderRadius: 3 }}
                            />
                          </Box>
                        </CardContent>
                        <CardActions>
                          <Button 
                            size="small" 
                            onClick={() => handleStartModule(module.id)}
                            startIcon={module.progress > 0 ? <PlayCircle /> : <ArrowForward />}
                          >
                            {module.progress > 0 ? 'Continue' : 'Start Learning'}
                          </Button>
                        </CardActions>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Grid>
              
              {/* Quick learning tips */}
              <Grid item xs={12} md={4}>
                <Typography variant="subtitle1" gutterBottom>
                  Quick Learning Tips
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <List dense disablePadding>
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Star fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Start with beginner modules to build your knowledge foundation" 
                      />
                    </ListItem>
                    <Divider component="li" sx={{ my: 1 }} />
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Star fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Practice with virtual trading before using real money" 
                      />
                    </ListItem>
                    <Divider component="li" sx={{ my: 1 }} />
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Star fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Use the glossary to understand financial terms" 
                      />
                    </ListItem>
                    <Divider component="li" sx={{ my: 1 }} />
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <Star fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary="Take quizzes to test your knowledge after each module" 
                      />
                    </ListItem>
                  </List>
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Button 
                      variant="outlined" 
                      size="small"
                      onClick={() => setQuizOpen(true)}
                    >
                      Try a Quick Quiz
                    </Button>
                  </Box>
                </Paper>
                
                {/* Achievement card */}
                <Paper variant="outlined" sx={{ p: 2, mt: 2 }}>
                  <Typography variant="subtitle1" gutterBottom display="flex" alignItems="center">
                    <Timeline sx={{ mr: 1, fontSize: 20 }} color="primary" />
                    Your Learning Goals
                  </Typography>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Box sx={{ 
                      width: 40, 
                      height: 40, 
                      borderRadius: '50%', 
                      bgcolor: 'primary.main',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                      fontWeight: 'bold',
                      mr: 2
                    }}>
                      1
                    </Box>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">Complete Your First Module</Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={modules[0].progress} 
                        sx={{ height: 4, borderRadius: 2, mt: 0.5, width: '100%' }}
                      />
                    </Box>
                  </Box>
                  
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ 
                      width: 40, 
                      height: 40, 
                      borderRadius: '50%', 
                      bgcolor: alpha(theme.palette.primary.main, 0.2),
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'primary.main',
                      fontWeight: 'bold',
                      mr: 2
                    }}>
                      2
                    </Box>
                    <Box>
                      <Typography variant="body2" fontWeight="medium">Place Your First Practice Trade</Typography>
                      <LinearProgress 
                        variant="determinate" 
                        value={0} 
                        sx={{ height: 4, borderRadius: 2, mt: 0.5, width: '100%' }}
                      />
                    </Box>
                  </Box>
                </Paper>
              </Grid>
            </Grid>
            
            {/* Recent activity section */}
            <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>Recent Activity</Typography>
            <Paper variant="outlined" sx={{ p: 2 }}>
              <List dense disablePadding>
                <ListItem sx={{ py: 1.5 }}>
                  <ListItemIcon>
                    <School color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="You started 'Introduction to the Stock Market'" 
                    secondary="2 days ago"
                  />
                  <Button size="small" onClick={() => handleStartModule('stock-basics')}>Continue</Button>
                </ListItem>
                <Divider component="li" />
                <ListItem sx={{ py: 1.5 }}>
                  <ListItemIcon>
                    <StarBorder color="primary" />
                  </ListItemIcon>
                  <ListItemText 
                    primary="New module added: 'Understanding Risk'" 
                    secondary="3 days ago"
                  />
                  <Button size="small" onClick={() => handleStartModule('understanding-risk')}>View</Button>
                </ListItem>
              </List>
            </Paper>
          </Box>
        )}

        {/* Practice Trading Tab */}
        {tab === 1 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>
              Practice Trading
              <EducationalTooltip
                term="Practice Trading"
                definition="A safe environment to learn how to buy and sell stocks without using real money."
                icon="help"
              />
            </Typography>
            
            <Typography variant="body1" paragraph>
              Practice making trades in a safe environment before using real money. 
              This simulator mirrors real-world trading but uses virtual currency.
            </Typography>
            
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Paper elevation={0} variant="outlined" sx={{ p: 2, mb: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>Place a Practice Trade</Typography>
                  <BeginnerOrderForm educationalMode={true} />
                </Paper>
              </Grid>
              
              <Grid item xs={12} md={4}>
                <Paper elevation={0} variant="outlined" sx={{ p: 2 }}>
                  <Typography variant="subtitle1" gutterBottom>Trading Tips</Typography>
                  <List dense>
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <StarBorder fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Box display="flex" alignItems="center">
                            Stock Symbol
                            <EducationalTooltip
                              term="Stock Symbol"
                              definition="A unique series of letters assigned to a security for trading purposes. For example, Apple's stock symbol is AAPL."
                              icon="info"
                            />
                          </Box>
                        }
                        secondary="Enter a company's ticker symbol (e.g., AAPL for Apple)" 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <StarBorder fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Box display="flex" alignItems="center">
                            Order Type
                            <EducationalTooltip
                              term="Order Type"
                              definition="Specifies how you want to buy or sell a stock. A market order executes immediately at the current price."
                              icon="info"
                            />
                          </Box>
                        }
                        secondary="Choose between buy (to purchase shares) or sell (to sell shares)" 
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon sx={{ minWidth: 36 }}>
                        <StarBorder fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={
                          <Box display="flex" alignItems="center">
                            Dollar vs. Share Investing
                            <EducationalTooltip
                              term="Dollar-Based Investing"
                              definition="Investing a specific dollar amount rather than a specific number of shares, allowing you to invest in stocks without buying whole shares."
                              icon="info"
                            />
                          </Box>
                        }
                        secondary="Choose dollars to invest a specific amount, or shares for a specific number" 
                      />
                    </ListItem>
                  </List>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Learning Modules Tab */}
        {tab === 2 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>Learning Modules</Typography>
            
            <Grid container spacing={3}>
              {modules.map(module => (
                <Grid item xs={12} sm={6} md={4} key={module.id}>
                  <Card variant="outlined">
                    <CardMedia
                      component="img"
                      height="140"
                      image={module.image}
                      alt={module.title}
                    />
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                        <Typography variant="h6">{module.title}</Typography>
                        <Box>
                          {module.completed ? (
                            <Tooltip title="Completed">
                              <CheckCircle color="success" />
                            </Tooltip>
                          ) : (
                            <Chip 
                              label={`${module.duration} min`}
                              size="small"
                              variant="outlined"
                            />
                          )}
                        </Box>
                      </Box>
                      <Box display="flex" alignItems="center" mt={1} mb={1}>
                        <Chip 
                          label={module.level.charAt(0).toUpperCase() + module.level.slice(1)} 
                          size="small" 
                          color="primary" 
                          sx={{ mr: 1 }} 
                        />
                      </Box>
                      <Typography variant="body2" color="text.secondary" mb={2}>
                        {module.description}
                      </Typography>
                      {!module.completed && (
                        <Box sx={{ width: '100%', mb: 1 }}>
                          <Box display="flex" justifyContent="space-between" mb={0.5}>
                            <Typography variant="body2" color="text.secondary">Progress</Typography>
                            <Typography variant="body2" color="text.secondary">{module.progress}%</Typography>
                          </Box>
                          <LinearProgress 
                            variant="determinate" 
                            value={module.progress} 
                            sx={{ height: 6, borderRadius: 3 }}
                          />
                        </Box>
                      )}
                    </CardContent>
                    <CardActions>
                      <Button 
                        size="small" 
                        onClick={() => 
                          module.progress > 0 && module.progress < 100 
                            ? handleStartModule(module.id)
                            : module.completed
                              ? handleCompleteModule(module.id) // This would actually restart in a real app
                              : handleStartModule(module.id)
                        }
                        startIcon={
                          module.completed 
                            ? <StarBorder /> 
                            : module.progress > 0 
                              ? <PlayCircle />
                              : <ArrowForward />
                        }
                      >
                        {module.completed 
                          ? 'Review Again' 
                          : module.progress > 0 
                            ? 'Continue' 
                            : 'Start'
                        }
                      </Button>
                      {module.progress > 0 && !module.completed && (
                        <Button 
                          size="small"
                          color="primary"
                          onClick={() => handleCompleteModule(module.id)}
                        >
                          Mark Complete
                        </Button>
                      )}
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Financial Terms Tab */}
        {tab === 3 && (
          <Box p={3}>
            <Typography variant="h6" gutterBottom>Financial Terms Glossary</Typography>
            <Typography variant="body1" paragraph>
              Familiarize yourself with important financial terms to build your investing knowledge.
            </Typography>
            
            <FinancialGlossary maxHeight={400} />
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default EducationalDashboard;