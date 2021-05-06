let cropper = '';
let file = '';

$(document).ready();

function initCropper() {
    let vEl = document.getElementById('cropper-img');
    cropper = new Cropper(vEl, {
        viewMode: 3,
        dragMode: 'move',
        aspectRatio: 1,
        checkOrientation: true,
        cropBoxMovable: true,
        cropBoxResizable: true,
        zoomOnTouch: true,
        zoomOnWheel: true,
        guides: true,
        highlight: true,
        ready: function () {
            let cropper = this.cropper;
            cropper.zoomTo(0);

            let imageData = cropper.getImageData();

            $(".cr-slider-wrap").show();
        }
    });
}

$("#crop").click(function () {
    $(this).attr('disabled', 'disabled');
    if (cropper === '') {
        alert('Загрузите фото');
        $(this).attr('disabled', 'disabled');
        return false;
    }

    let canvas = cropper.getCroppedCanvas({
        width: 250,
        height: 250,
    });

    let url = $(this).attr('action');

    canvas.toBlob(function (blob) {
        let data = new FormData();
        data.append("file", blob, 'avatar.png');

        $.ajax({
            url: url,
            type: 'POST',
            cache: false,
            data: data,
            processData: false,
            contentType: false,
            success: function () {
                location.reload();
            },
            error: function (response) {
                console.log(response);
                $("#crop").removeAttr('disabled');
            }
        })
    })
});
