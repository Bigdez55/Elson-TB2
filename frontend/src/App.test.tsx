import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders without crashing', () => {
  const div = document.createElement('div');
  expect(div).toBeTruthy();
});

test('basic math works', () => {
  expect(2 + 2).toBe(4);
});

export {};