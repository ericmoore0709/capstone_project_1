# Spotify Playlist Manager

Welcome to the **Spotify Playlist Manager**! You can explore the deployed site [here](https://capstone-project-1-wiz3.onrender.com).

## Description

The Spotify Playlist Manager is a web application that integrates with the Spotify API to provide users with the ability to manage their Spotify playlists effortlessly. Users can log in with their Spotify credentials, view their playlists, add or remove tracks, and create new playlists directly from the app.

## Features

1. **User Authentication**:
    - **Why**: Ensures that only authorized users can access and manage their Spotify playlists.
    - **Implementation**: Utilizes Spotify's OAuth2 authorization for secure user authentication.

2. **View Playlists**:
    - **Why**: Allows users to see all their saved playlists in one place.
    - **Implementation**: Fetches and displays playlists using Spotify's API.

3. **View Playlist Details**:
    - **Why**: Provides users with detailed information about the tracks in their playlists.
    - **Implementation**: Retrieves and displays track information for a selected playlist.

4. **Search Tracks**:
    - **Why**: Enables users to find tracks to add to their playlists.
    - **Implementation**: Implements a search bar that queries Spotify's database for tracks matching the user's input.

5. **Add Tracks to Playlist**:
    - **Why**: Gives users the ability to customize their playlists by adding new tracks.
    - **Implementation**: Allows users to select and add tracks to a playlist from the search results.

6. **Remove Tracks from Playlist**:
    - **Why**: Allows users to manage the content of their playlists by removing unwanted tracks.
    - **Implementation**: Enables users to remove tracks directly from their playlists.

7. **Create New Playlist**:
    - **Why**: Provides users with the flexibility to create new playlists.
    - **Implementation**: Allows users to create new playlists with a custom title and description.

## User Flow

1. **Landing Page**:
    - Users are greeted with a landing page where they can log in using their Spotify credentials.

2. **Dashboard**:
    - After logging in, users are redirected to the dashboard where they can see a list of their playlists.

3. **View Playlist**:
    - Users can click on a playlist to view its details, including the list of tracks.

4. **Search Tracks**:
    - Users can use the search bar to find new tracks to add to their playlists.

5. **Add Track**:
    - From the search results, users can add a track to one of their playlists.

6. **Remove Track**:
    - Users can remove tracks from their playlists by clicking on a remove button.

7. **Create Playlist**:
    - Users can create new playlists by providing a title and optional description.

## API Usage

The Spotify Playlist Manager relies heavily on the Spotify Web API to retrieve and manipulate user data. Some key API endpoints used include:
- `GET /me/playlists`: Retrieves the current user's playlists.
- `GET /playlists/{playlist_id}`: Retrieves detailed information about a specific playlist.
- `GET /search`: Searches for tracks based on a query.
- `POST /playlists/{playlist_id}/tracks`: Adds a track to a playlist.
- `DELETE /playlists/{playlist_id}/tracks`: Removes a track from a playlist.
- `POST /users/{user_id}/playlists`: Creates a new playlist.

The API calls are managed through Python requests in the Flask backend, ensuring secure and efficient communication with Spotify's servers.

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS (Bootstrap), JavaScript (jQuery, Axios)
- **Authentication**: OAuth2 (Spotify)
- **Environment Management**: Python-dotenv
- **Hosting**: Deployed on Render

## Additional Notes

- **Error Handling**: The app includes comprehensive error handling to manage API failures and user errors gracefully.
- **Security**: Uses Flask's session management and environment variables to secure user data and API keys.
- **Responsive Design**: The app is designed to be responsive and user-friendly across different devices.

We hope you enjoy using the Spotify Playlist Manager! If you have any questions or feedback, please feel free to reach out.