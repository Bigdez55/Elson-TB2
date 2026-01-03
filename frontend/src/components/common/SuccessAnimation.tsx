import React, { useEffect, useState, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Fade,
  Zoom,
  keyframes,
  styled,
} from '@mui/material';
import { CheckCircle, Celebration } from '@mui/icons-material';

// Confetti piece interface
interface ConfettiPiece {
  id: number;
  x: number;
  y: number;
  rotation: number;
  color: string;
  size: number;
  delay: number;
}

// Keyframe animations
const fall = keyframes`
  0% {
    transform: translateY(-100vh) rotate(0deg);
    opacity: 1;
  }
  100% {
    transform: translateY(100vh) rotate(720deg);
    opacity: 0;
  }
`;

const pulse = keyframes`
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
`;

const bounce = keyframes`
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-20px);
  }
  60% {
    transform: translateY(-10px);
  }
`;

const shimmer = keyframes`
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
`;

// Styled components
const ConfettiContainer = styled(Box)({
  position: 'fixed',
  top: 0,
  left: 0,
  width: '100%',
  height: '100%',
  pointerEvents: 'none',
  zIndex: 9999,
  overflow: 'hidden',
});

const ConfettiPieceStyled = styled(Box)<{ delay: number; duration: number }>(
  ({ delay, duration }) => ({
    position: 'absolute',
    animation: `${fall} ${duration}s linear ${delay}s forwards`,
    pointerEvents: 'none',
  })
);

const SuccessContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  padding: theme.spacing(4),
  textAlign: 'center',
}));

const CheckIcon = styled(CheckCircle)<{ animate?: boolean }>(
  ({ theme, animate }) => ({
    fontSize: 80,
    color: theme.palette.success.main,
    animation: animate ? `${pulse} 1s ease-in-out infinite` : 'none',
  })
);

const CelebrationIcon = styled(Celebration)(({ theme }) => ({
  fontSize: 40,
  color: theme.palette.warning.main,
  animation: `${bounce} 1s ease infinite`,
}));

const ShimmerText = styled(Typography)({
  background: 'linear-gradient(90deg, #4caf50, #81c784, #4caf50)',
  backgroundSize: '200% auto',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  animation: `${shimmer} 2s linear infinite`,
});

// Confetti colors
const CONFETTI_COLORS = [
  '#4CAF50', // Green
  '#2196F3', // Blue
  '#FFC107', // Amber
  '#E91E63', // Pink
  '#9C27B0', // Purple
  '#FF5722', // Deep Orange
  '#00BCD4', // Cyan
  '#8BC34A', // Light Green
];

interface SuccessAnimationProps {
  // Display options
  show: boolean;
  title?: string;
  subtitle?: string;
  amount?: number;
  symbol?: string;
  shares?: number;

  // Animation options
  showConfetti?: boolean;
  confettiCount?: number;
  duration?: number; // in ms

  // Milestone badges
  isMilestone?: boolean;
  milestoneType?: 'first_trade' | 'streak' | 'amount_goal' | 'custom';
  milestoneText?: string;

  // Callbacks
  onComplete?: () => void;
  onClose?: () => void;

  // Sound
  playSound?: boolean;
}

// Generate confetti pieces
const generateConfetti = (count: number): ConfettiPiece[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100, // percentage
    y: -10,
    rotation: Math.random() * 360,
    color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
    size: 8 + Math.random() * 8,
    delay: Math.random() * 0.5,
  }));
};

export const SuccessAnimation: React.FC<SuccessAnimationProps> = ({
  show,
  title = 'Order Placed!',
  subtitle,
  amount,
  symbol,
  shares,
  showConfetti = true,
  confettiCount = 50,
  duration = 3000,
  isMilestone = false,
  milestoneType,
  milestoneText,
  onComplete,
  onClose,
  playSound = false,
}) => {
  const [confetti, setConfetti] = useState<ConfettiPiece[]>([]);
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Generate default subtitle if not provided
  const displaySubtitle = subtitle || (amount && symbol && shares
    ? `You invested $${amount.toFixed(2)} in ${symbol} (${shares.toFixed(4)} shares)`
    : undefined);

  // Milestone badge text
  const getMilestoneBadge = useCallback(() => {
    if (milestoneText) return milestoneText;
    switch (milestoneType) {
      case 'first_trade':
        return '🎉 First Investment!';
      case 'streak':
        return '🔥 Investment Streak!';
      case 'amount_goal':
        return '🎯 Goal Reached!';
      default:
        return '🏆 Achievement Unlocked!';
    }
  }, [milestoneType, milestoneText]);

  // Play success sound
  const playSuccessSound = useCallback(() => {
    if (playSound && typeof Audio !== 'undefined') {
      try {
        // Simple success sound using Web Audio API
        const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
        oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
        oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5

        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.4);
      } catch (e) {
        // Audio not supported, ignore
      }
    }
  }, [playSound]);

  useEffect(() => {
    if (show) {
      setVisible(true);

      if (showConfetti) {
        setConfetti(generateConfetti(confettiCount));
      }

      playSuccessSound();

      // Auto-hide after duration
      timeoutRef.current = setTimeout(() => {
        setVisible(false);
        setConfetti([]);
        if (onComplete) {
          onComplete();
        }
      }, duration);
    } else {
      setVisible(false);
      setConfetti([]);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [show, showConfetti, confettiCount, duration, onComplete, playSuccessSound]);

  if (!visible && !show) {
    return null;
  }

  return (
    <>
      {/* Confetti Layer */}
      {showConfetti && confetti.length > 0 && (
        <ConfettiContainer>
          {confetti.map((piece) => (
            <ConfettiPieceStyled
              key={piece.id}
              delay={piece.delay}
              duration={2 + Math.random() * 2}
              sx={{
                left: `${piece.x}%`,
                top: piece.y,
                width: piece.size,
                height: piece.size * 0.6,
                backgroundColor: piece.color,
                borderRadius: '2px',
                transform: `rotate(${piece.rotation}deg)`,
              }}
            />
          ))}
        </ConfettiContainer>
      )}

      {/* Success Message Overlay */}
      <Fade in={visible} timeout={500}>
        <Box
          sx={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            bgcolor: 'rgba(0, 0, 0, 0.7)',
            zIndex: 9998,
          }}
          onClick={onClose}
        >
          <Zoom in={visible} timeout={300}>
            <SuccessContainer
              sx={{
                bgcolor: 'background.paper',
                borderRadius: 3,
                maxWidth: 400,
                mx: 2,
                boxShadow: 24,
              }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Celebration Icons */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <CelebrationIcon sx={{ transform: 'scaleX(-1)' }} />
                <CheckIcon animate />
                <CelebrationIcon />
              </Box>

              {/* Title */}
              <ShimmerText variant="h4" fontWeight="bold" gutterBottom>
                {title}
              </ShimmerText>

              {/* Subtitle */}
              {displaySubtitle && (
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  {displaySubtitle}
                </Typography>
              )}

              {/* Milestone Badge */}
              {isMilestone && (
                <Box
                  sx={{
                    mt: 2,
                    px: 3,
                    py: 1,
                    bgcolor: 'warning.light',
                    borderRadius: 2,
                    animation: `${bounce} 1s ease infinite`,
                  }}
                >
                  <Typography variant="subtitle1" fontWeight="bold">
                    {getMilestoneBadge()}
                  </Typography>
                </Box>
              )}

              {/* Tap to close hint */}
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mt: 3 }}
              >
                Tap anywhere to continue
              </Typography>
            </SuccessContainer>
          </Zoom>
        </Box>
      </Fade>
    </>
  );
};

// Simpler inline success indicator (for embedding in forms)
interface InlineSuccessProps {
  show: boolean;
  message?: string;
}

export const InlineSuccess: React.FC<InlineSuccessProps> = ({
  show,
  message = 'Success!',
}) => {
  return (
    <Fade in={show}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          p: 2,
          bgcolor: 'success.light',
          borderRadius: 1,
        }}
      >
        <CheckCircle color="success" />
        <Typography color="success.dark" fontWeight="medium">
          {message}
        </Typography>
      </Box>
    </Fade>
  );
};

export default SuccessAnimation;
