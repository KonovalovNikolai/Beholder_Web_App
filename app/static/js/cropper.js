var cropper = '';
var file = '';

$(document).ready(function () {
    $("#cropperfile")
        .change(function (e) {
            if (file = this.files[0]) {
                var oFReader = new FileReader();
                oFReader.readAsDataURL(file);
                oFReader.onload = function () {
                    if (cropper != ''){
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

$("#crop").click(function(){
    $(this).attr('disabled','disabled');
    if (cropper == ''){
        alert('Загрузить фото');
        return false;
    }

    canvas = cropper.getCroppedCanvas({
      width: 250,
      height: 250,
    });

    canvas.toBlob(function(blob) {
        var reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = function() {

            var url = "/api/upload_avatar/" + window.location.href.split('/')[4]
            var data = new FormData();

            blob = reader.result;
            data.append("blob", blob);

            $.ajax({
                url: url,
                type: 'POST',
                cache: false,
                data: data,
                processData: false,
                contentType: false,
                success: function(response) {
                    if(response["result"] == "Done"){
                        alert('Фото загружено');
                        document.location.reload();
                    }
                    else{
                        alert('Произошла ошибка');
                        $("#crop").removeAttr('disabled');
                    }
                },
                error: function(response) {
                    console.log(response);
                    $("#crop").removeAttr('disabled');
                }
            })
        }
    })
});
