import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  Chip,
  Button,
  Divider,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Lightbulb,
  Info,
  Check,
  Refresh,
  Launch
} from '@mui/icons-material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { formatCurrency } from '../../utils/formatters';

interface Recommendation {
  symbol: string;
  action: string;
  quantity: number;
  price: number;
  confidence: number;
  strategy: string;
  reason: string;
  timestamp: string;
}

const RecommendationsCard: React.FC = () => {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const navigate = useNavigate();

  const fetchRecommendations = useCallback(async () => {
    try {
      const isInitialLoad = loading;
      if (!isInitialLoad) {
        setRefreshing(true);
      }
      
      const response = await axios.get('/api/v1/ai/recommendations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setRecommendations(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError('Failed to load AI recommendations. Please try again later.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [loading]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const handleRefresh = () => {
    fetchRecommendations();
  };

  const handleExecuteRecommendation = (recommendation: Recommendation) => {
    navigate('/trading/new', { 
      state: { 
        prefilledData: {
          symbol: recommendation.symbol,
          quantity: recommendation.quantity,
          price: recommendation.price,
          trade_type: recommendation.action
        }
      } 
    });
  };

  if (loading) {
    return (
      <Card>
        <CardContent sx={{ minHeight: 200, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <CircularProgress />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <Lightbulb color="primary" sx={{ mr: 1 }} />
            AI Recommendations
          </Typography>
          
          <Tooltip title="Refresh recommendations">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              {refreshing ? <CircularProgress size={24} /> : <Refresh />}
            </IconButton>
          </Tooltip>
        </Box>
        
        <Divider sx={{ mb: 2 }} />
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {recommendations.length > 0 ? (
          <List>
            {recommendations.map((recommendation, index) => (
              <React.Fragment key={`${recommendation.symbol}-${index}`}>
                <ListItem
                  alignItems="flex-start"
                  sx={{ 
                    flexDirection: 'column', 
                    p: 2, 
                    border: '1px solid', 
                    borderColor: 'divider', 
                    borderRadius: 1,
                    mb: 2
                  }}
                >
                  <Box sx={{ display: 'flex', width: '100%', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                      {recommendation.symbol}
                    </Typography>
                    
                    <Chip 
                      icon={recommendation.action === 'buy' ? <TrendingUp /> : <TrendingDown />}
                      label={recommendation.action.toUpperCase()}
                      color={recommendation.action === 'buy' ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  
                  <ListItemText
                    primary={
                      <Typography variant="body2">
                        {formatCurrency(recommendation.price)} per share
                        <Chip 
                          label={`${Math.round(recommendation.confidence * 100)}% confidence`}
                          size="small"
                          color={
                            recommendation.confidence > 0.7 ? 'success' : 
                            recommendation.confidence > 0.4 ? 'warning' : 
                            'error'
                          }
                          sx={{ ml: 1 }}
                        />
                      </Typography>
                    }
                    secondary={
                      <>
                        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                          <Info fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                          {recommendation.reason}
                        </Typography>
                        
                        <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
                          Strategy: {recommendation.strategy}
                        </Typography>
                        
                        <Typography variant="caption" display="block" color="text.secondary">
                          Generated: {new Date(recommendation.timestamp).toLocaleDateString()}
                        </Typography>
                      </>
                    }
                  />
                  
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', width: '100%', mt: 2 }}>
                    <Typography variant="body2">
                      Recommended quantity: <strong>{recommendation.quantity}</strong> shares
                      <Typography variant="caption" color="text.secondary" component="span" sx={{ ml: 1 }}>
                        (Total: {formatCurrency(recommendation.quantity * recommendation.price)})
                      </Typography>
                    </Typography>
                    
                    <Button
                      variant="contained"
                      color="primary"
                      size="small"
                      startIcon={<Check />}
                      onClick={() => handleExecuteRecommendation(recommendation)}
                    >
                      Execute
                    </Button>
                  </Box>
                </ListItem>
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              No recommendations available at this time.
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Our AI is analyzing market data and will provide personalized recommendations soon.
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={handleRefresh}
              sx={{ mt: 2 }}
            >
              Check Again
            </Button>
          </Box>
        )}
        
        <Button 
          fullWidth 
          variant="outlined" 
          color="primary" 
          sx={{ mt: 2 }}
          endIcon={<Launch />}
          onClick={() => navigate('/ai/recommendations')}
        >
          View All Recommendations
        </Button>
      </CardContent>
    </Card>
  );
};

export default RecommendationsCard;