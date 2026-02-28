import React from 'react';
import { AbsoluteFill, Series, Audio, staticFile } from 'remotion';
import { FacelessVideoProps } from '../types';
import { HookScene } from '../HookScene';
import { ContentScene } from '../ContentScene';
import { CTAScene } from '../CTAScene';

export const MinimalTemplate: React.FC<FacelessVideoProps> = ({
    hook,
    hook_audio_file,
    hookDurationInFrames,
    scenes,
    cta,
    cta_audio_file,
    ctaDurationInFrames,
}) => {
    return (
        <AbsoluteFill style={{ backgroundColor: 'black' }}>
            <Series>
                {/* 1. Hook Scene */}
                <Series.Sequence durationInFrames={hookDurationInFrames}>
                    <HookScene text={hook} audioFile={hook_audio_file} />
                </Series.Sequence>

                {/* 2. Content Scenes */}
                {scenes.map((scene, index) => (
                    <Series.Sequence key={index} durationInFrames={scene.durationInFrames}>
                        <ContentScene scene={scene} />
                    </Series.Sequence>
                ))}

                {/* 3. CTA Scene */}
                <Series.Sequence durationInFrames={ctaDurationInFrames}>
                    <CTAScene text={cta} audioFile={cta_audio_file} />
                </Series.Sequence>
            </Series>

            {/* Optional background music could go here */}
            {/* <Audio src={staticFile("bgm.mp3")} volume={0.1} /> */}
        </AbsoluteFill>
    );
};
