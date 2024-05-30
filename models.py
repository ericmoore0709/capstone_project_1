class Playlist:

    """
    A class to represent a Spotify playlist.

    Attributes:
    -----------
    spotify_id : str
        The Spotify ID of the playlist.
    name : str
        The name of the playlist. This is a required field.
    description : str
        The description of the playlist.
    public : bool
        A flag indicating if the playlist is public. Defaults to True.
    collaborative : bool
        A flag indicating if the playlist is collaborative. Defaults to False.
    owner_id : str
        The Spotify ID of the owner of the playlist.
    """

    def __init__(self, data: dict):
        """
        Constructs all the necessary attributes for the Playlist object.

        Parameters:
        -----------
        data : dict
            A dictionary containing the following keys:
            - 'spotify_id' (str): The Spotify ID of the playlist.
            - 'name' (str): The name of the playlist. This is a required field.
            - 'description' (str): The description of the playlist.
            - 'public' (bool): Indicates if the playlist is public. Defaults to True.
            - 'collaborative' (bool): Indicates if the playlist is collaborative. Defaults to False.
            - 'owner_id' (str): The Spotify ID of the owner of the playlist.

        Raises:
        -------
        ValueError
            If the 'name' key is missing or the value is an empty string.
        """

        self.spotify_id = data.get('spotify_id', '')

        name = data.get('name', '')
        if not name:
            raise ValueError('Playlist Name is required and cannot be blank.')
        self.name = name

        self.description = data.get('description', '')
        self.public = data.get('public', True)
        self.collaborative = data.get('collaborative', False)
        self.owner_id = data.get('owner_id', '')
