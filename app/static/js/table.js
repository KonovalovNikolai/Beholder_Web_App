document.addEventListener('DOMContentLoaded', () => {

    const getSort = ({target}) => {
        const order = (target.dataset.order = -(target.dataset.order || -1));
        const index = [...target.parentNode.cells].indexOf(target);
        const collator = new Intl.Collator(['en', 'ru'], {numeric: true});
        const comparator = (index, order) => (a, b) => order * collator.compare(
            a.children[index].innerHTML,
            b.children[index].innerHTML
        );

        for (const tBody of target.closest('table').tBodies)
            tBody.append(...[...tBody.rows].sort(comparator(index, order)));

        for (const cell of target.parentNode.cells)
            cell.classList.toggle('sorted', cell === target);
    };

    document.querySelectorAll('#visitors-table .sortable').forEach(tableTH => tableTH.addEventListener('click', () => getSort(event)));

});
$(document).ready(function () {
    $(".table-search").keyup(function () {
        var _this = this;
        var t_id = $(this).siblings('.searchable-table').attr('id');
        console.log(`#${t_id} tbody tr`);
        $.each($(`#${t_id} tbody tr`), function () {
            if ($(this).children('.fullname').text().toLowerCase().indexOf($(_this).val().toLowerCase()) === -1) {
                $(this).hide();
            } else {
                $(this).show();
            }
        });
    });

    $("#header-checkbox").click(function () {
        $('.body-checkbox').prop('checked', $(this).is(':checked'))
    });

    $('.body-checkbox').click(function () {
        $('#header-checkbox').prop('checked', false)
    });

    $("#accept-selected").click(function () {
        $('input.body-checkbox:checked').parent().siblings('.button-td').children('.accept-button').click()
    });

    $("#cancel-selected").click(function () {
        $('input.body-checkbox:checked').parent().siblings('.button-td').children('.cancel-button').click()
    });

    $('.request-button').click(function () {
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
                if ($(button).data('action') === 'reload') {
                    document.location.reload();
                }
                $(button).closest('tr').remove();
                if ($('#request-table tbody').children('tr').length === 0) {
                    $('#request-table').hide();
                    $('#request-search').hide();
                    $('#no-request-message').show();
                }
            },
            error: function (response) {
                alert('Что-то пошло не так.\nПопробуйте ещё раз позже.');
                $(button).removeAttr('disabled');
            }
        });
    });
});
