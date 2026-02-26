import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { ShortClip } from './ShortClip';

export const RemotionRoot: React.FC = () => {
    const inputProps = getInputProps();

    // Default props for preview; overridden at render time
    const durationInFrames = inputProps?.durationInFrames || 30 * 30; // default 30s at 30fps
    const hookText = inputProps?.hookText || 'Preview Hook Text';
    const videoSrc = inputProps?.videoSrc || '';
    const captionPages = inputProps?.captionPages || [];

    return (
        <Composition
            id="ShortClip"
            component={ShortClip}
            durationInFrames={Number(durationInFrames)}
            fps={30}
            width={1080}
            height={1920}
            defaultProps={{
                videoSrc,
                captionPages,
                hookText,
            }}
        />
    );
};
