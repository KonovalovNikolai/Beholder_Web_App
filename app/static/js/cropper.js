var cropper = '';
var file = '';
var _URL = window.URL || window.webkitURL;

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
            console.log("imageData ", imageData);

            $(".cr-slider-wrap").show();
        }
    });
}
