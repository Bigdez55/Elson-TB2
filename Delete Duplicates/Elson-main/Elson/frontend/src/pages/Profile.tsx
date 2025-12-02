import React, { useState } from 'react';
import { authService } from '../services/authService';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/common/Button';
import Input from '../components/common/Input';

export default function Profile() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    username: user?.username || '',
    email: user?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await authService.updateProfile({
        username: formData.username,
        email: formData.email,
      });
      setSuccess('Profile updated successfully');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.newPassword !== formData.confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await authService.changePassword(
        formData.currentPassword,
        formData.newPassword
      );
      setSuccess('Password changed successfully');
      setFormData({
        ...formData,
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-6">Profile Settings</h2>
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <Input
            label="Username"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            required
          />
          <Input
            label="Email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleInputChange}
            required
          />
          <Button type="submit" variant="primary" isLoading={loading}>
            Update Profile
          </Button>
        </form>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-6">Change Password</h2>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <Input
            label="Current Password"
            name="currentPassword"
            type="password"
            value={formData.currentPassword}
            onChange={handleInputChange}
            required
          />
          <Input
            label="New Password"
            name="newPassword"
            type="password"
            value={formData.newPassword}
            onChange={handleInputChange}
            required
          />
          <Input
            label="Confirm New Password"
            name="confirmPassword"
            type="password"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            required
          />
          <Button type="submit" variant="primary" isLoading={loading}>
            Change Password
          </Button>
        </form>
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-6">Two-Factor Authentication</h2>
        <div className="space-y-4">
          <p className="text-gray-400">
            Two-factor authentication adds an extra layer of security to your account
          </p>
          <Button
            variant="secondary"
            onClick={() => {/* Handle 2FA setup */}}
          >
            {user?.twoFactorEnabled ? 'Disable 2FA' : 'Enable 2FA'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/50 text-red-500 p-4 rounded-lg">
          {error}
        </div>
      )}

      {success && (
        <div className="bg-green-900/50 text-green-500 p-4 rounded-lg">
          {success}
        </div>
      )}
    </div>
  );
}