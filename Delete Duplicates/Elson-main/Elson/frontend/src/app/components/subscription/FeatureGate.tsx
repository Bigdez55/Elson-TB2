import React, { useState, useEffect, ReactNode } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { subscriptionService, SubscriptionPlan } from '../../services/subscriptionService';
import UpgradePrompt from './UpgradePrompt';

interface FeatureGateProps {
  /**
   * The feature identifier to check against the backend
   */
  feature: string;
  
  /**
   * The content to render if the user has access to the feature
   */
  children: ReactNode;
  
  /**
   * Optional fallback content to render if the user doesn't have access
   * If not provided, the component will render an upgrade prompt
   */
  fallback?: ReactNode;
  
  /**
   * Whether to show a full upgrade prompt (true) or just a badge/indicator (false)
   * Default is false
   */
  showUpgradePrompt?: boolean;
  
  /**
   * Additional message to show in the upgrade prompt
   */
  upgradeMessage?: string;
  
  /**
   * If true, renders a badge/indicator but still shows the children
   * Useful for features that are available in a limited capacity to free users
   * Default is false
   */
  previewMode?: boolean;
}

/**
 * FeatureGate controls access to premium features based on the user's subscription
 */
const FeatureGate: React.FC<FeatureGateProps> = ({
  feature,
  children,
  fallback,
  showUpgradePrompt = false,
  upgradeMessage,
  previewMode = false,
}) => {
  const [hasAccess, setHasAccess] = useState<boolean | null>(null);
  const [requiredPlan, setRequiredPlan] = useState<SubscriptionPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkAccess = async () => {
      try {
        setIsLoading(true);
        const response = await subscriptionService.checkFeatureAccess(feature);
        setHasAccess(response.has_access);
        setRequiredPlan(response.required_plan || null);
      } catch (err) {
        console.error('Error checking feature access:', err);
        setError('Failed to check feature access. Please try again later.');
        // Default to allowing access on error
        setHasAccess(true);
      } finally {
        setIsLoading(false);
      }
    };

    checkAccess();
  }, [feature]);

  // While checking access, show a simple loading state or just render children
  if (isLoading) {
    return <Box sx={{ opacity: 0.6 }}>{children}</Box>;
  }

  // If there was an error, default to showing the content
  if (error) {
    console.warn('FeatureGate error:', error);
    return <>{children}</>;
  }

  // If user has access, render the children
  if (hasAccess) {
    return <>{children}</>;
  }
  
  // If in preview mode, show the content with a premium indicator
  if (previewMode) {
    return (
      <Box sx={{ position: 'relative' }}>
        <Box 
          sx={{ 
            position: 'absolute', 
            top: 0, 
            right: 0, 
            zIndex: 1,
            backgroundColor: 'warning.main',
            color: 'warning.contrastText',
            px: 1,
            py: 0.5,
            borderRadius: '0 0 0 4px',
            fontSize: '0.75rem',
            fontWeight: 'bold'
          }}
        >
          PREMIUM
        </Box>
        <Box sx={{ opacity: 0.8 }}>{children}</Box>
      </Box>
    );
  }

  // User doesn't have access - render fallback or upgrade prompt
  if (fallback) {
    return <>{fallback}</>;
  }

  // Show upgrade prompt
  if (showUpgradePrompt && requiredPlan) {
    return (
      <UpgradePrompt 
        requiredPlan={requiredPlan} 
        featureName={feature}
        message={upgradeMessage}
      />
    );
  }

  // Default fallback for restricted features
  return (
    <Box 
      sx={{
        p: 3,
        textAlign: 'center',
        backgroundColor: 'background.paper',
        borderRadius: 2,
        border: '1px dashed',
        borderColor: 'divider',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 2
      }}
    >
      <Typography variant="body1" color="text.secondary">
        This feature requires a {requiredPlan ? requiredPlan.charAt(0).toUpperCase() + requiredPlan.slice(1) : 'premium'} subscription.
      </Typography>
      <Button 
        variant="contained" 
        color="primary"
        href="/subscription"
      >
        Upgrade Now
      </Button>
    </Box>
  );
};

export default FeatureGate;