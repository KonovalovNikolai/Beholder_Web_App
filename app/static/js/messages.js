$('.toast').toast();

$('.toast').on('hidden.bs.toast', function () {
    let url = $(this).data('url');

    $.ajax({
        url: url,
        type: 'DELETE'
    });
});