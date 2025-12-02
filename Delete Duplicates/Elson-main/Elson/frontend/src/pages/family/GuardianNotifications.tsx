import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import { Button } from '../../app/components/common/Button';
import Select from '../../app/components/common/Select';
import LoadingSpinner from '../../app/components/common/LoadingSpinner';
import FamilyService, { Notification } from '../../app/services/familyService';
import { toast } from 'react-toastify';

const GuardianNotifications: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [loadingAction, setLoadingAction] = useState<Record<string, boolean>>({});

  // Fetch notifications from the API
  useEffect(() => {
    const fetchNotifications = async () => {
      setLoading(true);
      try {
        let options = {};
        if (filter === 'unread') {
          options = { unreadOnly: true };
        }
        
        const fetchedNotifications = await FamilyService.getNotifications(options);
        setNotifications(fetchedNotifications);
      } catch (error) {
        console.error('Error fetching notifications:', error);
        toast.error('Failed to fetch notifications. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();
  }, [filter]);

  const filterOptions = [
    { value: 'all', label: 'All Notifications' },
    { value: 'unread', label: 'Unread' },
    { value: 'requires_action', label: 'Requires Action' },
    { value: 'trade_request', label: 'Trade Requests' },
    { value: 'trade_executed', label: 'Trade Executions' },
    { value: 'trade_approved', label: 'Trade Approvals' },
    { value: 'withdrawal', label: 'Withdrawals' },
    { value: 'deposit', label: 'Deposits' },
    { value: 'login', label: 'Logins' },
  ];

  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !notification.isRead;
    if (filter === 'requires_action') return notification.requiresAction;
    return notification.type === filter;
  });

  const markAllAsRead = async () => {
    // Get all unread notification ids
    const unreadIds = notifications
      .filter(n => !n.isRead)
      .map(n => n.id);
      
    if (unreadIds.length === 0) return;
    
    setLoading(true);
    try {
      // Mark all as read one by one
      for (const id of unreadIds) {
        await FamilyService.markNotificationAsRead(id);
      }
      
      // Update local state
      setNotifications(notifications.map(notification => ({
        ...notification,
        isRead: true
      })));
      
      toast.success('All notifications marked as read');
    } catch (error) {
      console.error('Error marking all as read:', error);
      toast.error('Failed to mark notifications as read');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: string) => {
    setLoadingAction(prev => ({ ...prev, [id]: true }));
    try {
      await FamilyService.markNotificationAsRead(id);
      
      // Update local state
      setNotifications(notifications.map(notification => 
        notification.id === id 
          ? { ...notification, isRead: true }
          : notification
      ));
    } catch (error) {
      console.error('Error marking notification as read:', error);
      toast.error('Failed to mark notification as read');
    } finally {
      setLoadingAction(prev => ({ ...prev, [id]: false }));
    }
  };

  const approveRequest = async (id: string, tradeId?: number) => {
    if (!tradeId) {
      toast.error('Trade ID not found in notification');
      return;
    }
    
    setLoadingAction(prev => ({ ...prev, [id]: true }));
    try {
      await FamilyService.approveMinorTrade(tradeId, true);
      await markAsRead(id);
      
      // Update local state
      setNotifications(notifications.map(notification => 
        notification.id === id 
          ? { ...notification, requiresAction: false, isRead: true }
          : notification
      ));
      
      toast.success('Trade request approved');
    } catch (error) {
      console.error('Error approving trade:', error);
      toast.error('Failed to approve trade');
    } finally {
      setLoadingAction(prev => ({ ...prev, [id]: false }));
    }
  };

  const denyRequest = async (id: string, tradeId?: number) => {
    if (!tradeId) {
      toast.error('Trade ID not found in notification');
      return;
    }
    
    // Get the reason (in a real app, you would prompt the user for this)
    const rejectionReason = prompt('Please provide a reason for denial:');
    if (rejectionReason === null) return; // User cancelled
    
    setLoadingAction(prev => ({ ...prev, [id]: true }));
    try {
      await FamilyService.approveMinorTrade(tradeId, false, rejectionReason);
      await markAsRead(id);
      
      // Update local state
      setNotifications(notifications.map(notification => 
        notification.id === id 
          ? { ...notification, requiresAction: false, isRead: true }
          : notification
      ));
      
      toast.success('Trade request denied');
    } catch (error) {
      console.error('Error denying trade:', error);
      toast.error('Failed to deny trade');
    } finally {
      setLoadingAction(prev => ({ ...prev, [id]: false }));
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-8">
        <LoadingSpinner size="large" color="text-purple-600" text="Loading notifications..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Guardian Notifications</h1>
        <Button 
          onClick={markAllAsRead} 
          className="bg-transparent hover:bg-gray-700 border border-gray-600"
          disabled={!notifications.some(n => !n.isRead)}
        >
          Mark All as Read
        </Button>
      </div>

      {/* Filter */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center bg-gray-800 p-4 rounded-lg">
        <p className="mb-3 sm:mb-0 text-gray-400">
          {filteredNotifications.length} notification{filteredNotifications.length !== 1 ? 's' : ''}
          {filter !== 'all' ? ' (filtered)' : ''}
        </p>
        <Select
          value={filter}
          onChange={setFilter}
          options={filterOptions}
          className="w-full sm:w-64"
        />
      </div>

      {/* Notifications list */}
      {filteredNotifications.length === 0 ? (
        <div className="bg-gray-800 p-6 rounded-lg text-center">
          <p className="text-gray-400">No notifications match your filter.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredNotifications.map(notification => (
            <div 
              key={notification.id} 
              className={`bg-gray-800 p-4 rounded-lg border-l-4 ${
                !notification.isRead 
                  ? 'border-blue-500' 
                  : notification.requiresAction 
                    ? 'border-yellow-500' 
                    : 'border-gray-600'
              }`}
            >
              <div className="flex justify-between mb-2">
                <span className="font-semibold">{notification.minorName}</span>
                <span className="text-gray-400 text-sm">
                  {format(parseISO(notification.timestamp), 'MMM d, h:mm a')}
                </span>
              </div>
              
              <p className="mb-3">{notification.message}</p>
              
              <div className="flex justify-between items-center">
                {/* Type badge */}
                <span className={`px-2 py-1 rounded text-xs ${
                  notification.type.includes('trade') ? 'bg-green-900 text-green-300' :
                  notification.type === 'withdrawal' ? 'bg-red-900 text-red-300' :
                  notification.type === 'deposit' ? 'bg-blue-900 text-blue-300' :
                  notification.type === 'login' ? 'bg-purple-900 text-purple-300' :
                  notification.type === 'settings_change' ? 'bg-gray-700 text-gray-300' :
                  'bg-yellow-900 text-yellow-300'
                }`}>
                  {notification.type.replace(/_/g, ' ')}
                </span>
                
                {/* Action buttons */}
                <div className="space-x-2">
                  {notification.requiresAction && notification.type === 'trade_request' && (
                    <>
                      <Button 
                        onClick={() => approveRequest(notification.id, notification.tradeId)}
                        className="text-xs bg-green-600 hover:bg-green-700"
                        disabled={loadingAction[notification.id]}
                      >
                        {loadingAction[notification.id] ? 'Processing...' : 'Approve'}
                      </Button>
                      <Button 
                        onClick={() => denyRequest(notification.id, notification.tradeId)}
                        className="text-xs bg-red-600 hover:bg-red-700"
                        disabled={loadingAction[notification.id]}
                      >
                        {loadingAction[notification.id] ? 'Processing...' : 'Deny'}
                      </Button>
                    </>
                  )}

                  {!notification.isRead && (
                    <Button 
                      onClick={() => markAsRead(notification.id)}
                      className="text-xs bg-transparent border border-gray-600 hover:bg-gray-700"
                      disabled={loadingAction[notification.id]}
                    >
                      {loadingAction[notification.id] ? 'Processing...' : 'Mark as Read'}
                    </Button>
                  )}
                </div>
              </div>
              
              {/* Trade details if available */}
              {notification.symbol && notification.quantity && notification.price && (
                <div className="mt-3 pt-3 border-t border-gray-700 text-sm text-gray-400">
                  <p>
                    {notification.tradeType?.toUpperCase() || ''} {notification.quantity} {notification.symbol} @ ${notification.price}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default GuardianNotifications;