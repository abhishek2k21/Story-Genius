"""
GraphQL API with Real-Time Subscriptions.
Flexible queries and real-time updates via WebSocket.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from ariadne import QueryType, MutationType, SubscriptionType, make_executable_schema
from ariadne.asgi import GraphQL
from graphql import GraphQLResolveInfo
import asyncio
import logging

logger = logging.getLogger(__name__)


# GraphQL Schema Definition
type_defs = """
    scalar DateTime
    
    type Query {
        me: User!
        user(id: ID!): User
        
        videos(
            page: Int = 1
            limit: Int = 20
            filter: VideoFilter
            orderBy: VideoOrderBy
        ): VideoConnection!
        
        video(id: ID!): Video
        
        analytics(
            userId: ID
            period: Period!
            metrics: [Metric!]!
        ): Analytics!
    }
    
    type Mutation {
        createVideo(input: CreateVideoInput!): Video!
        updateVideo(id: ID!, input: UpdateVideoInput!): Video!
        deleteVideo(id: ID!): Boolean!
        publishVideo(id: ID!, platforms: [Platform!]!): PublishResult!
        
        updateProfile(input: UpdateProfileInput!): User!
        updateSettings(input: SettingsInput!): Settings!
    }
    
    type Subscription {
        videoViewsUpdated(videoId: ID!): VideoViews!
        analyticsUpdated(userId: ID!): Analytics!
        videoProcessingStatus(videoId: ID!): ProcessingStatus!
        notificationReceived: Notification!
    }
    
    type User {
        id: ID!
        email: String!
        firstName: String
        lastName: String
        profilePicture: String
        plan: String!
        createdAt: DateTime!
        videos(limit: Int = 10): [Video!]!
        analytics: UserAnalytics!
    }
    
    type Video {
        id: ID!
        title: String!
        description: String
        url: String!
        thumbnailUrl: String
        duration: Int
        views: Int!
        likes: Int!
        shares: Int!
        createdAt: DateTime!
        updatedAt: DateTime!
        user: User!
        analytics: VideoAnalytics
        versions: [VideoVersion!]!
    }
    
    type VideoConnection {
        edges: [VideoEdge!]!
        pageInfo: PageInfo!
        totalCount: Int!
    }
    
    type VideoEdge {
        node: Video!
        cursor: String!
    }
    
    type PageInfo {
        hasNextPage: Boolean!
        hasPreviousPage: Boolean!
        startCursor: String
        endCursor: String
    }
    
    type Analytics {
        period: Period!
        metrics: [MetricData!]!
        charts: [ChartData!]!
    }
    
    type MetricData {
        name: String!
        value: Float!
        change: Float
        trend: String
    }
    
    type VideoViews {
        videoId: ID!
        views: Int!
        timestamp: DateTime!
    }
    
    type ProcessingStatus {
        videoId: ID!
        status: String!
        progress: Int!
        message: String
    }
    
    input CreateVideoInput {
        title: String!
        description: String
        file: Upload!
    }
    
    input UpdateVideoInput {
        title: String
        description: String
    }
    
    input VideoFilter {
        platform: Platform
        dateFrom: DateTime
        dateTo: DateTime
        minViews: Int
    }
    
    input VideoOrderBy {
        field: String!
        direction: OrderDirection!
    }
    
    enum Platform {
        YOUTUBE
        INSTAGRAM
        TIKTOK
        FACEBOOK
        TWITTER
    }
    
    enum Period {
        DAY
        WEEK
        MONTH
        YEAR
    }
    
    enum Metric {
        VIEWS
        LIKES
        SHARES
        ENGAGEMENT
        REVENUE
    }
    
    enum OrderDirection {
        ASC
        DESC
    }
"""


# Query Resolvers
query = QueryType()

@query.field("me")
async def resolve_me(obj, info: GraphQLResolveInfo):
    """Get current authenticated user."""
    user_id = info.context["user_id"]
    
    # Use DataLoader to batch user queries
    user = await info.context["user_loader"].load(user_id)
    
    return user


@query.field("videos")
async def resolve_videos(
    obj,
    info: GraphQLResolveInfo,
    page: int = 1,
    limit: int = 20,
    filter: Optional[Dict] = None,
    orderBy: Optional[Dict] = None
):
    """
    Resolve videos with pagination and filtering.
    
    Uses DataLoader pattern for efficient database querying.
    """
    user_id = info.context["user_id"]
    
    # Build query
    query_params = {
        "user_id": user_id,
        "page": page,
        "limit": limit
    }
    
    if filter:
        query_params["filter"] = filter
    
    if orderBy:
        query_params["order_by"] = orderBy
    
    # Fetch videos
    videos = await info.context["video_service"].get_videos(**query_params)
    total_count = await info.context["video_service"].count_videos(user_id, filter)
    
    # Build connection
    edges = [
        {
            "node": video,
            "cursor": str(video["id"])
        }
        for video in videos
    ]
    
    return {
        "edges": edges,
        "pageInfo": {
            "hasNextPage": len(videos) == limit,
            "hasPreviousPage": page > 1,
            "startCursor": edges[0]["cursor"] if edges else None,
            "endCursor": edges[-1]["cursor"] if edges else None
        },
        "totalCount": total_count
    }


@query.field("analytics")
async def resolve_analytics(
    obj,
    info: GraphQLResolveInfo,
    userId: Optional[str] = None,
    period: str = "WEEK",
    metrics: List[str] = []
):
    """Resolve analytics data."""
    user_id = userId or info.context["user_id"]
    
    analytics = await info.context["analytics_service"].get_analytics(
        user_id=user_id,
        period=period.lower(),
        metrics=[m.lower() for m in metrics]
    )
    
    return analytics


# Mutation Resolvers
mutation = MutationType()

@mutation.field("createVideo")
async def resolve_create_video(
    obj,
    info: GraphQLResolveInfo,
    input: Dict
):
    """Create new video."""
    user_id = info.context["user_id"]
    
    video = await info.context["video_service"].create_video(
        user_id=user_id,
        title=input["title"],
        description=input.get("description"),
        file=input["file"]
    )
    
    logger.info(f"Created video {video['id']} via GraphQL")
    
    return video


@mutation.field("updateVideo")
async def resolve_update_video(
    obj,
    info: GraphQLResolveInfo,
    id: str,
    input: Dict
):
    """Update video."""
    user_id = info.context["user_id"]
    
    # Check permissions
    video = await info.context["video_service"].get_video(id)
    
    if video["user_id"] != user_id:
        raise PermissionError("Not authorized to update this video")
    
    updated_video = await info.context["video_service"].update_video(
        video_id=id,
        updates=input
    )
    
    return updated_video


@mutation.field("deleteVideo")
async def resolve_delete_video(
    obj,
    info: GraphQLResolveInfo,
    id: str
):
    """Delete video."""
    user_id = info.context["user_id"]
    
    success = await info.context["video_service"].delete_video(
        video_id=id,
        user_id=user_id
    )
    
    return success


@mutation.field("publishVideo")
async def resolve_publish_video(
    obj,
    info: GraphQLResolveInfo,
    id: str,
    platforms: List[str]
):
    """Publish video to platforms."""
    user_id = info.context["user_id"]
    
    result = await info.context["publishing_service"].publish_video(
        video_id=id,
        user_id=user_id,
        platforms=[p.lower() for p in platforms]
    )
    
    return result


# Subscription Resolvers
subscription = SubscriptionType()

@subscription.source("videoViewsUpdated")
async def video_views_generator(obj, info: GraphQLResolveInfo, videoId: str):
    """
    Real-time video view updates via WebSocket.
    
    Streams view count updates every 5 seconds.
    """
    while True:
        # Get current view count
        views = await info.context["analytics_service"].get_video_views(videoId)
        
        yield {
            "videoId": videoId,
            "views": views,
            "timestamp": datetime.utcnow()
        }
        
        await asyncio.sleep(5)


@subscription.field("videoViewsUpdated")
def resolve_video_views(view_data, info: GraphQLResolveInfo, videoId: str):
    """Resolve video views subscription."""
    return view_data


@subscription.source("analyticsUpdated")
async def analytics_generator(obj, info: GraphQLResolveInfo, userId: str):
    """Stream analytics updates."""
    while True:
        analytics = await info.context["analytics_service"].get_real_time_analytics(userId)
        
        yield analytics
        
        await asyncio.sleep(10)


@subscription.field("analyticsUpdated")
def resolve_analytics_updated(analytics, info: GraphQLResolveInfo, userId: str):
    """Resolve analytics subscription."""
    return analytics


@subscription.source("videoProcessingStatus")
async def processing_status_generator(obj, info: GraphQLResolveInfo, videoId: str):
    """Stream video processing status."""
    
    # Subscribe to processing events
    async for status in info.context["processing_service"].subscribe_status(videoId):
        yield status


@subscription.field("videoProcessingStatus")
def resolve_processing_status(status, info: GraphQLResolveInfo, videoId: str):
    """Resolve processing status subscription."""
    return status


# Field Resolvers
@query.field("user")
@mutation.field("user")
async def resolve_user_videos(user, info: GraphQLResolveInfo, limit: int = 10):
    """Resolve user's videos."""
    videos = await info.context["video_loader"].load_user_videos(
        user_id=user["id"],
        limit=limit
    )
    return videos


# Create executable schema
schema = make_executable_schema(type_defs, query, mutation, subscription)

# Create ASGI app
graphql_app = GraphQL(schema, debug=True)


# FastAPI integration
"""
from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# GraphQL endpoint
app.mount("/graphql", graphql_app)

# GraphQL Playground (development only)
from ariadne.explorer import ExplorerGraphQL

explorer = ExplorerGraphQL()
app.mount("/graphql/playground", explorer)
"""


# Usage Example - Client Side
"""
# GraphQL query from React Native

const GET_VIDEOS = gql`
  query GetVideos($page: Int, $limit: Int) {
    videos(page: $page, limit: $limit) {
      edges {
        node {
          id
          title
          thumbnailUrl
          views
          likes
          createdAt
        }
      }
      pageInfo {
        hasNextPage
      }
      totalCount
    }
  }
`;

// Subscription
const VIDEO_VIEWS_SUBSCRIPTION = gql`
  subscription OnVideoViewsUpdated($videoId: ID!) {
    videoViewsUpdated(videoId: $videoId) {
      videoId
      views
      timestamp
    }
  }
`;

// Apollo Client setup
import { ApolloClient, InMemoryCache, split, HttpLink } from '@apollo/client';
import { GraphQLWsLink } from '@apollo/client/link/subscriptions';
import { getMainDefinition } from '@apollo/client/utilities';
import { createClient } from 'graphql-ws';

const httpLink = new HttpLink({
  uri: 'https://api.ytvideocreator.com/graphql'
});

const wsLink = new GraphQLWsLink(
  createClient({
    url: 'wss://api.ytvideocreator.com/graphql'
  })
);

const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

const client = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache()
});
"""
