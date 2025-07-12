import React from 'react';
import { Tooltip, TooltipProps, styled } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import SchoolIcon from '@mui/icons-material/School';

// Define enhanced props for our educational tooltip
interface EducationalTooltipProps extends Omit<TooltipProps, 'children' | 'title'> {
  term: string;
  definition: string;
  icon?: 'info' | 'help' | 'school';
  link?: string;
  children?: React.ReactElement;
  iconColor?: string;
  placement?: TooltipProps['placement'];
}

// Styled tooltip with a more educational appearance
const StyledTooltip = styled(Tooltip)(({ theme }) => ({
  tooltip: {
    backgroundColor: theme.palette.background.paper,
    color: theme.palette.text.primary,
    maxWidth: 300,
    border: `1px solid ${theme.palette.divider}`,
    boxShadow: theme.shadows[3],
    padding: theme.spacing(2),
    fontSize: '0.9rem',
    '& a': {
      color: theme.palette.primary.main,
    },
  },
  arrow: {
    color: theme.palette.background.paper,
    '&::before': {
      border: `1px solid ${theme.palette.divider}`,
    },
  },
}));

const EducationalTooltip: React.FC<EducationalTooltipProps> = ({
  term,
  definition,
  icon = 'info',
  link,
  children,
  iconColor = 'primary.main',
  placement = 'top',
  ...props
}) => {
  // Generate tooltip content with definition
  const tooltipContent = (
    <div>
      <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>{term}</div>
      <div style={{ marginBottom: link ? '0.5rem' : 0 }}>{definition}</div>
      {link && (
        <a href={link} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.8rem' }}>
          Learn more
        </a>
      )}
    </div>
  );

  // Select the appropriate icon
  const IconComponent = icon === 'info' 
    ? InfoIcon 
    : icon === 'help' 
      ? HelpOutlineIcon 
      : SchoolIcon;

  // If children are provided, use them as the tooltip trigger
  // Otherwise, use the selected icon
  return (
    <StyledTooltip
      title={tooltipContent}
      arrow
      placement={placement}
      {...props}
    >
      {children || <IconComponent sx={{ color: iconColor, verticalAlign: 'middle', fontSize: '1rem', ml: 0.5, cursor: 'help' }} />}
    </StyledTooltip>
  );
};

export default EducationalTooltip;