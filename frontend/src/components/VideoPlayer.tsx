interface VideoPlayerProps {
    src: string;
}

export function VideoPlayer({ src }: VideoPlayerProps) {
    return (
        <div className="aspect-[9/16] max-w-sm mx-auto bg-black rounded-lg overflow-hidden shadow-2xl border border-slate-800">
            <video
                src={src}
                controls
                className="w-full h-full object-cover"
                preload="metadata"
                playsInline
            >
                Your browser does not support the video tag.
            </video>
        </div>
    );
}
