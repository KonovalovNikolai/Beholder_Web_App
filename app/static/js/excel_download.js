$('#excel-download').click(function () {
    var button = this;

    $(this).attr('disabled', 'disabled');

    var url = $(this).data('url');
    $.ajax({
        url: url,
        type: 'GET',
        success: function (response) {
            url = response['url'];
            var a = document.createElement('a');
            a.setAttribute('href', url);
            a.click();
            $(a).remove()
            $(button).removeAttr('disabled');
        },
    })
});