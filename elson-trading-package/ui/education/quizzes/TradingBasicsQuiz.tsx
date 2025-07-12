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
  Refresh,
  TrendingUp
} from '@mui/icons-material';

interface TradingBasicsQuizProps {
  onComplete?: (score: number) => void;
  onBack?: () => void;
}

// Define quiz questions
const quizQuestions = [
  {
    question: "What is the main difference between market orders and limit orders?",
    options: [
      "Market orders are only available during market hours, while limit orders can be placed anytime",
      "Market orders execute immediately at the best available price, while limit orders execute at a specified price or better",
      "Market orders are for buying stocks, while limit orders are for selling stocks",
      "Market orders are free, while limit orders have fees"
    ],
    correctAnswer: "Market orders execute immediately at the best available price, while limit orders execute at a specified price or better",
    explanation: "Market orders prioritize immediate execution at the current market price, while limit orders prioritize price control by only executing at your specified price or better."
  },
  {
    question: "What is the bid-ask spread?",
    options: [
      "The difference between a stock's highest and lowest price for the day",
      "The commission charged by a broker for buying and selling stocks",
      "The difference between the price buyers are willing to pay and the price sellers are willing to accept",
      "The difference between a stock's current price and its 52-week high"
    ],
    correctAnswer: "The difference between the price buyers are willing to pay and the price sellers are willing to accept",
    explanation: "The bid-ask spread is the difference between the highest price a buyer is willing to pay (bid) and the lowest price a seller is willing to accept (ask). This spread is an implicit cost of trading."
  },
  {
    question: "Which of the following is NOT a common factor affecting stock prices?",
    options: [
      "Company earnings reports",
      "Supply and demand for the stock",
      "Market sentiment and investor psychology",
      "The color of the company's logo"
    ],
    correctAnswer: "The color of the company's logo",
    explanation: "Stock prices are primarily affected by factors like company performance (earnings), supply and demand dynamics, market conditions, economic data, and investor sentiment — not cosmetic factors like logo colors."
  },
  {
    question: "What is the key difference between trading and investing?",
    options: [
      "Trading is illegal, investing is legal",
      "Trading focuses on short-term price movements, while investing focuses on long-term growth",
      "Trading is only for professionals, while investing is for individual investors",
      "Trading requires less money than investing"
    ],
    correctAnswer: "Trading focuses on short-term price movements, while investing focuses on long-term growth",
    explanation: "Trading typically involves shorter time frames (days, weeks, months) and focuses on capitalizing on market price movements, while investing involves longer holding periods (years, decades) with a focus on gradual wealth building."
  },
  {
    question: "Which risk management technique involves spreading your investments across different assets, sectors, and geographies?",
    options: [
      "Leveraging",
      "Diversification",
      "Short selling",
      "Day trading"
    ],
    correctAnswer: "Diversification",
    explanation: "Diversification is the practice of spreading investments across different assets, sectors, and geographies to reduce the impact of any single investment performing poorly, thereby reducing overall portfolio risk."
  },
  {
    question: "What is position sizing in trading?",
    options: [
      "Adjusting the size of your computer screen for better trading visibility",
      "Determining how much of your portfolio to allocate to each investment",
      "Analyzing how large a company is before investing",
      "Deciding how many trading screens to use"
    ],
    correctAnswer: "Determining how much of your portfolio to allocate to each investment",
    explanation: "Position sizing refers to determining the appropriate amount of capital to allocate to each investment, based on risk considerations, portfolio strategy, and money management principles."
  },
  {
    question: "Which of the following is an implicit cost of trading?",
    options: [
      "Broker commissions",
      "Account maintenance fees",
      "The bid-ask spread",
      "Subscription fees for trading platforms"
    ],
    correctAnswer: "The bid-ask spread",
    explanation: "The bid-ask spread is an implicit cost of trading that often goes unnoticed. It represents the difference between the buying price and the selling price of a security, and can significantly impact returns, especially for frequent traders."
  },
  {
    question: "When would a limit order be more appropriate than a market order?",
    options: [
      "When immediate execution is more important than the exact price",
      "When you're restricted to trading during market hours",
      "When you want control over the execution price and are willing to wait",
      "When trading highly liquid, blue-chip stocks"
    ],
    correctAnswer: "When you want control over the execution price and are willing to wait",
    explanation: "Limit orders are more appropriate when the execution price is more important than immediate execution. They're useful when you have a specific price target and are willing to wait for the market to reach that price."
  },
  {
    question: "Why are trading costs important to consider?",
    options: [
      "They are tax-deductible",
      "They can significantly reduce returns, especially for frequent traders",
      "They indicate the quality of the stock being traded",
      "They are always a fixed percentage of the trade value"
    ],
    correctAnswer: "They can significantly reduce returns, especially for frequent traders",
    explanation: "Trading costs, including commissions, spreads, and other fees, directly reduce investment returns. For active traders making many transactions, these costs can substantially impact overall performance."
  },
  {
    question: "Which of the following statements about investing is TRUE?",
    options: [
      "Investing guarantees returns if you hold for long enough",
      "Investing always outperforms trading in the short term",
      "Investing typically involves lower stress and transaction costs than active trading",
      "Investing requires more daily time commitment than trading"
    ],
    correctAnswer: "Investing typically involves lower stress and transaction costs than active trading",
    explanation: "Investing typically involves lower stress levels (less daily monitoring), fewer transactions leading to lower costs, and a focus on long-term growth rather than short-term market movements."
  }
];

const TradingBasicsQuiz: React.FC<TradingBasicsQuizProps> = ({ onComplete, onBack }) => {
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
              Congratulations! You've demonstrated a good understanding of trading basics.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              You're now ready to try our paper trading simulator or build your investment portfolio.
            </Typography>
          </Alert>
        ) : (
          <Alert severity="info" sx={{ my: 3 }}>
            <Typography variant="body1" sx={{ fontWeight: 'bold' }}>
              You might want to review the Trading Basics module again to strengthen your understanding.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              Focus particularly on understanding order types, risk management, and trading costs.
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
      <Typography variant="h4" gutterBottom color="primary" sx={{ mb: 3, fontWeight: 'bold', display: 'flex', alignItems: 'center' }}>
        <TrendingUp sx={{ mr: 2 }} /> Trading Basics Quiz
      </Typography>
      
      {quizComplete ? renderResults() : renderQuestion()}
    </Box>
  );
};

export default TradingBasicsQuiz;