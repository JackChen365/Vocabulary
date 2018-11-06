function session_list_selected(){
    $('table .session-item-class').click(function(){
        set_study_session(this.id)
    });
}
function set_session_list_selected(select_id){
    $.each($('table .session-item-class'),(index,ele)=>$(ele).removeClass('selected'));
    $(`table #${select_id}`).addClass('selected');
}

function set_study_session(id){
    let form_data = new FormData();
    form_data.append("id",id)
        $.ajax({
            type: 'POST',
            url:$("input[name=study-session-item]").val(),
            contentType:false,
            processData:false,
            cache: false,
            dataType: 'json',
            data:form_data,
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken", $("input[name=csrfmiddlewaretoken]").val())
            },
            success: function(data){
                if(data.is_valid){
                    set_session_list_selected(id)
                }
                console.info("set success:")
            },
            error: function(e){
                console.info("set failed:"+e)
            }
        })
}

window.onload=function(){
    session_list_selected();
}