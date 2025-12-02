import React from 'react';
import { 
  List, 
  ListItem, 
  ListItemText, 
  ListItemAvatar, 
  Avatar, 
  ListItemSecondaryAction, 
  IconButton, 
  Tooltip, 
  Chip,
  Typography,
  useTheme,
  useMediaQuery,
  Box,
  Button
} from '@mui/material';
import { AccountCircle, Visibility, School } from '@mui/icons-material';
import { formatDate } from '../../utils/formatters';
import ResponsiveContainer from '../common/ResponsiveContainer';

interface Minor {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  birthdate: string;
  account_id: number;
}

interface MinorAccountsListProps {
  minors: Minor[];
  onViewPortfolio: (minorId: number) => void;
}

const MinorAccountsList: React.FC<MinorAccountsListProps> = ({ minors, onViewPortfolio }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Calculate age from birthdate
  const calculateAge = (birthdate: string): number => {
    const today = new Date();
    const birthdateObj = new Date(birthdate);
    let age = today.getFullYear() - birthdateObj.getFullYear();
    const month = today.getMonth() - birthdateObj.getMonth();
    
    if (month < 0 || (month === 0 && today.getDate() < birthdateObj.getDate())) {
      age--;
    }
    
    return age;
  };

  return (
    <List sx={{ p: 0, '& .MuiListItem-root:hover': { bgcolor: 'rgba(0, 0, 0, 0.04)' } }}>
      {minors.map((minor) => (
        <ListItem 
          key={minor.id} 
          divider 
          component={ResponsiveContainer}
          mobileClasses="flex flex-col items-start py-1.5 px-1"
          desktopClasses="flex flex-row items-center py-1 px-2"
          className="transition-colors duration-200 ease-in-out"
        >
          <ResponsiveContainer
            mobileClasses="flex w-full items-center mb-1"
            desktopClasses="flex w-full items-center mb-0"
          >
            <ListItemAvatar>
              <Avatar sx={{ width: { xs: 32, sm: 40 }, height: { xs: 32, sm: 40 } }}>
                <AccountCircle fontSize={isMobile ? "small" : "medium"} />
              </Avatar>
            </ListItemAvatar>
            
            <ListItemText
              primary={
                <ResponsiveContainer
                  mobileClasses="flex flex-col items-start gap-0.5"
                  desktopClasses="flex flex-row items-center gap-1"
                >
                  <Typography 
                    variant="subtitle1"
                    sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }}
                  >
                    {`${minor.first_name} ${minor.last_name}`}
                  </Typography>
                  <Chip 
                    size="small" 
                    label={`${calculateAge(minor.birthdate)} years old`} 
                    color="primary" 
                    variant="outlined"
                    icon={<School fontSize="small" />} 
                    sx={{ 
                      height: { xs: 20, sm: 24 },
                      '& .MuiChip-label': { 
                        fontSize: { xs: '0.65rem', sm: '0.75rem' },
                        px: { xs: 0.5, sm: 0.8 }
                      },
                      '& .MuiChip-icon': {
                        fontSize: { xs: '0.75rem', sm: '1rem' }
                      }
                    }}
                  />
                </ResponsiveContainer>
              }
              secondary={
                <Box sx={{ mt: { xs: 0.5, sm: 0 } }}>
                  <Typography 
                    variant="body2" 
                    component="span" 
                    display="block"
                    sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
                  >
                    {minor.email}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    component="span" 
                    display="block" 
                    color="text.secondary"
                    sx={{ 
                      fontSize: { xs: '0.7rem', sm: '0.8rem' },
                      display: { xs: 'none', sm: 'block' }
                    }}
                  >
                    Birthdate: {formatDate(minor.birthdate)}
                  </Typography>
                  <Typography 
                    variant="body2" 
                    component="span" 
                    display="block" 
                    color="text.secondary"
                    sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem' } }}
                  >
                    Account ID: {minor.account_id}
                  </Typography>
                </Box>
              }
              primaryTypographyProps={{ 
                sx: { mb: { xs: 0, sm: 0.5 } } 
              }}
            />
          </ResponsiveContainer>
          
          <ResponsiveContainer
            mobileClasses="w-full flex justify-end"
            desktopClasses="w-full flex justify-end"
          >
            <Button
              variant="outlined"
              size={isMobile ? "small" : "medium"}
              startIcon={<Visibility />}
              onClick={() => onViewPortfolio(minor.id)}
              sx={{ 
                display: { xs: 'flex', sm: 'none' }, 
                fontSize: { xs: '0.75rem', sm: '0.875rem' }
              }}
            >
              View Portfolio
            </Button>
            
            <Tooltip title="View Portfolio">
              <IconButton 
                edge="end" 
                aria-label="view" 
                onClick={() => onViewPortfolio(minor.id)}
                color="primary"
                size={isMobile ? "small" : "medium"}
                sx={{ display: { xs: 'none', sm: 'inline-flex' } }}
              >
                <Visibility fontSize={isMobile ? "small" : "medium"} />
              </IconButton>
            </Tooltip>
          </ResponsiveContainer>
        </ListItem>
      ))}
    </List>
  );
};

export default MinorAccountsList;