import React, { useState } from 'react';
import { 
  List, 
  ListItem, 
  ListItemText, 
  ListItemAvatar, 
  Avatar,
  Button,
  ButtonGroup,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  Chip,
  Typography,
  Box
} from '@mui/material';
import { TrendingUp, TrendingDown, Person } from '@mui/icons-material';
import { formatCurrency, formatDate } from '../../utils/formatters';

interface PendingTrade {
  trade_id: number;
  minor_id: number;
  minor_name: string;
  symbol: string;
  quantity: number;
  price: number;
  trade_type: string;
  created_at: string;
  status: string;
}

interface PendingTradesListProps {
  pendingTrades: PendingTrade[];
  onApproveTrade: (tradeId: number, approved: boolean, rejectionReason?: string) => void;
}

const PendingTradesList: React.FC<PendingTradesListProps> = ({ pendingTrades, onApproveTrade }) => {
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [selectedTradeId, setSelectedTradeId] = useState<number | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [rejectionError, setRejectionError] = useState('');

  const handleApprove = (tradeId: number) => {
    onApproveTrade(tradeId, true);
  };

  const handleOpenRejectDialog = (tradeId: number) => {
    setSelectedTradeId(tradeId);
    setRejectionReason('');
    setRejectionError('');
    setRejectDialogOpen(true);
  };

  const handleCloseRejectDialog = () => {
    setRejectDialogOpen(false);
    setSelectedTradeId(null);
  };

  const handleRejectConfirm = () => {
    if (!rejectionReason.trim()) {
      setRejectionError('Please provide a reason for rejection');
      return;
    }

    if (selectedTradeId) {
      onApproveTrade(selectedTradeId, false, rejectionReason);
      handleCloseRejectDialog();
    }
  };

  return (
    <>
      <List>
        {pendingTrades.map((trade) => (
          <ListItem key={trade.trade_id} divider>
            <ListItemAvatar>
              <Avatar sx={{ bgcolor: trade.trade_type === 'buy' ? 'success.main' : 'error.main' }}>
                {trade.trade_type === 'buy' ? <TrendingUp /> : <TrendingDown />}
              </Avatar>
            </ListItemAvatar>
            
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="subtitle1">
                    {trade.symbol} - {trade.quantity} shares @ {formatCurrency(trade.price)}
                  </Typography>
                  <Chip 
                    size="small" 
                    label={trade.trade_type.toUpperCase()} 
                    color={trade.trade_type === 'buy' ? 'success' : 'error'}
                    sx={{ ml: 1 }}
                  />
                </Box>
              }
              secondary={
                <>
                  <Typography variant="body2" component="span" display="block">
                    <Person fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                    {trade.minor_name}
                  </Typography>
                  <Typography variant="body2" component="span" display="block" color="text.secondary">
                    Total: {formatCurrency(trade.quantity * trade.price)}
                  </Typography>
                  <Typography variant="body2" component="span" display="block" color="text.secondary">
                    Requested: {formatDate(trade.created_at)}
                  </Typography>
                </>
              }
            />
            
            <ButtonGroup variant="outlined" size="small" sx={{ ml: 2 }}>
              <Button 
                color="success" 
                onClick={() => handleApprove(trade.trade_id)}
              >
                Approve
              </Button>
              <Button 
                color="error" 
                onClick={() => handleOpenRejectDialog(trade.trade_id)}
              >
                Reject
              </Button>
            </ButtonGroup>
          </ListItem>
        ))}
      </List>

      {/* Rejection Dialog */}
      <Dialog open={rejectDialogOpen} onClose={handleCloseRejectDialog}>
        <DialogTitle>Reject Trade</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Please provide a reason for rejecting this trade request. This will be shown to the minor account holder.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            id="rejectionReason"
            label="Rejection Reason"
            type="text"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={rejectionReason}
            onChange={(e) => setRejectionReason(e.target.value)}
            error={!!rejectionError}
            helperText={rejectionError}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseRejectDialog} color="primary">
            Cancel
          </Button>
          <Button onClick={handleRejectConfirm} color="error">
            Reject Trade
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PendingTradesList;