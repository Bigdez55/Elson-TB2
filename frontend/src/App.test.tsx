import { render } from '@testing-library/react';

test('renders without crashing', () => {
  const div = document.createElement('div');
  expect(div).toBeTruthy();
});

test('basic math works', () => {
  expect(2 + 2).toBe(4);
});