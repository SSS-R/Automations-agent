import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, Audio, staticFile } from 'remotion';

interface CTASceneProps {
    text: string;
    audioFile?: string;
}

export const CTAScene: React.FC<CTASceneProps> = ({ text, audioFile }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const yOffset = spring({
        frame,
        fps,
        config: { damping: 15, stiffness: 80 },
        from: 100,
        to: 0,
    });

    const opacity = spring({
        frame,
        fps,
        config: { damping: 20 },
        from: 0,
        to: 1,
    });

    return (
        <AbsoluteFill style={{ backgroundColor: '#000', justifyContent: 'center', alignItems: 'center' }}>
            {audioFile && <Audio src={staticFile(audioFile)} />}

            <div
                style={{
                    fontSize: 60,
                    fontWeight: 800,
                    color: 'white',
                    textAlign: 'center',
                    fontFamily: "'Inter', sans-serif",
                    transform: `translateY(${yOffset}px)`,
                    opacity: opacity,
                    padding: '0 40px',
                    background: 'rgba(255,255,255,0.1)',
                    borderRadius: 20,
                    border: '2px solid rgba(255,255,255,0.2)',
                    paddingTop: 40,
                    paddingBottom: 40,
                }}
            >
                <div>🔥</div>
                <div style={{ marginTop: 20 }}>{text}</div>
            </div>
        </AbsoluteFill>
    );
};
