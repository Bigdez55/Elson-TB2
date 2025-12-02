import React, { useState } from 'react';
import { Button, Card, Input, Select, Badge, Tabs } from './index';
import { ToastProvider, useToastContext } from './ToastProvider';
import Modal, { ModalFooter } from './Modal';
import Loading from './Loading';
import ResponsiveContainer from './ResponsiveContainer';

const ToastExample = () => {
  const { showToast } = useToastContext();

  const handleShowToast = (type: 'success' | 'error' | 'warning' | 'info') => {
    showToast({
      type,
      title: `${type.charAt(0).toUpperCase() + type.slice(1)} Toast`,
      message: `This is a ${type} message that will disappear automatically.`,
      duration: 5000,
    });
  };

  return (
    <Card title="Toast Examples">
      <div className="flex flex-wrap gap-2">
        <Button onClick={() => handleShowToast('success')}>Show Success</Button>
        <Button onClick={() => handleShowToast('error')} variant="danger">Show Error</Button>
        <Button onClick={() => handleShowToast('warning')} variant="outline">Show Warning</Button>
        <Button onClick={() => handleShowToast('info')} variant="secondary">Show Info</Button>
      </div>
    </Card>
  );
};

const ModalExample = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Card title="Modal Example">
      <Button onClick={() => setIsOpen(true)}>Open Modal</Button>
      
      <Modal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        title="Example Modal"
        footer={
          <ModalFooter
            cancelText="Cancel"
            confirmText="Confirm"
            onCancel={() => setIsOpen(false)}
            onConfirm={() => setIsOpen(false)}
          />
        }
      >
        <p className="text-gray-300 mb-4">
          This is an example modal dialog with a footer that has cancel and confirm buttons.
        </p>
        <div className="bg-gray-800 p-4 rounded-lg">
          <Input
            label="Sample Input"
            placeholder="Enter some text..."
          />
        </div>
      </Modal>
    </Card>
  );
};

const FormExample = () => {
  return (
    <Card title="Form Components">
      <div className="space-y-4">
        <Input
          label="Text Input"
          placeholder="Enter text..."
          helperText="This is a helper text"
        />
        
        <Input
          label="Password Input"
          type="password"
          placeholder="Enter password..."
          error="This field is required"
        />
        
        <Input
          label="With Icons"
          placeholder="Search..."
          startIcon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
          actionIcon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          }
          onActionClick={() => console.log('Clearing input')}
        />
        
        <Select
          label="Select Example"
          options={[
            { value: 'option1', label: 'Option 1' },
            { value: 'option2', label: 'Option 2' },
            { value: 'option3', label: 'Option 3', disabled: true },
          ]}
          placeholder="Select an option"
        />
      </div>
    </Card>
  );
};

const BadgeExample = () => {
  return (
    <Card title="Badge Examples">
      <div className="flex flex-wrap gap-2">
        <Badge variant="primary">Primary</Badge>
        <Badge variant="secondary">Secondary</Badge>
        <Badge variant="success">Success</Badge>
        <Badge variant="warning">Warning</Badge>
        <Badge variant="danger">Danger</Badge>
        <Badge variant="info">Info</Badge>
        
        <div className="w-full my-2"></div>
        
        <Badge variant="primary" rounded>Primary</Badge>
        <Badge variant="secondary" rounded>Secondary</Badge>
        <Badge variant="success" rounded>Success</Badge>
        <Badge variant="warning" rounded>Warning</Badge>
        <Badge variant="danger" rounded>Danger</Badge>
        <Badge variant="info" rounded>Info</Badge>
      </div>
    </Card>
  );
};

const ButtonExample = () => {
  return (
    <Card title="Button Examples">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" size="xs">X-Small</Button>
          <Button variant="primary" size="sm">Small</Button>
          <Button variant="primary" size="md">Medium</Button>
          <Button variant="primary" size="lg">Large</Button>
        </div>
        
        <div className="flex flex-wrap gap-2">
          <Button variant="primary" loading>Loading</Button>
          <Button
            variant="primary"
            leftIcon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            }
          >
            With Left Icon
          </Button>
          <Button
            variant="primary"
            rightIcon={
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
            }
          >
            With Right Icon
          </Button>
        </div>
      </div>
    </Card>
  );
};

const TabsExample = () => {
  const tabs = [
    {
      id: 'tab1',
      label: 'First Tab',
      content: (
        <div className="p-4 bg-gray-800 rounded-lg">
          <h3 className="text-lg font-medium text-white mb-2">Tab 1 Content</h3>
          <p className="text-gray-300">This is the content for the first tab.</p>
        </div>
      ),
    },
    {
      id: 'tab2',
      label: 'Second Tab',
      content: (
        <div className="p-4 bg-gray-800 rounded-lg">
          <h3 className="text-lg font-medium text-white mb-2">Tab 2 Content</h3>
          <p className="text-gray-300">This is the content for the second tab.</p>
        </div>
      ),
    },
    {
      id: 'tab3',
      label: 'Disabled Tab',
      disabled: true,
      content: (
        <div className="p-4 bg-gray-800 rounded-lg">
          <h3 className="text-lg font-medium text-white mb-2">Tab 3 Content</h3>
          <p className="text-gray-300">This content should not be accessible.</p>
        </div>
      ),
    },
  ];

  return (
    <Card title="Tabs Examples">
      <div className="space-y-8">
        <div>
          <h3 className="text-white mb-2">Default Tabs</h3>
          <Tabs tabs={tabs} variant="default" />
        </div>
        
        <div>
          <h3 className="text-white mb-2">Pill Tabs</h3>
          <Tabs tabs={tabs} variant="pill" />
        </div>
        
        <div>
          <h3 className="text-white mb-2">Underline Tabs</h3>
          <Tabs tabs={tabs} variant="underline" />
        </div>
        
        <div>
          <h3 className="text-white mb-2">Vertical Tabs</h3>
          <Tabs tabs={tabs} orientation="vertical" />
        </div>
      </div>
    </Card>
  );
};

const ResponsiveContainerExample = () => {
  return (
    <Card title="ResponsiveContainer Examples">
      <div className="space-y-6">
        <div>
          <h3 className="text-white mb-2">Default (Column on mobile, Row on md+)</h3>
          <ResponsiveContainer className="border border-purple-500 p-4">
            <div className="bg-purple-800 p-4 m-2 text-white">Item 1</div>
            <div className="bg-purple-700 p-4 m-2 text-white">Item 2</div>
            <div className="bg-purple-600 p-4 m-2 text-white">Item 3</div>
          </ResponsiveContainer>
        </div>
        
        <div>
          <h3 className="text-white mb-2">Custom Breakpoint (lg)</h3>
          <ResponsiveContainer 
            breakpoint="lg" 
            className="border border-blue-500 p-4"
          >
            <div className="bg-blue-800 p-4 m-2 text-white">Item 1</div>
            <div className="bg-blue-700 p-4 m-2 text-white">Item 2</div>
            <div className="bg-blue-600 p-4 m-2 text-white">Item 3</div>
          </ResponsiveContainer>
        </div>
        
        <div>
          <h3 className="text-white mb-2">Custom Classes</h3>
          <ResponsiveContainer 
            mobileClasses="grid grid-cols-1 gap-4" 
            desktopClasses="grid grid-cols-3 gap-6"
            className="border border-green-500 p-4"
          >
            <div className="bg-green-800 p-4 text-white">Item 1</div>
            <div className="bg-green-700 p-4 text-white">Item 2</div>
            <div className="bg-green-600 p-4 text-white">Item 3</div>
          </ResponsiveContainer>
        </div>
        
        <div>
          <h3 className="text-white mb-2">Different HTML Element</h3>
          <ResponsiveContainer 
            as="section"
            className="border border-yellow-500 p-4"
          >
            <div className="bg-yellow-800 p-4 m-2 text-white">Item 1</div>
            <div className="bg-yellow-700 p-4 m-2 text-white">Item 2</div>
            <div className="bg-yellow-600 p-4 m-2 text-white">Item 3</div>
          </ResponsiveContainer>
        </div>
      </div>
    </Card>
  );
};

const LoadingExample = () => {
  const [showFullScreen, setShowFullScreen] = useState(false);
  
  return (
    <Card title="Loading Examples">
      <div className="space-y-6">
        <div className="flex flex-wrap gap-8">
          <div>
            <h3 className="text-white mb-2">Small</h3>
            <Loading size="sm" text="Loading small..." />
          </div>
          <div>
            <h3 className="text-white mb-2">Medium</h3>
            <Loading size="md" text="Loading medium..." />
          </div>
          <div>
            <h3 className="text-white mb-2">Large</h3>
            <Loading size="lg" text="Loading large..." />
          </div>
        </div>
        
        <div>
          <Button 
            variant="primary" 
            onClick={() => setShowFullScreen(!showFullScreen)}
          >
            Toggle Fullscreen Loading
          </Button>
          {showFullScreen && <Loading fullScreen text="Loading full screen..." />}
        </div>
      </div>
    </Card>
  );
};

const ComponentsTest: React.FC = () => {
  return (
    <ToastProvider position="top-right">
      <div className="min-h-screen bg-gray-900 text-white p-8">
        <h1 className="text-3xl font-bold mb-8">UI Components Test</h1>
        
        <div className="space-y-8 max-w-4xl mx-auto">
          <ButtonExample />
          <FormExample />
          <BadgeExample />
          <ModalExample />
          <ToastExample />
          <TabsExample />
          <ResponsiveContainerExample />
          <LoadingExample />
        </div>
      </div>
    </ToastProvider>
  );
};

export default ComponentsTest;