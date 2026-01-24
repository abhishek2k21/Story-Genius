try:
    from moviepy import VideoFileClip, vfx
    print("Import vfx success")
except ImportError:
    print("Direct import failed")
    try:
        import moviepy.video.fx.all as vfx
        print("Import fx.all success")
    except ImportError:
        print("fx.all failed")

try:
    from moviepy.video.fx import speedx
    print("Import speedx success")
except ImportError:
    print("Import speedx failed")
