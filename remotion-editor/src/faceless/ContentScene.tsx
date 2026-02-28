import React from 'react';
import { AbsoluteFill, Video, staticFile, Audio, Img } from 'remotion';
import { FacelessSceneData } from './types';
import { AnimatedCaptions } from '../AnimatedCaptions';

interface ContentSceneProps {
    scene: FacelessSceneData;
}

export const ContentScene: React.FC<ContentSceneProps> = ({ scene }) => {
    // If we have an asset, render it. If it ends in mp4, use Video, otherwise Img.
    const hasMedia = !!scene.asset_file;
    const isVideo = hasMedia && scene.asset_file!.endsWith('.mp4');

    return (
        <AbsoluteFill style={{ backgroundColor: '#222' }}>
            {/* Background Media */}
            {hasMedia ? (
                isVideo ? (
                    <Video
                        src={staticFile(scene.asset_file!)}
                        style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6 }}
                    />
                ) : (
                    <Img
                        src={staticFile(scene.asset_file!)}
                        style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6 }}
                    />
                )
            ) : (
                // Fallback gradient if no stock footage available
                <div style={{
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(135deg, #1f4037 0%, #99f2c8 100%)',
                    opacity: 0.8
                }} />
            )}

            {/* Audio narration */}
            {scene.audio_file && <Audio src={staticFile(scene.audio_file)} />}

            {/* Subtitles */}
            {scene.captionPages && scene.captionPages.length > 0 ? (
                <AnimatedCaptions pages={scene.captionPages} />
            ) : (
                // Fallback simple static text if no word-level timestamps exist yet
                <div style={{
                    position: 'absolute',
                    bottom: 400,
                    width: '100%',
                    textAlign: 'center',
                    padding: '0 40px',
                    fontSize: 44,
                    fontWeight: 800,
                    color: 'white',
                    fontFamily: "'Inter', sans-serif",
                    textShadow: '2px 2px 8px rgba(0,0,0,0.9)',
                }}>
                    {scene.text}
                </div>
            )}
        </AbsoluteFill>
    );
};
