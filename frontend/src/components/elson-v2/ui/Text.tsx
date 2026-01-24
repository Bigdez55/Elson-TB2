import React from 'react';
import { C } from '../primitives/Colors';

type TextColor = 'white' | 'gray' | 'green' | 'red' | 'yellow' | 'gold' | 'grayLight';

interface TxtProps {
  children: React.ReactNode;
  c?: TextColor;
  size?: number;
  bold?: boolean;
  style?: React.CSSProperties;
}

const textColors: Record<TextColor, string> = {
  white: C.white,
  gray: C.gray,
  grayLight: C.grayLight,
  green: C.green,
  red: C.red,
  yellow: C.yellow,
  gold: C.gold,
};

export const Txt = ({
  children,
  c = 'white',
  size = 14,
  bold = false,
  style = {},
}: TxtProps) => (
  <span
    style={{
      color: textColors[c],
      fontSize: size,
      fontWeight: bold ? 700 : 400,
      ...style,
    }}
  >
    {children}
  </span>
);
