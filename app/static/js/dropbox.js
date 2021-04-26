Dropzone.autoDiscover = false;

var myDropzone = new Dropzone(".dropzone", {
    autoProcessQueue: true,
    maxFiles: 5,
    parallelUploads: 5,
    acceptedFiles: "image/*",
    addRemoveLinks: true,
    init: function () {
        var myDropzone = this;
        $("#create").click(function (e) {
            e.preventDefault();

            if (myDropzone.getAcceptedFiles().length == 0) {
                alert("Загрузите изображения")
                return;
            }

            if (myDropzone.getRejectedFiles().length != 0) {
                alert("Уберите отклонённые изображения");
                return;
            } else {
                $(this).attr('disabled','disabled');
                $(this).attr("data-hystmodal","#myModal")
                myDropzone.disable()
                UploadImages();
            }
        });

        this.on('sending', function(file, xhr, formData) {
            let data = $('#post-info').serializeArray();
            $.each(data, function(key, el) {
                formData.append(el.name, el.value);
            });
        });

        this.on('successmultiple', function (file, response){
            console.log(response);
            var url = response['url'];
            var intervalID = setInterval(function (){
                $.ajax({
                     url: url,
                     type: 'GET',
                     dataType: 'json',
                     cache: false,
                    success: function (response){
                        if(response['done']){
                            url = response['url'];
                            clearInterval(intervalID);
                            window.location.href = url;
                        }
                    }
                });
            }, 1000);
        });
    }
});

function UploadImages() {
    // Пометить файлы как неотправленные
    myDropzone.files.forEach(function(item) {
      item.status = 'queued';
    });
    // Сменить адрес загрузки
    myDropzone.options.url = $(".dropzone").attr("upload_to");
    // Загрузить все файлы сразу
    myDropzone.options.uploadMultiple = true;
    // Начать загрузку
    myDropzone.processQueue();
}