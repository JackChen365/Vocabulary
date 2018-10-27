 function progress(e){
        if(e.lengthComputable){
            let progress = parseInt(e.loaded / e.total * 100, 10);
            let strProgress = progress + "%";
            $(".progress-bar").css({"width": strProgress});
            $(".progress-bar").text(strProgress);
        }
    }
$(document).ready(function(){
    $("#mdx_file_div").click(function(){
        return $('#mdx_file').click();
    });
    $("#mdd_file_div").click(function(){
        $("#mdd_file").click()
    });
    $("#mdx_file").change(function(e) {
        $("#mdx_file_div h3")[0].innerHTML=e.currentTarget.value
    });
    $("#mdd_file").change(function(e) {
        $("#mdd_file_div h3")[0].innerHTML=e.currentTarget.value
    });
  $("#upload_file").click(function(){
    let form_data = new FormData();
        let mdx_file = $('#mdx_file')[0].files[0];
        form_data.append('mdx_file',mdx_file);
        let mdd_file = $('#mdd_file')[0];
        if(0 < mdd_file.files.length) {
            form_data.append('mdd_file', mdd_file.files[0]);
        }
        console.info("开始发送！")
      $("#modal-progress").modal("show");
        $.ajax({
            type: 'POST',
            url: $("input[name=dict-upload-file]").val(),
            contentType:false,
            processData:false,
            data: form_data,
            cache: false,
            dataType: 'JSON',
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken", $("input[name=csrfmiddlewaretoken]").val())
            },
             xhr: function() {
                var myXhr = $.ajaxSettings.xhr();
                if(myXhr.upload){
                    myXhr.upload.addEventListener('progress',progress, false);
                }
                return myXhr;
            },
            success: function(data){
                console.info(data)
                 $("#modal-progress").modal("hide");
                if(data.is_valid){
                    $("#mdx_file_div h3")[0].innerHTML="Click here to choose mdx file!"
                    $("#mdd_file_div h3")[0].innerHTML="Click here to choose mdd file!"
                }
            },
            error: function(){
                console.info("error");
            }
        })
  });
});