var cropper = '';
var file = '';

$(document).ready(function () {
    $("#cropperfile")
        .change(function (e) {
            if (file = this.files[0]) {
                var oFReader = new FileReader();
                oFReader.readAsDataURL(file);
                oFReader.onload = function () {
                    if (cropper != '') {
                        cropper.destroy()
                    }
                    $("#cropper-img").attr('src', this.result);
                    $('#cropper-img').addClass('ready');
                    initCropper();
                }
            }
        });
});

function initCropper() {
    var vEl = document.getElementById('cropper-img');
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
        ready: function (e) {
            var cropper = this.cropper;
            cropper.zoomTo(0);

            var imageData = cropper.getImageData();

            $(".cr-slider-wrap").show();
        }
    });
}

$("#crop").click(function () {
    $(this).attr('disabled', 'disabled');
    if (cropper == '') {
        alert('Загрузите фото');
        $(this).attr('disabled', 'disabled');
        return false;
    }

    canvas = cropper.getCroppedCanvas({
        width: 250,
        height: 250,
    });

    var url = $(this).attr('action');
$("#crop").removeAttr('disabled');
    canvas.toBlob(function (blob) {
        var data = new FormData();
        data.append("file", blob, 'avatar.png');

        $.ajax({
            url: url,
            type: 'POST',
            cache: false,
            data: data,
            processData: false,
            contentType: false,
            success: function (response) {
                location.reload();
            },
            error: function (response) {
                console.log(response);
                $("#crop").removeAttr('disabled');
            }
        })
    })
});
