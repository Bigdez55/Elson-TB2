import React from 'react';
import { Box, Typography, Paper, Grid, Card, CardContent, CardHeader } from '@mui/material';
import FeatureGate from './FeatureGate';

/**
 * Example component demonstrating various ways to use the FeatureGate component
 */
const FeatureGateExample: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Feature Gate Examples
      </Typography>
      
      <Typography variant="body1" paragraph>
        This component demonstrates different ways to use the FeatureGate component to control access to premium features.
      </Typography>
      
      <Grid container spacing={3}>
        {/* Basic usage - block access */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Basic Usage (Block)
            </Typography>
            <Typography variant="body2" paragraph>
              This example shows a feature that requires a premium subscription.
              If the user doesn't have access, they'll see an upgrade prompt.
            </Typography>
            
            <FeatureGate feature="advanced_trading">
              <Card>
                <CardHeader title="Advanced Trading" />
                <CardContent>
                  <Typography>
                    This is premium content that requires a subscription.
                    You can see this because you have access to the "advanced_trading" feature.
                  </Typography>
                </CardContent>
              </Card>
            </FeatureGate>
          </Paper>
        </Grid>
        
        {/* Preview mode - show with badge */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Preview Mode
            </Typography>
            <Typography variant="body2" paragraph>
              This example shows content in "preview mode" - it's visible to everyone
              but has a premium badge and reduced opacity for free users.
            </Typography>
            
            <FeatureGate 
              feature="high_yield_savings" 
              previewMode={true}
            >
              <Card>
                <CardHeader title="High-Yield Savings" />
                <CardContent>
                  <Typography>
                    Earn 5.00% APY on your savings with our premium high-yield savings account.
                    This content is shown in preview mode with a badge for free users.
                  </Typography>
                </CardContent>
              </Card>
            </FeatureGate>
          </Paper>
        </Grid>
        
        {/* Custom fallback */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Custom Fallback
            </Typography>
            <Typography variant="body2" paragraph>
              This example provides a custom fallback to show when the user doesn't have access.
            </Typography>
            
            <FeatureGate 
              feature="custodial_accounts"
              fallback={
                <Card sx={{ bgcolor: 'background.paper', border: '1px dashed', borderColor: 'primary.main' }}>
                  <CardHeader title="Custodial Accounts (Family Plan)" />
                  <CardContent>
                    <Typography color="text.secondary">
                      Create and manage accounts for your children with our Family plan.
                      This is a custom fallback message for users without access.
                    </Typography>
                  </CardContent>
                </Card>
              }
            >
              <Card>
                <CardHeader title="Custodial Accounts" />
                <CardContent>
                  <Typography>
                    Manage your children's investment accounts and teach them about finance.
                    This content is only visible to Family plan subscribers.
                  </Typography>
                </CardContent>
              </Card>
            </FeatureGate>
          </Paper>
        </Grid>
        
        {/* Show full upgrade prompt */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Full Upgrade Prompt
            </Typography>
            <Typography variant="body2" paragraph>
              This example shows a full upgrade prompt with details when the user
              doesn't have access.
            </Typography>
            
            <FeatureGate 
              feature="tax_loss_harvesting"
              showUpgradePrompt={true}
              upgradeMessage="Optimize your tax strategy with automatic tax loss harvesting."
            >
              <Card>
                <CardHeader title="Tax Loss Harvesting" />
                <CardContent>
                  <Typography>
                    Automatically optimize your portfolio for tax efficiency.
                    This premium feature helps you save on taxes by strategically
                    selling securities at a loss to offset capital gains tax.
                  </Typography>
                </CardContent>
              </Card>
            </FeatureGate>
          </Paper>
        </Grid>
        
        {/* Free feature - always accessible */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Free Feature (Always Available)
            </Typography>
            <Typography variant="body2" paragraph>
              This example shows a feature that's available to all users, even those on the free plan.
            </Typography>
            
            <FeatureGate feature="basic_trading">
              <Card>
                <CardHeader title="Basic Trading" />
                <CardContent>
                  <Typography>
                    Commission-free trading for all users!
                    This feature is available on the free plan.
                  </Typography>
                </CardContent>
              </Card>
            </FeatureGate>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FeatureGateExample;