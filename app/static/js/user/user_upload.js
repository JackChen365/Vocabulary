$(document).ready(function(){
    $("#export_file_div").click(function(){
        return $('#export_file').click();
    });
    $("#unknown_file_div").click(function(){
        $("#unknown_file").click()
    });
    $("#export_file").change(function(e) {
        $("#export_file_div h3")[0].innerHTML=e.currentTarget.value
    });
    $("#unknown_file").change(function(e) {
        $("#unknown_file_div h3")[0].innerHTML=e.currentTarget.value
    });
  $("#upload_file").click(function(){
    let form_data = new FormData();
        let export_file = $('#export_file')[0].files[0];
        form_data.append('export_file',export_file);
        let unknown_file = $('#unknown_file')[0];
        if(0 < unknown_file.files.length){
            form_data.append('unknown_file',unknown_file.files[0]);
        }
        console.info("开始发送！")
      $("#modal-progress").modal("show");
        $.ajax({
            type: 'POST',
            url: $(".user-upload-file").val(),
            contentType:false,
            processData:false,
            data: form_data,
            cache: false,
            dataType: 'JSON',
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken", $("input[name=csrfmiddlewaretoken]").val())
            },
            success: function(data){
                console.info(data)
                 $("#modal-progress").modal("hide");
                if(data.is_valid){
                    $("#export_file_div h3")[0].innerHTML="Click here to choose source file!"
                    $("#unknown_file_div h3")[0].innerHTML="Click here to choose unknown file!"
                }
            },
            error: function(){
                console.info("error");
            }
        })
  });
});