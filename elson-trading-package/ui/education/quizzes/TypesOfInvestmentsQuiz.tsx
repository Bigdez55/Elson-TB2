import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Radio,
  RadioGroup,
  FormControlLabel,
  FormControl,
  FormLabel,
  Divider,
  Alert,
  LinearProgress,
  Card,
  CardContent,
  useTheme,
  Grid,
  Chip
} from '@mui/material';
import {
  Check,
  Close,
  EmojiEvents,
  School,
  Refresh
} from '@mui/icons-material';

interface TypesOfInvestmentsQuizProps {
  onComplete?: (score: number) => void;
  onBack?: () => void;
}

// Define quiz questions
const quizQuestions = [
  {
    question: "Which investment type represents ownership in a company?",
    options: [
      "Bonds",
      "Stocks",
      "Certificates of Deposit",
      "Treasury Bills"
    ],
    correctAnswer: "Stocks",
    explanation: "Stocks represent partial ownership (equity) in a company. When you buy a stock, you own a small piece of that business and may receive dividends and voting rights."
  },
  {
    question: "Which investment is generally considered the lowest risk?",
    options: [
      "Individual stocks",
      "Cryptocurrencies",
      "Certificates of Deposit (CDs)",
      "Real estate properties"
    ],
    correctAnswer: "Certificates of Deposit (CDs)",
    explanation: "CDs are time deposits at banks that offer guaranteed returns and are insured by the FDIC up to $250,000, making them among the lowest-risk investments available."
  },
  {
    question: "What is the main advantage of ETFs (Exchange-Traded Funds)?",
    options: [
      "Guaranteed returns",
      "No risk of loss",
      "Instant diversification",
      "Access to bank loans"
    ],
    correctAnswer: "Instant diversification",
    explanation: "ETFs contain many different securities in a single investment, providing instant diversification and reducing the risk compared to buying individual stocks or bonds."
  },
  {
    question: "Which statement about bonds is TRUE?",
    options: [
      "Bonds represent ownership in a company",
      "Bonds typically have higher returns than stocks over the long term",
      "Bonds are loans to companies or governments that pay interest",
      "Bonds have no risk and guarantee high returns"
    ],
    correctAnswer: "Bonds are loans to companies or governments that pay interest",
    explanation: "When you buy a bond, you're lending money to the issuer (a company or government) in exchange for regular interest payments and the return of principal at maturity."
  },
  {
    question: "Which investment type would be MOST suitable for a young investor with a long time horizon and higher risk tolerance?",
    options: [
      "Certificate of Deposit (CD)",
      "A portfolio primarily of stocks or stock ETFs",
      "Treasury bonds",
      "Money market account"
    ],
    correctAnswer: "A portfolio primarily of stocks or stock ETFs",
    explanation: "Young investors with long time horizons can generally take more risk since they have time to recover from market downturns. Stocks typically offer higher long-term returns despite higher volatility."
  },
  {
    question: "What is a key difference between mutual funds and ETFs?",
    options: [
      "ETFs can only hold stocks, while mutual funds can hold bonds",
      "Mutual funds trade throughout the day, while ETFs only trade once per day",
      "ETFs trade throughout the day, while mutual funds are priced once per day",
      "Mutual funds are always cheaper than ETFs"
    ],
    correctAnswer: "ETFs trade throughout the day, while mutual funds are priced once per day",
    explanation: "ETFs trade like stocks and can be bought and sold throughout the trading day at market prices. Mutual funds trade only once per day at the net asset value (NAV) calculated after market close."
  },
  {
    question: "For which age group would REITs (Real Estate Investment Trusts) typically be considered appropriate?",
    options: [
      "Only children under 13",
      "Only adults over 60",
      "Teens and adults",
      "Only professional investors"
    ],
    correctAnswer: "Teens and adults",
    explanation: "REITs are appropriate for teens and adults as they provide exposure to real estate without requiring the large capital and management responsibilities of direct property ownership."
  },
  {
    question: "Which of these is an important factor in creating a well-balanced portfolio?",
    options: [
      "Putting all your money in one high-performing stock",
      "Only investing in the safest assets with no risk",
      "Diversification across different investment types",
      "Changing your entire investment strategy daily"
    ],
    correctAnswer: "Diversification across different investment types",
    explanation: "Diversification across different types of investments (stocks, bonds, etc.) with varying risk levels helps balance risk and potential returns, making your portfolio more resilient."
  },
  {
    question: "What does the risk level of an investment generally tell you about its potential return?",
    options: [
      "Lower risk generally means higher potential returns",
      "Risk and potential returns are usually unrelated",
      "Higher risk generally means higher potential returns",
      "All investments have the same risk-return profile"
    ],
    correctAnswer: "Higher risk generally means higher potential returns",
    explanation: "In finance, there's typically a risk-return tradeoff: investments with higher risk generally offer the potential for higher returns to compensate investors for taking on that additional risk."
  },
  {
    question: "Which of these investment types would typically be best for a short-term goal (1-2 years)?",
    options: [
      "Growth stocks",
      "Cryptocurrency",
      "Certificates of Deposit or Money Market funds",
      "Real estate property"
    ],
    correctAnswer: "Certificates of Deposit or Money Market funds",
    explanation: "For short-term goals (1-2 years), you want to preserve capital and maintain liquidity. CDs and Money Market funds offer safety, guaranteed returns, and accessibility when you need the money."
  }
];

const TypesOfInvestmentsQuiz: React.FC<TypesOfInvestmentsQuizProps> = ({ onComplete, onBack }) => {
  const theme = useTheme();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [answers, setAnswers] = useState<{[key: number]: string}>({});
  const [showExplanation, setShowExplanation] = useState(false);
  const [quizComplete, setQuizComplete] = useState(false);
  const [score, setScore] = useState(0);

  // Handler for selecting an answer
  const handleAnswerSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedAnswer(event.target.value);
  };

  // Handle checking answer
  const handleCheckAnswer = () => {
    if (!selectedAnswer) return;
    
    // Record the answer
    const newAnswers = { ...answers };
    newAnswers[currentQuestion] = selectedAnswer;
    setAnswers(newAnswers);
    
    // Show explanation
    setShowExplanation(true);
  };

  // Handle moving to next question
  const handleNextQuestion = () => {
    // Calculate if the answer was correct
    if (selectedAnswer === quizQuestions[currentQuestion].correctAnswer) {
      setScore(score + 1);
    }
    
    // Reset for next question
    setSelectedAnswer(null);
    setShowExplanation(false);
    
    // If we're at the last question, finish the quiz
    if (currentQuestion === quizQuestions.length - 1) {
      setQuizComplete(true);
    } else {
      // Otherwise go to next question
      setCurrentQuestion(currentQuestion + 1);
    }
  };

  // Handle restart quiz
  const handleRestartQuiz = () => {
    setCurrentQuestion(0);
    setSelectedAnswer(null);
    setAnswers({});
    setShowExplanation(false);
    setQuizComplete(false);
    setScore(0);
  };

  // Render the current question
  const renderQuestion = () => {
    const question = quizQuestions[currentQuestion];
    const isAnswered = showExplanation;
    const isCorrect = selectedAnswer === question.correctAnswer;
    
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
        {/* Progress indicator */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Question {currentQuestion + 1} of {quizQuestions.length}
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={(currentQuestion / quizQuestions.length) * 100} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        </Box>
        
        {/* Question */}
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 'medium', color: 'primary.main' }}>
          {question.question}
        </Typography>
        
        {/* Answer options */}
        <FormControl component="fieldset" sx={{ width: '100%', my: 2 }}>
          <RadioGroup value={selectedAnswer || ''} onChange={handleAnswerSelect}>
            {question.options.map((option, index) => (
              <FormControlLabel
                key={index}
                value={option}
                control={<Radio />}
                label={option}
                disabled={isAnswered}
                sx={{
                  p: 1, 
                  borderRadius: 1,
                  ...(isAnswered && option === question.correctAnswer && {
                    bgcolor: 'success.light',
                    color: 'success.contrastText',
                  }),
                  ...(isAnswered && selectedAnswer === option && option !== question.correctAnswer && {
                    bgcolor: 'error.light',
                    color: 'error.contrastText',
                  })
                }}
              />
            ))}
          </RadioGroup>
        </FormControl>
        
        {/* Explanation (shown after answering) */}
        {showExplanation && (
          <Alert severity={isCorrect ? "success" : "error"} sx={{ my: 2 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
              {isCorrect ? "Correct!" : "Incorrect"}
            </Typography>
            <Typography variant="body1">
              {question.explanation}
            </Typography>
          </Alert>
        )}
        
        {/* Action buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 3 }}>
          <Button onClick={onBack}>
            Back to Module
          </Button>
          
          {!showExplanation ? (
            <Button 
              variant="contained" 
              color="primary"
              onClick={handleCheckAnswer}
              disabled={!selectedAnswer}
            >
              Check Answer
            </Button>
          ) : (
            <Button 
              variant="contained" 
              color="primary"
              onClick={handleNextQuestion}
            >
              {currentQuestion === quizQuestions.length - 1 ? 'See Results' : 'Next Question'}
            </Button>
          )}
        </Box>
      </Paper>
    );
  };

  // Render the results
  const renderResults = () => {
    const percentage = (score / quizQuestions.length) * 100;
    const passed = percentage >= 70;
    
    return (
      <Paper elevation={1} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <EmojiEvents fontSize="large" color={passed ? "primary" : "action"} sx={{ fontSize: 60, mb: 2 }} />
          <Typography variant="h4" gutterBottom color={passed ? "primary" : "text.secondary"}>
            Quiz Results
          </Typography>
          
          <Typography variant="h5" sx={{ fontWeight: 'bold', my: 2 }}>
            You scored {score} out of {quizQuestions.length} ({percentage.toFixed(0)}%)
          </Typography>
          
          <Chip
            label={passed ? "Passed!" : "Try Again"}
            color={passed ? "success" : "warning"}
            icon={passed ? <Check /> : <Refresh />}
            sx={{ fontWeight: 'bold', fontSize: '1rem', py: 2, px: 1 }}
          />
        </Box>
        
        <Divider sx={{ my: 3 }} />
        
        <Typography variant="h6" gutterBottom>
          Performance Summary
        </Typography>
        
        <LinearProgress 
          variant="determinate" 
          value={percentage} 
          color={passed ? "success" : "warning"}
          sx={{ height: 16, borderRadius: 4, mb: 3 }} 
        />
        
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ textAlign: 'center', bgcolor: 'success.light' }}>
              <CardContent>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  {score}
                </Typography>
                <Typography variant="body2">Correct Answers</Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ textAlign: 'center', bgcolor: 'error.light' }}>
              <CardContent>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  {quizQuestions.length - score}
                </Typography>
                <Typography variant="body2">Incorrect Answers</Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Card variant="outlined" sx={{ textAlign: 'center', bgcolor: 'primary.light' }}>
              <CardContent>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  {percentage.toFixed(0)}%
                </Typography>
                <Typography variant="body2">Overall Score</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
        
        {passed ? (
          <Alert severity="success" sx={{ my: 3 }}>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              Congratulations! You've demonstrated a good understanding of different investment types.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              You're now ready to explore the next module or try building your own portfolio.
            </Typography>
          </Alert>
        ) : (
          <Alert severity="info" sx={{ my: 3 }}>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              You might want to review the module content again to strengthen your understanding.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Don't worry - learning about investments takes time. Try the quiz again after reviewing.
            </Typography>
          </Alert>
        )}
        
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
          <Button onClick={handleRestartQuiz} startIcon={<Refresh />}>
            Restart Quiz
          </Button>
          
          <Button 
            variant="contained" 
            color="primary" 
            onClick={() => {
              if (onComplete) onComplete(score);
            }}
            startIcon={<School />}
          >
            Back to Learning
          </Button>
        </Box>
      </Paper>
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom color="primary" sx={{ mb: 3, fontWeight: 'bold' }}>
        Types of Investments Quiz
      </Typography>
      
      {quizComplete ? renderResults() : renderQuestion()}
    </Box>
  );
};

export default TypesOfInvestmentsQuiz;