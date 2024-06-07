function showAlert(message, type) {
    const alertContainer = $('#alert-container');
    const alert = $(`
        <div class="alert alert-${type} alert-dismissible fade show w-50 mx-auto" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `);
    alertContainer.append(alert);
}

$('#search_input').keyup(async (e) => {
    e.preventDefault();
    const searchTerm = $(e.target).val().trim();

    if (!searchTerm) {
        $('#searchbar_results_list').empty();
        return;
    }

    await axios.post('http://localhost:5000/searchbar', {
        q: searchTerm
    })
        .then((result) => {
            const tracks = result.data.tracks.items;
            $('#searchbar_results_list').empty();

            if (tracks.length > 0) {
                tracks.forEach((track) => {
                    const trackId = track.id;
                    const trackName = track.name;
                    const albumImage = track.album.images[0]?.url || 'default-image-url.jpg';  // Fallback if no image
                    const artistName = track.artists[0].name;

                    let $li = $(`
                        <li class="list-group-item p-0">
                            <div class="d-flex align-items-center">
                                <img src="${albumImage}" class="img-fluid rounded" alt="Album Image" style="width: 50px; height: 50px; object-fit: cover;">
                                <div class="d-flex flex-column justify-content-center mx-auto">
                                    <p class="mb-1 text-center"><strong><a href="/track/${trackId}">${trackName}</a></strong></p>
                                    <p class="mb-0 text-center"><small>${artistName}</small></p>
                                </div>
                            </div>
                        </li>
                    `);
                    $('#searchbar_results_list').append($li);
                });
            } else {
                let $li = $('<li></li>').addClass('list-group-item').text('No results found');
                $('#searchbar_results_list').append($li);
            }

        })
        .catch((err) => {
            console.log(err);

            $('#searchbar_results_list').empty();
            let $li = $('<li></li>').addClass('list-group-item list-group-item-danger').text('Failed to fetch results');
            $('#searchbar_results_list').append($li);
        });

});

$('#add_track_to_playlist_form').submit(async (e) => {
    e.preventDefault();

    // clear result message
    $('#addtrack_results_container').empty();

    // get the track uri and playlist id from the form
    const trackUri = $('#input_track_uri').val();
    const playlistId = $('#select_playlist_id').val();

    if (!playlistId) {
        // pop up an error message and return
        return;
    }

    let $resultMsg = $('<p></p>').addClass('list-group-item');

    // create backend API request
    await axios.post('http://localhost:5000/addtrack', {
        'track_uri': trackUri,
        'playlist_id': playlistId
    })
        .then((result) => {

            if (result.data.error) {
                // pop up error message
                $resultMsg.addClass('list-group-item-danger').text('Failed to add track to playlist.');
            }
            else {
                // pop up success message
                $resultMsg.addClass('list-group-item-success').text('Track added to playlist.');
            }
        })
        .catch((err) => {
            console.log(err);
            // pop up error message
            $resultMsg.addClass('list-group-item-danger').text('Something went wrong.');
        })
        .finally(() => {
            $('#addtrack_results_container').append($resultMsg)
        });

});

$('.track_remove').submit(async function (e) {
    e.preventDefault();

    const trackUri = $(this).find('input[name="track_uri"]').val();
    const playlistId = $(this).find('input[name="playlist_id"]').val();

    await axios.delete(`http://localhost:5000/playlists/${playlistId}/tracks`, {
        data: { 'track_uri': trackUri }
    })
        .then((result) => {
            console.log(result);
            $(this).closest('.card').remove();
            showAlert('Track removed from playlist.', 'success');
        })
        .catch((err) => {
            console.error(err);
            showAlert('Failed to remove track from playlist.', 'danger');
        });

});

$('#playlist_create_form').submit(async (e) => {
    e.preventDefault();

    const title = $('#playlist_title').val();
    const description = $('#playlist_description').val();

    if (!title) {
        $('#title_error').text('Title is required.');
        return;
    }

    await axios.post('http://localhost:5000/playlists', {
        title: title,
        description: description
    })
        .then((result) => {
            console.log(result);
            $('#create_playlist_modal').modal('toggle');
            showAlert('Playlist created.', 'success');

            const playlist = result.data;
            const playlistCard = `
            <div class="card mx-auto my-2" style="width: 18rem;">
                ${playlist.images && playlist.images[0] ?
                    `<img src="${playlist.images[0].url}" class="card-img-top" alt="...">` :
                    `<img src="https://cdn.pixabay.com/photo/2017/01/09/20/11/music-1967480_1280.png" class="card-img-top" alt="...">`}
                <div class="card-body">
                    <a href="/playlists/${playlist.id}">
                        <h5 class="card-title text-light">${playlist.name}</h5>
                    </a>
                    <p class="card-text text-light">${playlist.description}</p>
                </div>
            </div>`;

            $('#playlists_container').prepend(playlistCard);
        }).catch((err) => {
            console.error(err);
            $('#create_playlist_modal').modal('toggle');
            showAlert('Failed to create playlist.', 'danger');
        });


});