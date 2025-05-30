## Deployment Instructions

1. Go to the [Render dashboard](https://dashboard.render.com/blueprints).
2. Click **Add New Blueprint Instance** by visiting this [link](https://dashboard.render.com/select-repo?type=blueprint).
3. Add the public Director Git repository: [Director Repository](https://github.com/video-db/Director). Alternatively, you can fork the repository and connect your fork to your Railway account.
4. Set a name for the blueprint and deploy it. This will deploy both the frontend and backend services.


### Backend Configuration

After deployment, update the backend environment variables:
    ``` 
    VIDEO_DB_API_KEY="your_video_db_api_key"
    ```

### Frontend Configuration

Next, update the frontend environment variables:
    ```
    VITE_APP_BACKEND_URL="deployed_backend_service_public_url"
    ```

Once the deployment is complete, navigate to the frontend service URL in your web browser to access the Director application.
