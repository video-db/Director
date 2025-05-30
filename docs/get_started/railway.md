!!! note

    You need to be connected to GitHub account in https://railway.app/account/plans to perform the deployment.

## Deployment Instructions via Railway Template

1. Go to the [Director's Railway Template](https://railway.app/template/QJbo7o?referralCode=XiD6Mt).
2. Click **Deploy Now**.
3. Set the frontend environment variable `VITE_APP_BACKEND_URL` with a placeholder.
4. For the backend, configure the required environment variables `VIDEO_DB_API_KEY` and `OPENAI_API_KEY`. Optionally, you can configure additional environment variables as needed.
5. Click **Deploy**.
6. Once both services are deployed successfully, click on the backend service and copy the public URL (e.g., `https://backend-production-xxxx.up.railway.app`).
7. Update the frontend's `VITE_APP_BACKEND_URL` variable with the copied backend URL.
8. After updating the `VITE_APP_BACKEND_URL` variable, a **Deploy** option will appear. Click it to re-deploy the frontend.
9. Once deployment is complete, access the application through the frontend's public URL, such as `https://frontend-production-xxxx.up.railway.app`.

## Deployment Instructions via Railway CLI

1. Clone the Director repository to your local machine:
    ```
    git clone https://github.com/video-db/Director
    ```
2. Change the directory to the cloned repository:
    ```
    cd Director
    ```
3. Install the [Railway CLI](https://docs.railway.app/guides/cli).
4. Navigate to the Railway [Dashboard](https://railway.app/dashboard) and create an empty project.
5. Add two empty services to the project, and rename them as backend and frontend.
6. Log in to Railway via the CLI:
    ```
    railway login
    ```

### Deploy the backend service:

* Navigate to the backend service directory
* Link your project and the backend service
    ```
    railway link 
    ```
* Deploy the backend service
    ```
    railway up
    ```
    
### Deploy the frontend service:

* Navigate to the frontend service directory
* Link your project and the frontend service
    ```
    railway link 
    ```
* Deploy the frontend service
    ```
    railway up
    ```

### Backend Configuration
* After deployment, go to the [Railway project dashboard](https://railway.app/dashboard), and under the backend service, update the environment variables:
    ``` 
    VIDEO_DB_API_KEY="your_video_db_api_key"
    ```

* Go to Settings → Networking → Public Networking, generate a domain, and copy the domain. You will need to use this domain in the frontend service configuration.


### Frontend Configuration
* In the frontend service , update the following environment variable:
    ```
    VITE_APP_BACKEND_URL="deployed_backend_service_public_url"
    ```

* After deployment, generate a domain and navigate to the frontend service URL (which can be found in Settings → Networking → Public Networking) in your web browser to access the Director application.
