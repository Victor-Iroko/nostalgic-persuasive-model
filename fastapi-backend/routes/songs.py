"""
Song recommendation API routes.

This module provides endpoints for song recommendations using pgvector.
"""

from fastapi import APIRouter, Depends, HTTPException

from core.dependencies import get_song_recommender
from services.song_recommender import SongRecommender
from core.schemas import (
    ErrorResponse,
    SongDetails,
    SongInfo,
    SongRecommendation,
    SongRecommendByIdRequest,
    SongRecommendRequest,
    SongRecommendResponse,
    SongSearchRequest,
    SongSearchResponse,
)

router = APIRouter(prefix="/songs", tags=["Songs"])


@router.post(
    "/recommend",
    response_model=SongRecommendResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get song recommendations",
    description="Generate song recommendations based on a list of songs the user likes.",
)
async def recommend_songs(
    request: SongRecommendRequest,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongRecommendResponse:
    """
    Get song recommendations based on liked songs.

    Uses content-based filtering with pgvector similarity search.
    Averages the embeddings of liked songs and finds similar songs.
    """
    try:
        # Get info for query songs
        query_songs: list[SongInfo] = []
        for song_id in request.liked_song_ids:
            info = recommender.get_song_info(song_id)
            if info:
                query_songs.append(
                    SongInfo(
                        spotify_id=str(info.get("id", song_id)),
                        name=str(info.get("name", "Unknown")),
                        artists=str(info.get("artists", "Unknown")),
                        genre=str(info.get("genre")) if info.get("genre") else None,
                        year=int(info.get("year")) if info.get("year") else None,
                    )
                )

        # Generate recommendations - convert song IDs to the expected format
        liked_items = [{"spotify_id": sid, "timestamp": None} for sid in request.liked_song_ids]
        recommendations_df = recommender.recommend(
            liked_items=liked_items,
            n_recommendations=request.n_recommendations,
            exclude_liked=request.exclude_liked,
        )

        if recommendations_df.empty:
            return SongRecommendResponse(
                recommendations=[],
                query_songs=query_songs,
            )

        recommendations: list[SongRecommendation] = []
        for _, row in recommendations_df.iterrows():
            recommendations.append(
                SongRecommendation(
                    spotify_id=str(row["spotify_id"]),
                    name=str(row["name"]),
                    artists=str(row["artists"]),
                    genre=str(row.get("genre")) if row.get("genre") else None,
                    year=int(row.get("year")) if row.get("year") else None,
                    similarity=float(row.get("similarity", 0.0)),
                )
            )

        return SongRecommendResponse(
            recommendations=recommendations,
            query_songs=query_songs,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {e}") from e


@router.post(
    "/recommend/by-id",
    response_model=SongRecommendResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Song not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="Get song recommendations by single song ID",
    description="Generate song recommendations based on a single song.",
)
async def recommend_songs_by_id(
    request: SongRecommendByIdRequest,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongRecommendResponse:
    """
    Get song recommendations based on a single song.

    Uses the pre-computed embedding from pgvector for fastest query.
    """
    try:
        # Get info for query song
        info = recommender.get_song_info(request.spotify_id)
        if not info:
            raise HTTPException(
                status_code=404, detail=f"Song {request.spotify_id} not found in database"
            )

        query_song = SongInfo(
            spotify_id=str(info.get("id", request.spotify_id)),
            name=str(info.get("name", "Unknown")),
            artists=str(info.get("artists", "Unknown")),
            genre=str(info.get("genre")) if info.get("genre") else None,
            year=int(info.get("year")) if info.get("year") else None,
        )

        # Generate recommendations
        recommendations_df = recommender.recommend_by_id(
            spotify_id=request.spotify_id,
            n_recommendations=request.n_recommendations,
        )

        recommendations: list[SongRecommendation] = []
        for _, row in recommendations_df.iterrows():
            recommendations.append(
                SongRecommendation(
                    spotify_id=str(row["spotify_id"]),
                    name=str(row["name"]),
                    artists=str(row["artists"]),
                    genre=str(row.get("genre")) if row.get("genre") else None,
                    year=int(row.get("year")) if row.get("year") else None,
                    similarity=float(row.get("similarity", 0.0)),
                )
            )

        return SongRecommendResponse(
            recommendations=recommendations,
            query_songs=[query_song],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {e}") from e


@router.get(
    "/{spotify_id}",
    response_model=SongDetails,
    responses={
        404: {"model": ErrorResponse, "description": "Song not found"},
    },
    summary="Get song information",
    description="Get detailed information about a specific song by its Spotify ID.",
)
async def get_song(
    spotify_id: str,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongDetails:
    """Get detailed information about a specific song."""
    info = recommender.get_song_info(spotify_id)

    if not info:
        raise HTTPException(status_code=404, detail=f"Song {spotify_id} not found")

    return SongDetails(
        spotify_id=str(info.get("id", spotify_id)),
        name=str(info.get("name", "Unknown")),
        artists=str(info.get("artists", "Unknown")),
        genre=str(info.get("genre")) if info.get("genre") else None,
        year=int(info.get("year")) if info.get("year") else None,
        danceability=float(info.get("danceability")) if info.get("danceability") is not None else None,
        energy=float(info.get("energy")) if info.get("energy") is not None else None,
        key=int(info.get("key")) if info.get("key") is not None else None,
        loudness=float(info.get("loudness")) if info.get("loudness") is not None else None,
        mode=int(info.get("mode")) if info.get("mode") is not None else None,
        speechiness=float(info.get("speechiness")) if info.get("speechiness") is not None else None,
        acousticness=float(info.get("acousticness")) if info.get("acousticness") is not None else None,
        instrumentalness=float(info.get("instrumentalness")) if info.get("instrumentalness") is not None else None,
        liveness=float(info.get("liveness")) if info.get("liveness") is not None else None,
        valence=float(info.get("valence")) if info.get("valence") is not None else None,
        tempo=float(info.get("tempo")) if info.get("tempo") is not None else None,
        niche_genres=str(info.get("niche_genres")) if info.get("niche_genres") else None,
    )


@router.post(
    "/search",
    response_model=SongSearchResponse,
    summary="Search for songs",
    description="Search for songs by name or artist.",
)
async def search_songs(
    request: SongSearchRequest,
    recommender: SongRecommender = Depends(get_song_recommender),
) -> SongSearchResponse:
    """Search for songs by name or artist."""
    try:
        results_df = recommender.search_songs(request.query, limit=request.limit)

        results: list[SongInfo] = []
        for _, row in results_df.iterrows():
            results.append(
                SongInfo(
                    spotify_id=str(row["spotify_id"]),
                    name=str(row["name"]),
                    artists=str(row["artists"]),
                    genre=str(row.get("genre")) if row.get("genre") else None,
                    year=int(row.get("year")) if row.get("year") else None,
                )
            )

        return SongSearchResponse(
            results=results,
            query=request.query,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching songs: {e}") from e
