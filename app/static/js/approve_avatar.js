$('.approveBtn').click(function () {
    $(this).attr('disabled', 'disabled');
    var button = this;

    var url = $(this).data('url');

    $.ajax({
        url: url,
        type: 'POST',
        cache: false,
        processData: false,
        contentType: false,
        success: function (response) {
            $(button).parent().parent().hide();
        },
        error: function (response) {
            console.log(response);
        }
    })

});