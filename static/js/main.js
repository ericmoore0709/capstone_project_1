$('#search_input').keyup((e) => {
    e.preventDefault();
    const searchTerm = $(e.target).val().trim();
    const selectedTypes = $('input[type=checkbox]:checked').map(function () {
        return this.value;
    }).get();

    if (!searchTerm) {
        $('#searchbar_results_list').empty();
        return;
    }

    axios.post('http://localhost:5000/searchbar', {
        q: searchTerm,
        type: selectedTypes
    })
        .then((result) => {
            const tracks = result.data.tracks.items;
            $('#searchbar_results_list').empty();

            if (tracks.length > 0) {
                tracks.forEach((track) => {
                    let $li = $('<li></li>').addClass('list-group-item').text(track.name);
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