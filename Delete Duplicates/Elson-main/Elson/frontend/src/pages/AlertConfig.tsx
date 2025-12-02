import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { fetchAlerts, createAlert, updateAlert, deleteAlert } from '../store/slices/alertsSlice';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Select from '../components/common/Select';
import { formatDateTime } from '../utils/formatters';

const ALERT_TYPES = [
  { value: 'PRICE', label: 'Price Alert' },
  { value: 'VOLUME', label: 'Volume Alert' },
  { value: 'INDICATOR', label: 'Indicator Alert' },
];

const ALERT_OPERATORS = [
  { value: '>', label: 'Greater Than' },
  { value: '<', label: 'Less Than' },
  { value: '=', label: 'Equal To' },
  { value: '>=', label: 'Greater Than or Equal' },
  { value: '<=', label: 'Less Than or Equal' },
];

interface AlertFormData {
  symbol: string;
  type: string;
  operator: string;
  value: string;
  message: string;
  enabled: boolean;
}

const initialFormData: AlertFormData = {
  symbol: '',
  type: 'PRICE',
  operator: '>',
  value: '',
  message: '',
  enabled: true,
};

export default function AlertConfig() {
  const dispatch = useDispatch();
  const { alerts, loading, error } = useSelector((state: any) => state.alerts);
  const [formData, setFormData] = useState<AlertFormData>(initialFormData);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    dispatch(fetchAlerts());
  }, [dispatch]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (editingId) {
      await dispatch(updateAlert({ alertId: editingId, data: formData }));
    } else {
      await dispatch(createAlert(formData));
    }
    setFormData(initialFormData);
    setEditingId(null);
    setShowForm(false);
  };

  const handleEdit = (alert: any) => {
    setFormData({
      symbol: alert.symbol,
      type: alert.type,
      operator: alert.operator,
      value: alert.value.toString(),
      message: alert.message,
      enabled: alert.enabled,
    });
    setEditingId(alert.id);
    setShowForm(true);
  };

  const handleDelete = async (alertId: string) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      await dispatch(deleteAlert(alertId));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Alert Configuration</h1>
        <Button onClick={() => setShowForm(true)}>Create New Alert</Button>
      </div>

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">
            {editingId ? 'Edit Alert' : 'Create Alert'}
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Symbol"
              name="symbol"
              value={formData.symbol}
              onChange={handleInputChange}
              placeholder="BTC/USD"
              required
            />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Select
                label="Alert Type"
                value={formData.type}
                onChange={(value) => setFormData(prev => ({ ...prev, type: value }))}
                options={ALERT_TYPES}
              />

              <Select
                label="Condition"
                value={formData.operator}
                onChange={(value) => setFormData(prev => ({ ...prev, operator: value }))}
                options={ALERT_OPERATORS}
              />

              <Input
                label="Value"
                name="value"
                type="number"
                value={formData.value}
                onChange={handleInputChange}
                required
              />
            </div>

            <Input
              label="Message"
              name="message"
              value={formData.message}
              onChange={handleInputChange}
              placeholder="Alert message when triggered"
              required
            />

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                name="enabled"
                checked={formData.enabled}
                onChange={handleInputChange}
                className="form-checkbox h-4 w-4 text-primary-600"
              />
              <label>Enable Alert</label>
            </div>

            <div className="flex space-x-3">
              <Button type="submit" variant="primary">
                {editingId ? 'Update Alert' : 'Create Alert'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setFormData(initialFormData);
                  setEditingId(null);
                  setShowForm(false);
                }}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-6 py-3 text-left">Symbol</th>
              <th className="px-6 py-3 text-left">Type</th>
              <th className="px-6 py-3 text-left">Condition</th>
              <th className="px-6 py-3 text-left">Message</th>
              <th className="px-6 py-3 text-left">Status</th>
              <th className="px-6 py-3 text-left">Last Triggered</th>
              <th className="px-6 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((alert: any) => (
              <tr key={alert.id} className="border-t border-gray-700">
                <td className="px-6 py-4">{alert.symbol}</td>
                <td className="px-6 py-4">{alert.type}</td>
                <td className="px-6 py-4">
                  {alert.operator} {alert.value}
                </td>
                <td className="px-6 py-4">{alert.message}</td>
                <td className="px-6 py-4">
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      alert.enabled
                        ? 'bg-green-900/50 text-green-500'
                        : 'bg-gray-900/50 text-gray-500'
                    }`}
                  >
                    {alert.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {alert.lastTriggered
                    ? formatDateTime(alert.lastTriggered)
                    : 'Never'}
                </td>
                <td className="px-6 py-4">
                  <div className="flex space-x-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleEdit(alert)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDelete(alert.id)}
                    >
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}