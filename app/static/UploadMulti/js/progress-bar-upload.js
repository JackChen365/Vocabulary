$(function () {
    $('.alert').hide()
    $(".js-upload-sessions").click(function () {
        let text=$(".form-control").val()
        if(text){
            $("#fileupload").click();
        } else {
            $('.alert')[0].innerText="Please Input Session Title!"
            $('.alert').removeClass("in").show();
            $(".alert").delay(2000).addClass("in").fadeOut(1000);
        }
    });
    $('#fileupload').on('fileuploadsubmit', function (e, data) {
        // The example input, doesn't have to be part of the upload form:
        let file_items=new Array();
        for ( let i = 0; i <data.originalFiles.length; i++){
            file_items.push(data.originalFiles[i].name)
        }
        const timestamp =Date.parse(new Date());
        data.formData = [
            {name:"title", value:$(".form-control").val()},
            {name:"files", value:file_items},
            {name:"timestamp", value:timestamp},
            {name:"file-length", value:file_items.length},
            { name: "csrfmiddlewaretoken", value: $("input[name=csrfmiddlewaretoken]").val()}]
    });
    $("#fileupload").fileupload({
        dataType: 'json',
        sequentialUploads: true,
        start: function (e) {
            $("#modal-progress").modal("show");
        },

        stop: function (e) {
            $("#modal-progress").modal("hide");
        },

        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            var strProgress = progress + "%";
            $(".progress-bar").css({"width": strProgress});
            $(".progress-bar").text(strProgress);
        },

        done: function (e, data) {
            if (!data.result.is_valid) {
                $('.alert')[0].innerText="Upload files fail!"
                $('.alert').removeClass("in").show();
                $(".alert").delay(2000).addClass("in").fadeOut(1000);
            } else if(data.result.is_finished){
                location.reload();
            }
        }
    });
});