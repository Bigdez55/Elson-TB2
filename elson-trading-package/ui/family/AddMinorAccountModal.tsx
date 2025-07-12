import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import axios from 'axios';

interface Minor {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  birthdate: string;
  account_id: number;
}

interface AddMinorAccountModalProps {
  open: boolean;
  onClose: () => void;
  onMinorCreated: (minor: Minor) => void;
}

interface FormErrors {
  email?: string;
  first_name?: string;
  last_name?: string;
  birthdate?: string;
}

const AddMinorAccountModal: React.FC<AddMinorAccountModalProps> = ({ 
  open, 
  onClose, 
  onMinorCreated 
}) => {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    birthdate: null as Date | null
  });
  
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value
    });
    
    // Clear error for this field when user types
    if (errors[name as keyof FormErrors]) {
      setErrors({
        ...errors,
        [name]: undefined
      });
    }
  };

  const handleDateChange = (newDate: Date | null) => {
    setFormData({
      ...formData,
      birthdate: newDate
    });
    
    // Clear birthdate error when user changes date
    if (errors.birthdate) {
      setErrors({
        ...errors,
        birthdate: undefined
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    let isValid = true;
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
      isValid = false;
    }
    
    if (!formData.first_name) {
      newErrors.first_name = 'First name is required';
      isValid = false;
    }
    
    if (!formData.last_name) {
      newErrors.last_name = 'Last name is required';
      isValid = false;
    }
    
    if (!formData.birthdate) {
      newErrors.birthdate = 'Birthdate is required';
      isValid = false;
    } else {
      // Check if minor is under 18
      const today = new Date();
      const birthDate = new Date(formData.birthdate);
      let age = today.getFullYear() - birthDate.getFullYear();
      const m = today.getMonth() - birthDate.getMonth();
      
      if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }
      
      if (age >= 18) {
        newErrors.birthdate = 'Minor must be under 18 years old';
        isValid = false;
      }
    }
    
    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    setSubmitting(true);
    setApiError(null);
    
    try {
      const response = await axios.post(
        '/api/v1/family/minor',
        {
          email: formData.email,
          first_name: formData.first_name,
          last_name: formData.last_name,
          birthdate: formData.birthdate?.toISOString().split('T')[0] // Format as YYYY-MM-DD
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        }
      );
      
      onMinorCreated(response.data);
      
      // Reset form
      setFormData({
        email: '',
        first_name: '',
        last_name: '',
        birthdate: null
      });
    } catch (err: any) {
      console.error('Error creating minor account:', err);
      setApiError(
        err.response?.data?.detail || 
        'Failed to create minor account. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Minor Account</DialogTitle>
      
      <DialogContent>
        {apiError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {apiError}
          </Alert>
        )}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={6}>
            <TextField
              name="first_name"
              label="First Name"
              value={formData.first_name}
              onChange={handleChange}
              fullWidth
              error={!!errors.first_name}
              helperText={errors.first_name}
              disabled={submitting}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <TextField
              name="last_name"
              label="Last Name"
              value={formData.last_name}
              onChange={handleChange}
              fullWidth
              error={!!errors.last_name}
              helperText={errors.last_name}
              disabled={submitting}
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              name="email"
              label="Email Address"
              type="email"
              value={formData.email}
              onChange={handleChange}
              fullWidth
              error={!!errors.email}
              helperText={errors.email}
              disabled={submitting}
            />
          </Grid>
          
          <Grid item xs={12}>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <DatePicker
                label="Birthdate"
                value={formData.birthdate}
                onChange={handleDateChange}
                slotProps={{
                  textField: {
                    fullWidth: true,
                    error: !!errors.birthdate,
                    helperText: errors.birthdate,
                    disabled: submitting
                  }
                }}
              />
            </LocalizationProvider>
          </Grid>
        </Grid>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button 
          onClick={handleSubmit} 
          color="primary" 
          variant="contained" 
          disabled={submitting}
          startIcon={submitting ? <CircularProgress size={20} /> : null}
        >
          {submitting ? 'Creating...' : 'Create Account'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddMinorAccountModal;