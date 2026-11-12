# API Routes

Routes are defined in the `routes` folder.


## Session routes

### GET /session

Returns all the sessions

```json
[
    {
        "collection_id": "c-**",
        "created_at": 1729092742,
        "metadata": {},
        "session_id": "52881f6b-7560-4844-ac35-52af41d07ab8",
        "updated_at": 1729092742,
        "video_id": "m-**"
    },
    {
        "collection_id": "c-**",
        "created_at": 1729092642,
        "metadata": {},
        "session_id": "6bf075a7-e7d4-4aba-985c-4cf0d3dc6f5b",
        "updated_at": 1729092642,
        "video_id": "m-**"
    }
]
```

### GET /session/:session_id

Returns the session

```json
{
    "collection_id": "c-**",
    "conversation": [
        {
            "actions": [],
            "agents": [],
            "content": [
                {
                    "text": "No of video in my collection?",
                    "type": "text"
                }
            ],
            "conv_id": "b36c0a31-3c95-4f48-a1aa-daad351a30c3",
            "created_at": 1729852558,
            "metadata": {},
            "msg_id": "1b753948-3672-446d-a7ab-ecd623d4244a",
            "msg_type": "input",
            "session_id": "33a41576-ffb3-4cec-993c-eedd728c21ac",
            "status": "success",
            "updated_at": 1729852558
        },
        {
            "actions": [
                "Reasoning the message.."
            ],
            "agents": [],
            "content": [
                {
                    "agent_name": null,
                    "status": "success",
                    "status_message": "Here is the summary of the response",
                    "text": "There are 36 videos in your collection.",
                    "type": "text"
                }
            ],
            "conv_id": "b36c0a31-3c95-4f48-a1aa-daad351a30c3",
            "created_at": 1729852562,
            "metadata": {},
            "msg_id": "172985255862403.2",
            "msg_type": "output",
            "session_id": "33a41576-ffb3-4cec-993c-eedd728c21ac",
            "status": "success",
            "updated_at": 1729852562
        }
    ],
    "created_at": 1729852558,
    "metadata": {},
    "session_id": "33a41576-ffb3-4cec-993c-eedd728c21ac",
    "updated_at": 1729852558,
    "video_id": null
}
```

### DELETE /session/:session_id

Deletes the session

```json
{
    "message": "Session deleted successfully."
}
```


## VideoDB routes

### GET /videodb/collection

Returns all the collections

```json
[
    {
        "description": "Test collection",
        "id": "c-**",
        "name": "Ankit Raj's collection"
    },
    {
        "description": "Test1 collection",
        "id": "c-**",
        "name": "Ankit Raj's collection"
    },
]
```

### GET /videodb/collection/:collection_id

Returns the collection

```json
{
    "description": "Test collection",
    "id": "c-**",
    "name": "Ankit Raj's collection"
}
```


### GET /videodb/collection/:collection_id/video

Returns all the videos in the collection

```json
[
    {
        "collection_id": "c-**",
        "description": null,
        "id": "m-**",
        "length": 1247.468844,
        "name": "Test video",
        "stream_url": "https://stream.videodb.io/v3/published/manifests/test.m3u8",
        "thumbnail_url": null
    },
    {
        "collection_id": "c-**",
        "description": null,
        "id": "m-**",
        "length": 155.620136,
        "name": "Test video",
        "stream_url": "https://stream.videodb.io/v3/published/manifests/test.m3u8",
        "thumbnail_url": null
    },
]
```

### GET /videodb/collection/:collection_id/video/:video_id

Returns the video

```json
{
    "collection_id": "c-**",
    "description": null,
    "id": "m-**",
    "length": 1247.468844,
    "name": "Test video",
    "stream_url": "https://stream.videodb.io/v3/published/manifests/test.m3u8",
    "thumbnail_url": null
}
```


## Config routes

### GET /config/check

Check the configuration

```json
{
    "db_configured": true,
    "llm_configured": true,
    "videodb_configured": true
}
```