import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect, vi } from 'vitest';
import Button from './src/app/components/common/Button';
import Card from './src/app/components/common/Card';
import Badge from './src/app/components/common/Badge';
import Input from './src/app/components/common/Input';
import Toast from './src/app/components/common/Toast';

describe('UI Components', () => {
  describe('Button', () => {
    test('renders with children', () => {
      render(<Button>Click me</Button>);
      expect(screen.getByText('Click me')).toBeDefined();
    });

    test('calls onClick when clicked', () => {
      const onClick = vi.fn();
      render(<Button onClick={onClick}>Click me</Button>);
      fireEvent.click(screen.getByText('Click me'));
      expect(onClick).toHaveBeenCalledTimes(1);
    });

    test('renders with different variants', () => {
      const { rerender } = render(<Button variant="primary">Primary</Button>);
      expect(screen.getByText('Primary')).toBeDefined();
      
      rerender(<Button variant="secondary">Secondary</Button>);
      expect(screen.getByText('Secondary')).toBeDefined();
      
      rerender(<Button variant="danger">Danger</Button>);
      expect(screen.getByText('Danger')).toBeDefined();
    });
  });

  describe('Card', () => {
    test('renders with title and children', () => {
      render(
        <Card title="Card Title">
          <p>Card content</p>
        </Card>
      );
      expect(screen.getByText('Card Title')).toBeDefined();
      expect(screen.getByText('Card content')).toBeDefined();
    });

    test('renders without title', () => {
      render(
        <Card>
          <p>Card content</p>
        </Card>
      );
      expect(screen.getByText('Card content')).toBeDefined();
    });

    test('renders with action', () => {
      render(
        <Card 
          title="Card Title"
          action={<Button>Action</Button>}
        >
          <p>Card content</p>
        </Card>
      );
      expect(screen.getByText('Card Title')).toBeDefined();
      expect(screen.getByText('Action')).toBeDefined();
      expect(screen.getByText('Card content')).toBeDefined();
    });
  });

  describe('Badge', () => {
    test('renders with text', () => {
      render(<Badge>Status</Badge>);
      expect(screen.getByText('Status')).toBeDefined();
    });

    test('renders with different variants', () => {
      const { rerender } = render(<Badge variant="primary">Primary</Badge>);
      expect(screen.getByText('Primary')).toBeDefined();
      
      rerender(<Badge variant="success">Success</Badge>);
      expect(screen.getByText('Success')).toBeDefined();
      
      rerender(<Badge variant="warning">Warning</Badge>);
      expect(screen.getByText('Warning')).toBeDefined();
    });
  });

  describe('Input', () => {
    test('renders with label', () => {
      render(<Input label="Username" />);
      expect(screen.getByText('Username')).toBeDefined();
    });

    test('handles change events', () => {
      const onChange = vi.fn();
      render(<Input onChange={onChange} />);
      fireEvent.change(screen.getByRole('textbox'), { target: { value: 'test' } });
      expect(onChange).toHaveBeenCalledTimes(1);
    });

    test('renders with error', () => {
      render(<Input error="This field is required" />);
      expect(screen.getByText('This field is required')).toBeDefined();
    });
  });

  describe('Toast', () => {
    test('renders with title and message', () => {
      const onClose = vi.fn();
      render(
        <Toast 
          id="toast-1"
          type="success"
          title="Success"
          message="Operation completed successfully"
          onClose={onClose}
        />
      );
      expect(screen.getByText('Success')).toBeDefined();
      expect(screen.getByText('Operation completed successfully')).toBeDefined();
    });
  });
});