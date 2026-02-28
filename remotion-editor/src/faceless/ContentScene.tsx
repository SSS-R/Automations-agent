import React from 'react';
import { AbsoluteFill, Video, staticFile, Audio, Img, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { FacelessSceneData } from './types';
import { PALETTES, FONTS, ColorPalette, FontPreset } from './theme';
import { AnimatedCaptions } from '../AnimatedCaptions';

interface ContentSceneProps {
    scene: FacelessSceneData;
    color_palette?: ColorPalette;
    font_preset?: FontPreset;
}

export const ContentScene: React.FC<ContentSceneProps> = ({
    scene,
    color_palette = 'default',
    font_preset = 'inter'
}) => {
    const frame = useCurrentFrame();
    const { fps, durationInFrames } = useVideoConfig();

    // Ken Burns effect: subtle zoom from 1 to 1.15 over the duration of the scene
    const scale = interpolate(
        frame,
        [0, durationInFrames],
        [1, 1.15],
        { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    );

    const hasMedia = !!scene.asset_file;
    const isVideo = hasMedia && scene.asset_file!.endsWith('.mp4');

    // Theme values
    const theme = PALETTES[color_palette];
    const fontFamily = FONTS[font_preset];

    return (
        <AbsoluteFill style={{ backgroundColor: theme.bg }}>
            {/* Background Media with Ken Burns */}
            <AbsoluteFill style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}>
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
                    // Fallback gradient matching theme
                    <div style={{
                        width: '100%',
                        height: '100%',
                        background: `linear-gradient(135deg, ${theme.bg} 0%, ${theme.primary}55 100%)`, // 55 is hex opacity
                        opacity: 0.8
                    }} />
                )}
            </AbsoluteFill>

            {/* Audio narration */}
            {scene.audio_file && <Audio src={staticFile(scene.audio_file)} />}

            {/* Subtitles */}
            {scene.captionPages && scene.captionPages.length > 0 ? (
                // Pass font and color to AnimatedCaptions if we want theming there too
                // For now, standard AnimatedCaptions style, maybe wrap in a themed div if needed
                <div style={{ fontFamily }}>
                    <AnimatedCaptions pages={scene.captionPages} />
                </div>
            ) : (
                <div style={{
                    position: 'absolute',
                    bottom: 400,
                    width: '100%',
                    textAlign: 'center',
                    padding: '0 40px',
                    fontSize: 44,
                    fontWeight: 800,
                    color: theme.text,
                    fontFamily,
                    textShadow: '2px 2px 8px rgba(0,0,0,0.9)',
                }}>
                    {scene.text}
                </div>
            )}
        </AbsoluteFill>
    );
};
