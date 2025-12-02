import React, { useState, useMemo } from 'react';
import {
  Box,
  Typography,
  TextField,
  InputAdornment,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Link,
  useTheme
} from '@mui/material';
import {
  Search as SearchIcon,
  Category as CategoryIcon,
  School as SchoolIcon,
  Close as CloseIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import FeatureGate from '../subscription/FeatureGate';
import { useNavigate } from 'react-router-dom';

import { 
  glossaryTerms, 
  getTermsByCategory, 
  searchTerms, 
  GlossaryTerm 
} from '../../../utils/glossaryTerms';

interface FinancialGlossaryProps {
  onClose?: () => void;
  defaultCategory?: GlossaryTerm['category'];
  defaultSearchTerm?: string;
  allowLinking?: boolean;
  maxHeight?: string | number;
  variant?: 'dialog' | 'embedded';
  isOpen?: boolean;
}

// Map categories to readable names
const categoryLabels: Record<GlossaryTerm['category'], string> = {
  basics: 'Market Basics',
  stocks: 'Stocks',
  trading: 'Trading',
  portfolio: 'Portfolio',
  risk: 'Risk Management',
  advanced: 'Advanced'
};

const FinancialGlossary: React.FC<FinancialGlossaryProps> = ({
  onClose,
  defaultCategory = 'basics',
  defaultSearchTerm = '',
  allowLinking = true,
  maxHeight = 400,
  variant = 'embedded',
  isOpen = false
}) => {
  // We need the useNavigate hook for TypeScript setup, but not using it directly
  // @ts-ignore - Ignoring unused variable
  const _unused = useNavigate;

  const theme = useTheme();
  // State
  const [selectedCategory, setSelectedCategory] = useState<GlossaryTerm['category']>(defaultCategory);
  const [searchQuery, setSearchQuery] = useState(defaultSearchTerm);
  const [selectedTerm, setSelectedTerm] = useState<GlossaryTerm | null>(null);

  // Filter terms based on category and search query
  const filteredTerms = useMemo(() => {
    if (searchQuery.trim()) {
      return searchTerms(searchQuery);
    }
    return selectedCategory ? getTermsByCategory(selectedCategory) : glossaryTerms;
  }, [selectedCategory, searchQuery]);

  // Handle category change
  const handleCategoryChange = (_event: React.SyntheticEvent, newValue: GlossaryTerm['category']) => {
    setSelectedCategory(newValue);
    setSearchQuery(''); // Clear search when changing category
  };

  // Handle search
  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
    if (event.target.value.trim()) {
      setSelectedCategory('basics'); // Reset to first tab when searching
    }
  };

  // Handle term selection
  const handleTermSelect = (term: GlossaryTerm) => {
    setSelectedTerm(term);
  };

  // Render term detail dialog
  const renderTermDetail = () => {
    if (!selectedTerm) return null;

    return (
      <Dialog open={!!selectedTerm} onClose={() => setSelectedTerm(null)} maxWidth="sm" fullWidth>
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">{selectedTerm.term}</Typography>
            <IconButton edge="end" color="inherit" onClick={() => setSelectedTerm(null)} aria-label="close">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" paragraph>
            {selectedTerm.definition}
          </Typography>
          <Chip 
            icon={<CategoryIcon fontSize="small" />}
            label={categoryLabels[selectedTerm.category]}
            size="small"
            color="primary"
            variant="outlined"
            sx={{ mr: 1 }}
          />
          {selectedTerm.link && allowLinking && (
            <Button
              variant="outlined"
              size="small"
              startIcon={<SchoolIcon />}
              component={Link}
              href={selectedTerm.link}
              sx={{ mt: 2 }}
            >
              Learn More
            </Button>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedTerm(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    );
  };

  // Glossary content
  const glossaryContent = (
    <Box>
      {/* Search Bar */}
      <TextField
        placeholder="Search financial terms..."
        variant="outlined"
        fullWidth
        value={searchQuery}
        onChange={handleSearch}
        margin="normal"
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
          endAdornment: searchQuery ? (
            <InputAdornment position="end">
              <IconButton
                aria-label="clear search"
                onClick={() => setSearchQuery('')}
                edge="end"
                size="small"
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </InputAdornment>
          ) : null
        }}
      />

      {/* Category Tabs */}
      {!searchQuery.trim() && (
        <Tabs
          value={selectedCategory}
          onChange={handleCategoryChange}
          variant="scrollable"
          scrollButtons="auto"
          aria-label="financial terms categories"
          sx={{ mb: 2 }}
        >
          {Object.entries(categoryLabels).map(([category, label]) => (
            <Tab 
              key={category} 
              label={label} 
              value={category} 
              sx={{ textTransform: 'none' }}
            />
          ))}
        </Tabs>
      )}

      {/* Search Results or Category Terms */}
      <Paper
        variant="outlined"
        sx={{
          maxHeight,
          overflow: 'auto',
          borderRadius: 1,
          backgroundColor: theme.palette.background.paper
        }}
      >
        {searchQuery.trim() && (
          <Box sx={{ p: 2, backgroundColor: theme.palette.background.default }}>
            <Typography variant="subtitle1">
              {filteredTerms.length} {filteredTerms.length === 1 ? 'result' : 'results'} for "{searchQuery}"
            </Typography>
          </Box>
        )}
        
        {filteredTerms.length > 0 ? (
          <List dense disablePadding>
            {filteredTerms.map((term, index) => (
              <React.Fragment key={term.term}>
                <ListItem 
                  onClick={() => handleTermSelect(term)}
                  alignItems="flex-start"
                  sx={{ py: 1.5, cursor: 'pointer' }}
                >
                  <ListItemText
                    primary={
                      <Typography variant="subtitle2" fontWeight="medium">
                        {term.term}
                        {term.link && (
                          <LinkIcon fontSize="small" sx={{ ml: 0.5, verticalAlign: 'text-bottom', opacity: 0.6 }} />
                        )}
                      </Typography>
                    }
                    secondary={
                      <>
                        <Typography variant="body2" color="text.secondary" sx={{ 
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}>
                          {term.definition}
                        </Typography>
                        <Chip 
                          label={categoryLabels[term.category]}
                          size="small"
                          variant="outlined"
                          sx={{ mt: 1, fontSize: '0.7rem' }}
                        />
                      </>
                    }
                    secondaryTypographyProps={{ component: 'div' }}
                  />
                </ListItem>
                {index < filteredTerms.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))}
          </List>
        ) : (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No terms found for "{searchQuery}"
            </Typography>
            <Button 
              variant="text" 
              onClick={() => setSearchQuery('')} 
              sx={{ mt: 1 }}
            >
              Clear Search
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );

  if (variant === 'dialog') {
    return (
      <>
        <Dialog
          open={isOpen}
          onClose={onClose}
          maxWidth="md"
          fullWidth
          PaperProps={{
            sx: { maxHeight: '90vh' }
          }}
        >
          <DialogTitle>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="h6" display="flex" alignItems="center">
                <SchoolIcon sx={{ mr: 1 }} />
                Financial Glossary
              </Typography>
              {onClose && (
                <IconButton edge="end" color="inherit" onClick={onClose} aria-label="close">
                  <CloseIcon />
                </IconButton>
              )}
            </Box>
          </DialogTitle>
          <DialogContent>
            {glossaryContent}
          </DialogContent>
          <DialogActions>
            <Button onClick={onClose}>Close</Button>
          </DialogActions>
        </Dialog>
        {renderTermDetail()}
      </>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={2}>
        <SchoolIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6">Financial Glossary</Typography>
      </Box>
      {glossaryContent}
      {renderTermDetail()}
    </Box>
  );
};

// Wrap the glossary component with feature gate to only show advanced terms for premium users
const GatedFinancialGlossary: React.FC<FinancialGlossaryProps> = (props) => {
  const navigate = useNavigate();
  
  return (
    <FeatureGate
      feature="advanced_financial_education"
      fallback={
        <Box>
          {/* Show basic glossary with limited categories */}
          <Box display="flex" alignItems="center" mb={2}>
            <SchoolIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">Financial Glossary</Typography>
          </Box>
          <Paper
            variant="outlined"
            sx={{
              p: 3,
              textAlign: 'center',
              backgroundColor: 'background.paper'
            }}
          >
            <Typography variant="body1" paragraph>
              Access our comprehensive financial glossary with detailed explanations, examples, and advanced trading concepts.
            </Typography>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/pricing')}
            >
              Upgrade to Premium
            </Button>
          </Paper>
        </Box>
      }
    >
      <FinancialGlossary {...props} />
    </FeatureGate>
  );
};

export default GatedFinancialGlossary;