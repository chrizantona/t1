"""
Track (sphere) determination logic.
"""
from typing import Literal

TrackType = Literal["backend", "frontend", "fullstack", "data", "devops", "mobile", "other"]

# Keywords for track detection
TRACK_KEYWORDS = {
    "backend": [
        "python", "java", "spring", "fastapi", "django", "flask",
        "rest", "api", "sql", "postgres", "mysql", "mongodb",
        "node", "express", "golang", "rust", "backend"
    ],
    "frontend": [
        "javascript", "typescript", "react", "vue", "angular",
        "css", "html", "sass", "webpack", "vite", "frontend",
        "ui", "ux", "dom", "browser"
    ],
    "fullstack": [
        "fullstack", "full-stack", "full stack", "mern", "mean",
        "lamp", "jamstack"
    ],
    "data": [
        "data", "ml", "machine learning", "ai", "pandas", "numpy",
        "tensorflow", "pytorch", "sklearn", "jupyter", "analytics",
        "bigdata", "spark", "hadoop"
    ],
    "devops": [
        "devops", "docker", "kubernetes", "k8s", "ci/cd", "jenkins",
        "gitlab", "terraform", "ansible", "aws", "azure", "gcp",
        "cloud", "infrastructure"
    ],
    "mobile": [
        "mobile", "ios", "android", "swift", "kotlin", "react native",
        "flutter", "xamarin", "app store", "play store"
    ]
}


def determine_track(
    self_claimed_track: str | None,
    resume_text: str,
    resume_tracks: list[str] | None = None
) -> TrackType:
    """
    Determine candidate's track based on:
    1. Self-claimed track (highest priority)
    2. Resume tracks from LLM
    3. Keyword analysis of resume text
    
    Returns one of: backend, frontend, fullstack, data, devops, mobile, other
    """
    # 1. If explicitly claimed, use it
    if self_claimed_track and self_claimed_track in TRACK_KEYWORDS:
        return self_claimed_track
    
    # 2. If LLM extracted tracks, use first one
    if resume_tracks and len(resume_tracks) > 0:
        for track in resume_tracks:
            if track in TRACK_KEYWORDS:
                return track
    
    # 3. Keyword-based detection
    resume_lower = resume_text.lower()
    
    track_scores = {}
    for track, keywords in TRACK_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in resume_lower)
        track_scores[track] = score
    
    # Get track with highest score
    if track_scores:
        best_track = max(track_scores.items(), key=lambda x: x[1])
        if best_track[1] > 0:  # At least one keyword found
            return best_track[0]
    
    # Default to backend if nothing found
    return "backend"


def get_track_display_name(track: TrackType) -> str:
    """Get human-readable track name."""
    names = {
        "backend": "Backend разработка",
        "frontend": "Frontend разработка",
        "fullstack": "Fullstack разработка",
        "data": "Data Science / ML",
        "devops": "DevOps / Infrastructure",
        "mobile": "Mobile разработка",
        "other": "Другое"
    }
    return names.get(track, track)

# пидормот
