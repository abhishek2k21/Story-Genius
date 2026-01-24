from dataclasses import dataclass

@dataclass
class GenreConfig:
    id: str
    name: str
    description: str
    llm_prompt_style: str
    veo_style_prefix: str
    default_voice: str
    output_suffix: str

GENRE_PRESETS = {
    "1": GenreConfig(
        id="kids",
        name="Kids Animation",
        description="Disney/Pixar style, cheerful, and educational.",
        llm_prompt_style="Write a cute, moral-driven children's story. Simple language, happy ending.",
        veo_style_prefix="Animation, Disney Pixar style, 3d render, cute character design, vibrant colors, 4k",
        default_voice="en-US-AnaNeural", # Child-like or soft female
        output_suffix="kids_story"
    ),
    "2": GenreConfig(
        id="thriller",
        name="Thriller/Horror",
        description="Dark, suspenseful, and cinematic.",
        llm_prompt_style="Write a suspenseful thriller script. Short, punchy sentences. Unexpected twists. Dark tone.",
        veo_style_prefix="Cinematic, Photorealistic, 4k, Dark Atmosphere, Horror movie lighting, suspenseful",
        default_voice="en-US-ChristopherNeural", # Deep male
        output_suffix="thriller"
    ),
    "3": GenreConfig(
        id="scifi",
        name="Sci-Fi / Future",
        description="Futuristic, cyberpunk, and high-tech.",
        llm_prompt_style="Write a sci-fi narrative about the future, technology, or space. Tech-heavy vocabulary.",
        veo_style_prefix="Cinematic, Sci-fi, Cyberpunk, Neon lights, Futuristic city, High tech, 4k",
        default_voice="en-US-EricNeural", # Energetic/Neutral
        output_suffix="scifi"
    ),
    "4": GenreConfig(
        id="nature",
        name="Nature Documentary",
        description="National Geographic style, realistic nature.",
        llm_prompt_style="Write a documentary-style script about nature or wildlife. Informative and majestic tone.",
        veo_style_prefix="National Geographic footage, 4k, Photorealistic, Wildlife photography, cinematic nature",
        default_voice="en-US-GuyNeural", # Neutral Male
        output_suffix="nature"
    ),
    "5": GenreConfig(
        id="history",
        name="History / Mythology",
        description="Historical events or myths with epic visuals.",
        llm_prompt_style="Write an epic historical or mythological tale. Grandiose language, legends, and battles.",
        veo_style_prefix="Cinematic, Historical drama, Oil painting style, Epic scale, detailed costumes, 4k",
        default_voice="en-GB-RyanNeural", # British Male
        output_suffix="history"
    ),
    "6": GenreConfig(
        id="motivation",
        name="Motivation / Success",
        description="High energy, lux aesthetic for reels.",
        llm_prompt_style="Write a motivational speech. Powerful, Alpha mentality, success-oriented.",
        veo_style_prefix="Cinematic, Luxury aesthetic, Success, High contrast, 4k, commercial look",
        default_voice="en-US-ChristopherNeural", # Deep Male
        output_suffix="motivation"
    ),
    "7": GenreConfig(
        id="bedtime",
        name="Bedtime Story",
        description="Soothing, dreamy, and calm.",
        llm_prompt_style="Write a very calming, slow-paced bedtime story. Focus on sleep, dreams, and comfort.",
        veo_style_prefix="Watercolor style, Dreamy, Soft lighting, ethereal, pastel colors, 4k",
        default_voice="en-US-MichelleNeural", # Soft Female
        output_suffix="bedtime"
    ),
    "8": GenreConfig(
        id="comedy",
        name="Comedy / Skit",
        description="Funny, bright, and cartoonish.",
        llm_prompt_style="Write a funny, slapstick comedy script. Jokes, funny situations, lighthearted.",
        veo_style_prefix="Animation, 3D cartoon, Bright lighting, Funny character expressions, 4k",
        default_voice="en-US-EricNeural",
        output_suffix="comedy"
    ),
    "9": GenreConfig(
        id="noir",
        name="Crime / Noir",
        description="Black and white, detective style.",
        llm_prompt_style="Write a hard-boiled detective noir script. Cynical tone, crime mystery.",
        veo_style_prefix="Film Noir, Black and White, High Contrast, Shadowy, 1940s style, Cinematic",
        default_voice="en-US-ChristopherNeural",
        output_suffix="noir"
    ),
    "10": GenreConfig(
        id="romance",
        name="Love / Romance",
        description="Romantic, soft, and emotional.",
        llm_prompt_style="Write a romantic love story. Emotional, poetic, focusing on feelings and relationships.",
        veo_style_prefix="Cinematic, Warm lighting, Romance, Soft focus, Aesthetic, 4k",
        default_voice="en-US-AriaNeural",
        output_suffix="romance"
    )
}
