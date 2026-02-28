export interface CaptionToken {
    text: string;
    startMs: number;
    endMs: number;
}

export interface CaptionPage {
    startMs: number;
    endMs: number;
    tokens: CaptionToken[];
}

export interface FacelessSceneData {
    text: string;
    durationInFrames: number;
    asset_file?: string;
    audio_file?: string;
    captionPages?: CaptionPage[];
    emotion?: string;
    visual_keyword?: string;
}

export interface FacelessVideoProps {
    title: string;
    hook: string;
    hookDurationInFrames: number;
    hook_audio_file?: string;
    scenes: FacelessSceneData[];
    cta: string;
    ctaDurationInFrames: number;
    cta_audio_file?: string;
    template?: 'minimal' | 'bold' | 'tech';
}
