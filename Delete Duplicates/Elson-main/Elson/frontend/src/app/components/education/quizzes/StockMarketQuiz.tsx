import React, { useState, useEffect } from 'react';
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
  Card,
  CardContent,
  LinearProgress,
  Grid,
  Chip,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  useTheme
} from '@mui/material';
import {
  School,
  CheckCircle,
  Cancel,
  EmojiEvents,
  Refresh,
  NavigateNext,
  ArrowBack
} from '@mui/icons-material';
import EducationalTooltip from '../../common/EducationalTooltip';

// Define quiz questions
const questions = [
  {
    id: 1,
    question: "What is the stock market?",
    options: [
      "A physical location where stocks are kept in vaults",
      "A collection of markets where stocks are bought and sold",
      "A government agency that regulates financial institutions",
      "A type of investment fund managed by banks"
    ],
    correctAnswer: 1,
    explanation: "The stock market is a collection of markets where investors buy and sell shares of publicly-traded companies through exchanges such as the NYSE or Nasdaq."
  },
  {
    id: 2,
    question: "Why do companies typically go public through an IPO?",
    options: [
      "To reduce their tax burden",
      "To avoid government regulations",
      "To raise capital for expansion and growth",
      "To reduce the number of shareholders"
    ],
    correctAnswer: 2,
    explanation: "Companies go public primarily to raise capital for expansion, pay off debt, fund research and development, or allow early investors to cash out their investments."
  },
  {
    id: 3,
    question: "What determines stock prices in the market?",
    options: [
      "Stock prices are set exclusively by company executives",
      "Stock prices are determined by a government committee",
      "Stock prices are determined by supply and demand in the market",
      "Stock prices are always equal to the company's book value"
    ],
    correctAnswer: 2,
    explanation: "Stock prices are determined by supply and demand in the market. When more people want to buy a stock than sell it, the price goes up. When more people want to sell than buy, the price goes down."
  },
  {
    id: 4,
    question: "What characterizes a 'bull market'?",
    options: [
      "Falling stock prices and pessimistic investors",
      "Rising stock prices and optimistic investors",
      "Stable stock prices with little movement",
      "High trading volume but no price changes"
    ],
    correctAnswer: 1,
    explanation: "A bull market is characterized by rising stock prices and investor optimism about future market performance. It's typically associated with economic growth and low unemployment."
  },
  {
    id: 5,
    question: "What role do brokers play in the stock market?",
    options: [
      "They set the prices of stocks",
      "They own the majority of shares in the market",
      "They act as intermediaries who execute trades for clients",
      "They regulate the stock exchanges"
    ],
    correctAnswer: 2,
    explanation: "Brokers act as intermediaries who execute buy and sell orders on behalf of investors. They provide the connection between investors and the stock exchange."
  }
];

interface StockMarketQuizProps {
  onComplete?: (score: number) => void;
  onBack?: () => void;
  standalone?: boolean;
}

const StockMarketQuiz: React.FC<StockMarketQuizProps> = ({ 
  onComplete, 
  onBack,
  standalone = true
}) => {
  const theme = useTheme();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<{ [key: number]: number }>({});
  const [showResults, setShowResults] = useState(false);
  const [score, setScore] = useState(0);
  const [showExplanation, setShowExplanation] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [certificateOpen, setCertificateOpen] = useState(false);

  // Handle answer selection
  const handleAnswerSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const answerIndex = parseInt(event.target.value);
    const newSelectedAnswers = { ...selectedAnswers };
    newSelectedAnswers[currentQuestion] = answerIndex;
    setSelectedAnswers(newSelectedAnswers);
  };

  // Move to next question
  const handleNextQuestion = () => {
    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
      setShowExplanation(false);
    } else {
      calculateScore();
      setShowResults(true);
    }
  };

  // Move to previous question
  const handlePreviousQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
      setShowExplanation(false);
    }
  };

  // Check answer and show explanation
  const handleCheckAnswer = () => {
    setShowExplanation(true);
  };

  // Calculate final score
  const calculateScore = () => {
    let correctAnswers = 0;
    questions.forEach((question, index) => {
      if (selectedAnswers[index] === question.correctAnswer) {
        correctAnswers++;
      }
    });
    setScore(correctAnswers);
    setCompleted(correctAnswers >= 4); // Pass threshold is 4/5 correct
  };

  // Handle completion of quiz
  const handleComplete = () => {
    if (onComplete) {
      onComplete(score);
    }
    if (score >= 4) {
      setCertificateOpen(true);
    }
  };

  // Restart quiz
  const handleRestartQuiz = () => {
    setCurrentQuestion(0);
    setSelectedAnswers({});
    setShowResults(false);
    setScore(0);
    setShowExplanation(false);
    setCompleted(false);
  };

  // Calculate progress percentage
  const progressPercentage = ((currentQuestion + 1) / questions.length) * 100;

  // Current question object
  const currentQuestionData = questions[currentQuestion];
  
  // Check if current question is answered
  const isCurrentQuestionAnswered = selectedAnswers[currentQuestion] !== undefined;
  
  // Check if answer is correct
  const isCurrentAnswerCorrect = 
    isCurrentQuestionAnswered && 
    selectedAnswers[currentQuestion] === currentQuestionData.correctAnswer;

  return (
    <Box>
      {/* Quiz Header */}
      {standalone && (
        <Box mb={4}>
          <Box display="flex" alignItems="center">
            {onBack && (
              <Button 
                startIcon={<ArrowBack />} 
                onClick={onBack}
                sx={{ mr: 2 }}
              >
                Back to Module
              </Button>
            )}
            <Typography variant="h4" component="h1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
              <School sx={{ mr: 1.5, color: 'primary.main' }} />
              Stock Market Quiz
            </Typography>
          </Box>
          <Typography variant="body1" color="text.secondary" paragraph>
            Test your knowledge about the stock market basics. You'll need to answer 4 out of 5 questions correctly to complete this module.
          </Typography>
        </Box>
      )}

      {/* Progress Indicator */}
      {!showResults && (
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Question {currentQuestion + 1} of {questions.length}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {Math.round(progressPercentage)}% complete
            </Typography>
          </Box>
          <LinearProgress 
            variant="determinate" 
            value={progressPercentage} 
            sx={{ height: 8, borderRadius: 4 }} 
          />
        </Box>
      )}

      {/* Quiz Questions */}
      {!showResults ? (
        <Paper 
          elevation={0} 
          variant="outlined" 
          sx={{ p: 3, borderRadius: 2, mb: 3 }}
        >
          <Typography variant="h6" gutterBottom>
            {currentQuestionData.question}
          </Typography>
          
          <FormControl component="fieldset" sx={{ width: '100%', mt: 2 }}>
            <RadioGroup 
              value={selectedAnswers[currentQuestion] !== undefined ? selectedAnswers[currentQuestion].toString() : ''} 
              onChange={handleAnswerSelect}
            >
              {currentQuestionData.options.map((option, index) => (
                <FormControlLabel 
                  key={index}
                  value={index.toString()} 
                  control={<Radio />} 
                  label={option}
                  disabled={showExplanation}
                  sx={{
                    p: 1,
                    borderRadius: 1,
                    mb: 1,
                    ...(showExplanation && index === currentQuestionData.correctAnswer && {
                      bgcolor: 'success.light',
                      color: 'success.contrastText',
                    }),
                    ...(showExplanation && 
                      selectedAnswers[currentQuestion] === index && 
                      index !== currentQuestionData.correctAnswer && {
                        bgcolor: 'error.light',
                        color: 'error.contrastText',
                    }),
                  }}
                />
              ))}
            </RadioGroup>
          </FormControl>
          
          {/* Explanation area */}
          {showExplanation && (
            <Box sx={{ mt: 3, p: 2, bgcolor: 'background.paper', borderRadius: 2, border: '1px solid', borderColor: 'divider' }}>
              <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                {isCurrentAnswerCorrect ? (
                  <>
                    <CheckCircle color="success" sx={{ mr: 1 }} />
                    <span>Correct!</span>
                  </>
                ) : (
                  <>
                    <Cancel color="error" sx={{ mr: 1 }} />
                    <span>Incorrect</span>
                  </>
                )}
              </Typography>
              <Typography variant="body2">
                {currentQuestionData.explanation}
              </Typography>
            </Box>
          )}
        </Paper>
      ) : (
        // Results section
        <Paper 
          elevation={0} 
          variant="outlined" 
          sx={{ p: 3, borderRadius: 2, mb: 3 }}
        >
          <Box sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <EmojiEvents color={score >= 4 ? "primary" : "action"} sx={{ mr: 1.5, fontSize: 32 }} />
              Quiz Results
            </Typography>
            
            <Typography variant="h4" sx={{ my: 2, color: score >= 4 ? 'success.main' : 'text.primary' }}>
              {score} / {questions.length} correct
            </Typography>
            
            {score >= 4 ? (
              <Alert severity="success" sx={{ mb: 3, mx: 'auto', maxWidth: 500 }}>
                <AlertTitle>Congratulations!</AlertTitle>
                You've passed the quiz and completed this module. You can now proceed to the next module in your learning journey.
              </Alert>
            ) : (
              <Alert severity="info" sx={{ mb: 3, mx: 'auto', maxWidth: 500 }}>
                <AlertTitle>Almost there!</AlertTitle>
                You need at least 4 correct answers to pass. Review the content and try again!
              </Alert>
            )}
            
            <Box sx={{ mt: 4 }}>
              <Button 
                variant="outlined" 
                startIcon={<Refresh />} 
                onClick={handleRestartQuiz}
                sx={{ mr: 2 }}
              >
                Try Again
              </Button>
              
              {score >= 4 && (
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={handleComplete}
                  startIcon={<CheckCircle />}
                >
                  Complete Module
                </Button>
              )}
              
              {score < 4 && onBack && (
                <Button 
                  variant="contained" 
                  color="primary" 
                  onClick={onBack}
                  startIcon={<ArrowBack />}
                >
                  Review Module
                </Button>
              )}
            </Box>
          </Box>
          
          <Divider sx={{ my: 3 }} />
          
          {/* Detailed results */}
          <Typography variant="h6" gutterBottom>Question Summary</Typography>
          
          <Grid container spacing={2}>
            {questions.map((question, index) => {
              const isCorrect = selectedAnswers[index] === question.correctAnswer;
              return (
                <Grid item xs={12} key={question.id}>
                  <Card variant="outlined" sx={{ 
                    mb: 2, 
                    borderColor: isCorrect ? 'success.main' : 'error.main',
                    bgcolor: isCorrect ? theme.palette.success.light + '15' : theme.palette.error.light + '15'
                  }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                        <Typography variant="subtitle1">
                          Question {index + 1}
                        </Typography>
                        <Chip 
                          icon={isCorrect ? <CheckCircle fontSize="small" /> : <Cancel fontSize="small" />}
                          label={isCorrect ? "Correct" : "Incorrect"}
                          color={isCorrect ? "success" : "error"}
                          size="small"
                        />
                      </Box>
                      <Typography variant="body2" paragraph>
                        {question.question}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        <strong>Your answer:</strong> {question.options[selectedAnswers[index] || 0]}
                      </Typography>
                      {!isCorrect && (
                        <Typography variant="body2" color="success.main" sx={{ mt: 1 }}>
                          <strong>Correct answer:</strong> {question.options[question.correctAnswer]}
                        </Typography>
                      )}
                      <Typography variant="body2" sx={{ mt: 2, fontSize: '0.875rem', fontStyle: 'italic' }}>
                        {question.explanation}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </Paper>
      )}
      
      {/* Navigation Buttons */}
      {!showResults && (
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
          <Button
            onClick={handlePreviousQuestion}
            disabled={currentQuestion === 0}
            variant="outlined"
          >
            Previous
          </Button>
          
          <Box>
            {!showExplanation && (
              <Button
                variant="outlined"
                color="primary"
                onClick={handleCheckAnswer}
                disabled={!isCurrentQuestionAnswered}
                sx={{ mr: 2 }}
              >
                Check Answer
              </Button>
            )}
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleNextQuestion}
              disabled={!isCurrentQuestionAnswered}
              endIcon={currentQuestion < questions.length - 1 ? <NavigateNext /> : undefined}
            >
              {currentQuestion < questions.length - 1 ? 'Next Question' : 'See Results'}
            </Button>
          </Box>
        </Box>
      )}
      
      {/* Completion Certificate Dialog */}
      <Dialog 
        open={certificateOpen} 
        onClose={() => setCertificateOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{ textAlign: 'center', pt: 3 }}>
          <EmojiEvents color="primary" sx={{ fontSize: 60, mb: 1 }} />
          <Typography variant="h5">Certificate of Completion</Typography>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ 
            border: '2px solid', 
            borderColor: 'primary.main', 
            p: 3, 
            textAlign: 'center',
            position: 'relative',
            background: `linear-gradient(45deg, ${theme.palette.primary.light}1A 0%, ${theme.palette.primary.main}0D 100%)`,
            borderRadius: 2,
            overflow: 'hidden'
          }}>
            <Typography variant="subtitle1" gutterBottom>
              This certifies that
            </Typography>
            <Typography variant="h6" sx={{ my: 2, fontStyle: 'italic' }}>
              Elson Learner
            </Typography>
            <Typography variant="body1" paragraph>
              has successfully completed the
            </Typography>
            <Typography variant="h5" sx={{ my: 2, color: 'primary.main', fontWeight: 'bold' }}>
              Introduction to the Stock Market
            </Typography>
            <Typography variant="body2" sx={{ mb: 3 }}>
              with a score of {score}/{questions.length} ({Math.round((score/questions.length)*100)}%)
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {new Date().toLocaleDateString('en-US', { 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ justifyContent: 'center', pb: 3 }}>
          <Button onClick={() => setCertificateOpen(false)} variant="outlined">
            Close
          </Button>
          <Button variant="contained" color="primary" onClick={() => setCertificateOpen(false)}>
            Continue Learning
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default StockMarketQuiz;