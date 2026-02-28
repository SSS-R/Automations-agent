import React from 'react';
import { AbsoluteFill, Series, Audio, staticFile } from 'remotion';
import { FacelessVideoProps } from '../types';
import { HookScene } from '../HookScene';
import { ContentScene } from '../ContentScene';
import { CTAScene } from '../CTAScene';

export const TechTemplate: React.FC<FacelessVideoProps> = ({
    hook,
    hook_audio_file,
    hookDurationInFrames,
    scenes,
    cta,
    cta_audio_file,
    ctaDurationInFrames,
    font_preset = 'roboto',
    color_palette = 'cyberpunk'
}) => {
    return (
        <AbsoluteFill style={{ backgroundColor: '#101820' }}>
            {/* Subtle grid overlay could go here */}
            <div style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundImage: 'linear-gradient(rgba(0, 255, 65, 0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 255, 65, 0.1) 1px, transparent 1px)',
                backgroundSize: '40px 40px',
                zIndex: 1,
                pointerEvents: 'none'
            }} />

            <Series>
                <Series.Sequence durationInFrames={hookDurationInFrames}>
                    <HookScene text={hook} audioFile={hook_audio_file} />
                </Series.Sequence>

                {scenes.map((scene, index) => (
                    <Series.Sequence key={index} durationInFrames={scene.durationInFrames}>
                        <ContentScene scene={scene} />
                    </Series.Sequence>
                ))}

                <Series.Sequence durationInFrames={ctaDurationInFrames}>
                    <CTAScene text={cta} audioFile={cta_audio_file} />
                </Series.Sequence>
            </Series>
        </AbsoluteFill>
    );
};
