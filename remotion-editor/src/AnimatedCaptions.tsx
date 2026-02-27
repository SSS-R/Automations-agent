import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

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

export const AnimatedCaptions: React.FC<{ pages: CaptionPage[] }> = ({ pages }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();
    const currentTimeMs = (frame / fps) * 1000;

    return (
        <div
            style={{
                position: 'absolute',
                bottom: 400,
                left: 0,
                right: 0,
                textAlign: 'center',
                padding: '0 40px',
            }}
        >
            {pages.map((page, i) => {
                if (currentTimeMs < page.startMs || currentTimeMs > page.endMs) return null;
                return (
                    <div
                        key={i}
                        style={{
                            fontSize: 44,
                            fontWeight: 800,
                            color: 'white',
                            textShadow: '2px 2px 8px rgba(0,0,0,0.9), 0 0 20px rgba(0,0,0,0.5)',
                            lineHeight: 1.3,
                            fontFamily: "'Inter', 'Helvetica Neue', sans-serif",
                            letterSpacing: '-0.5px',
                        }}
                    >
                        {page.tokens.map((token: CaptionToken, j: number) => {
                            const isActive = currentTimeMs >= token.startMs;
                            return (
                                <span
                                    key={j}
                                    style={{
                                        color: isActive ? '#FFD700' : 'white',
                                        transition: 'color 0.05s ease-out',
                                        display: 'inline',
                                    }}
                                >
                                    {token.text}
                                </span>
                            );
                        })}
                    </div>
                );
            })}
        </div>
    );
};
