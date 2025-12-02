import React, { useState } from 'react';
import { useSettings } from '../hooks/useSettings';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Modal from '../components/common/Modal';

interface APIKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (name: string, permissions: string[]) => void;
}

const APIKeyModal: React.FC<APIKeyModalProps> = ({ isOpen, onClose, onSubmit }) => {
  const [name, setName] = useState('');
  const [permissions, setPermissions] = useState({
    read: true,
    trade: false,
    withdraw: false,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const selectedPermissions = Object.entries(permissions)
      .filter(([_, value]) => value)
      .map(([key]) => key);
    onSubmit(name, selectedPermissions);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create API Key">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Key Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />

        <div className="space-y-2">
          <h3 className="text-sm font-medium">Permissions</h3>
          {Object.entries(permissions).map(([key, value]) => (
            <label key={key} className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => setPermissions(prev => ({
                  ...prev,
                  [key]: e.target.checked
                }))}
                className="form-checkbox h-4 w-4 text-primary-600"
              />
              <span className="capitalize">{key}</span>
            </label>
          ))}
        </div>

        <div className="flex justify-end space-x-3">
          <Button variant="secondary" onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="primary">Create</Button>
        </div>
      </form>
    </Modal>
  );
};

export default function APIKeys() {
  const { createAPIKey, deleteAPIKey } = useSettings();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [newKey, setNewKey] = useState<any>(null);

  const handleCreateKey = async (name: string, permissions: string[]) => {
    const key = await createAPIKey(name, permissions);
    setNewKey(key);
    setApiKeys(prev => [...prev, key]);
  };

  const handleDeleteKey = async (id: string) => {
    await deleteAPIKey(id);
    setApiKeys(prev => prev.filter(key => key.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">API Keys</h1>
        <Button onClick={() => setIsModalOpen(true)}>Create New Key</Button>
      </div>

      {newKey && (
        <div className="bg-gray-700 p-4 rounded-lg">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-medium">New API Key Created</h3>
              <p className="text-sm text-gray-400 mt-1">
                Make sure to copy your API key and secret now. You won't be able to see them again!
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setNewKey(null)}
            >
              Close
            </Button>
          </div>
          <div className="mt-4 space-y-2">
            <div>
              <label className="text-sm text-gray-400">API Key:</label>
              <Input
                value={newKey.key}
                readOnly
                onClick={(e) => (e.target as HTMLInputElement).select()}
              />
            </div>
            <div>
              <label className="text-sm text-gray-400">API Secret:</label>
              <Input
                value={newKey.secret}
                readOnly
                onClick={(e) => (e.target as HTMLInputElement).select()}
              />
            </div>
          </div>
        </div>
      )}

      <div className="bg-gray-800 rounded-lg">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-700">
                <th className="px-6 py-3 text-left">Name</th>
                <th className="px-6 py-3 text-left">Permissions</th>
                <th className="px-6 py-3 text-left">Created</th>
                <th className="px-6 py-3 text-left">Last Used</th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {apiKeys.map((key) => (
                <tr key={key.id} className="border-t border-gray-700">
                  <td className="px-6 py-4">{key.name}</td>
                  <td className="px-6 py-4">
                    <div className="flex space-x-2">
                      {key.permissions.map((perm: string) => (
                        <span
                          key={perm}
                          className="px-2 py-1 bg-gray-700 rounded text-xs capitalize"
                        >
                          {perm}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-gray-400">
                    {new Date(key.createdAt).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 text-gray-400">
                    {key.lastUsed
                      ? new Date(key.lastUsed).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-6 py-4">
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => handleDeleteKey(key.id)}
                    >
                      Delete
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <APIKeyModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleCreateKey}
      />
    </div>
  );
}