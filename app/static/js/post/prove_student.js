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
            $(button).parent().siblings('.prove-td').text('☑')
        },
        error: function (response) {
            alert('Что-то пошло не так.\nПопробуйте ещё раз позже.');
        }
    });
});