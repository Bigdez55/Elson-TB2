import React from 'react';
import { C } from '../primitives/Colors';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  style?: React.CSSProperties;
}

export const Input = (props: InputProps) => (
  <input
    {...props}
    style={{
      width: '100%',
      backgroundColor: C.inner,
      color: C.white,
      padding: '12px 16px',
      borderRadius: 10,
      border: `1px solid ${C.border}`,
      outline: 'none',
      marginTop: 6,
      fontSize: 14,
      ...props.style,
    }}
  />
);
