import React from 'react';
import { Composition, getInputProps } from 'remotion';
import { ShortClip, ShortClipProps } from './ShortClip';
import { FacelessVideo } from './faceless/FacelessVideo';
import { FacelessVideoProps } from './faceless/types';
import mockData from '../../mock_faceless_script.json';

export const RemotionRoot: React.FC = () => {
    const inputProps = getInputProps();

    // Default props for preview; overridden at render time
    const durationInFrames = inputProps?.durationInFrames || 30 * 30; // default 30s at 30fps

    const defaultProps: ShortClipProps = {
        videoSrc: (inputProps?.videoSrc as string) || '',
        captionPages: (inputProps?.captionPages as any) || [],
        hookText: (inputProps?.hookText as string) || 'Preview Hook Text',
    };

    // Calculate duration for faceless video
    const facelessProps = ((inputProps as any)?.title ? inputProps : mockData) as unknown as FacelessVideoProps;
    const facelessDuration = facelessProps.hookDurationInFrames
        + facelessProps.scenes.reduce((acc, s) => acc + s.durationInFrames, 0)
        + facelessProps.ctaDurationInFrames;

    return (
        <>
            <Composition
                id="ShortClip"
                component={ShortClip as React.FC<any>}
                durationInFrames={Number(durationInFrames)}
                fps={30}
                width={1080}
                height={1920}
                defaultProps={defaultProps}
            />
            <Composition
                id="FacelessVideo"
                component={FacelessVideo as React.FC<any>}
                durationInFrames={facelessDuration || 300} // fallback to 10s if calculation fails
                fps={30}
                width={1080}
                height={1920}
                defaultProps={facelessProps}
            />
        </>
    );
};
