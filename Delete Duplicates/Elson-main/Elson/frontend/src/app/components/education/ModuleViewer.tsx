import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  Button,
  Container,
  useTheme,
  Breadcrumbs,
  Link,
  Divider
} from '@mui/material';
import { 
  School, 
  ArrowBack, 
  Home as HomeIcon,
  NavigateNext
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

// Import educational modules
import StockMarketIntroduction from './modules/StockMarketIntroduction';
import StockMarketQuiz from './quizzes/StockMarketQuiz';
import TypesOfInvestments from './modules/TypesOfInvestments';
import TypesOfInvestmentsQuiz from './quizzes/TypesOfInvestmentsQuiz';
import TradingBasics from './modules/TradingBasics';
import TradingBasicsQuiz from './quizzes/TradingBasicsQuiz';

interface ModuleViewerProps {
  onBack?: () => void;
}

// Module mapping system to load modules dynamically
const moduleComponents: { [key: string]: React.FC<any> } = {
  'stock-market-intro': StockMarketIntroduction,
  'stock-market-quiz': StockMarketQuiz,
  'types-of-investments': TypesOfInvestments,
  'types-of-investments-quiz': TypesOfInvestmentsQuiz,
  'trading-basics': TradingBasics,
  'trading-basics-quiz': TradingBasicsQuiz,
};

const moduleNames: { [key: string]: string } = {
  'stock-market-intro': 'Introduction to the Stock Market',
  'stock-market-quiz': 'Stock Market Quiz',
  'types-of-investments': 'Types of Investments',
  'types-of-investments-quiz': 'Types of Investments Quiz',
  'trading-basics': 'Trading Basics',
  'trading-basics-quiz': 'Trading Basics Quiz',
};

// Module relationships (which quiz corresponds to which module)
const moduleToQuizMap: { [key: string]: string } = {
  'stock-market-intro': 'stock-market-quiz',
  'types-of-investments': 'types-of-investments-quiz',
  'trading-basics': 'trading-basics-quiz',
};

// Quiz to module relationships (which module a quiz belongs to)
const quizToModuleMap: { [key: string]: string } = {
  'stock-market-quiz': 'stock-market-intro',
  'types-of-investments-quiz': 'types-of-investments',
  'trading-basics-quiz': 'trading-basics',
};

const ModuleViewer: React.FC<ModuleViewerProps> = ({ onBack }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [moduleId, setModuleId] = useState<string | null>(null);
  const [quizMode, setQuizMode] = useState(false);
  const [progress, setProgress] = useState(0);

  // Parse module ID from URL query parameters
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const module = params.get('module');
    const quiz = params.get('quiz');
    
    if (module) {
      setModuleId(module);
      setQuizMode(false);
    } else if (quiz) {
      setModuleId(quiz);
      setQuizMode(true);
    } else {
      // Default module if none specified
      setModuleId('stock-market-intro');
      setQuizMode(false);
    }
  }, [location]);

  // Handle module completion
  const handleModuleComplete = () => {
    // In a real app, this would save progress to the user's profile
    if (moduleId && moduleToQuizMap[moduleId]) {
      // Redirect to the corresponding quiz
      navigate(`/learning?quiz=${moduleToQuizMap[moduleId]}`);
    } else {
      // If no quiz is mapped, go back to learning dashboard
      navigate('/learning');
    }
  };

  // Handle quiz completion
  const handleQuizComplete = (score: number) => {
    // In a real app, save the score and progress
    console.log(`Quiz completed with score: ${score}`);
    
    // After a short delay, redirect to learning dashboard
    setTimeout(() => {
      navigate('/learning');
    }, 3000);
  };

  // Handle navigation back to learning dashboard
  const handleBackToLearning = () => {
    navigate('/learning');
  };

  // Handle quiz back button (go back to the associated module)
  const handleBackToModule = () => {
    if (moduleId && quizToModuleMap[moduleId]) {
      navigate(`/learning?module=${quizToModuleMap[moduleId]}`);
    } else {
      // Fallback to learning dashboard if no module is associated
      navigate('/learning');
    }
  };

  // Handle progress tracking
  const handleProgress = (progressValue: number) => {
    setProgress(progressValue);
    // In a real app, save progress to user profile
  };

  // Render the appropriate module component
  const renderModule = () => {
    if (!moduleId || !moduleComponents[moduleId]) {
      return (
        <Box textAlign="center" py={5}>
          <Typography variant="h5" color="text.secondary">
            Module not found
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={handleBackToLearning}
            sx={{ mt: 2 }}
          >
            Return to Learning Dashboard
          </Button>
        </Box>
      );
    }

    const ModuleComponent = moduleComponents[moduleId];
    
    if (quizMode) {
      return (
        <ModuleComponent 
          onComplete={handleQuizComplete} 
          onBack={handleBackToModule}
        />
      );
    }
    
    return (
      <ModuleComponent 
        onComplete={handleModuleComplete} 
        onProgress={handleProgress}
      />
    );
  };

  return (
    <Container maxWidth="lg">
      {/* Breadcrumb navigation */}
      <Box mt={3} mb={2}>
        <Breadcrumbs separator={<NavigateNext fontSize="small" />} aria-label="breadcrumb">
          <Link 
            color="inherit" 
            href="/dashboard" 
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Home
          </Link>
          <Link
            color="inherit"
            href="/learning"
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <School sx={{ mr: 0.5 }} fontSize="inherit" />
            Learning Center
          </Link>
          <Typography color="text.primary">
            {moduleId && moduleNames[moduleId]}
          </Typography>
        </Breadcrumbs>
      </Box>
      
      {/* Back button */}
      <Box mb={3}>
        <Button 
          startIcon={<ArrowBack />} 
          onClick={quizMode && moduleId && quizToModuleMap[moduleId] 
            ? handleBackToModule 
            : handleBackToLearning}
          variant="outlined"
        >
          {quizMode && moduleId && quizToModuleMap[moduleId]
            ? `Back to ${moduleNames[quizToModuleMap[moduleId]]}`
            : 'Back to Learning Dashboard'}
        </Button>
      </Box>
      
      {/* Module content */}
      <Box mb={6}>
        {renderModule()}
      </Box>
    </Container>
  );
};

export default ModuleViewer;