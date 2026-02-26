import React from 'react';
import {
    AbsoluteFill,
    Video,
    Sequence,
    useCurrentFrame,
    useVideoConfig,
    staticFile,
    interpolate,
    spring,
} from 'remotion';
import { AnimatedCaptions } from './AnimatedCaptions';

interface CaptionToken {
    text: string;
    startMs: number;
    endMs: number;
}

interface CaptionPage {
    startMs: number;
    endMs: number;
    tokens: CaptionToken[];
}

interface ShortClipProps {
    videoSrc: string;
    captionPages: CaptionPage[];
    hookText: string;
}

export const ShortClip: React.FC<ShortClipProps> = ({
    videoSrc,
    captionPages,
    hookText,
}) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    // Hook text animation (first 3 seconds)
    const hookOpacity = interpolate(frame, [0, fps * 0.3, fps * 2.5, fps * 3], [0, 1, 1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
    });
    const hookScale = spring({ frame, fps, config: { damping: 15, stiffness: 120 } });

    // Progress bar
    const progress = (frame / durationInFrames) * 100;

    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            {/* Background video — already has blurred background from FFmpeg */}
            <Video
                src={videoSrc}
                style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            />

            {/* Hook text overlay (first 3 seconds) */}
            {hookText && (
                <Sequence durationInFrames={Math.floor(fps * 3)}>
                    <div
                        style={{
                            position: 'absolute',
                            top: '12%',
                            left: '8%',
                            right: '8%',
                            fontSize: 38,
                            fontWeight: 900,
                            color: 'white',
                            textAlign: 'center',
                            textShadow: '3px 3px 12px rgba(0,0,0,0.95)',
                            fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
                            opacity: hookOpacity,
                            transform: `scale(${hookScale})`,
                            lineHeight: 1.2,
                            background: 'linear-gradient(135deg, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0.3) 100%)',
                            padding: '16px 24px',
                            borderRadius: 16,
                            backdropFilter: 'blur(8px)',
                        }}
                    >
                        {hookText}
                    </div>
                </Sequence>
            )}

            {/* Animated TikTok-style captions */}
            <AnimatedCaptions pages={captionPages} />

            {/* Progress bar at bottom */}
            <div
                style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    height: 4,
                    width: `${progress}%`,
                    background: 'linear-gradient(90deg, #FF0050, #FF6B35)',
                    borderRadius: '0 2px 2px 0',
                }}
            />
        </AbsoluteFill>
    );
};
