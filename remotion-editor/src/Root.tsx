import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { ShortClip, ShortClipProps } from './ShortClip';

export const RemotionRoot: React.FC = () => {
    const inputProps = getInputProps();

    // Default props for preview; overridden at render time
    const durationInFrames = inputProps?.durationInFrames || 30 * 30; // default 30s at 30fps

    const defaultProps: ShortClipProps = {
        videoSrc: (inputProps?.videoSrc as string) || '',
        captionPages: (inputProps?.captionPages as any) || [],
        hookText: (inputProps?.hookText as string) || 'Preview Hook Text',
    };

    return (
        <Composition
            id="ShortClip"
            component={ShortClip as React.FC<any>}
            durationInFrames={Number(durationInFrames)}
            fps={30}
            width={1080}
            height={1920}
            defaultProps={defaultProps}
        />
    );
};
