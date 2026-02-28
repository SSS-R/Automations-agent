import React from 'react';
import { AbsoluteFill, Series, Audio, staticFile } from 'remotion';
import { FacelessVideoProps } from '../types';
import { HookScene } from '../HookScene';
import { ContentScene } from '../ContentScene';
import { CTAScene } from '../CTAScene';

export const BoldTemplate: React.FC<FacelessVideoProps> = ({
    hook,
    hook_audio_file,
    hookDurationInFrames,
    scenes,
    cta,
    cta_audio_file,
    ctaDurationInFrames,
    font_preset = 'montserrat',
    color_palette = 'neon'
}) => {
    return (
        <AbsoluteFill style={{ backgroundColor: '#000' }}>
            <Series>
                <Series.Sequence durationInFrames={hookDurationInFrames}>
                    <HookScene text={hook} audioFile={hook_audio_file} />
                </Series.Sequence>

                {scenes.map((scene, index) => (
                    <Series.Sequence key={index} durationInFrames={scene.durationInFrames}>
                        {/* Wrapper to apply theme props to ContentScene later, or just bold styles here */}
                        <AbsoluteFill style={{
                            border: '20px solid #00FF41', // bold neon border
                            boxSizing: 'border-box'
                        }}>
                            <ContentScene scene={scene} />
                        </AbsoluteFill>
                    </Series.Sequence>
                ))}

                <Series.Sequence durationInFrames={ctaDurationInFrames}>
                    <CTAScene text={cta} audioFile={cta_audio_file} />
                </Series.Sequence>
            </Series>
            {/* Optional BGM */}
            {/* <Audio src={staticFile("bgm.mp3")} volume={0.15} /> */}
        </AbsoluteFill>
    );
};
