$('.prove-button').click(function () {
    var button = this;
    $(this).attr('disabled', 'disabled');
    var url = $(this).data('url');

    var data = new FormData();
    data.append('id', $(this).data('id'));
    $.ajax({
        url: url,
        type: 'POST',
        cache: false,
        data: data,
        processData: false,
        contentType: false,
        success: function (response) {
            $(button).hide();
            $(button).removeAttr('disabled');
            $(button).siblings('.prove-button').show();
            let target = $(button).data('target');
            let td = $(button).parent().siblings('.prove-td');
            $(td).children().hide();
            $(td).children(target).show();
        },
        error: function (response) {
            $(button).removeAttr('disabled');
        }
    });
});

$('.delete-journal-button').click(function () {
    var button = this;
    $(this).attr('disabled', 'disabled');
    var url = $(this).data('url');

    $.ajax({
        url: url,
        type: 'DELETE',
        success: function (response) {
            $(button).closest('tr').remove();
            if ($('#visitors-table tbody').children('tr').length === 0) {
                $('#visitors-table').hide();
                $('#visitors-search').hide();
                $('#no-visitors-message').show();
            }
        },
        error: function (response) {
            $(button).removeAttr('disabled');
        }
    });
});