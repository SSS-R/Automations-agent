import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, Audio, staticFile } from 'remotion';

interface HookSceneProps {
    text: string;
    audioFile?: string;
}

export const HookScene: React.FC<HookSceneProps> = ({ text, audioFile }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const scale = spring({
        frame,
        fps,
        config: { damping: 12, stiffness: 100 },
    });

    const opacity = spring({
        frame,
        fps,
        config: { damping: 20, stiffness: 100 },
        durationInFrames: 15,
    });

    return (
        <AbsoluteFill style={{ backgroundColor: '#111', justifyContent: 'center', alignItems: 'center' }}>
            {audioFile && <Audio src={staticFile(audioFile)} />}

            <div
                style={{
                    fontSize: 80,
                    fontWeight: 900,
                    color: 'white',
                    textAlign: 'center',
                    textTransform: 'uppercase',
                    lineHeight: 1.1,
                    fontFamily: "'Inter', sans-serif",
                    transform: `scale(${scale})`,
                    opacity: opacity,
                    padding: '0 40px',
                    textShadow: '0 10px 30px rgba(0,0,0,0.5)',
                }}
            >
                {/* Highlight specific words by making them a different color, simple implementation: randomly or by parsing */}
                {text.split(' ').map((word, i) => (
                    <span key={i} style={{ color: i % 3 === 0 ? '#FFD700' : 'white' }}>
                        {word}{' '}
                    </span>
                ))}
            </div>
        </AbsoluteFill>
    );
};
