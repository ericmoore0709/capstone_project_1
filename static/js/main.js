$('#search_input').keyup((e) => {
    e.preventDefault();
    const searchTerm = $(e.target).val().trim();

    if (!searchTerm) {
        $('#searchbar_results_list').empty();
        return;
    }

    axios.post('http://localhost:5000/searchbar', {
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

})